import { useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import ChatWindow from "./components/ChatWindow.jsx";

// Static demo data so the deployed shell shows what a finished conversation
// will look like. Replaced by real API data in Phases 9–13.
const DEMO_CONVERSATIONS = [
  {
    id: "demo-1",
    category: "ioc",
    title: "Phishing campaign report (demo)",
    date: "Preview",
    messages: [
      {
        role: "user",
        text: "Extract the IOCs from this incident report.",
        attachment: "incident-report.pdf",
      },
      {
        role: "bot",
        text: "Sample of how extracted findings will be rendered (demo data):",
        findings: [
          {
            value: "192.168.24.7",
            original_form: "192[.]168[.]24[.]7",
            subtype: "ip",
            confidence: 0.97,
            reasoning: "Defanged IPv4 address listed as a C2 callback in the report.",
          },
          {
            value: "http://malware-drop.example.com/stage2",
            original_form: "hxxp://malware-drop[.]example[.]com/stage2",
            subtype: "url",
            confidence: 0.94,
            reasoning: "Defanged URL described as the second-stage payload location.",
          },
          {
            value: "d41d8cd98f00b204e9800998ecf8427e",
            original_form: "d41d8cd98f00b204e9800998ecf8427e",
            subtype: "file_hash",
            confidence: 0.88,
            reasoning: "32-character hex string labeled as the dropper's MD5 hash.",
          },
          {
            value: "CVE-2024-21412",
            original_form: "CVE-2024-21412",
            subtype: "cve",
            confidence: 0.99,
            reasoning: "CVE identifier cited as the exploited vulnerability.",
          },
        ],
      },
    ],
  },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("ioc");
  const [activeConversationId, setActiveConversationId] = useState("demo-1");
  const [selectedCategories, setSelectedCategories] = useState(["ioc"]);

  const conversation = DEMO_CONVERSATIONS.find((c) => c.id === activeConversationId) || null;

  const toggleCategory = (id) =>
    setSelectedCategories((prev) => (prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]));

  return (
    <div className="app-layout">
      <Sidebar
        activeTab={activeTab}
        onTabChange={(tab) => {
          setActiveTab(tab);
          setActiveConversationId(null);
        }}
        conversations={DEMO_CONVERSATIONS}
        activeConversationId={activeConversationId}
        onSelectConversation={setActiveConversationId}
      />
      <ChatWindow
        conversation={conversation}
        selectedCategories={selectedCategories}
        onToggleCategory={toggleCategory}
      />
    </div>
  );
}
