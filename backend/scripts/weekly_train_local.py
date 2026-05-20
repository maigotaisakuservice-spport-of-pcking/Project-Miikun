import os
import subprocess
import time
import logging
from datetime import datetime

# Configuration
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # miikun-core/backend
PROJECT_ROOT = os.path.dirname(BACKEND_DIR) # miikun-core
LOG_EXPORT_SCRIPT = os.path.join(BACKEND_DIR, "scripts/export_logs.py")
TRAIN_SCRIPT = os.path.join(BACKEND_DIR, "scripts/train.py")
DATA_DIR = os.path.join(BACKEND_DIR, "data")
VENV_PYTHON = os.path.join(PROJECT_ROOT, "venv/bin/python3")

logging.basicConfig(
    filename=os.path.join(DATA_DIR, "weekly_train.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_step(command, description):
    logging.info(f"Starting: {description}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logging.info(f"Finished: {description}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during {description}: {e.stderr}")
        return False

def main():
    logging.info("=== Starting Weekly Local Training Cycle ===")

    # 1. Export logs from SQLite to JSONL
    if not run_step([VENV_PYTHON, LOG_EXPORT_SCRIPT], "Log Export"):
        return

    # 2. Run Training with 3-Model Deliberation
    # This script will pick up the exported JSONL files and perform filtering + training
    if not run_step([VENV_PYTHON, TRAIN_SCRIPT], "Model Training (LoRA)"):
        return

    # 3. Trigger Reload (Optional if backend is running)
    # The reload can be done via a simple internal function call or via HTTP to itself
    import httpx
    try:
        WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your_webhook_secret")
        # We assume the server is running on localhost:8000
        with httpx.Client() as client:
            client.post(
                "http://127.0.0.1:8000/api/webhook/reload",
                headers={"Authorization": f"Bearer {WEBHOOK_SECRET}"}
            )
        logging.info("Hot Reload triggered successfully.")
    except Exception as e:
        logging.warning(f"Failed to trigger hot reload automatically: {e}")

    logging.info("=== Weekly Local Training Cycle Completed ===")

if __name__ == "__main__":
    main()
