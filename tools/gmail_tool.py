import base64
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"


# =========================================================
# GMAIL SCOPES
# =========================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]


# =========================================================
# GMAIL AUTHENTICATION
# =========================================================

def get_gmail_service():
    """Authenticate and return Gmail API service."""

    creds = None

    # Akhri token.json haddii uu jiro
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(
                str(TOKEN_FILE),
                SCOPES,
            )
        except Exception:
            creds = None

    # Haddii credentials-ku aysan valid ahayn
    if not creds or not creds.valid:

        # Refresh token haddii uu dhacay
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            # Hubi credentials.json
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    "credentials.json lama helin.\n"
                    f"Waxaa laga raadinayaa:\n{CREDENTIALS_FILE}"
                )

            # OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE),
                SCOPES,
            )

            creds = flow.run_local_server(
                port=0,
            )

        # Kaydi token-ka cusub
        TOKEN_FILE.write_text(
            creds.to_json(),
            encoding="utf-8",
        )

    return build(
        "gmail",
        "v1",
        credentials=creds,
    )


# =========================================================
# HELPER: GET HEADER
# =========================================================

def _get_header(headers: list, name: str) -> str:
    """Ka soo saar Gmail header sida From, To, Subject ama Date."""

    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")

    return ""


# =========================================================
# HELPER: DECODE BODY
# =========================================================

def _decode_body(data: str) -> str:
    """Decode Gmail base64url body."""

    if not data:
        return ""

    try:
        return base64.urlsafe_b64decode(
            data.encode("utf-8")
        ).decode(
            "utf-8",
            errors="replace",
        )

    except Exception:
        return ""


# =========================================================
# HELPER: EXTRACT TEXT BODY
# =========================================================

def _extract_body(payload: dict) -> str:
    """Ka soo saar text/plain body-ga email-ka."""

    mime_type = payload.get("mimeType", "")
    body = payload.get("body", {})
    data = body.get("data")

    # Email text/plain ah
    if mime_type == "text/plain" and data:
        return _decode_body(data)

    # Multipart email
    for part in payload.get("parts", []):

        part_mime_type = part.get("mimeType", "")

        if part_mime_type == "text/plain":
            part_data = (
                part.get("body", {})
                .get("data")
            )

            if part_data:
                return _decode_body(part_data)

        # Nested multipart
        nested_body = _extract_body(part)

        if nested_body:
            return nested_body

    # Fallback
    if data:
        return _decode_body(data)

    return ""


# =========================================================
# LIST RECENT EMAILS
# =========================================================

def list_recent_emails(max_results: int = 5) -> str:
    """Soo celi emails-kii ugu dambeeyay."""

    service = get_gmail_service()

    try:
        max_results = int(max_results)
    except (TypeError, ValueError):
        max_results = 5

    max_results = max(
        1,
        min(max_results, 20),
    )

    result = (
        service.users()
        .messages()
        .list(
            userId="me",
            maxResults=max_results,
        )
        .execute()
    )

    messages = result.get("messages", [])

    if not messages:
        return "Wax email ah lama helin."

    output = []

    for message in messages:

        data = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message["id"],
                format="metadata",
                metadataHeaders=[
                    "From",
                    "Subject",
                    "Date",
                ],
            )
            .execute()
        )

        headers = (
            data.get("payload", {})
            .get("headers", [])
        )

        sender = (
            _get_header(headers, "From")
            or "Unknown"
        )

        subject = (
            _get_header(headers, "Subject")
            or "(No subject)"
        )

        date = (
            _get_header(headers, "Date")
            or "Unknown"
        )

        output.append(
            "\n".join(
                [
                    f"From: {sender}",
                    f"Subject: {subject}",
                    f"Date: {date}",
                    f"Message ID: {message['id']}",
                ]
            )
        )

    return "\n\n---\n\n".join(output)


# =========================================================
# SEARCH EMAILS
# =========================================================

