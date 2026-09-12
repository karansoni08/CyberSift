import { useRef, useState } from "react";
import FormatSelector from "./FormatSelector.jsx";

export default function ChatInputBar({ onSend, busy }) {
  const [format, setFormat] = useState("auto");
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const fileInputRef = useRef(null);

  const canSend = !busy && (text.trim() || file);

  const submit = () => {
    if (!canSend) return;
    onSend({ text: text.trim(), file, format });
    setText("");
    setFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="chat-input-area">
      {file && (
        <div className="pending-attachment">
          📄 {file.name}
          <button
            className="remove-attachment"
            title="Remove file"
            onClick={() => {
              setFile(null);
              if (fileInputRef.current) fileInputRef.current.value = "";
            }}
          >
            ✕
          </button>
        </div>
      )}
      <div className="chat-input-bar">
        <FormatSelector value={format} onChange={setFormat} />
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.log,.md,.pdf,.docx,.csv"
          hidden
          onChange={(e) => setFile(e.target.files[0] || null)}
        />
        <button className="attach-btn" title="Attach a file" onClick={() => fileInputRef.current?.click()}>
          📎
        </button>
        <input
          className="chat-text-input"
          placeholder="Paste text or attach a report to analyze…"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") submit();
          }}
        />
        <button className="send-btn" disabled={!canSend} title="Send" onClick={submit}>
          {busy ? "…" : "➤"}
        </button>
      </div>
    </div>
  );
}
