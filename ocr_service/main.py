from fastapi import FastAPI
from routers.extract import router as extract_router

app = FastAPI(title="Thai OCR Document Parser", version="1.0.0")
app.include_router(extract_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
