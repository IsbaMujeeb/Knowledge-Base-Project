document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("diagnosisForm");
    const problemText = document.getElementById("problemDescription");
    const idleState = document.getElementById("idleState");
    const resultState = document.getElementById("resultState");
    const resetBtn = document.getElementById("resetBtn");

    // Component Chips Click Handler
    const compChips = document.querySelectorAll(".comp-chip");
    compChips.forEach(chip => {
        chip.addEventListener("click", () => {
            chip.classList.toggle("active");
            const comp = chip.getAttribute("data-component");
            if (chip.classList.contains("active")) {
                if (!problemText.value.toLowerCase().includes(comp)) {
                    problemText.value = (problemText.value + " Suspected issue around " + comp + ".").trim();
                }
            }
        });
    });

    // Reset Button
    resetBtn.addEventListener("click", () => {
        form.reset();
        compChips.forEach(c => c.classList.remove("active"));
        resultState.style.display = "none";
        idleState.style.display = "flex";
    });

    // Quick Sample Scenarios
    window.loadSample = (scenario) => {
        form.reset();
        compChips.forEach(c => c.classList.remove("active"));

        if (scenario === 'bearing') {
            problemText.value = "The pump is vibrating violently and the casing is extremely hot with a screeching sound.";
            document.querySelector('input[value="vibration"]').checked = true;
            document.querySelector('input[value="overheating"]').checked = true;
            document.querySelector('input[value="grinding_noise"]').checked = true;
            document.getElementById("vibrationValue").value = "7.8";
            document.getElementById("tempValue").value = "86";
            document.querySelector('[data-component="bearings"]').classList.add("active");
        } else if (scenario === 'cavitation') {
            problemText.value = "Sounds like marbles or gravel inside pump chamber, flow rate has dropped significantly.";
            document.querySelector('input[value="gravel_noise"]').checked = true;
            document.querySelector('input[value="low_flow"]').checked = true;
            document.getElementById("vibrationValue").value = "4.2";
            document.querySelector('[data-component="impeller"]').classList.add("active");
        } else if (scenario === 'seal') {
            problemText.value = "Noticeable continuous fluid dripping near shaft sleeve with warm casing.";
            document.querySelector('input[value="leakage"]').checked = true;
            document.querySelector('input[value="overheating"]').checked = true;
            document.querySelector('[data-component="seal"]').classList.add("active");
        }
    };

    // Form Submit Event (Asli Backend Call)
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const submitBtn = document.getElementById("submitBtn");
        const originalBtnHtml = submitBtn.innerHTML;

        const selectedSymptoms = Array.from(document.querySelectorAll('input[name="symptom"]:checked')).map(cb => cb.value);
        const selectedComponents = Array.from(document.querySelectorAll('.comp-chip.active')).map(c => c.getAttribute("data-component"));
        const textVal = problemText.value.trim();
        const vibVal = document.getElementById("vibrationValue").value;
        const tempVal = document.getElementById("tempValue").value;
        const priorityVal = document.querySelector('input[name="priority"]:checked')?.value || "safety";

        if (selectedSymptoms.length === 0 && selectedComponents.length === 0 && !textVal && !vibVal && !tempVal) {
            alert("Please provide problem details, select symptoms, or input sensor readings.");
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Reasoning in Progress...`;

        try {
            // Python Backend ko Request bhejna
            const response = await fetch("/api/diagnose", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    text: textVal,
                    symptoms: selectedSymptoms,
                    components: selectedComponents,
                    vibration: vibVal,
                    temp: tempVal,
                    priority: priorityVal
                })
            });

            const data = await response.json();

            if (!data.success) {
                alert(data.message || "Diagnosis could not be completed.");
                return;
            }

            // Results screen par set karna
            document.getElementById("faultTitle").textContent = data.fault;
            document.getElementById("componentName").innerHTML = `<i class="fa-solid fa-gears"></i> Subsystem: <strong>${data.component} (${data.subsystem})</strong>`;
            document.getElementById("severityLevel").textContent = data.severity;
            document.getElementById("confidenceValue").textContent = `${data.confidence}%`;
            document.getElementById("actionDescription").textContent = data.action;

            document.getElementById("urgencyBox").innerHTML = `<i class="fa-solid fa-bell"></i> <span>Urgency: <strong>${data.urgency}</strong></span>`;
            document.getElementById("downtimeBox").innerHTML = `<i class="fa-solid fa-clock"></i> <span>Est. Repair Time: <strong>${data.downtime}</strong></span>`;

            // Explanation Trace
            const traceList = document.getElementById("inferenceTraceList");
            traceList.innerHTML = "";
            data.explanations.forEach(exp => {
                const li = document.createElement("li");
                li.innerHTML = `<i class="fa-solid fa-check text-cyan" style="margin-right: 6px; color: #06b6d4;"></i> ${exp}`;
                traceList.appendChild(li);
            });

            idleState.style.display = "none";
            resultState.style.display = "flex";

        } catch (error) {
            console.error("Diagnosis Error:", error);
            alert("Failed to communicate with the KBS server.");
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnHtml;
        }
    });
});