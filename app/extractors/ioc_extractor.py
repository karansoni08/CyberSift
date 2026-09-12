"""extractors.ioc_extractor
Indicators of compromise: the classic threat-intel observables.
"""

from app.extractors.base import BaseExtractor


class IocExtractor(BaseExtractor):
    category_id = "ioc"
    label = "IOC"
    subtypes = (
        "ip",
        "domain",
        "url",
        "file_hash",
        "email",
        "cve",
        "filename",
        "file_path",
        "registry_key",
        "mutex",
        "user_agent",
        "bitcoin_address",
    )
    guidance = """
Extract indicators of compromise: attacker infrastructure (IPs, domains, URLs),
malware artifacts (hashes of any algorithm, filenames, dropped file paths,
registry keys, mutexes), phishing sender addresses, exploited CVE identifiers,
distinctive User-Agent strings, and ransom-payment cryptocurrency addresses.
Defanged indicators (192[.]168..., hxxp://, evil[.]com, user[@]bad.com) are the
most important case — refang them in "value" and keep the defanged text verbatim
in "original_form". Classify hashes as file_hash regardless of algorithm; note
the likely algorithm (MD5/SHA-1/SHA-256) in the reasoning. Do not extract the
report author's own organization, analysis-sandbox domains, or vendor product
names as indicators.
"""
