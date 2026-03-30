import os
from fastapi import FastAPI, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from typing import List, Dict, Optional
import subprocess
import os
from dotenv import load_dotenv

from .db import init_db, insert_log, get_memories, update_memory
from .llm_engine import engine
from .tts_engine import generate_voice

load_dotenv()

app = FastAPI(title="Miikun Intelligence API")

# Security Config
SHARED_SECRET = os.getenv("SHARED_SECRET", "miikun_shared_pass") # Visible in frontend source
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your_webhook_secret")
MASTER_SECRET = os.getenv("MASTER_SECRET", "your_admin_master_secret") # NOT visible in frontend
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# CORS Middleware for Domain-based security
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models for Request/Response
class ChatRequest(BaseModel):
    session_id: str
    subject: str = "general"
    text: str
    history: List[Dict[str, str]] = []

@app.on_event("startup")
async def startup_event():
    init_db()

async def verify_shared_secret(x_api_key: str = Header(...)):
    """
    Check the 'Shared Secret' from frontend.
    Note: Domain restriction (CORS) is the primary security for frontend clients.
    """
    if x_api_key != SHARED_SECRET:
        raise HTTPException(status_code=403, detail="Invalid Shared Secret")

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/chat", dependencies=[Depends(verify_shared_secret)])
async def chat(request: ChatRequest):
    memories = get_memories(request.session_id, request.subject)
    result = engine.generate_reply(request.history, request.text, subject=request.subject, memories=memories)
    reply_text = result["reply"]
    emotion = result["emotion"]

    insert_log(request.session_id, request.subject, request.text, reply_text)

    return {
        "status": "success",
        "reply_text": reply_text,
        "emotion": emotion
    }

@app.get("/api/tts", dependencies=[Depends(verify_shared_secret)])
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

@app.post("/api/admin/train")
async def trigger_manual_train(authorization: str = Header(...)):
    """
    1. Run log export.
    2. Trigger GitHub Actions via Repository Dispatch.
    Secured by MASTER_SECRET.
    """
    if authorization != f"Bearer {MASTER_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # 1. Export Logs
        export_result = subprocess.run(
            ["python3", "backend/scripts/export_logs.py"],
            capture_output=True, text=True, check=True
        )

        # 2. Trigger GHA (Optional if secrets are set)
        repo = os.getenv("GH_REPO") # e.g. "user/repo"
        token = os.getenv("GH_PAT")

        gha_status = "skipped (no GH_PAT)"
        if repo and token:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.github.com/repos/{repo}/dispatches",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github.v3+json"
                    },
                    json={"event_type": "manual_train"}
                )
                gha_status = f"triggered (Status: {response.status_code})"

        return {
            "status": "success",
            "message": f"Log export complete. GHA {gha_status}.",
            "export_output": export_result.stdout
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
@app.post("/api/chat_full", dependencies=[Depends(verify_shared_secret)])
async def chat_full(request: ChatRequest):
    memories = get_memories(request.session_id, request.subject)
    result = engine.generate_reply(request.history, request.text, subject=request.subject, memories=memories)
    reply_text = result["reply"]
    emotion = result["emotion"]

    insert_log(request.session_id, request.subject, request.text, reply_text)

    # Memory extraction
    new_memories = engine.extract_memories(request.text, reply_text)
    for k, v in new_memories.items():
        update_memory(request.session_id, request.subject, k, v)

    try:
        audio_data = await generate_voice(reply_text)
        import base64
        audio_base64 = base64.b64encode(audio_data).decode("utf-8")
        return {
            "status": "success",
            "reply_text": reply_text,
            "emotion": emotion,
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
