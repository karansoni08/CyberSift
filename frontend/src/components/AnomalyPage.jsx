import { useRef, useState } from "react";
import { extract } from "../api/client.js";

const SEVERITY_META = {
  high: { label: "High", icon: "🔴", blurb: "likely active compromise or exposure — act now" },
  medium: { label: "Medium", icon: "🟠", blurb: "suspicious deviation worth investigating" },
  low: { label: "Low", icon: "🟡", blurb: "notable oddity — review when convenient" },
};

const ORDER = { high: 0, medium: 1, low: 2 };

function NoveltyBadge({ f }) {
  if (f.novel === true) return <span className="novelty-badge new">🆕 first time seen</span>;
  if (f.novel === false)
    return (
      <span className="novelty-badge known">
        seen in {f.times_seen} previous scan{f.times_seen === 1 ? "" : "s"}
      </span>
    );
  return null;
}

function AnomalyCard({ f, open }) {
  const meta = SEVERITY_META[f.severity] || { label: "Unrated", icon: "⚪", blurb: "" };
  return (
    <details className={"finding-card severity-" + (f.severity || "none")} open={open}>
      <summary className="finding-row">
        <span className="severity-tag">{meta.icon} {meta.label}</span>
        <span className="subtype-label">{f.subtype}</span>
        <code className="finding-value">{f.value}</code>
        <NoveltyBadge f={f} />
        <span className="confidence-badge">{Math.round(f.confidence * 100)}%</span>
      </summary>
      <div className="finding-details">
        <div><span className="detail-label">Why it's anomalous:</span> {f.reasoning}</div>
        <div><span className="detail-label">Evidence in your data:</span> <code>{f.original_form}</code></div>
        {f.novel === false && f.first_seen && (
          <div><span className="detail-label">Corpus history:</span> first seen {f.first_seen.slice(0, 10)}, in {f.times_seen} previous scan{f.times_seen === 1 ? "" : "s"}</div>
        )}
        {meta.blurb && <div><span className="detail-label">Severity meaning:</span> {meta.blurb}</div>}
      </div>
    </details>
  );
}

export default function AnomalyPage({ onBack }) {
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const fileInputRef = useRef(null);

  const scan = async () => {
    if (busy || (!text.trim() && !file)) return;
    setBusy(true);
    setError(null);
    try {
      setResult(await extract({ text: text.trim(), file, categories: ["anomaly"], format: "auto" }));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const findings = (result?.findings || [])
    .slice()
    .sort((a, b) => (ORDER[a.severity] ?? 3) - (ORDER[b.severity] ?? 3) || b.confidence - a.confidence);
  const counts = { high: 0, medium: 0, low: 0 };
  for (const f of findings) if (counts[f.severity] !== undefined) counts[f.severity]++;

  return (
    <main className="chat-window anomaly-page">
      <div className="top-bar anomaly-top-bar">
        <span className="chips-label">Anomaly Detection</span>
        <button className="anomaly-top-btn" onClick={onBack}>◈ Back to chat</button>
      </div>
      <div className="anomaly-header">
        <h1>🔍 Anomaly Detection</h1>
        <p>
          Detect the unknown: give CyberSift data in <strong>any format</strong> — logs, CSV/JSON exports, configs,
          reports — and it profiles the data's own patterns, then warns you about deviations nothing has flagged as
          malicious yet. Every warning cites verbatim evidence from your data. Anomaly ≠ confirmed malicious: findings
          are ranked leads, judge them in context.
        </p>
      </div>

      <div className="anomaly-input">
        <input ref={fileInputRef} type="file" hidden onChange={(e) => setFile(e.target.files[0] || null)} />
        <div className="anomaly-input-row">
          <button className="attach-btn" onClick={() => fileInputRef.current?.click()}>
            📎 {file ? file.name : "Upload data (any format)"}
          </button>
          {file && (
            <button
              className="remove-attachment"
              onClick={() => {
                setFile(null);
                if (fileInputRef.current) fileInputRef.current.value = "";
              }}
            >
              ✕ remove
            </button>
          )}
        </div>
        <textarea
          className="anomaly-textarea"
          placeholder="…or paste raw data here (logs, records, config content)"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={7}
        />
        <button className="scan-btn" disabled={busy || (!text.trim() && !file)} onClick={scan}>
          {busy ? "Scanning… this can take a couple of minutes for large data" : "🔍 Scan for anomalies"}
        </button>
        {error && <div className="message-error">⚠ {error}</div>}
      </div>

      {result && (
        <div className="anomaly-results">
          {findings.length === 0 ? (
            <div className="anomaly-banner clean">
              ✅ No anomalies detected in {result.characters.toLocaleString()} characters ({result.chunks} chunk
              {result.chunks === 1 ? "" : "s"} analyzed). The data looks internally consistent.
            </div>
          ) : (
            <>
              <div className={"anomaly-banner " + (counts.high ? "high" : counts.medium ? "medium" : "low")}>
                {counts.high
                  ? `⚠ ${counts.high} high-severity anomal${counts.high === 1 ? "y" : "ies"} detected — possible active compromise or exposure. Investigate first.`
                  : counts.medium
                    ? `${counts.medium} medium-severity anomal${counts.medium === 1 ? "y" : "ies"} detected — suspicious deviations worth investigating.`
                    : `${findings.length} low-severity oddit${findings.length === 1 ? "y" : "ies"} noted — review when convenient.`}
              </div>
              <div className="anomaly-metrics">
                <span>🔴 High: {counts.high}</span>
                <span>🟠 Medium: {counts.medium}</span>
                <span>🟡 Low: {counts.low}</span>
                <span>🆕 Never seen before: {findings.filter((f) => f.novel === true).length}</span>
                <span>Analyzed: {result.characters.toLocaleString()} chars</span>
                {result.corpus && <span>Corpus memory: {result.corpus.scans} prior scan{result.corpus.scans === 1 ? "" : "s"}, {result.corpus.known_values} known values</span>}
              </div>
              {findings.filter((f) => f.severity !== "low").map((f, i) => (
                <AnomalyCard key={i} f={f} open={f.severity === "high"} />
              ))}
              {counts.low > 0 && (
                <details className="low-group">
                  <summary className="low-group-summary">
                    🟡 {counts.low} low-severity oddit{counts.low === 1 ? "y" : "ies"} (collapsed — click to review)
                  </summary>
                  {findings.filter((f) => f.severity === "low").map((f, i) => (
                    <AnomalyCard key={i} f={f} open={false} />
                  ))}
                </details>
              )}
              <button
                className="scan-btn secondary"
                onClick={() => {
                  const blob = new Blob([JSON.stringify(findings, null, 2)], { type: "application/json" });
                  const a = Object.assign(document.createElement("a"), {
                    href: URL.createObjectURL(blob),
                    download: "cybersift-anomalies.json",
                  });
                  a.click();
                  URL.revokeObjectURL(a.href);
                }}
              >
                Download anomaly report (JSON)
              </button>
            </>
          )}
          {result.errors?.map((e, i) => (
            <div key={i} className="message-error">⚠ {e}</div>
          ))}
        </div>
      )}
    </main>
  );
}
