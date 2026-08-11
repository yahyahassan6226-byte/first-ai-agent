from datetime import datetime

from langchain_core.tools import tool

from tools.gmail_tool import (
    create_draft as gmail_create_draft,
    list_recent_emails as gmail_recent_emails,
    read_email as gmail_read_email,
    search_emails as gmail_search_emails,
)

from tools.weather_tool import (
    get_weather as weather_lookup,
)


# =========================================================
# TOOL ERROR HELPER
# =========================================================

def tool_error(
    tool_name: str,
    error: Exception,
) -> str:
    """
    Error-ka u beddel format cad oo Agent-ku fahmi karo.
    """

    return (
        "TOOL_ERROR\n"
        f"Tool: {tool_name}\n"
        f"Type: {type(error).__name__}\n"
        f"Message: {error}\n"
        "The requested action did not succeed."
    )


# =========================================================
# CALCULATOR
# =========================================================

@tool
def calculator(expression: str) -> str:
    """
    Calculate a mathematical expression.

    Use this tool whenever the user asks for
    arithmetic or mathematical calculations.
    """

    try:
        allowed_characters = set(
            "0123456789+-*/().% "
        )

        if not set(expression).issubset(
            allowed_characters
        ):
            return (
                "TOOL_ERROR\n"
                "Tool: calculator\n"
                "Type: InvalidExpression\n"
                "Message: Expression-ka wuxuu leeyahay "
                "characters aan la oggolayn.\n"
                "The requested action did not succeed."
            )

        result = eval(
            expression,
            {"__builtins__": {}},
            {},
        )

        return str(result)

    except Exception as error:
        return tool_error(
            "calculator",
            error,
        )


# =========================================================
# CURRENT TIME
# =========================================================

@tool
def current_time() -> str:
    """
    Return the current local date and time.

    Use this tool when the user asks for
    the current local date or time.
    """

    try:
        return datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    except Exception as error:
        return tool_error(
            "current_time",
            error,
        )


# =========================================================
# WEATHER
# =========================================================

@tool
def get_weather(city: str) -> str:
    """
    Get the current weather for a city.

    Use this tool for current weather,
    temperature, humidity, wind,
    or weather conditions.
    """

    try:
        city = city.strip()

        if not city:
            return (
                "TOOL_ERROR\n"
                "Tool: get_weather\n"
                "Type: MissingCity\n"
                "Message: City lama bixin.\n"
                "The requested action did not succeed."
            )

        return weather_lookup(
            city
        )

    except Exception as error:
        return tool_error(
            "get_weather",
            error,
        )


# =========================================================
# GMAIL: RECENT EMAILS
# =========================================================

@tool
def list_recent_emails(
    max_results: int = 5,
) -> str:
    """
    Return the user's most recent Gmail messages.

    Use this when the user asks for
    latest or recent emails.
    """

    try:
        max_results = int(
            max_results
        )

        max_results = max(
            1,
            min(
                max_results,
                10,
            ),
        )

        return gmail_recent_emails(
            max_results
        )

    except Exception as error:
        return tool_error(
            "list_recent_emails",
            error,
        )


# =========================================================
# GMAIL: SEARCH EMAILS
# =========================================================

@tool
def search_emails(
    query: str,
    max_results: int = 5,
) -> str:
    """
    Search Gmail messages.

    Use this when the user asks to find emails
    by sender, subject, keyword, unread status,
    date, or Gmail search syntax.

    Examples:
    from:zapier.com
    from:google.com
    is:unread
    subject:security
    newer_than:7d
    """

    try:
        query = query.strip()

        if not query:
            return (
                "TOOL_ERROR\n"
                "Tool: search_emails\n"
                "Type: MissingQuery\n"
                "Message: Gmail search query waa madhan yahay.\n"
                "The requested action did not succeed."
            )

        max_results = int(
            max_results
        )

        max_results = max(
            1,
            min(
                max_results,
                10,
            ),
        )

        return gmail_search_emails(
            query,
            max_results,
        )

    except Exception as error:
        return tool_error(
            "search_emails",
            error,
        )


# =========================================================
# GMAIL: READ EMAIL
# =========================================================

@tool
def read_email(
    message_id: str,
) -> str:
    """
    Read a specific Gmail message using its Message ID.

    Use this after a Gmail search when the user
    needs the actual contents of an email.
    """

    try:
        message_id = message_id.strip()

        if not message_id:
            return (
                "TOOL_ERROR\n"
                "Tool: read_email\n"
                "Type: MissingMessageID\n"
                "Message: Gmail Message ID lama bixin.\n"
                "The requested action did not succeed."
            )

        return gmail_read_email(
            message_id
        )

    except Exception as error:
        return tool_error(
            "read_email",
            error,
        )


# =========================================================
# GMAIL: CREATE DRAFT
# =========================================================

@tool
def create_draft(
    to_email: str,
    subject: str,
    body: str,
) -> str:
    """
    Create and save an email draft in Gmail.

    IMPORTANT:
    This tool saves a draft only.
    It does NOT send the email.

    Use only when the user explicitly asks
    to create or save a Gmail draft.
    """

    try:
        to_email = to_email.strip()
        subject = subject.strip()
        body = body.strip()

        if not to_email:
            return (
                "TOOL_ERROR\n"
                "Tool: create_draft\n"
                "Type: MissingRecipient\n"
                "Message: Recipient email lama bixin.\n"
                "The requested action did not succeed."
            )

        if not subject:
            return (
                "TOOL_ERROR\n"
                "Tool: create_draft\n"
                "Type: MissingSubject\n"
                "Message: Subject lama bixin.\n"
                "The requested action did not succeed."
            )

        if not body:
            return (
                "TOOL_ERROR\n"
                "Tool: create_draft\n"
                "Type: MissingBody\n"
                "Message: Draft body lama bixin.\n"
                "The requested action did not succeed."
            )

        return gmail_create_draft(
            to_email,
            subject,
            body,
        )

    except Exception as error:
        return tool_error(
            "create_draft",
            error,
        )