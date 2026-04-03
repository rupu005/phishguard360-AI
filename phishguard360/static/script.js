let currentResult = "";

async function analyzeEmail() {
    const email = document.getElementById("emailInput").value.trim();
    if (!email) return alert("Please paste an email first!");

    document.getElementById("loading").style.display = "block";
    document.getElementById("results").style.display = "none";
    document.getElementById("exportBtn").style.display = "none";

    await new Promise(r => setTimeout(r, 3000)); 

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email })
        });

        const data = await response.json();
        currentResult = data.result;

        const resultBox = document.getElementById("resultText");

        
        if (currentResult.toLowerCase().includes("phishing")) {
            resultBox.className = "phishing-box";
            resultBox.innerText = "⚠ " + currentResult;
        } else {
            resultBox.className = "safe-box";
            resultBox.innerText = "✔ " + currentResult;
        }

        document.getElementById("results").style.display = "block";
        document.getElementById("exportBtn").style.display = "block";

    } catch (err) {
        alert("Error: " + err.message);
    }

    document.getElementById("loading").style.display = "none";
}



async function exportResult() {
    const response = await fetch("/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            email: document.getElementById("emailInput").value,
            result: currentResult
        })
    });

    const blob = await response.blob();
    const link = document.createElement("a");
    link.href = window.URL.createObjectURL(blob);
    link.download = "Phishing_Report.pdf";
    link.click();
}