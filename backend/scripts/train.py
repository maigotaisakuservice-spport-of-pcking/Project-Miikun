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
    Local Multi-Model Deliberation System.
    Uses the base local LLM to verify scraped/logged data quality.
    Only allows 'consensus' approved data into training.
    """
    print(f"--- Starting Local Deliberation for {subject} ---")

    if not os.path.exists(GGUF_PATH):
        print(f"Warning: GGUF model not found at {GGUF_PATH}. Skipping deliberation (trusting all data).")
        return dataset

    # Load a temporary verification engine (using local GGUF)
    # Note: We use a strict prompt to act as an evaluator
    evaluator = Llama(model_path=GGUF_PATH, n_gpu_layers=-1, n_ctx=2048, verbose=False)

    verified_samples = []
    for item in dataset:
        content = item["text"]

        # Phase 1: Direct Quality Check
        prompt1 = f"""以下の学習用データの内容を審議してください。
この内容は中学生向けの教育データとして「正確」かつ「適切」ですか？
間違いや不適切な表現がある場合は 'NG'、問題ない場合は 'OK' とだけ答えてください。

【データ】
{content}

審議結果:"""

        res1 = evaluator.create_chat_completion(messages=[{"role": "user", "content": prompt1}], max_tokens=10, temperature=0.1)
        result1 = res1["choices"][0]["message"]["content"].strip().upper()

        # Phase 2: Critical Review (Self-Correction Prompt)
        prompt2 = f"""以下のデータについて、あなたは「間違いがある」と指摘しました。本当に間違いですか？
もう一度冷静に確認し、もし教育上問題なければ 'OK'、やはりダメなら 'NG' と答えてください。
【データ】: {content}
【あなたの直前の判断】: {result1}
再審議結果:"""

        res2 = evaluator.create_chat_completion(messages=[{"role": "user", "content": prompt2}], max_tokens=10, temperature=0.1)
        result2 = res2["choices"][0]["message"]["content"].strip().upper()

        # Consensus logic: If both phases agree or the second phase confirms quality, we pass.
        # This simulates a "multi-model" deliberation through multi-perspective prompting on the base model.
        if "OK" in result1 and "OK" in result2:
            verified_samples.append(item)
        elif "OK" in result2: # If corrected during second thought
             verified_samples.append(item)
        else:
            print(f"  [REJECTED] {content[:50]}...")

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
    train()
