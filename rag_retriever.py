from langchain_core.documents import Document

from rag_vectorstore import (
    load_vector_store,
)


# =========================================================
# CONFIG
# =========================================================

TOP_K = 4


# =========================================================
# CREATE RETRIEVER
# =========================================================

def create_retriever():
    """
    Chroma vector store-ka u beddel retriever.

    k = inta chunks ee ugu dhow su'aasha
    la soo celinayo.
    """

    vector_store = load_vector_store()

    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": TOP_K,
        }
    )

    return retriever


# =========================================================
# RETRIEVE DOCUMENTS
# =========================================================

def retrieve_documents(
    question: str,
) -> list[Document]:
    """
    Su'aasha semantic search ku samee,
    kadib soo celi relevant chunks.
    """

    if not question.strip():
        raise ValueError(
            "Question-ku madhan ma noqon karo."
        )

    retriever = create_retriever()

    documents = retriever.invoke(
        question
    )

    return documents


# =========================================================
# DISPLAY RESULTS
# =========================================================

def show_results(
    question: str,
    documents: list[Document],
) -> None:
    """
    Soo bandhig chunks-ka retriever-ku helay.
    """

    print(
        "\n========================================"
    )

    print(
        "🔎 RETRIEVER RESULT"
    )

    print(
        "========================================"
    )

    print(
        f"\nQuestion:\n{question}"
    )

    print(
        f"\nChunks found: {len(documents)}"
    )

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

        print(
            "\n----------------------------------------"
        )

        print(
            f"CHUNK {index}"
        )

        print(
            "----------------------------------------"
        )

        print(
            f"Source: {source}"
        )

        print(
            f"Page: {page}"
        )

        print(
            "\nContent:"
        )

        print(
            document.page_content[:1000]
        )


# =========================================================
# MAIN
# =========================================================

def main() -> None:

    try:

        question = (
            "What are the main skills needed "
            "for personal development?"
        )

        documents = retrieve_documents(
            question
        )

        show_results(
            question,
            documents,
        )

    except Exception as error:

        print(
            f"\n❌ Retriever Error: {error}"
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()