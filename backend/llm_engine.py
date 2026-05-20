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

【長期記憶（心のノート）】
以下の情報は、これまでの会話からボクが覚えている大切なことだよ。会話に活かしてね：
{memory_text}
"""

class LLMEngine:
    def __init__(self):
        self.llm = None
        self.current_adapter = None
        # Lazy loading or handle missing model at startup
        try:
            if os.path.exists(MODEL_PATH):
                self.load_model()
            else:
                print(f"Warning: Model file not found at {MODEL_PATH}. Skipping initial load.")
        except Exception as e:
            print(f"Failed to load model on startup: {e}")

    def load_model(self, subject: str = "general"):
        """
        Load or switch to a subject-specific LoRA adapter.
        AI自体は一つだが、教科ごとに学習内容（LoRA）を使い分ける。
        """
        # If model is not loaded at all, initialize base model first
        if self.llm is None:
            print(f"Initializing base model: {MODEL_PATH}")
            self.llm = Llama(
                model_path=MODEL_PATH,
                n_gpu_layers=N_GPU_LAYERS,
                n_ctx=4096,
                chat_format="llama-2"
            )

        # Path for subject-specific LoRA
        specific_lora_path = os.path.join(LORA_PATH, subject)
        lora_file = os.path.join(specific_lora_path, "adapter_model.safetensors")

        # If already loaded the correct adapter, skip
        if self.current_adapter == subject:
            return

        print(f"Switching to subject: {subject}...")

        # Note: Dynamic LoRA swapping is complex in llama-cpp.
        # We perform a full re-initialization if the adapter changes to ensure clean weights.
        # While slower than hot-swapping, it avoids "ghost weights" from previous adapters.
        try:
            target_lora = specific_lora_path if os.path.exists(lora_file) else None
            if not target_lora:
                general_lora_path = os.path.join(LORA_PATH, "general")
                if os.path.exists(os.path.join(general_lora_path, "adapter_model.safetensors")):
                    target_lora = general_lora_path

            # Re-initialize only if necessary
            print(f"Reloading model with adapter: {target_lora}")
            self.llm = Llama(
                model_path=MODEL_PATH,
                lora_path=target_lora,
                n_gpu_layers=N_GPU_LAYERS,
                n_ctx=4096,
                chat_format="llama-2",
                verbose=False
            )
            self.current_adapter = subject
        except Exception as e:
            print(f"Error switching LoRA: {e}. Re-initializing base model as fallback.")
            self.llm = Llama(model_path=MODEL_PATH, n_gpu_layers=N_GPU_LAYERS, n_ctx=4096, chat_format="llama-2")
            self.current_adapter = "general"

    def reload_lora(self):
        """Called by Webhook after new weights are pushed."""
        print("Reloading current adapter...")
        self.load_model(self.current_adapter)

    def generate_reply(self, history: List[Dict[str, str]], user_text: str, subject: str = "general", memories: Dict[str, str] = {}) -> Dict[str, str]:
        # Attempt to load model if it failed previously or subject changed
        if self.llm is None or self.current_adapter != subject:
            try:
                self.load_model(subject)
            except Exception as e:
                print(f"Error loading model: {e}")
                return {
                    "reply": "（ごめん、ボクの頭の準備がまだできてないみたいだ。モデルファイルが見当たらないか、読み込み中にエラーが起きちゃった。管理者さんに確認してみてね！）",
                    "emotion": "sorrow"
                }

        if self.llm is None:
            return {
                "reply": "（ごめん、ボクの頭の準備がまだできてないみたいだ。ちょっと待ってね！）",
                "emotion": "sorrow"
            }

        memory_text = "\n".join([f"- {k}: {v}" for k, v in memories.items()]) if memories else "（まだ特になし）"
        system_prompt = SYSTEM_PROMPT.format(memory_text=memory_text)

        messages = [{"role": "system", "content": system_prompt}]
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

        # Simple heuristic for emotion detection
        emotion = "neutral"
        joy_words = ["嬉しい", "楽しい", "やった", "おめでとう", "すごい", "！", "笑"]
        sorrow_words = ["悲しい", "困った", "難しい", "できない", "ごめん", "うーん"]
        angry_words = ["ダメ", "嫌い", "怒", "違う"]

        if any(w in reply for w in joy_words): emotion = "joy"
        elif any(w in reply for w in sorrow_words): emotion = "sorrow"
        elif any(w in reply for w in angry_words): emotion = "angry"

        return {
            "reply": reply,
            "emotion": emotion
        }

    def extract_memories(self, user_text: str, ai_reply: str) -> Dict[str, str]:
        """
        Extract key facts from the conversation to store in the notebook.
        In a real scenario, this would be a second LLM call.
        For now, we'll use a placeholder or simple logic.
        """
        # Example: if "ボクの名前はXXXです" is in user_text, extract XXX
        import re
        memories = {}
        name_match = re.search(r"ボクの名前は(.+?)(です|だよ|だぞ|$)", user_text)
        if name_match:
            memories["user_name"] = name_match.group(1).strip()

        return memories

# Singleton instance
engine = LLMEngine()
