import { useState } from "react";
import FormatSelector from "./FormatSelector.jsx";

export default function ChatInputBar() {
  const [format, setFormat] = useState("auto");
  const [text, setText] = useState("");

  return (
    <div className="chat-input-bar">
      <FormatSelector value={format} onChange={setFormat} />
      <button className="attach-btn" title="Attach a file">
        📎
      </button>
      <input
        className="chat-text-input"
        placeholder="Paste text or attach a report to analyze…"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <button className="send-btn" disabled={!text.trim()} title="Send">
        ➤
      </button>
    </div>
  );
}
