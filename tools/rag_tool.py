from pathlib import Path

import chromadb
from openai import OpenAI
from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "documents"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

openai_client = OpenAI()

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = chroma_client.get_or_create_collection(
    name="pdf_documents"
)


def extract_pdf_text(file_name: str) -> str:
    """Ka soo saar qoraalka PDF-ga."""

    pdf_path = DOCUMENTS_DIR / file_name

    if not pdf_path.exists():
        return ""

    reader = PdfReader(str(pdf_path))

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[str]:
    """Qoraalka u kala jar chunks is dul saaran."""

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def create_embedding(text: str) -> list[float]:
    """Qoraalka u beddel vector embedding."""

    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )

    return response.data[0].embedding


def index_pdf(file_name: str) -> str:
    """PDF akhri, chunk garee, kadib ChromaDB geli."""

    text = extract_pdf_text(file_name)

    if not text:
        return (
            f"Error: PDF-ga '{file_name}' lama helin "
            "ama qoraal lagama soo saari karin."
        )

    chunks = chunk_text(text)

    if not chunks:
        return "Error: Wax chunks ah lama samayn."

    for index, chunk in enumerate(chunks):
        embedding = create_embedding(chunk)

        chunk_id = f"{file_name}-{index}"

        collection.upsert(
            ids=[chunk_id],
            documents=[chunk],
            embeddings=[embedding],
            metadatas=[
                {
                    "file_name": file_name,
                    "chunk": index,
                }
            ],
        )

    return (
        f"PDF indexed successfully: {file_name}\n"
        f"Chunks: {len(chunks)}"
    )


def search_pdf(
    file_name: str,
    question: str,
    n_results: int = 4,
) -> str:
    """Ka raadi chunks-ka ugu dhow su'aasha."""

    question_embedding = create_embedding(question)

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=n_results,
        where={
            "file_name": file_name,
        },
    )

    documents = results.get("documents", [])

    if not documents or not documents[0]:
        return (
            f"Wax xog ah lagama helin PDF-ga '{file_name}'. "
            "Hubi in marka hore la index gareeyay."
        )

    chunks = documents[0]

    output = []

    for number, chunk in enumerate(chunks, start=1):
        output.append(
            f"--- Relevant Chunk {number} ---\n{chunk}"
        )

    return "\n\n".join(output)