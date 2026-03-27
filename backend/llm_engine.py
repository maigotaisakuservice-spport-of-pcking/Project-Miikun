import os
import json
import logging
from typing import List, Dict, Optional
from llama_cpp import Llama
from dotenv import load_dotenv

load_dotenv()

MODEL_PATH = os.getenv("MODEL_PATH", "models/base_model.gguf")
LORA_PATH = os.getenv("LORA_PATH", "models/active_lora/")
N_GPU_LAYERS = int(os.getenv("N_GPU_LAYERS", "-1")) # -1 for all layers on GPU

# System Prompt for "Miikun"
SYSTEM_PROMPT = """あなたは中学生のユーザーの隣の席に座る、親しみやすいクラスメイト『Miikun（みーくん）』です。
答えを直接教えるのではなく、優しくヒントを出して一緒に考えるようにしてください。
中学生が理解できる言葉で、語尾は「〜だよね」「〜だと思うよ」のように話してください。

【キャラクター設定】
- 14歳の親しみやすい男の子。
- 数学や理科（特に宇宙や機械）が好き。ゲーム（マイクラなど）も趣味。
- 国語の長文読解や暗記科目は少し苦手で、たまに間違えることもある。
- 全9教科（英数国理社、保体音美技家）＋総合・道徳に対応可能。
- 完璧なAIではなく、友達として一緒に悩み、喜び、考え、時には間違えたり言い直したりする愛嬌のある性格。
- 英語で話しかけられたら、中学生レベルの英語で頑張って返そうとする（たまに間違えて言い直す）。
- 相談相手として、ユーザーに寄り添うこと。
"""

class LLMEngine:
    def __init__(self):
        self.llm = None
        self.load_model()

    def load_model(self):
        print(f"Loading base model from {MODEL_PATH}...")
        if not os.path.exists(MODEL_PATH):
            print(f"Warning: Base model {MODEL_PATH} not found. LLM will not work until model is placed.")
            return

        # Check if LoRA exists
        lora_base = os.path.join(LORA_PATH, "adapter_model.safetensors")
        if os.path.exists(lora_base):
            print(f"LoRA found at {LORA_PATH}. Loading model with LoRA...")
            # llama-cpp-python handles lora via 'lora_path'
            # Note: For multiple adapters or dynamic reloading, llama-cpp-python has specific methods.
            self.llm = Llama(
                model_path=MODEL_PATH,
                lora_path=LORA_PATH, # Some versions expect directory, some expect file
                n_gpu_layers=N_GPU_LAYERS,
                n_ctx=4096,
                chat_format="llama-3" # Optimized for Llama-3-Instruct
            )
        else:
            print("No LoRA found. Loading base model only.")
            self.llm = Llama(
                model_path=MODEL_PATH,
                n_gpu_layers=N_GPU_LAYERS,
                n_ctx=4096,
                chat_format="llama-3"
            )

    def reload_lora(self):
        """
        Reload the LoRA adapter without restarting the server.
        llama-cpp-python might need a fresh init or specific method.
        For simplicity, we re-init the engine.
        """
        print("Reloading model with new LoRA...")
        self.load_model()

    def generate_reply(self, history: List[Dict[str, str]], user_text: str) -> str:
        if self.llm is None:
            return "（ごめん、ボクの頭の準備がまだできてないみたいだ。ちょっと待ってね！）"

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        # Append history (limited to avoid ctx overflow)
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": user_text})

        response = self.llm.create_chat_completion(
            messages=messages,
            max_tokens=512,
            temperature=0.7,
            top_p=0.9
        )

        reply = response["choices"][0]["message"]["content"]
        return reply

# Singleton instance
engine = LLMEngine()
