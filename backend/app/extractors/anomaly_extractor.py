"""extractors.anomaly_extractor
The "detect the unknown" category: instead of extracting indicators the
document already labels as bad, this one reasons about what looks wrong
even though nothing flags it, and assigns each finding a severity so the
UI can warn the user in tiers.
"""

from app.extractors.base import BaseExtractor


class AnomalyExtractor(BaseExtractor):
    category_id = "anomaly"
    label = "Anomaly"
    subtypes = (
        "typosquat_domain",
        "high_entropy_string",
        "encoded_payload",
        "suspicious_process_path",
        "temporal_anomaly",
        "geographic_anomaly",
        "unusual_port_protocol",
        "statistical_outlier",
        "structural_anomaly",
        "covert_channel_hint",
        "privilege_anomaly",
        "other_suspicious",
    )
    guidance = """
You are hunting for the UNKNOWN: things the document does NOT label as
malicious but that deviate from what normal data of this kind looks like.
Do not re-extract indicators the document already calls out as bad — flag
what nobody has noticed yet. Look for:
- Domains/URLs that imitate legitimate brands or services (typosquats,
  homoglyphs, digit-for-letter swaps, suspicious extra words like "login-",
  "-verify", odd TLDs for the brand) even when mentioned neutrally.
- High-entropy or encoded strings where they do not belong: base64/hex blobs
  in configs, logs, user-agent strings, DNS labels, URL parameters — possible
  payloads or exfiltration.
- Legitimate-looking process names running from wrong locations, misspelled
  system binaries (svch0st, lsasss), LOLBins used oddly, scripts spawned by
  Office apps.
- Temporal oddities: activity at unusual hours, impossible-travel logins,
  bursts of identical events, timestamps out of sequence or from the future.
- Geographic/network oddities: internal services talking to unexpected
  countries or residential ranges, unusual port/protocol pairings (DNS over
  odd ports, HTTP on high ports), traffic volumes that stand out.
- Structural anomalies in tabular/log data: a column value wildly unlike the
  rest, accounts with logins but no other activity, rows breaking the file's
  own pattern, sudden format changes mid-file.
- Privilege oddities: service accounts logging in interactively, dormant
  admin accounts waking up, permission changes buried in routine noise.
- Possible covert channels: regular small beacon-like intervals, oversized
  DNS TXT lookups, unusually structured subdomains.
Confidence expresses how anomalous the item is IN THIS DOCUMENT'S OWN
CONTEXT — calibrate against what the rest of the data looks like. In the
reasoning, state the norm it deviates from, then why it matters. It is fine
to return few or zero findings for genuinely clean data; do not manufacture
suspicion.
"""

    def system_prompt(self) -> str:
        # Severity is part of this category's element schema, so splice it into
        # the output contract line itself — a field mentioned outside the schema
        # gets dropped by strict contract-following.
        prompt = super().system_prompt().replace(
            '"confidence": float, "reasoning": str}',
            '"confidence": float, "reasoning": str, "severity": str}',
        )
        return (
            prompt
            + '\n\n"severity" is required in every element: "high" (likely active '
            'compromise or exposure, act now), "medium" (suspicious deviation worth '
            'investigating), or "low" (notable oddity, review when convenient).'
        )
