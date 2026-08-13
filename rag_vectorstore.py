from pathlib import Path
import shutil

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from rag_loader import (
    load_documents,
    split_documents,
)


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# CONFIG
# =========================================================

CHROMA_DIR = Path("rag_chroma_db")

COLLECTION_NAME = "lesson24_documents"

EMBEDDING_MODEL = "text-embedding-3-small"


# =========================================================
# CREATE EMBEDDINGS
# =========================================================

def create_embeddings() -> OpenAIEmbeddings:
    """
    Embedding model-ka RAG.
    """

    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
    )


# =========================================================
# DELETE OLD VECTOR STORE
# =========================================================

def reset_vector_store() -> None:
    """
    Database-kii hore tirtir.

    Tani waxay faa'iido leedahay inta aan
    development/testing ku jirno si chunks
    isku mid ah marar badan aan loo kaydin.
    """

    if CHROMA_DIR.exists():

        print(
            f"🗑️ Removing old vector store: "
            f"{CHROMA_DIR}"
        )

        shutil.rmtree(
            CHROMA_DIR
        )


# =========================================================
# BUILD VECTOR STORE
# =========================================================

def build_vector_store(
    reset: bool = True,
) -> Chroma:
    """
    Pipeline:

    PDFs
      ↓
    Documents
      ↓
    Chunks
      ↓
    Embeddings
      ↓
    Chroma
    """

    print(
        "📚 Loading documents..."
    )

    documents = load_documents()

    print(
        f"\nPages loaded: {len(documents)}"
    )

    print(
        "\n✂️ Splitting documents..."
    )

    chunks = split_documents(
        documents
    )

    print(
        f"Chunks created: {len(chunks)}"
    )

    if not chunks:

        raise RuntimeError(
            "Wax chunks ah lama helin."
        )

    if reset:
        reset_vector_store()

    print(
        "\n🧠 Creating embeddings + "
        "Chroma vector store..."
    )

    embeddings = create_embeddings()

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(
            CHROMA_DIR
        ),
    )

    print(
        "\n✅ Vector store created."
    )

    return vector_store


# =========================================================
# LOAD EXISTING VECTOR STORE
# =========================================================

def load_vector_store() -> Chroma:
    """
    Disk-ka ka fur vector database hore loo sameeyay.
    """

    if not CHROMA_DIR.exists():

        raise FileNotFoundError(
            "Vector database lama helin. "
            "Marka hore build_vector_store() orod."
        )

    embeddings = create_embeddings()

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(
            CHROMA_DIR
        ),
    )

    return vector_store


# =========================================================
# TEST SIMILARITY SEARCH
# =========================================================

def test_search(
    vector_store: Chroma,
) -> None:
    """
    Samee semantic similarity search.
    """

    question = (
        "What skills are important "
        "for personal development?"
    )

    print(
        "\n========================================"
    )

    print(
        "🔎 SEMANTIC SEARCH TEST"
    )

    print(
        "========================================"
    )

    print(
        f"\nQuestion:\n{question}"
    )

    results = vector_store.similarity_search(
        question,
        k=3,
    )

    print(
        f"\nResults found: {len(results)}"
    )

    for index, document in enumerate(
        results,
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
            f"RESULT {index}"
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
            document.page_content[:800]
        )


# =========================================================
# SHOW DATABASE INFO
# =========================================================

def show_database_info(
    vector_store: Chroma,
) -> None:
    """
    Chroma collection-ka tirada records-ka muuji.
    """

    try:

        count = (
            vector_store
            ._collection
            .count()
        )

        print(
            "\n========================================"
        )

        print(
            "🗄️ CHROMA DATABASE"
        )

        print(
            "========================================"
        )

        print(
            f"Directory: {CHROMA_DIR}"
        )

        print(
            f"Collection: {COLLECTION_NAME}"
        )

        print(
            f"Stored chunks: {count}"
        )

        print(
            f"Embedding model: {EMBEDDING_MODEL}"
        )

    except Exception as error:

        print(
            f"Database count unavailable: {error}"
        )


# =========================================================
# MAIN
# =========================================================

def main() -> None:

    try:

        vector_store = build_vector_store(
            reset=True,
        )

        show_database_info(
            vector_store
        )

        test_search(
            vector_store
        )

    except Exception as error:

        print(
            f"\n❌ Vector Store Error: {error}"
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()