import { CATEGORIES } from "../categories.js";

export default function Sidebar({
  activeTab,
  onTabChange,
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewAnalysis,
  onDeleteConversation,
  anomalyActive,
  onOpenAnomaly,
}) {
  const visible = conversations.filter((c) => c.category === activeTab);

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="brand-mark">◈</span>
        <span className="brand-name">CyberSift</span>
      </div>

      <button className="new-chat-btn" onClick={onNewAnalysis}>+ New analysis</button>

      <nav className="sidebar-tabs">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            className={"sidebar-tab" + (activeTab === cat.id ? " active" : "")}
            style={activeTab === cat.id ? { "--tab-color": cat.color } : undefined}
            onClick={() => onTabChange(cat.id)}
          >
            {cat.label}
          </button>
        ))}
        <button
          className={"sidebar-tab anomaly-tab" + (anomalyActive ? " active" : "")}
          style={anomalyActive ? { "--tab-color": "#e08a3c" } : undefined}
          onClick={onOpenAnomaly}
        >
          🔍 Anomaly Detection
        </button>
      </nav>

      <div className="conversation-list">
        {visible.length === 0 && <div className="conversation-empty">No conversations yet</div>}
        {visible.map((conv) => (
          <div key={conv.id} className={"conversation-item" + (conv.id === activeConversationId ? " active" : "")}>
            <button className="conversation-select" onClick={() => onSelectConversation(conv.id)}>
              <div className="conversation-title">{conv.title}</div>
              <div className="conversation-date">{conv.date}</div>
            </button>
            <button
              className="conversation-delete"
              title="Delete conversation"
              onClick={() => onDeleteConversation(conv.id)}
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}
