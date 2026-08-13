from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


# =========================================================
# CONFIG
# =========================================================

DOCUMENTS_DIR = Path("documents")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


# =========================================================
# LOAD ONE PDF
# =========================================================

def load_pdf(
    pdf_path: Path,
) -> list[Document]:
    """
    Hal PDF file akhri.
    """

    print(
        f"📄 Loading: {pdf_path.name}"
    )

    loader = PyPDFLoader(
        str(pdf_path)
    )

    documents = loader.load()

    return documents


# =========================================================
# LOAD ALL PDFs
# =========================================================

def load_documents() -> list[Document]:
    """
    documents/ folder-ka ka load garee
    dhammaan PDF files.
    """

    if not DOCUMENTS_DIR.exists():

        raise FileNotFoundError(
            "documents/ folder lama helin."
        )

    pdf_files = sorted(
        DOCUMENTS_DIR.glob("*.pdf")
    )

    if not pdf_files:

        raise FileNotFoundError(
            "Wax PDF files ah lagama helin "
            "documents/ folder-ka."
        )

    all_documents: list[Document] = []

    for pdf_path in pdf_files:

        try:

            documents = load_pdf(
                pdf_path
            )

            all_documents.extend(
                documents
            )

            print(
                f"   ✅ {len(documents)} pages loaded"
            )

        except Exception as error:

            print(
                f"   ❌ Failed: {error}"
            )

    if not all_documents:

        raise RuntimeError(
            "Wax document ah lama load-gareyn."
        )

    return all_documents


# =========================================================
# CREATE TEXT SPLITTER
# =========================================================

def create_text_splitter() -> RecursiveCharacterTextSplitter:
    """
    Samee text splitter.

    chunk_size:
        inta characters chunk kasta leeyahay.

    chunk_overlap:
        inta characters ee laba chunk
        ay wadaagaan.
    """

    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )


# =========================================================
# SPLIT DOCUMENTS INTO CHUNKS
# =========================================================

def split_documents(
    documents: list[Document],
) -> list[Document]:
    """
    Documents/pages-ka u kala jar chunks.
    """

    splitter = create_text_splitter()

    chunks = splitter.split_documents(
        documents
    )

    return chunks


# =========================================================
# SHOW CHUNK INFO
# =========================================================

def show_chunk_info(
    documents: list[Document],
    chunks: list[Document],
) -> None:
    """
    Soo bandhig statistics iyo sample chunk.
    """

    print(
        "\n========================================"
    )

    print(
        "✂️ TEXT SPLITTING RESULT"
    )

    print(
        "========================================"
    )

    print(
        f"Original pages/documents: {len(documents)}"
    )

    print(
        f"Total chunks: {len(chunks)}"
    )

    print(
        f"Chunk size: {CHUNK_SIZE}"
    )

    print(
        f"Chunk overlap: {CHUNK_OVERLAP}"
    )

    if not chunks:
        return

    first_chunk = chunks[0]

    print(
        "\n--- First Chunk Metadata ---"
    )

    print(
        first_chunk.metadata
    )

    print(
        "\n--- First Chunk Length ---"
    )

    print(
        len(first_chunk.page_content)
    )

    print(
        "\n--- First Chunk Preview ---"
    )

    print(
        first_chunk.page_content[:1000]
    )

    print(
        "\n========================================"
    )


# =========================================================
# MAIN
# =========================================================

def main() -> None:

    try:

        documents = load_documents()

        chunks = split_documents(
            documents
        )

        show_chunk_info(
            documents,
            chunks,
        )

    except Exception as error:

        print(
            f"\n❌ RAG Loader Error: {error}"
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()