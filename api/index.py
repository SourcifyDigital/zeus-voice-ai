from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from mangum import Mangum
import uuid

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "ok", "name": "Zeus Voice AI API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/ask")
async def ask(text: str):
    # For the demo, return a simple echo response
    return {
        "transcript": text,
        "text": f"You said: {text}",
        "audio_url": None
    }

handler = Mangum(app)
