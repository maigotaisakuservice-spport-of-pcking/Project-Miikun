import os
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from typing import List, Dict, Optional
import subprocess
from dotenv import load_dotenv

from .db import init_db, insert_log
from .llm_engine import engine
from .tts_engine import generate_voice

load_dotenv()

app = FastAPI(title="Miikun Intelligence API")

API_KEY = os.getenv("API_KEY", "your_secret_api_key")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your_webhook_secret")

# Models for Request/Response
class ChatRequest(BaseModel):
    session_id: str
    text: str
    history: List[Dict[str, str]] = []

@app.on_event("startup")
async def startup_event():
    init_db()

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/chat", dependencies=[Depends(verify_api_key)])
async def chat(request: ChatRequest):
    """
    1. Inference with LLM
    2. Save log to SQLite
    3. Generate reply text (TTS audio is requested separately or as Base64?
       Let's return reply_text and frontend can call /api/tts/ or we combine.
       To reduce latency, let's just return reply_text for now and add TTS endpoint.
    )
    """
    reply_text = engine.generate_reply(request.history, request.text)
    insert_log(request.session_id, request.text, reply_text)

    return {
        "status": "success",
        "reply_text": reply_text
    }

@app.get("/api/tts", dependencies=[Depends(verify_api_key)])
async def tts(text: str):
    """
    Generates audio from text and returns a WAV stream.
    """
    try:
        audio_data = await generate_voice(text)
        return Response(content=audio_data, media_type="audio/wav")
    except Exception as e:
        print(f"TTS Error: {e}")
        raise HTTPException(status_code=500, detail="Voice synthesis failed")

@app.post("/api/webhook/reload")
async def reload_lora(authorization: str = Header(...)):
    """
    Webhook called by GitHub Actions after training/deployment.
    Authorization: Bearer <WEBHOOK_SECRET>
    """
    if authorization != f"Bearer {WEBHOOK_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # 1. Pull latest code/models
        # Note: Working directory needs to be root or we specify cwd
        subprocess.run(["git", "pull", "origin", "main"], cwd=os.getcwd(), check=True)

        # 2. Reload engine with new LoRA
        engine.reload_lora()

        return {"status": "success", "message": "Model updated and reloaded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reload failed: {str(e)}")

# Add a combined endpoint if we want lower latency (Text + Base64 Audio)
@app.post("/api/chat_full", dependencies=[Depends(verify_api_key)])
async def chat_full(request: ChatRequest):
    reply_text = engine.generate_reply(request.history, request.text)
    insert_log(request.session_id, request.text, reply_text)

    try:
        audio_data = await generate_voice(reply_text)
        import base64
        audio_base64 = base64.b64encode(audio_data).decode("utf-8")
        return {
            "status": "success",
            "reply_text": reply_text,
            "audio": audio_base64
        }
    except Exception as e:
        # Fallback to text only
        return {
            "status": "success",
            "reply_text": reply_text,
            "audio": None,
            "error": "TTS failed"
        }
