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

## 🧠 🧠 継続的自己進化 (Continuous Evolution) システム
みーくんは、ユーザーとの対話を通じて毎週成長します。その仕組みは以下の通りです：

1. **対話ログの蓄積**: 日々の会話は `backend/data/logs.db` に保存されます。
2. **週次データ抽出**: 毎週日曜 AM3:00（JST）、GitHub Actions が起動し、VPS 上の `backend/scripts/export_logs.py` を呼び出します。
   - **セーフティガード**: 新規ログが **50件以上** ある場合のみ、学習用の `train_data.jsonl` を生成します。
3. **クラウド学習 (LoRA)**: 生成されたデータは GitHub Actions ランナーへ転送され、GPU を用いて LoRA（Low-Rank Adaptation）学習が実行されます。
   - ベースモデル（Llama-3-8B等）の知識を保ちつつ、直近の会話傾向を微調整します。
4. **自動デプロイと反映**:
   - 新しい学習済み重み（`models/active_lora`）がリポジトリに push されます。
   - その後、VPS の `/api/webhook/reload` エンドポイントが叩かれます。
5. **ホットリロード (Hot Reload)**:
   - バックエンドが `git pull` を実行して最新の重みを取得します。
   - 推論エンジンが再起動なしで LoRA アダプタを付け替え、即座に新しい「みーくん」として会話を再開します。

このサイクルにより、みーくんは「昨日よりも少しだけ自分を理解してくれるクラスメイト」へと進化し続けます。

## 🎨 🎨 ライセンスと帰属 (License & Attribution)
- **System Code**: MIT License
- **3D Model (`assets/miikun.vrm`)**: [Meshy](https://www.meshy.ai/) で作成。 **CC BY 4.0** (Creative Commons Attribution 4.0 International) に基づき、帰属が必要です。
- **Base LLM**: Meta Llama-3 License に準拠します。
- **TTS Engine**: VOICEVOX (利用規約に従ってください)。

---
**Miikun Intelligence Project**
"Together We Learn, Together We Grow."
