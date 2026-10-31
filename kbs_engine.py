"""
kbs_engine.py - Knowledge-Based System Engine
Domain: Industrial Centrifugal Pump Fault Diagnosis & Auto Logging
"""

import os
import json
from difflib import SequenceMatcher
from datetime import datetime

LOGS_FILE = "audit_logs.json"

# 1. Dictionary (English aur Roman Urdu dono ke liye)
SYMPTOM_MAP = {
    "vibration": ["vibration", "shake", "kanp", "hilna", "jhatkay", "larza", "shaking"],
    "overheating": ["hot", "garam", "tapna", "heat", "jalna", "warm", "overheating"],
    "grinding_noise": ["grind", "screech", "shor", "cheekh", "ghisna", "raghar", "grinding"],
    "gravel_noise": ["gravel", "popping", "pathar", "bajri", "bubbles", "cavitation"],
    "seal_leakage": ["leak", "drip", "tapak", "pani", "oil", "fluid", "leaking"],
    "low_flow": ["flow", "pressure", "kam", "ruk", "low flow", "low pressure"]
}

# 2. Production Rules (Knowledge Base)
KNOWLEDGE_BASE = [
    {
        "id": "RULE_1",
        "fault": "Shaft Bearing Degradation & Lubrication Breakdown",
        "component": "Drive-End / Non-Drive End Ball Bearings",
        "subsystem": "Rotating Assembly",
        "target_component": "bearings",
        "severity": "Critical Severity",
        "symptoms": ["vibration", "overheating", "grinding_noise"],
        "min_vibration": 6.5,  # mm/s RMS (ISO limit)
        "min_temp": 75,        # °C
        "base_cf": 0.90,
        "action_safety": "Immediate emergency shutdown. Isolate pump, lock out power (LOTO), and replace worn ball bearings.",
        "action_uptime": "Throttle motor load to 60%, engage cooling line, and schedule repair for shift change.",
        "downtime": "3 - 4 Hours",
        "urgency_safety": "Emergency Stop Required",
        "urgency_uptime": "Controlled Throttling",
        "reason": "Tez vibration aur garam casing ke sath grinding awaaz aana bearing damage ki nishani hai."
    },
    {
        "id": "RULE_2",
        "fault": "Hydraulic Cavitation & Vapor Bubble Collapse",
        "component": "Closed Impeller Blades & Suction Volute",
        "subsystem": "Hydraulic Wet-End",
        "target_component": "impeller",
        "severity": "Severe Wear",
        "symptoms": ["gravel_noise", "low_flow", "vibration"],
        "min_vibration": 4.5,
        "min_temp": 0,
        "base_cf": 0.88,
        "action_safety": "Throttle discharge valve, inspect suction basket strainer, and verify NPSH.",
        "action_uptime": "Open suction line bypass valve to equalize fluid pressure without halting the line.",
        "downtime": "1 - 2 Hours",
        "urgency_safety": "High Priority Action",
        "urgency_uptime": "Monitor closely",
        "reason": "Kankad/pathar jaisi popping awaaz aur flow kam hona cavitation (bubbles collapse) ka saboot hai."
    },
    {
        "id": "RULE_3",
        "fault": "Mechanical Seal Breakdown & Packing Breach",
        "component": "Silicon Carbide Seal Faces",
        "subsystem": "Shaft Sealing Assembly",
        "target_component": "seal",
        "severity": "High Hazard",
        "symptoms": ["seal_leakage", "overheating"],
        "min_vibration": 2.5,
        "min_temp": 68,
        "base_cf": 0.85,
        "action_safety": "Stop pump to prevent fluid pooling. Drain volute casing and install pre-tested cartridge seal assembly.",
        "action_uptime": "Divert flow to secondary standby pump unit (Asset #P-104B) and overhaul primary pump.",
        "downtime": "2 - 3 Hours",
        "urgency_safety": "Emergency Stop Required",
        "urgency_uptime": "Switch to Standby",
        "reason": "Shaft ke paas se liquid nikalna aur garam hona mechanical seal tootne ki nishani hai."
    },
    {
        "id": "RULE_4",
        "fault": "Dynamic Shaft Misalignment & Soft-Foot",
        "component": "Flexible Elastomeric Coupling",
        "subsystem": "Power Transmission",
        "target_component": "coupling",
        "severity": "Moderate Severity",
        "symptoms": ["vibration", "overheating"],
        "min_vibration": 5.0,
        "min_temp": 65,
        "base_cf": 0.82,
        "action_safety": "De-energize motor. Uncouple shafts, inspect rubber spider, and realign shaft centerlines with laser tool.",
        "action_uptime": "Tighten base-plate anchor bolts and continue running at reduced load until shift end.",
        "downtime": "1.5 - 2 Hours",
        "urgency_safety": "Scheduled Stop Required",
        "urgency_uptime": "Temporary Run",
        "reason": "Bina kisi grinding awaz ke lagataar vibration hona motor aur pump ki sedh out hone ki nishani hai."
    }
]

# 3. Spelling / Fuzzy Similarity Matcher
def is_similar(w1, w2, threshold=0.75):
    """Do lafzon ka match ratio nikaalta hai (75% match ho toh True)."""
    return SequenceMatcher(None, w1, w2).ratio() >= threshold

