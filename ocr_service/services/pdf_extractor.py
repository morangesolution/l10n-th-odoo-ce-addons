import io
import base64
import pdfplumber
from pdf2image import convert_from_bytes
from PIL import Image


def extract_text_from_pdf(content: bytes) -> tuple[str, bool]:
    """Extract text from PDF bytes.

    Returns (text, is_scanned). is_scanned=True means text was too short
    (image-based PDF) and the caller should use vision instead.
    """
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages_text = [page.extract_text() or "" for page in pdf.pages]
        text = "\n".join(pages_text).strip()
    except Exception:
        text = ""

    from config import settings
    is_scanned = len(text) < settings.scanned_text_threshold
    return text, is_scanned


def pdf_to_base64_image(content: bytes, page: int = 0) -> str:
    """Convert the first page of a PDF to a base64-encoded PNG for vision."""
    images = convert_from_bytes(content, first_page=page + 1, last_page=page + 1, dpi=150)
    if not images:
        raise ValueError("Could not convert PDF page to image")
    buf = io.BytesIO()
    images[0].save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def image_bytes_to_base64(content: bytes, mimetype: str) -> str:
    """Return base64 string of image bytes (already in correct format)."""
    return base64.b64encode(content).decode()
