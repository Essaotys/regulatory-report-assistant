import React, { useState, useEffect } from "react";

export default function App() {
  const [report, setReport] = useState("");
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

//This is the URL of the backend server (FastAPI) running locally on port 8000.
  const backendBase = "http://127.0.0.1:8000";


//This method is responsible for sending the report to backend /process-report,Save the response in 'result'
// and refresh the report history
  const handleProcess = async () => {
    try {
      const res = await fetch(`${backendBase}/process-report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report })
      });
      const data = await res.json();
      setResult(data);
      fetchHistory();
    } catch (err) {
      console.error(err);
      alert("Error contacting backend. Make sure backend is running on port 8000.");
    }
  };

// Fetches the latest reports from the backend and updates the history state with the data.
  const fetchHistory = async () => {
    try {
      const res = await fetch(`${backendBase}/reports`);
      const data = await res.json();
      setHistory(data);
    } catch (err) {
      console.error(err);
    }
  };

//Sends a request to the backend to translate a given text (text) into a chosen language (lang).
//Languages supported in the buttons are French (fr) and Swahili (sw).
  const handleTranslate = async (text, lang) => {
    try {
      const res = await fetch(`${backendBase}/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, lang })
      });
      const data = await res.json();
      alert(`Translation (${lang}): ${data.translation}`);
    } catch (err) {
      console.error(err);
    }
  };
//Fetches the history of reports once when the component mounts.
  useEffect(() => {
    fetchHistory();
  }, []);

//Renders the UI components including textarea for report input, buttons for processing and translating and the History table.,
  return (
    <div style={{ padding: 20, fontFamily: "Arial, sans-serif" }}>
      <h1>Regulatory Report Assistant</h1>

      <textarea
        rows={6}
        cols={80}
        placeholder="Paste an adverse event report here..."
        value={report}
        onChange={(e) => setReport(e.target.value)}
      />
      <br />
      <button onClick={handleProcess} style={{ marginTop: 10, padding: "8px 12px" }}>
        Process Report
      </button>

      {result && (
        <div style={{ marginTop: 20 }}>
          <h3>Result</h3>
          <p><strong>Drug:</strong> {result.drug}</p>
          <p><strong>Adverse Events:</strong> {result.adverse_events && result.adverse_events.join(", ")}</p>
          <p><strong>Severity:</strong> {result.severity}</p>
          <p><strong>Outcome:</strong> {result.outcome}</p>
          <button onClick={() => handleTranslate(result.outcome, "fr")}>Translate Outcome (FR)</button>
          <button onClick={() => handleTranslate(result.outcome, "sw")} style={{ marginLeft: 8 }}>Translate Outcome (SW)</button>
        </div>
      )}

      <div style={{ marginTop: 30 }}>
        <h3>History (latest 10)</h3>
        <table border="1" cellPadding="6">
          <thead>
            <tr>
              <th>ID</th><th>Drug</th><th>Events</th><th>Severity</th><th>Outcome</th><th>Created At</th>
            </tr>
          </thead>
          <tbody>
            {history.slice(0,10).map((r) => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{r.drug}</td>
                <td>{r.adverse_events && r.adverse_events.join(", ")}</td>
                <td>{r.severity}</td>
                <td>{r.outcome}</td>
                <td>{r.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}