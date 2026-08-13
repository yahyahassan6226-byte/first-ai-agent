from dotenv import load_dotenv
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

EMBEDDING_MODEL = "text-embedding-3-small"


# =========================================================
# CREATE EMBEDDING MODEL
# =========================================================

def create_embeddings() -> OpenAIEmbeddings:
    """
    Samee OpenAI embedding model.
    """

    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
    )


# =========================================================
# EMBED ONE TEXT
# =========================================================

def embed_text(
    text: str,
) -> list[float]:
    """
    Hal qoraal u beddel embedding vector.
    """

    embeddings = create_embeddings()

    vector = embeddings.embed_query(
        text
    )

    return vector


# =========================================================
# TEST CHUNK EMBEDDING
# =========================================================

def test_chunk_embedding() -> None:
    """
    Load PDFs -> split chunks ->
    chunk-ka ugu horreeya embedding u samee.
    """

    print(
        "📚 Loading documents..."
    )

    documents = load_documents()

    print(
        "\n✂️ Splitting documents..."
    )

    chunks = split_documents(
        documents
    )

    print(
        f"\nTotal chunks: {len(chunks)}"
    )

    if not chunks:
        raise RuntimeError(
            "Wax chunks ah lama helin."
        )

    first_chunk = chunks[0]

    print(
        "\n📝 First chunk:"
    )

    print(
        first_chunk.page_content[:300]
    )

    print(
        "\n🧠 Creating embedding..."
    )

    embeddings = create_embeddings()

    vector = embeddings.embed_query(
        first_chunk.page_content
    )

    print(
        "\n========================================"
    )

    print(
        "🧠 EMBEDDING RESULT"
    )

    print(
        "========================================"
    )

    print(
        f"Model: {EMBEDDING_MODEL}"
    )

    print(
        f"Vector dimensions: {len(vector)}"
    )

    print(
        "\nFirst 10 vector values:"
    )

    print(
        vector[:10]
    )

    print(
        "\nSource:"
    )

    print(
        first_chunk.metadata.get(
            "source",
            "Unknown",
        )
    )

    print(
        "\nPage:"
    )

    print(
        first_chunk.metadata.get(
            "page_label",
            first_chunk.metadata.get(
                "page",
                "Unknown",
            ),
        )
    )

    print(
        "\n========================================"
    )


# =========================================================
# SIMPLE SEMANTIC TEST
# =========================================================

def test_query_embedding() -> None:
    """
    User question embedding u samee.
    """

    question = (
        "What skills are important "
        "for personal development?"
    )

    print(
        "\n🔎 Test question:"
    )

    print(
        question
    )

    vector = embed_text(
        question
    )

    print(
        f"\nQuery vector dimensions: {len(vector)}"
    )

    print(
        "First 10 values:"
    )

    print(
        vector[:10]
    )


# =========================================================
# MAIN
# =========================================================

def main() -> None:

    try:

        test_chunk_embedding()

        test_query_embedding()

    except Exception as error:

        print(
            f"\n❌ Embedding Error: {error}"
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()