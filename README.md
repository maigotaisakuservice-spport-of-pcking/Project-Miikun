# Miikun Intelligence (v6.0 Ultimate Master Edition)

「教えるAI」から「共に学ぶクラスメイト」へ。プレーンなWeb技術で描画される極限の透過UI、音声のみの自然な対話、そしてGitHub Actionsで自己進化する完全自動学習AIコンパニオン。

## 🚀 🚀 セットアップガイド (VPS & Local Deployment)

### 1. 必須要件 (Requirements)
- **OS**: Ubuntu 22.04 LTS (推奨)
- **GPU**: NVIDIA GPU (VRAM 16GB以上推奨 / 推論: Llama-3-8B)
- **Engine**: [VOICEVOX Engine](https://github.com/VOICEVOX/voicevox_engine)
- **Runtime**: Python 3.10+, Node.js (ブラウザ閲覧用)

### 2. クイックスタート (Docker Compose 推奨)
GPU環境がある場合、Docker Compose を使うのが最も簡単です。

```bash
git clone https://github.com/your-username/miikun-core.git
cd miikun-core
cp backend/.env.example backend/.env

# .env を編集
# ALLOWED_ORIGINS に自分のドメインを記載してください
# MASTER_SECRET, WEBHOOK_SECRET を安全な文字列に変更してください

# 起動
docker-compose -f backend/infra/docker-compose.yml up -d
```

### 3. Ubuntu 22.04 LTS での手動セットアップ詳細

#### 3.1 Python 環境構築
```bash
sudo apt update && sudo apt install -y python3-venv python3-pip git-lfs

# 仮想環境の作成
cd miikun-core
python3 -m venv venv
source venv/bin/activate

# llama-cpp-python の GPU 高速化ビルド (CUDA環境の場合)
# 事前に CUDA Toolkit がインストールされている必要があります
export CMAKE_ARGS="-DLLAMA_CUBLAS=on"
export FORCE_CMAKE=1
pip install -r backend/requirements.txt
```

#### 3.2 VOICEVOX Engine の起動 (Docker)
```bash
# GPU版
docker run -d -p 50021:50021 voicevox/voicevox_engine:gpu-ubuntu22.04-latest
```

#### 3.3 Nginx と SSL (Certbot) 設定
`/etc/nginx/sites-available/miikun` を `backend/infra/nginx.conf` を元に作成し、以下のコマンドを実行します。

```bash
sudo ln -s /etc/nginx/sites-available/miikun /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# SSL化 (マイクの使用に必須)
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

#### 3.4 Systemd サービス登録
```bash
sudo cp backend/infra/miikun.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable miikun
sudo systemctl start miikun
```

## 🔑 🔑 GitHub Secrets の登録
GitHub Actions を正常に動作させるため、リポジトリの **Settings > Secrets and variables > Actions** から以下のシークレットを登録してください。

| Secret 名 | 内容 | 例 |
| :--- | :--- | :--- |
| `VPS_HOST` | VPS の IP アドレスまたはドメイン | `123.456.78.90` |
| `VPS_USER` | SSH 接続に使用するユーザー名 | `ubuntu` |
| `VPS_SSH_KEY` | VPS への SSH 秘密鍵 (id_rsa の中身) | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `VPS_URL` | バックエンド API のベース URL (SSL推奨) | `https://your-domain.com` |
| `HF_TOKEN` | Hugging Face のアクセストークン (Read権限) | `hf_xxxxxxxxxxxxxxxxxxxxxxxx` |
| `HF_BASE_MODEL` | 使用するベースモデルのパス | `elyza/ELYZA-japanese-Llama-3-8B-Instruct` |
| `WEBHOOK_SECRET` | リロード用シークレット (backend/.env と一致させる) | `your_secure_random_string` |

## 🔐 🔐 セキュリティ設定
- **ドメイン制限 (CORS)**: `ALLOWED_ORIGINS` に設定されたドメイン以外からのブラウザアクセスを遮断します。
- **Shared Secret**: フロントエンドとバックエンド間の簡易的な合言葉（`SHARED_SECRET`）です。
- **Master Secret**: 手動学習トリガー（`/api/admin/train`）を叩くための管理者用秘密鍵です。コードには含めず `.env` で管理してください。

## 🧠 🧠 継続的自己進化 (Continuous Evolution) システム
みーくんは、ユーザーとの対話を通じて毎週成長します。

### 初回トレーニング (Initial Setup)
システムを最初に起動した直後は LoRA 重みがありません。以下の手順で最初のアダプタを生成してください：
1. GitHub のリポジトリページから **Actions** タブを開きます。
2. 左メニューの **"Initial Miikun Training"** を選択します。
3. **"Run workflow"** ボタンをクリックして実行してください。

### 継続的学習サイクル
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
