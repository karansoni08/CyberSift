import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import ChatWindow from "./components/ChatWindow.jsx";
import { extract } from "./api/client.js";

const STORAGE_KEY = "cybersift.conversations.v1";

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
  const [conversations, setConversations] = useState(loadConversations);
  const [activeTab, setActiveTab] = useState("ioc");
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [selectedCategories, setSelectedCategories] = useState(["ioc"]);
  const [busy, setBusy] = useState(false);

  useEffect(() => saveConversations(conversations), [conversations]);

  const conversation = conversations.find((c) => c.id === activeConversationId) || null;

  const toggleCategory = (id) =>
    setSelectedCategories((prev) => (prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]));

  const newAnalysis = () => setActiveConversationId(null);

  const appendMessage = (convId, message) =>
    setConversations((prev) =>
      prev.map((c) => (c.id === convId ? { ...c, messages: [...c.messages, message] } : c))
    );

  const send = async ({ text, file, format }) => {
    if (busy) return;
    const categories = selectedCategories.length ? selectedCategories : [activeTab];

    let convId = activeConversationId;
    if (!convId) {
      convId = "conv-" + Date.now();
      const title = file ? file.name : text.slice(0, 60) || "New analysis";
      const conv = {
        id: convId,
        category: categories[0],
        title,
        date: new Date().toLocaleDateString(),
        messages: [],
      };
      setConversations((prev) => [conv, ...prev]);
      setActiveTab(categories[0]);
      setActiveConversationId(convId);
    }

    appendMessage(convId, {
      role: "user",
      text: text || (file ? "Extract from this file." : ""),
      attachment: file ? file.name : undefined,
    });

    setBusy(true);
    try {
      const result = await extract({ text, file, categories, format });
      appendMessage(convId, {
        role: "bot",
        text: result.summary,
        findings: result.findings,
        errors: result.errors,
      });
    } catch (err) {
      appendMessage(convId, { role: "bot", error: err.message });
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
          setActiveTab(tab);
          setActiveConversationId(null);
        }}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={setActiveConversationId}
        onNewAnalysis={newAnalysis}
        onDeleteConversation={deleteConversation}
      />
      <ChatWindow
        conversation={conversation}
        selectedCategories={selectedCategories}
        onToggleCategory={toggleCategory}
        onSend={send}
        busy={busy}
      />
    </div>
  );
}
