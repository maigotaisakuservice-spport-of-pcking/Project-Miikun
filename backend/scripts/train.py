import os
import sys
import time
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer

# Configs
BASE_MODEL = os.getenv("BASE_MODEL", "elyza/ELYZA-japanese-Llama-3-8B-Instruct")
TRAIN_DATA = "train_data.jsonl"
OUTPUT_DIR = "models/active_lora/"
MAX_MINUTES = 25 # Training timeout safety guard

def train():
    start_time = time.time()

    if not os.path.exists(TRAIN_DATA):
        print(f"Skipping: {TRAIN_DATA} not found.")
        sys.exit(0)

    dataset = load_dataset("json", data_files=TRAIN_DATA, split="train")

    print(f"Loading tokenizer for {BASE_MODEL}...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token

    print(f"Loading base model {BASE_MODEL}...")
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
        output_dir="./tmp_lora",
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-5,
        logging_steps=10,
        max_steps=100, # Control by steps or epochs. For speed, limited steps.
        save_strategy="no",
        fp16=True,
        optim="paged_adamw_32bit",
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        dataset_text_field="text",
        max_seq_length=1024,
        tokenizer=tokenizer,
        args=training_args,
    )

    print("Starting training...")
    # Manual timeout check in loop could be complex.
    # For simplicity, we just run. SFTTrainer doesn't easily support timeout callback.
    # We can monitor elapsed time in a separate thread if needed.

    trainer.train()

    # Save final LoRA
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    trainer.model.save_pretrained(OUTPUT_DIR)

    elapsed = (time.time() - start_time) / 60
    print(f"Training finished in {elapsed:.2f} minutes. Saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    train()
