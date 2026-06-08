import json
from openai import OpenAI
from config import settings
from schemas import ExtractResponse

_SYSTEM_PROMPT = """\
You are a document OCR assistant. Extract invoice/bill information from the provided content and return valid JSON.
Always return a JSON object with these exact keys (use null for missing values):
vendor_name, vendor_vat, vendor_address, invoice_number, invoice_date (YYYY-MM-DD),
due_date (YYYY-MM-DD), currency (ISO code), lines (array of objects with keys:
description, quantity, unit_price, tax_percent), subtotal, tax_amount, total, confidence (0.0-1.0).
For Thai documents: vendor_vat is the 13-digit tax ID, vendor_address may include branch info.
Only extract what you can clearly read. Set confidence < 0.5 if the document is unclear or not a bill/invoice.
"""

_USER_TEXT_PROMPT = "Extract all invoice/bill fields from this document text:\n\n{text}"
_USER_IMAGE_PROMPT = "Extract all invoice/bill fields from this document image."


def _get_client() -> OpenAI:
    extra_headers = {}
    if settings.llm_site_url:
        extra_headers["HTTP-Referer"] = settings.llm_site_url
    if settings.llm_site_name:
        extra_headers["X-Title"] = settings.llm_site_name
    return OpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key or "none",
        default_headers=extra_headers or None,
    )


def extract_from_text(text: str) -> ExtractResponse:
    client = _get_client()
    response = client.chat.completions.create(
        model=settings.llm_model,
        **({"response_format": {"type": "json_object"}} if settings.llm_json_mode else {}),
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _USER_TEXT_PROMPT.format(text=text)},
        ],
        timeout=settings.ocr_timeout,
    )
    raw = response.choices[0].message.content or "{}"
    return _parse_response(raw, text)


def extract_from_image(image_b64: str, mimetype: str = "image/png") -> ExtractResponse:
    client = _get_client()
    response = client.chat.completions.create(
        model=settings.llm_vision_model,
        **({"response_format": {"type": "json_object"}} if settings.llm_json_mode else {}),
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _USER_IMAGE_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mimetype};base64,{image_b64}"},
                    },
                ],
            },
        ],
        timeout=settings.ocr_timeout,
    )
    raw = response.choices[0].message.content or "{}"
    return _parse_response(raw, None)


def _parse_response(raw: str, raw_text: str | None) -> ExtractResponse:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return ExtractResponse(confidence=0.0, raw_text=raw_text)

    lines = []
    for item in data.get("lines") or []:
        lines.append(
            {
                "description": str(item.get("description") or ""),
                "quantity": float(item.get("quantity") or 1),
                "unit_price": float(item.get("unit_price") or 0),
                "tax_percent": float(item["tax_percent"]) if item.get("tax_percent") is not None else None,
            }
        )
    data["lines"] = lines
    data["raw_text"] = raw_text

    try:
        return ExtractResponse(**data)
    except Exception:
        return ExtractResponse(confidence=0.0, raw_text=raw_text)
