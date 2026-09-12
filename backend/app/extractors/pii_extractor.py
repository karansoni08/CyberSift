"""extractors.pii_extractor
Personally identifiable information found in the document.
"""

from app.extractors.base import BaseExtractor


class PiiExtractor(BaseExtractor):
    category_id = "pii"
    label = "PII"
    subtypes = (
        "person_name",
        "email",
        "phone",
        "physical_address",
        "national_id",
        "date_of_birth",
        "passport_number",
        "drivers_license",
        "financial_account",
        "ip_address_personal",
    )
    guidance = """
Extract personally identifiable information about real individuals mentioned in
the document: full names of specific people (not company names, not malware
names, not threat-actor group aliases), personal email addresses, phone numbers,
home/mailing addresses, government ID numbers (SSN and national equivalents),
dates of birth tied to a person, passport and driver's license numbers, and
bank/credit-card account numbers. Use national_id for SSNs and similar. An IP
address is ip_address_personal only when the document ties it to an identified
individual (e.g. a subscriber record). Report authors' names in a byline count
as person_name with lower confidence; generic role mentions ("the CFO") without
a name are not PII.
"""
