from flask import Flask, render_template, request, jsonify
from kbs_engine import diagnose_fault, get_all_logs

app = Flask(__name__)

@app.route("/")
def home():
    """Page 1: Live Diagnostics Terminal"""
    return render_template("index.html")

@app.route("/knowledge")
def knowledge_page():
    """Page 2: Knowledge Base & Rules Table"""
    return render_template("knowledge.html")

@app.route("/analytics")
def analytics_page():
    """Page 3: Dynamic Logs aur Calculated Health Score"""
    logs = get_all_logs()
    total_logs = len(logs)
    
    # Real health score: Jitne critical faults zyada hon, health score utna kam
    critical_count = sum(1 for log in logs if "Critical" in log.get("severity", ""))
    health_score = max(100 - (critical_count * 8), 45) if total_logs > 0 else 98

    return render_template(
        "analytics.html", 
        logs=logs, 
        total_logs=total_logs, 
        health_score=health_score
    )

@app.route("/api/diagnose", methods=["POST"])
def run_diagnosis():
    """API Endpoint: Frontend ka data le kar engine ko chalata hai"""
    data = request.get_json() or {}

    user_text = data.get("text", "")
    symptoms = data.get("symptoms", [])
    components = data.get("components", [])
    vibration = data.get("vibration", "")
    temp = data.get("temp", "")
    priority = data.get("priority", "safety")

    result = diagnose_fault(
        user_text=user_text,
        selected_symptoms=symptoms,
        selected_components=components,
        vibration=vibration,
        temp=temp,
        priority=priority
    )
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5000)