def search_emails(
    query: str,
    max_results: int = 5,
) -> str:
    """Ka raadi Gmail iyadoo Gmail search syntax la isticmaalayo."""

    service = get_gmail_service()

    query = query.strip()

    if not query:
        return "Error: Gmail search query waa madhan yahay."

    try:
        max_results = int(max_results)
    except (TypeError, ValueError):
        max_results = 5

    max_results = max(
        1,
        min(max_results, 20),
    )

    result = (
        service.users()
        .messages()
        .list(
            userId="me",
            q=query,
            maxResults=max_results,
        )
        .execute()
    )

    messages = result.get("messages", [])

    if not messages:
        return (
            "Wax email ah lagama helin search-kan:\n"
            f"{query}"
        )

    output = []

    for message in messages:

        data = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message["id"],
                format="metadata",
                metadataHeaders=[
                    "From",
                    "Subject",
                    "Date",
                ],
            )
            .execute()
        )

        headers = (
            data.get("payload", {})
            .get("headers", [])
        )

        sender = (
            _get_header(headers, "From")
            or "Unknown"
        )

        subject = (
            _get_header(headers, "Subject")
            or "(No subject)"
        )

        date = (
            _get_header(headers, "Date")
            or "Unknown"
        )

        output.append(
            "\n".join(
                [
                    f"From: {sender}",
                    f"Subject: {subject}",
                    f"Date: {date}",
                    f"Message ID: {message['id']}",
                ]
            )
        )

    return (
        f"Gmail search: {query}\n"
        f"Results: {len(output)}\n\n"
        + "\n\n---\n\n".join(output)
    )


# =========================================================
# READ EMAIL
# =========================================================

def read_email(message_id: str) -> str:
    """Akhri email gaar ah iyadoo Message ID la isticmaalayo."""

    service = get_gmail_service()

    message_id = message_id.strip()

    if not message_id:
        return "Error: Message ID lama bixin."

    message = (
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="full",
        )
        .execute()
    )

    payload = message.get("payload", {})
    headers = payload.get("headers", [])

    sender = (
        _get_header(headers, "From")
        or "Unknown"
    )

    to_email = (
        _get_header(headers, "To")
        or "Unknown"
    )

    subject = (
        _get_header(headers, "Subject")
        or "(No subject)"
    )

    date = (
        _get_header(headers, "Date")
        or "Unknown"
    )

    body = _extract_body(payload)

    if not body:
        body = "[Text body lama helin.]"

    return (
        f"From: {sender}\n"
        f"To: {to_email}\n"
        f"Subject: {subject}\n"
        f"Date: {date}\n"
        f"Message ID: {message_id}\n\n"
        f"Body:\n{body}"
    )


# =========================================================
# CREATE GMAIL DRAFT
# =========================================================

def create_draft(
    to_email: str,
    subject: str,
    body: str,
) -> str:
    """
    Draft email ku kaydi Gmail.

    Function-kan EMAIL MA DIRO.
    Wuxuu Gmail Drafts ku kaydiyaa oo keliya.
    """

    service = get_gmail_service()

    to_email = to_email.strip()
    subject = subject.strip()
    body = body.strip()

    if not to_email:
        return "Error: Recipient email lama bixin."

    if not subject:
        return "Error: Subject lama bixin."

    if not body:
        return "Error: Draft body lama bixin."

    # Samee MIME email
    message = EmailMessage()

    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(body)

    # Gmail API wuxuu rabaa base64url encoded raw message
    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode("utf-8")

    draft_body = {
        "message": {
            "raw": encoded_message,
        }
    }

    # IMPORTANT:
    # drafts().create() oo keliya.
    # Ma jiro messages().send() ama drafts().send().
    draft = (
        service.users()
        .drafts()
        .create(
            userId="me",
            body=draft_body,
        )
        .execute()
    )

    draft_id = draft.get(
        "id",
        "Unknown",
    )

    return (
        "✅ Draft-ka Gmail waa la kaydiyay.\n"
        f"Draft ID: {draft_id}\n"
        f"To: {to_email}\n"
        f"Subject: {subject}\n\n"
        "Status: DRAFT ONLY — NOT SENT"
    )


# =========================================================
# OPTIONAL TEST
# =========================================================

if __name__ == "__main__":
    print(
        list_recent_emails(3)
    )