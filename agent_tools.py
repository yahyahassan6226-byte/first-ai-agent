import json

from tools.calculator import calculator
from tools.gmail_tool import (
    create_draft,
    list_recent_emails,
    read_email,
    search_emails,
)
from tools.memory_tool import (
    get_memory,
    list_memories,
    save_memory,
)
from tools.pdf_tool import read_pdf
from tools.random_tool import random_number
from tools.rag_tool import index_pdf, search_pdf
from tools.time_tool import current_time
from tools.weather_tool import get_weather


TOOLS = [
    {
        "type": "function",
        "name": "calculator",
        "description": "Calculate a mathematical expression accurately.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression such as 25*30.",
                }
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "current_time",
        "description": "Return the current local time.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "random_number",
        "description": "Generate a random number between 1 and 100.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name such as Mogadishu, SO.",
                }
            },
            "required": ["city"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "read_pdf",
        "description": (
            "Read the entire PDF from the local documents folder. "
            "Use when the user asks to read or summarize an entire PDF."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "Exact PDF filename including .pdf.",
                }
            },
            "required": ["file_name"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "index_pdf",
        "description": "Index a PDF into the local vector database for RAG.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "Exact PDF filename including .pdf.",
                }
            },
            "required": ["file_name"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "search_pdf",
        "description": "Search an indexed PDF using semantic RAG search.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "Exact PDF filename including .pdf.",
                },
                "question": {
                    "type": "string",
                    "description": "Question to search for inside the PDF.",
                },
            },
            "required": ["file_name", "question"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "save_memory",
        "description": (
            "Save a stable user fact or preference. "
            "Use only when the user explicitly asks you to remember it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Memory key such as favorite_city.",
                },
                "value": {
                    "type": "string",
                    "description": "Value to remember.",
                },
            },
            "required": ["key", "value"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_memory",
        "description": "Retrieve a saved memory using its key.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Memory key.",
                }
            },
            "required": ["key"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "list_memories",
        "description": "List all saved memories from SQLite.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "list_recent_emails",
        "description": "List the user's most recent Gmail messages.",
        "parameters": {
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Number of emails to retrieve.",
                }
            },
            "required": ["max_results"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "search_emails",
        "description": (
            "Search Gmail by sender, subject, keyword, date, "
            "unread status, or Gmail search syntax."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Gmail query such as from:google.com, "
                        "is:unread or subject:security."
                    ),
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results.",
                },
            },
            "required": ["query", "max_results"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "read_email",
        "description": "Read a specific Gmail message using its Message ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "Gmail Message ID.",
                }
            },
            "required": ["message_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "create_draft",
        "description": (
            "Create and save an email draft in Gmail. "
            "This tool does NOT send the email."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "to_email": {
                    "type": "string",
                    "description": "Recipient email address.",
                },
                "subject": {
                    "type": "string",
                    "description": "Draft email subject.",
                },
                "body": {
                    "type": "string",
                    "description": "Draft email body.",
                },
            },
            "required": ["to_email", "subject", "body"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "web_search",
    },
]


def execute_tool(tool_name: str, arguments: dict) -> str:
    """Fulinta custom Python tool-ka uu GPT doortay."""

    if tool_name == "calculator":
        return calculator(arguments["expression"])

    if tool_name == "current_time":
        return current_time()

    if tool_name == "random_number":
        return random_number()

    if tool_name == "get_weather":
        return get_weather(arguments["city"])

    if tool_name == "read_pdf":
        return read_pdf(arguments["file_name"])

    if tool_name == "index_pdf":
        return index_pdf(arguments["file_name"])

    if tool_name == "search_pdf":
        return search_pdf(
            arguments["file_name"],
            arguments["question"],
        )

    if tool_name == "save_memory":
        return save_memory(
            arguments["key"],
            arguments["value"],
        )

    if tool_name == "get_memory":
        return get_memory(arguments["key"])

    if tool_name == "list_memories":
        return list_memories()

    if tool_name == "list_recent_emails":
        return list_recent_emails(
            arguments["max_results"]
        )

    if tool_name == "search_emails":
        return search_emails(
            arguments["query"],
            arguments["max_results"],
        )

    if tool_name == "read_email":
        return read_email(
            arguments["message_id"]
        )

    if tool_name == "create_draft":
        return create_draft(
            arguments["to_email"],
            arguments["subject"],
            arguments["body"],
        )

    return f"Error: Tool aan la aqoon: {tool_name}"