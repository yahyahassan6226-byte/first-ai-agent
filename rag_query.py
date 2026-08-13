from pathlib import Path

from langchain_core.documents import Document
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
)
from langchain_openai import ChatOpenAI

from config import MODEL
from prompts.rag_prompt import RAG_PROMPT
from rag_retriever import retrieve_documents


# =========================================================
# MODEL
# =========================================================

model = ChatOpenAI(
    model=MODEL,
)


# =========================================================
# SHORT-TERM CONVERSATION MEMORY
# =========================================================

conversation_history = []


# =========================================================
# BUILD CONTEXT
# =========================================================

def build_context(
    documents: list[Document],
) -> str:
    """
    Retrieved chunks-ka u beddel context.
    """

    context_parts = []

    for index, document in enumerate(
        documents,
        start=1,
    ):

        source = document.metadata.get(
            "source",
            "Unknown",
        )

        page = document.metadata.get(
            "page_label",
            document.metadata.get(
                "page",
                "Unknown",
            ),
        )

        block = (
            f"[DOCUMENT {index}]\n"
            f"Source: {source}\n"
            f"Page: {page}\n\n"
            f"{document.page_content}"
        )

        context_parts.append(
            block
        )

    return "\n\n".join(
        context_parts
    )


# =========================================================
# VERIFIED SOURCES
# =========================================================

def get_sources(
    documents: list[Document],
) -> list[str]:
    """
    Retrieved metadata-ga ka samee source list.
    """

    sources = []
    seen = set()

    for document in documents:

        source = document.metadata.get(
            "source",
            "Unknown",
        )

        page = document.metadata.get(
            "page_label",
            document.metadata.get(
                "page",
                "Unknown",
            ),
        )

        source_name = Path(
            str(source)
        ).name

        key = (
            source_name,
            str(page),
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        sources.append(
            f"{source_name} — Page {page}"
        )

    return sources


# =========================================================
# FORMAT SOURCES
# =========================================================

def format_sources(
    sources: list[str],
) -> str:

    if not sources:

        return (
            "Sources:\n"
            "- No verified sources"
        )

    lines = [
        "Sources:"
    ]

    for source in sources:

        lines.append(
            f"- {source}"
        )

    return "\n".join(
        lines
    )


# =========================================================
# BUILD HISTORY TEXT
# =========================================================

def build_history_text() -> str:
    """
    Conversation history-ga u beddel text
    prompt-ka lagu dari karo.
    """

    if not conversation_history:

        return "No previous conversation."

    parts = []

    for message in conversation_history:

        if isinstance(
            message,
            HumanMessage,
        ):

            parts.append(
                f"User: {message.content}"
            )

        elif isinstance(
            message,
            AIMessage,
        ):

            parts.append(
                f"Assistant: {message.content}"
            )

    return "\n".join(
        parts
    )


# =========================================================
# REWRITE FOLLOW-UP QUESTION
# =========================================================

def rewrite_question(
    question: str,
) -> str:
    """
    Follow-up question-ka ka dhig standalone question.

    Tusaale:

    History:
    User: What is personal development?

    Current:
    Why is it important?

    Standalone:
    Why is personal development important?
    """

    if not conversation_history:

        return question

    history_text = build_history_text()

    prompt = f"""
You rewrite follow-up questions for a RAG system.

Use the conversation history only to resolve references
such as:
- it
- that
- this
- there
- the topic
- the document
- the previous point

Do not answer the question.

Return only one standalone question.

Conversation history:

{history_text}

Current user question:

{question}

Standalone question:
"""

    response = model.invoke(
        prompt
    )

    rewritten = str(
        response.content
    ).strip()

    if not rewritten:
        return question

    return rewritten


# =========================================================
# ASK RAG
# =========================================================

def ask_rag(
    question: str,
) -> str:
    """
    Conversation-aware RAG pipeline.

    User question
        ↓
    Rewrite using history
        ↓
    Retriever
        ↓
    Relevant chunks
        ↓
    RAG Prompt
        ↓
    LLM
        ↓
    Answer + verified sources
        ↓
    Save conversation history
    """

    question = question.strip()

    if not question:

        raise ValueError(
            "Question-ku madhan ma noqon karo."
        )

    # -----------------------------------------------------
    # REWRITE FOLLOW-UP QUESTION
    # -----------------------------------------------------

    standalone_question = rewrite_question(
        question
    )

    # -----------------------------------------------------
    # RETRIEVAL
    # -----------------------------------------------------

    documents = retrieve_documents(
        standalone_question
    )

    if not documents:

        answer = (
            "Wax relevant document ah lama helin."
        )

        conversation_history.append(
            HumanMessage(
                content=question
            )
        )

        conversation_history.append(
            AIMessage(
                content=answer
            )
        )

        return (
            f"{answer}\n\n"
            "Sources:\n"
            "- No verified sources"
        )

    # -----------------------------------------------------
    # CONTEXT
    # -----------------------------------------------------

    context = build_context(
        documents
    )

    # -----------------------------------------------------
    # RAG PROMPT
    # -----------------------------------------------------

    prompt_value = RAG_PROMPT.invoke(
        {
            "context": context,
            "question": standalone_question,
        }
    )

    # -----------------------------------------------------
    # MODEL
    # -----------------------------------------------------

    response = model.invoke(
        prompt_value
    )

    answer = str(
        response.content
    )

    # -----------------------------------------------------
    # VERIFIED SOURCES
    # -----------------------------------------------------

    sources = get_sources(
        documents
    )

    source_text = format_sources(
        sources
    )

    final_answer = (
        f"{answer}\n\n"
        f"{source_text}"
    )

    # -----------------------------------------------------
    # SAVE ORIGINAL CONVERSATION
    # -----------------------------------------------------

    conversation_history.append(
        HumanMessage(
            content=question
        )
    )

    conversation_history.append(
        AIMessage(
            content=answer
        )
    )

    return final_answer


# =========================================================
# CLEAR MEMORY
# =========================================================

def clear_memory() -> None:
    """
    Nadiifi current session conversation history.
    """

    conversation_history.clear()


# =========================================================
# MAIN
# =========================================================

def main() -> None:

    print(
        "🤖 RAG Agent + Conversation Memory waa diyaar!"
    )

    print("Commands:")
    print("  exit   -> ka bax")
    print(
        "  /clear -> nadiifi conversation memory"
    )

    print()

    while True:

        question = input(
            "Adiga: "
        ).strip()

        # ---------------------------------------------
        # EXIT
        # ---------------------------------------------

        if question.lower() == "exit":

            print(
                "Nabadgelyo!"
            )

            break

        # ---------------------------------------------
        # CLEAR
        # ---------------------------------------------

        if question.lower() == "/clear":

            clear_memory()

            print(
                "🧹 RAG conversation memory "
                "waa la nadiifiyay.\n"
            )

            continue

        # ---------------------------------------------
        # EMPTY INPUT
        # ---------------------------------------------

        if not question:

            print(
                "Fadlan su'aal qor.\n"
            )

            continue

        # ---------------------------------------------
        # ASK RAG
        # ---------------------------------------------

        try:

            answer = ask_rag(
                question
            )

            print(
                f"\nRAG Agent:\n\n{answer}\n"
            )

        except KeyboardInterrupt:

            print(
                "\nOperation-ka waa la joojiyay.\n"
            )

        except Exception as error:

            print(
                f"\n❌ RAG Error: {error}\n"
            )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()