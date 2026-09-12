function ConfidenceBadge({ value }) {
  const level = value >= 0.85 ? "high" : value >= 0.6 ? "medium" : "low";
  return <span className={"confidence-badge " + level}>{Math.round(value * 100)}%</span>;
}

function FindingsBlock({ findings }) {
  // Group generically by category + subtype — no category-specific logic here.
  const groups = {};
  for (const f of findings) {
    const key = f.category ? `${f.category} · ${f.subtype}` : f.subtype;
    (groups[key] = groups[key] || []).push(f);
  }

  return (
    <div className="findings">
      {Object.entries(groups).map(([subtype, items]) => (
        <div key={subtype} className="findings-group">
          <div className="findings-group-header">
            <span className="subtype-label">{subtype}</span>
            <span className="findings-count">{items.length}</span>
          </div>
          {items.map((f, i) => (
            <details key={i} className="finding-card">
              <summary className="finding-row">
                <code className="finding-value">{f.value}</code>
                {f.novel === true && <span className="novelty-badge new">🆕</span>}
                {f.novel === false && <span className="novelty-badge known">{f.times_seen}× before</span>}
                <ConfidenceBadge value={f.confidence} />
              </summary>
              <div className="finding-details">
                {f.original_form && f.original_form !== f.value && (
                  <div>
                    <span className="detail-label">As seen in source:</span> <code>{f.original_form}</code>
                  </div>
                )}
                <div>
                  <span className="detail-label">Reasoning:</span> {f.reasoning}
                </div>
              </div>
            </details>
          ))}
        </div>
      ))}
    </div>
  );
}

export default function MessageBubble({ message }) {
  return (
    <div className={"message-row " + message.role}>
      <div className={"message-bubble " + message.role}>
        {message.attachment && <div className="attachment-chip">📄 {message.attachment}</div>}
        {message.text && <div className="message-text">{message.text}</div>}
        {message.error && <div className="message-error">⚠ {message.error}</div>}
        {message.findings && message.findings.length > 0 && <FindingsBlock findings={message.findings} />}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="tool-calls-note">🛠 Tools used: {message.toolCalls.join(", ")}</div>
        )}
        {message.errors && message.errors.length > 0 && (
          <div className="message-error">{message.errors.map((e, i) => (
            <div key={i}>⚠ {e}</div>
          ))}</div>
        )}
      </div>
    </div>
  );
}
