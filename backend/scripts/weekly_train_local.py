import os
import sys
import subprocess
import time
from datetime import datetime

# Set working directory to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(PROJECT_ROOT)

def run_step(name, cmd):
    print(f"\n--- {name} ---")
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during {name}: {e}")
        return False
    return True

def main():
    print(f"Weekly Training Started at {datetime.now()}")

    # 1. Export logs from SQLite to JSONL
    if not run_step("Exporting Logs", f"{PROJECT_ROOT}/venv/bin/python backend/scripts/export_logs.py"):
        sys.exit(1)

    # 2. Check if training data exists and has enough samples
    # (export_logs.py handles the 50-sample limit, but we check existence here)
    if not os.path.exists("train_data.jsonl") and not any(os.path.exists(f) for f in os.listdir(".") if f.startswith("train_data_")):
        print("No training data generated (likely insufficient new logs). Skipping training.")
        sys.exit(0)

    # 3. Run LoRA training locally on VPS (includes Deliberation)
    # We use the local environment variables or .env
    if not run_step("LoRA Training & Deliberation", f"{PROJECT_ROOT}/venv/bin/python backend/scripts/train.py"):
        sys.exit(1)

    # 4. Git Push the new weights (to keep monorepo in sync)
    print("\n--- Syncing weights to GitHub ---")
    subprocess.run("git add models/active_lora/ && git commit -m 'Weekly Auto-Learning Update' && git push origin main", shell=True)

    # 5. Hot Reload the backend
    # This calls the internal reload logic (or we can just wait for the webhook/manual reload)
    # Since we are local, we can just hit our own API
    webhook_secret = os.getenv("WEBHOOK_SECRET")
    if webhook_secret:
        import requests
        print("\n--- Triggering Hot Reload ---")
        try:
            res = requests.post("http://127.0.0.1:8000/api/webhook/reload",
                                headers={"Authorization": f"Bearer {webhook_secret}"})
            print(f"Reload status: {res.status_code}")
        except Exception as e:
            print(f"Reload failed: {e}")

    print(f"\nWeekly Training Finished at {datetime.now()}")

if __name__ == "__main__":
    main()
