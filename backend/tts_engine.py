import os
import httpx
from dotenv import load_dotenv

load_dotenv()

VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://localhost:50021")
SPEAKER_ID = int(os.getenv("SPEAKER_ID", "32")) # Default: Shirakami Kotaro (Wa-i)

async def generate_voice(text: str) -> bytes:
    """
    Generate audio (WAV) from text using VOICEVOX engine.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create synthesis query
        query_response = await client.post(
            f"{VOICEVOX_URL}/audio_query",
            params={"text": text, "speaker": SPEAKER_ID}
        )
        query_response.raise_for_status()
        query_data = query_response.json()

        # Modify query if needed (e.g. speed, pitch)
        # query_data["speedScale"] = 1.1

        # Synthesize audio
        synthesis_response = await client.post(
            f"{VOICEVOX_URL}/synthesis",
            params={"speaker": SPEAKER_ID},
            json=query_data
        )
        synthesis_response.raise_for_status()

        return synthesis_response.content
