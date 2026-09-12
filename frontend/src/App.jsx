import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import ChatWindow from "./components/ChatWindow.jsx";
import AnomalyPage from "./components/AnomalyPage.jsx";
import { chat, ingest } from "./api/client.js";

const STORAGE_KEY = "cybersift.conversations.v2";

function loadConversations() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveConversations(conversations) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
  } catch {
    // storage unavailable (private window, quota) — conversations just won't persist
  }
}

export default function App() {
  const [view, setView] = useState("chat"); // "chat" | "anomaly"
  const [conversations, setConversations] = useState(loadConversations);
  const [activeTab, setActiveTab] = useState("ioc");
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [selectedCategories, setSelectedCategories] = useState(["ioc"]);
  const [busy, setBusy] = useState(false);

  useEffect(() => saveConversations(conversations), [conversations]);

  const conversation = conversations.find((c) => c.id === activeConversationId) || null;

  const toggleCategory = (id) =>
    setSelectedCategories((prev) => (prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]));

  const appendMessage = (convId, message) =>
    setConversations((prev) =>
      prev.map((c) => (c.id === convId ? { ...c, messages: [...c.messages, message] } : c))
    );

  const setConversationDocument = (convId, document) =>
    setConversations((prev) => prev.map((c) => (c.id === convId ? { ...c, document } : c)));

  const send = async ({ text, file, format }) => {
    if (busy) return;
    setBusy(true);
    try {
      // Ensure a conversation exists.
      let convId = activeConversationId;
      let conv = conversations.find((c) => c.id === convId) || null;
      if (!conv) {
        convId = "conv-" + Date.now();
        conv = {
          id: convId,
          category: selectedCategories[0] || activeTab,
          title: file ? file.name : text.slice(0, 60) || "New analysis",
          date: new Date().toLocaleDateString(),
          document: null,
          messages: [],
        };
        setConversations((prev) => [conv, ...prev]);
        setActiveTab(conv.category);
        setActiveConversationId(convId);
      }

      // If a file is attached, convert it to text first — it becomes the
      // conversation's document that the agent's tools operate on.
      let document = conv.document;
      if (file) {
        const loaded = await ingest({ file, format });
        document = { filename: loaded.filename, text: loaded.text };
        setConversationDocument(convId, document);
      }

      const userText =
        text ||
        (file ? "I attached a document. Extract the selected categories from it." : "");
      const hint =
        selectedCategories.length > 0 ? `\n\n(Categories selected in the UI: ${selectedCategories.join(", ")})` : "";

      appendMessage(convId, { role: "user", text: userText, attachment: file ? file.name : undefined });

      const history = [...conv.messages, { role: "user", text: userText + hint }].map((m) => ({
        role: m.role === "bot" ? "assistant" : m.role,
        content: m.text || "(see findings above)",
      }));

      const result = await chat({ messages: history, document });
      appendMessage(convId, {
        role: "bot",
        text: result.reply,
        findings: result.findings,
        toolCalls: result.tool_calls,
      });
    } catch (err) {
      if (activeConversationId) {
        appendMessage(activeConversationId, { role: "bot", error: err.message });
      }
    } finally {
      setBusy(false);
    }
  };

  const deleteConversation = (id) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (id === activeConversationId) setActiveConversationId(null);
  };

  return (
    <div className="app-layout">
      <Sidebar
        activeTab={activeTab}
        onTabChange={(tab) => {
          setView("chat");
          setActiveTab(tab);
          setActiveConversationId(null);
        }}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={(id) => {
          setView("chat");
          setActiveConversationId(id);
        }}
        onNewAnalysis={() => {
          setView("chat");
          setActiveConversationId(null);
        }}
        onDeleteConversation={deleteConversation}
        anomalyActive={view === "anomaly"}
        onOpenAnomaly={() => setView("anomaly")}
      />
      {view === "anomaly" ? (
        <AnomalyPage />
      ) : (
        <ChatWindow
          conversation={conversation}
          selectedCategories={selectedCategories}
          onToggleCategory={toggleCategory}
          onSend={send}
          busy={busy}
        />
      )}
    </div>
  );
}