# 4. Smart Symptom Extractor
def extract_symptoms_smart(user_text):
    found_symptoms = set()
    user_words = user_text.lower().split()

    for symptom, standard_words in SYMPTOM_MAP.items():
        for std_word in standard_words:
            if std_word in user_text.lower():
                found_symptoms.add(symptom)
                break
            matched = False
            for u_word in user_words:
                if is_similar(u_word, std_word, threshold=0.75):
                    found_symptoms.add(symptom)
                    matched = True
                    break
            if matched:
                break

    return list(found_symptoms)

# 5. Logs Functions (JSON Save & Read)
def get_all_logs():
    """File se saare puraane logs parhta hai."""
    if not os.path.exists(LOGS_FILE):
        return []
    try:
        with open(LOGS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_log(entry):
    """Naye diagnosis ko JSON file mein append karta hai."""
    logs = get_all_logs()
    logs.insert(0, entry) # Sabse naya log upar aayega
    with open(LOGS_FILE, "w") as f:
        json.dump(logs, f, indent=4)

# 6. Main Forward Chaining Inference Function
def diagnose_fault(user_text="", selected_symptoms=None, selected_components=None, vibration=None, temp=None, priority="safety"):
    selected_symptoms = selected_symptoms or []
    selected_components = selected_components or []
    
    text_symptoms = extract_symptoms_smart(user_text)
    all_active_symptoms = set(selected_symptoms).union(set(text_symptoms))
    active_components = set(selected_components)

    try:
        vib_val = float(vibration) if vibration not in (None, "") else 0.0
    except ValueError:
        vib_val = 0.0

    try:
        temp_val = float(temp) if temp not in (None, "") else 0.0
    except ValueError:
        temp_val = 0.0

    if not all_active_symptoms and not active_components and vib_val == 0.0 and temp_val == 0.0:
        return {
            "success": False,
            "message": "Please provide problem description, select symptoms, or input sensor readings."
        }

    best_rule = None
    highest_score = 0
    telemetry_logs = []

    for rule in KNOWLEDGE_BASE:
        rule_syms = set(rule["symptoms"])
        matched_syms = all_active_symptoms.intersection(rule_syms)
        sym_score = len(matched_syms) / len(rule_syms) if rule_syms else 0

        comp_bonus = 0.15 if rule["target_component"] in active_components else 0.0

        sensor_score = 0.0
        cur_logs = []
        if vib_val > 0:
            if vib_val >= rule["min_vibration"]:
                sensor_score += 0.5
                cur_logs.append(f"Vibration velocity ({vib_val} mm/s) breaches ISO limit (>= {rule['min_vibration']} mm/s).")
            else:
                cur_logs.append(f"Vibration velocity ({vib_val} mm/s) is within acceptable range.")

        if temp_val > 0:
            if temp_val >= rule["min_temp"] and rule["min_temp"] > 0:
                sensor_score += 0.5
                cur_logs.append(f"Bearing temperature ({temp_val}°C) exceeds thermal limit (>= {rule['min_temp']}°C).")
            elif rule["min_temp"] > 0:
                cur_logs.append(f"Bearing temperature ({temp_val}°C) is normal.")

        total_cf = (rule["base_cf"] * sym_score * 0.6) + (sensor_score * 0.25) + comp_bonus
        final_percent = min(round(total_cf * 100), 96)

        if final_percent > highest_score:
            highest_score = final_percent
            best_rule = rule
            telemetry_logs = cur_logs

    if not best_rule or highest_score < 25:
        return {
            "success": True,
            "fault": "Normal Mechanical Operation / Undetermined",
            "component": "Centrifugal Pump (Asset #P-104)",
            "subsystem": "General Equipment",
            "severity": "Normal Baseline",
            "confidence": 35,
            "action": "Maintain scheduled routine inspections. No critical fault patterns matched.",
            "urgency": "Routine Inspection",
            "downtime": "0 Minutes",
            "timestamp": datetime.now().strftime("%d %b, %I:%M %p"),
            "explanations": [
                "Observed evidence does not breach critical safety limits in the rule base.",
                f"Active symptoms evaluated: {list(all_active_symptoms) if all_active_symptoms else 'None'}"
            ]
        }

    is_safety = (priority == "safety")
    action_text = best_rule["action_safety"] if is_safety else best_rule["action_uptime"]
    urgency_text = best_rule["urgency_safety"] if is_safety else best_rule["urgency_uptime"]

    explanations = [
        f"Rule Triggered: {best_rule['id']} ({best_rule['fault']})",
        best_rule["reason"]
    ]
    explanations.extend(telemetry_logs)
    if is_safety:
        explanations.append("Stakeholder Constraint: Zero-risk Safety Priority enforced (Emergency shutdown recommended).")
    else:
        explanations.append("Stakeholder Constraint: Production Uptime Continuity prioritized (Load throttling recommended).")

    output = {
        "success": True,
        "fault": best_rule["fault"],
        "component": best_rule["component"],
        "subsystem": best_rule["subsystem"],
        "severity": best_rule["severity"],
        "confidence": highest_score,
        "action": action_text,
        "urgency": urgency_text,
        "downtime": best_rule["downtime"],
        "timestamp": datetime.now().strftime("%d %b, %I:%M %p"),
        "explanations": explanations
    }

    # Automatically audit log mein entry save kardo
    all_current = get_all_logs()
    save_log({
        "id": f"#LOG-{1000 + len(all_current) + 1}",
        "timestamp": output["timestamp"],
        "asset": f"P-104 ({best_rule['target_component'].title()})",
        "fault": output["fault"],
        "confidence": f"{output['confidence']}%",
        "action": output["action"][:40] + "...",
        "severity": output["severity"]
    })

    return output