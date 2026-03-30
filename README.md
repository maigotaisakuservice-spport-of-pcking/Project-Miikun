# Miikun Intelligence (v6.0 Ultimate Master Edition)

「教えるAI」から「共に学ぶクラスメイト」へ。プレーンなWeb技術で描画される極限の透過UI、音声のみの自然な対話、そしてGitHub Actionsで自己進化する完全自動学習AIコンパニオン。

## 🚀 🚀 セットアップガイド (VPS & Local Deployment)

### 1. 必須要件 (Requirements)
- **OS**: Ubuntu 22.04 LTS (推奨)
- **GPU**: NVIDIA GPU (VRAM 16GB以上推奨 / 推論: Llama-2-7B)。
- **Engine**: [VOICEVOX Engine](https://github.com/VOICEVOX/voicevox_engine)
- **Runtime**: Python 3.10+, Node.js (ブラウザ閲覧用)

### 2. かんたんセットアップ (推奨)
VPS（Ubuntu 22.04 LTS）上で以下のコマンドを実行するだけで、対話形式でセットアップが完了します。

```bash
git clone https://github.com/your-username/miikun-core.git
cd miikun-core
python3 backend/scripts/setup_vps.py
```

このスクリプトは、以下の工程をすべて自動化します：
- **環境設定**: ドメイン、ディレクトリ、ユーザー、シークレット等の対話的入力。
- **.env生成**: 入力に基づいた最適な設定ファイルの作成。
- **システム構築**: Nginx, Docker, Python 仮想環境の自動セットアップ。
- **インフラ設定**: Nginx 逆プロキシ、Systemd デーモン登録の自動構成。
- **学習スケジュール**: 毎週日曜 AM3:00 に VPS 側で継続学習を実行する cron ジョブを自動登録。

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

## 🔐 🔐 セキュリティ設定
- **ドメイン制限 (CORS)**: `ALLOWED_ORIGINS` に設定されたドメイン以外からのブラウザアクセスを遮断します。
- **Webhook Secret**: `setup_vps.py` 実行時に生成される、デプロイおよびホットリロード用の秘密鍵です。

---
**Miikun Intelligence Project**
"Together We Learn, Together We Grow."
