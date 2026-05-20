# Miikun Intelligence (v6.0 Ultimate Master Edition)

「教えるAI」から「共に学ぶクラスメイト」へ。プレーンなWeb技術で描画される極限の透過UI、音声のみの自然な対話、そしてGitHub Actionsで自己進化する完全自動学習AIコンパニオン。

## 🚀 🚀 VPS オールインワン・セットアップガイド

本プロジェクトは、VPS（Ubuntu 22.04 LTS）一台でフロントエンド、バックエンド、AI学習のすべてを完結させる「オールインワン構成」を推奨しています。

### 1. 事前準備 (Checklist)
セットアップを開始する前に、以下の情報を用意してください。

| 項目 | 内容 | 取得方法・例 |
| :--- | :--- | :--- |
| **Domain Name** | あなたのドメイン | `miikun.com` など。お名前.comやCloudflare等で取得。 |
| **GH_REPO (任意)** | 自身のリポジトリ名 | `your-username/miikun-core`。Actionsを使わないなら不要。 |
| **GH_PAT (任意)** | GitHub 個人トークン | Actionsを使わないなら不要。 |
| **GGUF Model** | ベースモデルファイル | `elyza-japanese-llama-2-7b-instruct.gguf` 等。Hugging Face等から入手。 |
| **VRM Model** | 3Dキャラクター | `miikun.vrm`。VRoid Studio等で作成。 |

### 2. かんたんセットアップ
VPSにSSHでログインし、以下のコマンドを実行してください。

```bash
git clone https://github.com/your-username/miikun-core.git
cd miikun-core
python3 backend/scripts/setup_vps.py
```

### 🔑 🔑 セットアップ時の回答ガイド
スクリプト実行中の質問には、以下のように回答してください。

- **Installation Directory**: そのまま **Enter**。
- **Linux User Name**: そのまま **Enter**（`root` 以外の一般ユーザーを推奨）。
- **Shared Secret**: `miikun_shared_pass` と入力（フロントエンドの固定値）。
- **Master/Webhook Secret**: そのまま **Enter**。
- **GitHub Repo/PAT**: Actionsを使わない場合はそのまま **Enter** (none)。
- **VOICEVOX Speaker ID**: そのまま **Enter**（32: 白上虎太郎）。
- **Run initial scraping and model training now?**: **`y`** を入力。
    - **【重要】** 初回学習は全ての科目を完了させるため、タイムアウト制限なしで実行されます。データの量やマシンスペックによっては数時間〜半日かかる場合があります。

### 💡 💡 運用上のアドバイスとトラブルシューティング
快適に「みーくん」を運用するために、以下の点に注意してください。

1.  **マイクが反応しない場合 (HTTPS必須)**:
    - ブラウザの仕様上、音声入力（Web Speech API）を使用するには **SSL化（HTTPS）が必須条件** です。
    - セットアップの最後に表示される `sudo certbot --nginx -d [あなたのドメイン]` を必ず実行してください。
2.  **最新の改善を反映させる**:
    - 学習データ拡張やバグ修正などの最新アップデートを取り込むには、VPSで以下のコマンドを実行してください。
    ```bash
    git pull origin main
    sudo systemctl restart miikun
    ```
3.  **学習のパフォーマンス**:
    - **GPU (NVIDIA) がある場合**: 推奨される 7B モデルでも数十分で学習が完了します。
    - **CPU のみの場合**: 学習は非常に低速になります。初回学習や週次学習がタイムアウト（3時間）で終わらない場合は、モデルを `TinyLlama-1.1B` 等の軽量版に変更することを検討してください。

このスクリプトは、以下の工程をすべて自動化します：
- **環境設定**: ドメイン、ディレクトリ、ユーザー、シークレット等の対話的入力。
- **.env生成**: 入力に基づいた最適な設定ファイルの作成。
- **システム構築**: Nginx, Docker, Python 仮想環境の自動セットアップ。
- **インフラ設定**: Nginx 逆プロキシ、Systemd デーモン登録の自動構成。
- **学習スケジュール**: 毎週日曜 AM3:00 に VPS 側で継続学習を実行する cron ジョブを自動登録。

### 🛠️ 🛠️ 手動セットアップ (高度なユーザー向け)
スクリプトを使用せず、手動で設定を行う場合は以下の手順に従ってください。

