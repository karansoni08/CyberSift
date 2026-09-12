"""extractors.credentials_extractor
Credentials and secrets exposed in the document.
"""

from app.extractors.base import BaseExtractor


class CredentialsExtractor(BaseExtractor):
    category_id = "creds"
    label = "Credentials"
    subtypes = (
        "password",
        "username",
        "credential_pair",
        "api_key",
        "access_token",
        "private_key",
        "connection_string",
        "webhook_url",
        "session_cookie",
    )
    guidance = """
Extract credentials and secrets that appear in the document: plaintext or hashed
passwords, usernames/account names tied to credentials, combined user:password
pairs (use credential_pair with the whole pair as the value), API keys and
secret keys (AWS AKIA..., GitHub ghp_..., generic hex/base64 secrets labeled as
keys), bearer/OAuth/JWT tokens, private key material (extract the header line
"-----BEGIN ... PRIVATE KEY-----" plus a note in reasoning rather than the full
body), database connection strings containing credentials, webhook URLs with
embedded tokens, and session cookie values. Redacted values ("password: ****")
are not extractable secrets — skip them or extract the username half only.
Field labels without a value ("Password:") are not findings.
"""
