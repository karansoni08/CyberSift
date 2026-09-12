"""CyberSift — Streamlit frontend.

A chat UI over the CyberSift backend's tool-using agent (/api/chat).
Attach a report in the sidebar, then talk to the assistant; it decides
when to run the extraction tools and the findings render as tables.

Run:  streamlit run frontend/streamlit_app.py
Point at a different backend with:  CYBERSIFT_API_URL=http://localhost:8000
"""

import json

import pandas as pd
import streamlit as st

from common import API_URL, api_post

CATEGORY_LABELS = {
    "ioc": "IOC",
    "pii": "PII",
    "creds": "Credentials",
    "network": "Network",
    "forensic": "Forensic",
}

st.set_page_config(page_title="CyberSift", page_icon="◈", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []  # [{role, content, findings?, tool_calls?}]
if "document" not in st.session_state:
    st.session_state.document = None  # {"filename", "text"}


def render_findings(findings: list[dict]):
    df = pd.DataFrame(findings)
    df = df[["category", "subtype", "value", "original_form", "confidence", "reasoning"]]
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button(
        "Download findings (JSON)",
        data=json.dumps(findings, indent=2),
        file_name="cybersift-findings.json",
        mime="application/json",
        key=f"dl-{len(st.session_state.messages)}-{len(findings)}",
    )


# ---------- Sidebar ----------
with st.sidebar:
    st.title("◈ CyberSift")
    st.caption("LLM-based security data extraction")

    uploaded = st.file_uploader(
        "Attach a report", type=["txt", "log", "md", "pdf", "docx", "csv"],
        help="The file is converted to text on the backend, then the chat agent can extract from it.",
    )
    format_override = st.selectbox("Format override", ["auto", "txt", "pdf", "docx", "csv"])

    if uploaded is not None:
        already = st.session_state.document and st.session_state.document.get("filename") == uploaded.name
        if not already:
            with st.spinner("Loading file…"):
                try:
                    result = api_post(
                        "/api/ingest",
                        files={"file": (uploaded.name, uploaded.getvalue())},
                        data={"format": format_override},
                    )
                    st.session_state.document = {"filename": result["filename"], "text": result["text"]}
                except RuntimeError as exc:
                    st.error(str(exc))

    pasted = st.text_area("…or paste report text", height=120)
    if st.button("Use pasted text", disabled=not pasted.strip()):
        st.session_state.document = {"filename": "pasted text", "text": pasted}

    doc = st.session_state.document
    if doc:
        st.success(f"Attached: **{doc['filename']}** ({len(doc['text']):,} chars)")
        if st.button("Detach document"):
            st.session_state.document = None
            st.rerun()
    else:
        st.info("No document attached.")

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption(f"Backend: {API_URL}")


# ---------- Chat ----------
st.title("CyberSift")
st.caption("Attach a report, then ask — e.g. *“extract the IOCs”*, *“run every category”*, *“any credentials in here?”*")

# Category row — the first five run through the chat agent; Anomaly Detection
# opens its own page for detecting the unknown in any data format.
cols = st.columns([1, 1, 1.3, 1.1, 1.1, 2.2])
for col, label in zip(cols, ["🔴 IOC", "🟡 PII", "🟣 Creds", "🔵 Network", "🟢 Forensic"]):
    col.markdown(f"<div style='text-align:center; padding:6px; border:1px solid #444; border-radius:8px; font-size:13px'>{label}</div>", unsafe_allow_html=True)
with cols[5]:
    st.page_link("pages/Anomaly_Detection.py", label="🔍 Anomaly Detection", icon=None, use_container_width=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="◈" if msg["role"] == "assistant" else None):
        st.markdown(msg["content"])
        if msg.get("tool_calls"):
            st.caption("Tools used: " + ", ".join(msg["tool_calls"]))
        if msg.get("findings"):
            render_findings(msg["findings"])

if prompt := st.chat_input("Ask CyberSift…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="◈"):
        with st.spinner("Working… extraction can take up to a minute for large documents."):
            try:
                payload = {
                    "messages": [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    "document": st.session_state.document,
                }
                result = api_post("/api/chat", json=payload)
                reply = result.get("reply") or "(no reply)"
                st.markdown(reply)
                if result.get("tool_calls"):
                    st.caption("Tools used: " + ", ".join(result["tool_calls"]))
                if result.get("findings"):
                    render_findings(result["findings"])
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": reply,
                        "findings": result.get("findings") or [],
                        "tool_calls": result.get("tool_calls") or [],
                    }
                )
            except RuntimeError as exc:
                st.error(str(exc))
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"⚠ {exc}"}
                )