1.  **環境変数の設定**: `backend/.env` を作成し、 `backend/.env.example` を参考に各値を設定します。
2.  **依存関係のインストール**:
    ```bash
    python3 -m venv venv
    ./venv/bin/pip install -r backend/requirements.txt
    ./venv/bin/pip install -r backend/requirements_train.txt
    ```
3.  **Nginx の構成**: `backend/infra/nginx.conf` を `/etc/nginx/sites-available/miikun` にコピーし、 `{{DOMAIN}}` と `{{INSTALL_DIR}}` を実際の値に置換して有効化します。
4.  **Systemd サービスの登録**: `backend/infra/miikun.service` を `/etc/systemd/system/miikun.service` にコピーし、 `{{USER}}` と `{{INSTALL_DIR}}` を実際の値に置換して起動します。
5.  **週次学習の Cron 登録**: 毎週日曜 AM3:00 に `backend/scripts/weekly_train_local.py` が実行されるよう `crontab -e` でスケジュールを登録します。

## 🧠 🧠 継続的自己進化 (Continuous Evolution) システム
みーくんは、文科省の「中学校学習指導要領」をベースに学習し、ユーザーとの対話を通じて毎週成長します。

### 初回トレーニング (Initial Setup)
初回起動時は、スクレイピングと学習に **合計 3.5〜5時間** 程度（RTX 3090/4090 クラス想定）かかります。
1. `python3 backend/scripts/scrape_educational_data.py` で基礎データを取得。
2. `python3 backend/scripts/train.py` で最初の LoRA を生成。
   - **多モデル審議**: 3つの異なるペルソナ（厳格な教師、客観的な研究者、中学3年生の先輩）が、取得したデータを教育的に適切か、個人情報が含まれていないか 2対1 以上の多数決で審議します。

### 継続的学習サイクル (VPS-Local)
1. **対話ログの蓄積**: 日々の会話は `backend/data/logs.db` に保存されます。
2. **週次自動学習**: 毎週日曜 AM3:00（JST）、VPS 上で `backend/scripts/weekly_train_local.py` が cron により起動します。
3. **多モデル審議 (Deliberation)**: 新規ログは学習前に、3つのモデルペルソナによる「合議制」で検証されます。
   - MiikunAI 本人は審議に参加せず、客観性を保ちます。
4. **ローカル学習 (LoRA)**: 検証済みのデータを用いて、全12教科（英数国理社、保体音美技家、道徳、総合）の LoRA アダプタを VPS 側で更新します。

## 🎨 🎨 ライセンスと帰属 (License & Attribution)
- **System Code**: MIT License
- **TTS Engine**: [VOICEVOX: 白上虎太郎](https://voicevox.hiroshiba.jp/) (わーいスタイル)。
  - **利用規約遵守**: 商用・非商用問わず使用可能ですが、クレジット表記が必須です。
  - **権利関係**: 本システムのボイスモデルを用いた機械学習や追加のファインチューニングは規約により禁止されています。
  - **3Dモデル**: 独自の VRoid モデルの使用は、VirVox プロジェクトの二次創作ガイドライン（キャラクターのイメージを損なわない範囲）に従い、個人の創作として許可されています。

## 🔐 🔐 セキュリティと詳細設定
- **ドメイン制限 (CORS)**: `ALLOWED_ORIGINS` に設定されたドメイン以外からのブラウザアクセスを遮断します。
- **VPS_URL**: 自身のドメインを登録してください。Web Speech API（マイク）を利用するには、ブラウザの仕様により **HTTPS（SSL化）** が必須条件となります。
- **Webhook Secret**: `setup_vps.py` 実行時にランダム生成（または指定）され、VPSの環境変数ファイル（`.env`）に保存されます。この値を GitHub Actions のシークレットに登録することで、学習完了後の自動デプロイとモデルの即時反映（ホットリロード）が有効になります。

## 🌐 🌐 GitHub Pages でのフロントエンド公開
フロントエンドのみを GitHub Pages で公開する場合（CORS環境）、以下の追加設定が必要です。

1.  **`js/api.js` の `BASE_URL`**: `github.io` での動作時に VPS の URL（例: `https://miikun-ai.pdg.f5.si/api`）を指すように設定してください。
2.  **VPS側の CORS 許可**: VPS上の `backend/.env` にある `ALLOWED_ORIGINS` に、GitHub Pages のドメイン（`https://username.github.io`）を追記し、サーバーを再起動してください。

---
**Miikun Intelligence Project**
"Together We Learn, Together We Grow."
