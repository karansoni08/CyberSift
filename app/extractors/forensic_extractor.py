"""extractors.forensic_extractor
Malware and host-forensic artifacts from incident analysis.
"""

from app.extractors.base import BaseExtractor


class ForensicExtractor(BaseExtractor):
    category_id = "forensic"
    label = "Forensic"
    subtypes = (
        "process_name",
        "command_line",
        "scheduled_task",
        "service_name",
        "registry_key",
        "mutex",
        "event_id",
        "log_entry",
        "timestamp",
        "malware_family",
        "persistence_mechanism",
        "yara_rule",
    )
    guidance = """
Extract host-level forensic and malware-analysis artifacts: process names and
full command lines observed during execution, scheduled task names, Windows
service names, registry keys touched for persistence or configuration, mutex
names, log/event identifiers (e.g. Windows Event ID 4624 — include the log
source in reasoning), distinctive log entries quoted in the document,
timestamps tied to attack activity (keep the document's format in
original_form), named malware families/tools (Emotet, Cobalt Strike, Mimikatz),
described persistence mechanisms (value = the concrete artifact, e.g. the Run
key or task name), and YARA rule names referenced or defined. Generic system
processes (svchost.exe, explorer.exe) count only when the document flags their
use as suspicious (injection, masquerading) — say so in the reasoning.
"""
