"""CyberSift — Anomaly Detection page.

Give it data in ANY format (logs, CSV exports, JSON dumps, configs,
reports…) and the AI profiles what "normal" looks like inside that data,
then flags deviations — suspicious items nothing has labeled as bad yet —
with severity-tiered warnings.
"""

import json
import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import api_post  # noqa: E402

st.set_page_config(page_title="CyberSift — Anomaly Detection", page_icon="🔍", layout="wide")

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, None: 3}
SEVERITY_BADGE = {"high": "🔴 High", "medium": "🟠 Medium", "low": "🟡 Low", None: "⚪ Unrated"}

st.title("🔍 Anomaly Detection")
st.caption(
    "Detect the unknown: upload data in any format — logs, CSV/JSON exports, configs, reports — "
    "and CyberSift profiles the data's own patterns, then warns you about deviations that nothing "
    "has flagged as malicious yet. Every warning cites verbatim evidence from your data."
)

with st.sidebar:
    st.page_link("streamlit_app.py", label="← Back to extraction chat", icon="◈")
    st.divider()
    st.caption(
        "Anomaly ≠ confirmed malicious. Findings are leads ranked by severity, "
        "each with the reasoning and the norm it deviates from — judge them in context."
    )

uploaded = st.file_uploader(
    "Upload data in any format",
    type=None,
    help="Text-based formats work best (logs, csv, json, xml, conf, txt, pdf, docx). "
    "Unknown extensions are read as plain text.",
)
pasted = st.text_area("…or paste raw data", height=160, placeholder="Paste logs, records, config content…")

scan = st.button("🔍 Scan for anomalies", type="primary", disabled=not (uploaded or pasted.strip()))

if scan:
    with st.spinner("Profiling the data and hunting for anomalies… large inputs can take a couple of minutes."):
        try:
            data = {"categories": "anomaly", "format": "auto", "text": pasted or ""}
            files = {"file": (uploaded.name, uploaded.getvalue())} if uploaded else None
            result = api_post("/api/extract", data=data, files=files)
            st.session_state.anomaly_result = result
        except RuntimeError as exc:
            st.error(str(exc))

result = st.session_state.get("anomaly_result")
if result:
    findings = sorted(result["findings"], key=lambda f: (SEVERITY_ORDER.get(f.get("severity"), 3), -f["confidence"]))
    high = [f for f in findings if f.get("severity") == "high"]
    medium = [f for f in findings if f.get("severity") == "medium"]

    st.divider()
    if not findings:
        st.success(
            f"No anomalies detected in {result['characters']:,} characters "
            f"({result['chunks']} chunk(s) analyzed). The data looks internally consistent."
        )
    else:
        if high:
            st.error(
                f"⚠ **{len(high)} high-severity anomaly(ies) detected** — these look like "
                "possible active compromise or exposure. Investigate them first."
            )
        elif medium:
            st.warning(f"**{len(medium)} medium-severity anomaly(ies) detected** — suspicious deviations worth investigating.")
        else:
            st.info(f"{len(findings)} low-severity oddity(ies) noted — review when convenient.")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔴 High", len(high))
        c2.metric("🟠 Medium", len(medium))
        c3.metric("🟡 Low", len([f for f in findings if f.get("severity") == "low"]))
        c4.metric("Data analyzed", f"{result['characters']:,} chars")

        for f in findings:
            badge = SEVERITY_BADGE.get(f.get("severity"))
            with st.expander(f"{badge} · {f['subtype']} — `{f['value'][:80]}` ({round(f['confidence'] * 100)}%)"):
                st.markdown(f"**Why it's anomalous:** {f['reasoning']}")
                st.markdown(f"**Evidence in your data:** `{f['original_form']}`")

        df = pd.DataFrame(findings)[["severity", "subtype", "value", "original_form", "confidence", "reasoning"]]
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download anomaly report (JSON)",
            data=json.dumps(findings, indent=2),
            file_name="cybersift-anomalies.json",
            mime="application/json",
        )

    if result.get("errors"):
        for e in result["errors"]:
            st.warning(e)
