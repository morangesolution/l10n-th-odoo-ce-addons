import base64
from fastapi import APIRouter, HTTPException
from schemas import ExtractRequest, ExtractResponse
from services.pdf_extractor import extract_text_from_pdf, pdf_to_base64_image, image_bytes_to_base64
from services.llm_client import extract_from_text, extract_from_image

router = APIRouter()


@router.post("/extract", response_model=ExtractResponse)
async def extract(req: ExtractRequest) -> ExtractResponse:
    try:
        content = base64.b64decode(req.content)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 content")

    mimetype = req.mimetype.lower()

    if mimetype == "application/pdf":
        text, is_scanned = extract_text_from_pdf(content)
        if is_scanned:
            image_b64 = pdf_to_base64_image(content)
            result = extract_from_image(image_b64, mimetype="image/png")
        else:
            result = extract_from_text(text)
            result.raw_text = text
    elif mimetype in ("image/png", "image/jpeg", "image/jpg"):
        image_b64 = image_bytes_to_base64(content, mimetype)
        result = extract_from_image(image_b64, mimetype=mimetype)
    else:
        raise HTTPException(status_code=415, detail=f"Unsupported mimetype: {req.mimetype}")

    return result
