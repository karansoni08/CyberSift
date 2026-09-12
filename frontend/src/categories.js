// Shared category metadata. Components stay generic — they render whatever
// is in this list, mirroring the backend extractor registry.
export const CATEGORIES = [
  { id: "ioc", label: "IOC", color: "#e05d5d" },
  { id: "pii", label: "PII", color: "#d9a23c" },
  { id: "creds", label: "Creds", color: "#b06dd6" },
  { id: "network", label: "Network", color: "#4d9de0" },
  { id: "forensic", label: "Forensic", color: "#4fb286" },
];

export const FORMATS = ["auto", "txt", "pdf", "docx", "csv"];
