import { FORMATS } from "../categories.js";

export default function FormatSelector({ value, onChange }) {
  return (
    <select className="format-select" value={value} onChange={(e) => onChange(e.target.value)} title="File format override">
      {FORMATS.map((f) => (
        <option key={f} value={f}>
          {f === "auto" ? "auto-detect" : f}
        </option>
      ))}
    </select>
  );
}
