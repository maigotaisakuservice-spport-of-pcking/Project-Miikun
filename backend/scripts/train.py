import os
import sys
import time
import torch
import glob
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
from llama_cpp import Llama

# Configs
# BASE_MODEL should be the Hugging Face repo ID for training
BASE_MODEL = os.getenv("BASE_MODEL", "elyza/ELYZA-japanese-Llama-2-7b-instruct")
# GGUF_PATH should be the local path to the GGUF model for deliberation
GGUF_PATH = os.getenv("MODEL_PATH", "models/base_model.gguf")
OUTPUT_DIR = "models/active_lora/"
MAX_MINUTES = 25 # Training timeout safety guard

def deliberate_and_filter(dataset, subject):
    """
    Local Multi-Model Deliberation System (V2: 3-Persona Voting).
    Uses three distinct personas to vote on data quality and PII removal.
    A majority (2/3) is required for approval.
    """
    print(f"--- Starting 3-Model Deliberation for {subject} ---")

    if not os.path.exists(GGUF_PATH):
        print(f"Warning: GGUF model not found at {GGUF_PATH}. Skipping deliberation.")
        return dataset

    evaluator = Llama(model_path=GGUF_PATH, n_gpu_layers=-1, n_ctx=2048, verbose=False)

    # Define Personas
    personas = [
        {"name": "Strict Teacher", "prompt": "あなたは非常に厳格な中学校の教師です。教育的に不適切な内容や、少しでも個人情報（名前、住所等）が含まれていれば即座に 'NG' と判定します。"},
        {"name": "Objective Researcher", "prompt": "あなたは客観的なデータ研究者です。事実関係が正確か、個人情報の漏洩リスクがないかを冷静に分析し、合格なら 'OK'、不合格なら 'NG' と判定します。"},
        {"name": "Friendly Senior Student", "prompt": "あなたは頼りになる中学3年生の先輩です。後輩に見せても恥ずかしくない内容か、誰かのプライバシーを傷つけていないかをチェックして 'OK' か 'NG' を出します。"}
    ]

    verified_samples = []
    for item in dataset:
        content = item["text"]
        votes = []

        for p in personas:
            full_prompt = f"""{p['prompt']}
以下の学習用データを審議し、'OK' または 'NG' で回答してください。

【審議基準】
1. 中学生向けの学習内容として正確か。
2. 歴史上の人物以外の一般人の名前（生徒名、教師名など）が含まれていないか。
3. 住所、電話番号、SNSアカウントなどの個人情報が含まれていないか。

【データ】
{content}

判定（OK/NG）:"""
            res = evaluator.create_chat_completion(messages=[{"role": "user", "content": full_prompt}], max_tokens=10, temperature=0.1)
            vote = res["choices"][0]["message"]["content"].strip().upper()
            votes.append("OK" in vote)

        # 2/3 Majority Consensus
        if sum(votes) >= 2:
            verified_samples.append(item)
        else:
            rejected_reason = [personas[i]['name'] for i, v in enumerate(votes) if not v]
            print(f"  [REJECTED by {', '.join(rejected_reason)}] {content[:50]}...")

    print(f"Deliberation complete. {len(verified_samples)}/{len(dataset)} samples verified.")
    return verified_samples

def train_subject(subject, data_file):
    print(f"\n>>> Starting training for Subject: {subject} <<<")

    # Load raw data
    import json
    raw_data = []
    with open(data_file, "r", encoding="utf-8") as f:
        for line in f:
            raw_data.append(json.loads(line))

    # Local Deliberation Phase
    verified_data = deliberate_and_filter(raw_data, subject)
    if not verified_data:
        print(f"Skipping {subject}: No data passed local deliberation.")
        return

    # Save verified data to temp file for SFTTrainer
    verified_file = f"verified_{data_file}"
    with open(verified_file, "w", encoding="utf-8") as f:
        for item in verified_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    dataset = load_dataset("json", data_files=verified_file, split="train")

    print(f"Loading base model and tokenizer for training {subject}...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    model = prepare_model_for_kbit_training(model)

    peft_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, peft_config)

    training_args = TrainingArguments(
        output_dir=f"./tmp_lora_{subject}",
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-5,
        max_steps=50, # Optimized for speed
        save_strategy="no",
        fp16=True,
        optim="paged_adamw_32bit",
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset, # Use verified_data in real impl
        peft_config=peft_config,
        dataset_text_field="text",
        max_seq_length=1024,
        tokenizer=tokenizer,
        args=training_args,
    )

    trainer.train()

    # Save to dedicated subject subfolder
    subject_output = os.path.join(OUTPUT_DIR, subject)
    os.makedirs(subject_output, exist_ok=True)
    trainer.model.save_pretrained(subject_output)
    print(f"Successfully saved {subject} adapter to {subject_output}")

def train():
    start_time = time.time()

    # CUDA Check
    if not torch.cuda.is_available():
        print("Error: CUDA is not available. Training requires a GPU.")
        sys.exit(0)

    # Gather data files
    data_files = glob.glob("train_data_*.jsonl")
    if os.path.exists("scraped_data.jsonl"):
        data_files.append("scraped_data.jsonl")

    if not data_files:
        # Fallback to standard train_data.jsonl if exists
        if os.path.exists("train_data.jsonl"):
            data_files.append("train_data.jsonl")
        else:
            print("No training data found.")
            sys.exit(0)

    for df in data_files:
        # Extract subject from filename
        if "scraped_data.jsonl" in df:
            subject = "general"
        elif "train_data_" in df:
            subject = df.replace("train_data_", "").replace(".jsonl", "")
        else:
            subject = "general"

        train_subject(subject, df)

        # Timeout safety check
        if (time.time() - start_time) / 60 > MAX_MINUTES:
            print("Global training time limit reached. Stopping further training.")
            break

    elapsed = (time.time() - start_time) / 60
    print(f"Total training process finished in {elapsed:.2f} minutes.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", type=str, default=None)
    parser.add_argument("--data", type=str, default=None)
    args = parser.parse_args()

    if args.subject and args.data:
        # Single subject mode (used by parallel Actions)
        train_subject(args.subject, args.data)
    else:
        # Batch mode (used by VPS)
        train()
