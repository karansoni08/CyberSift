import { useEffect, useRef } from "react";
import CategorySelector from "./CategorySelector.jsx";
import ChatInputBar from "./ChatInputBar.jsx";
import MessageBubble from "./MessageBubble.jsx";

export default function ChatWindow({ conversation, selectedCategories, onToggleCategory, onSend, busy }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation?.messages.length, busy]);

  return (
    <main className="chat-window">
      <CategorySelector selected={selectedCategories} onToggle={onToggleCategory} />

      <div className="messages">
        {!conversation && (
          <div className="empty-state">
            <div className="empty-mark">◈</div>
            <h2>Drop a report. Get the signal.</h2>
            <p>
              Attach a security report or paste raw text below, pick which categories to extract, and CyberSift will
              pull out the indicators — normalized, verified against the source, and scored by confidence.
            </p>
          </div>
        )}
        {conversation && conversation.messages.map((m, i) => <MessageBubble key={i} message={m} />)}
        {busy && (
          <div className="message-row bot">
            <div className="message-bubble bot loading">
              <span className="spinner" /> Extracting… this can take up to a minute for large documents.
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <ChatInputBar onSend={onSend} busy={busy} />
    </main>
  );
}
