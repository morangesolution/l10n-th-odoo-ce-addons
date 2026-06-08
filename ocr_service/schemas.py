from pydantic import BaseModel


class ExtractRequest(BaseModel):
    content: str       # base64-encoded file bytes
    filename: str
    mimetype: str      # application/pdf | image/png | image/jpeg


class InvoiceLine(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    tax_percent: float | None = None


class ExtractResponse(BaseModel):
    vendor_name: str | None = None
    vendor_vat: str | None = None
    vendor_address: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None   # YYYY-MM-DD
    due_date: str | None = None       # YYYY-MM-DD
    currency: str | None = None
    lines: list[InvoiceLine] = []
    subtotal: float | None = None
    tax_amount: float | None = None
    total: float | None = None
    confidence: float = 0.0           # 0.0 – 1.0
    raw_text: str | None = None
