from langchain_core.tools import tool

from rag_query import ask_rag


# =========================================================
# ERROR FORMAT
# =========================================================

def rag_error(
    error_type: str,
    message: str,
) -> str:
    """
    RAG errors-ka u samee format cad
    oo Agent-ku fahmi karo.
    """

    return (
        "RAG_ERROR\n"
        f"Type: {error_type}\n"
        f"Message: {message}\n"
        "The document search did not succeed."
    )


# =========================================================
# RAG TOOL
# =========================================================

@tool
def search_documents(
    question: str,
) -> str:
    """
    Search the local indexed document knowledge base.

    Use this tool when the user's request depends on
    information contained in local PDFs/documents.

    Returns a grounded answer with verified sources.

    If the knowledge base is unavailable or retrieval fails,
    the tool returns RAG_ERROR instead of inventing an answer.
    """

    question = question.strip()

    if not question:

        return rag_error(
            "MissingQuestion",
            "Document search question cannot be empty.",
        )

    try:

        result = ask_rag(
            question
        )

        if not result:

            return rag_error(
                "EmptyResult",
                "RAG pipeline returned no result.",
            )

        return str(result)

    except FileNotFoundError as error:

        return rag_error(
            "KnowledgeBaseMissing",
            str(error),
        )

    except ConnectionError as error:

        return rag_error(
            "ConnectionError",
            str(error),
        )

    except TimeoutError as error:

        return rag_error(
            "TimeoutError",
            str(error),
        )

    except Exception as error:

        return rag_error(
            type(error).__name__,
            str(error),
        )


# =========================================================
# MAIN TEST
# =========================================================

def main() -> None:

    question = (
        "What does the personal development "
        "guide say about goal setting?"
    )

    result = search_documents.invoke(
        {
            "question": question,
        }
    )

    print(result)


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()