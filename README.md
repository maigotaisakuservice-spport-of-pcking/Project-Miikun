# Miikun Intelligence (v6.0 Ultimate Master Edition)

「教えるAI」から「共に学ぶクラスメイト」へ。プレーンなWeb技術で描画される極限の透過UI、音声のみの自然な対話、そしてGitHub Actionsで自己進化する完全自動学習AIコンパニオン。

## 🚀 🚀 セットアップガイド (VPS & Local Deployment)

### 1. 必須要件 (Requirements)
- **OS**: Ubuntu 22.04 LTS (推奨)
- **GPU**: NVIDIA GPU (VRAM 16GB以上推奨 / 推論: Llama-3-8B)
- **Engine**: [VOICEVOX Engine](https://github.com/VOICEVOX/voicevox_engine)
- **Runtime**: Python 3.10+, Node.js (ブラウザ閲覧用)

### 2. インストール手順 (Quick Start with Docker)
```bash
git clone https://github.com/your-username/miikun-core.git
cd miikun-core
cp backend/.env.example backend/.env
# .env を編集して API_KEY 等を設定してください

# Docker Compose で一括起動
docker-compose up -d
```

### 3. 手動セットアップ (Manual Setup)
1. **Backend**:
   - `python -m venv venv && source venv/bin/activate`
   - `pip install -r backend/requirements.txt`
   - `python backend/main.py`
2. **Frontend**:
   - Nginx 等で `frontend` ディレクトリを公開してください。
   - `assets/miikun.vrm` を配置してください。

## 🧠 🧠 MLOps: 週次学習の仕組み
1. **データ抽出**: 毎週日曜 AM3:00、50件以上の新規会話ログがある場合に `export_logs.py` が実行されます。
2. **学習 (LoRA)**: GitHub Actions 上で LoRA 学習が行われ、`models/active_lora` が更新されます。
3. **ホットリロード**: 学習完了後、VPS の `/api/webhook/reload` が叩かれ、サーバーを止めずに新しい知識が適用されます。

## 🎨 🎨 ライセンスと帰属 (License & Attribution)
- **System Code**: MIT License
- **3D Model (`assets/miikun.vrm`)**: [Meshy](https://www.meshy.ai/) で作成。 **CC BY 4.0** (Creative Commons Attribution 4.0 International) に基づき、帰属が必要です。
- **Base LLM**: Meta Llama-3 License に準拠します。
- **TTS Engine**: VOICEVOX (利用規約に従ってください)。

---
**Miikun Intelligence Project**
"Together We Learn, Together We Grow."
