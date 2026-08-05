from pathlib import Path

from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_FOLDER = PROJECT_ROOT / "documents"


def read_pdf(file_name: str, max_characters: int = 12000) -> str:
    """
    Ka soo saar qoraalka PDF ku jira folder-ka documents.

    file_name:
        Tusaale: sample.pdf

    max_characters:
        Tirada ugu badan ee xarfo loo celinayo AI model-ka.
    """

    if not file_name or not file_name.strip():
        return "Error: Magaca PDF-ga lama bixin."

    # Path(file_name).name wuxuu ka saarayaa folder aan la oggolayn.
    safe_file_name = Path(file_name.strip()).name
    pdf_path = DOCUMENTS_FOLDER / safe_file_name

    if pdf_path.suffix.lower() != ".pdf":
        return "Error: File-ku waa inuu noqdaa PDF."

    if not pdf_path.exists():
        return (
            f"Error: PDF-ga '{safe_file_name}' lama helin.\n"
            f"Ku rid gudaha folder-kan: {DOCUMENTS_FOLDER}"
        )

    try:
        reader = PdfReader(str(pdf_path))

        if reader.is_encrypted:
            return "Error: PDF-ga wuxuu leeyahay password ama encryption."

        extracted_pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""

            if page_text.strip():
                extracted_pages.append(
                    f"\n--- Bogga {page_number} ---\n{page_text.strip()}"
                )
            else:
                extracted_pages.append(
                    f"\n--- Bogga {page_number} ---\n"
                    "[Qoraal lagama soo saari karin boggan]"
                )

        full_text = "\n".join(extracted_pages).strip()

        if not full_text:
            return (
                "Error: Wax qoraal ah lagama soo saari karin PDF-ga. "
                "Waxaa laga yaabaa inuu yahay PDF sawir ahaan loo scan-gareeyay."
            )

        was_shortened = len(full_text) > max_characters
        returned_text = full_text[:max_characters]

        result = (
            f"File: {safe_file_name}\n"
            f"Bogag: {len(reader.pages)}\n"
            f"Xarfo la soo saaray: {len(full_text)}\n"
            f"\nQoraalka PDF-ga:\n{returned_text}"
        )

        if was_shortened:
            result += (
                "\n\n[Ogeysiis: PDF-gu wuu dheeraa; qayb ka mid ah "
                "qoraalka oo keliya ayaa la soo celiyay.]"
            )

        return result

    except Exception as error:
        return f"Error reading PDF: {error}"