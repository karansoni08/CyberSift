import { CATEGORIES } from "../categories.js";

// Horizontal chip row at the top of the chat area — selects which
// extractor(s) run on the file/text in the current message.
export default function CategorySelector({ selected, onToggle }) {
  return (
    <div className="category-chips">
      <span className="chips-label">Extract:</span>
      {CATEGORIES.map((cat) => {
        const isOn = selected.includes(cat.id);
        return (
          <button
            key={cat.id}
            className={"chip" + (isOn ? " on" : "")}
            style={isOn ? { "--chip-color": cat.color } : undefined}
            onClick={() => onToggle(cat.id)}
          >
            {cat.label}
          </button>
        );
      })}
    </div>
  );
}
