import sqlite3
import json
import os
import sys

# Paths relative to backend root or script location
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "logs.db")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "train_data.jsonl")

def export_logs():
    if not os.path.exists(DB_PATH):
        print(f"Error: DB not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get subjects that have new logs
    cursor.execute("SELECT DISTINCT subject FROM chat_logs WHERE is_used_for_training = 0")
    subjects = [row["subject"] for row in cursor.fetchall()]

    for subject in subjects:
        cursor.execute("SELECT id, user_text, ai_text FROM chat_logs WHERE subject = ? AND is_used_for_training = 0", (subject,))
        rows = cursor.fetchall()

        if len(rows) < 10: # Lower limit per subject
            continue

        print(f"Exporting {len(rows)} logs for subject: {subject}")
        output_file = os.path.join(os.path.dirname(__file__), "..", "..", f"train_data_{subject}.jsonl")

        with open(output_file, "w", encoding="utf-8") as f:
            for row in rows:
                data = {
                    "text": f"### Subject: {subject}\n### User: {row['user_text']}\n### Assistant: {row['ai_text']}"
                }
                f.write(json.dumps(data, ensure_ascii=False) + "\n")

        # Mark as used
        ids = [row["id"] for row in rows]
        cursor.execute(f"UPDATE chat_logs SET is_used_for_training = 1 WHERE id IN ({','.join(['?']*len(ids))})", ids)
    conn.commit()
    conn.close()

    print(f"Export complete: {OUTPUT_FILE}")

if __name__ == "__main__":
    export_logs()
