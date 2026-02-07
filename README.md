# ACE-Step 1.5 Standalone Web App

AIで音楽を生成するスタンドアロンWebアプリケーション

## � インストール

### 必要環境

- OS: Linux
- Python 3.10以上
- pip

### 1. リポジトリをクローン（または配置）

```bash
cd /home/animede/gm_song
git clone <repository_url> ace_step_standalone
# または既存のディレクトリを使用
cd ace_step_standalone
```

### 2. 仮想環境を作成

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# Windows: .venv\Scripts\activate
```

### 3. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数を設定（オプション）

```bash
cp .env.example .env
# .envファイルを編集して設定をカスタマイズ
```

## �🚀 クイックスタート

### 1. 仮想環境の有効化

```bash
cd /home/animede/gm_song/ace_step_standalone
source .venv/bin/activate
```

### 2. 起動

```bash
python main.py
```

または

```bash
./start.sh
```

### 3. ブラウザでアクセス

http://localhost:8888

## 📋 前提条件

- **ACE-Step 1.5 API Server** が `localhost:8001` で稼働していること
- **LLM API** （作詞/タグ生成用）が利用可能であること

#### 🌐 REST API Server

```bash
uv run acestep-api
```

## 🔧 設定

### 環境変数（.envファイル）

`.env` ファイルで設定を変更できます:

```env
# ACE-Step API
ACE_STEP_API_URL=http://localhost:8001

# LLM API
OPENAI_BASE_URL=http://XXX.XXX.XXX.XXX:YYYYY/v1
OPENAI_CHAT_MODEL=gemma3:latest

# サーバー
PORT=8888
```

### コマンドラインオプション

起動時にコマンドラインオプションで設定を上書きできます：

```bash
python main.py [オプション]
```

| オプション | 説明 | 例 |
|-----------|------|-----|
| `--host HOST` | アプリのホスト | `--host 0.0.0.0` |
| `--port PORT` | アプリのポート | `--port 9000` |
| `--ace-host HOST` | ACE-Step APIホスト | `--ace-host YOUR_ACE_HOST` |
| `--ace-port PORT` | ACE-Step APIポート | `--ace-port 8001` |
| `--ace-url URL` | ACE-Step API完全URL | `--ace-url http://YOUR_ACE_HOST:8001` |
| `--llm-host HOST` | LLM APIホスト | `--llm-host YOUR_LLM_HOST` |
| `--llm-port PORT` | LLM APIポート（Ollamaのデフォルトは11434） | `--llm-port 11434` |
| `--llm-url URL` | LLM API完全URL（例: Ollama） | `--llm-url http://localhost:11434/v1` |
| `--llm-model MODEL` | LLMモデル名 | `--llm-model gpt-4o` |
| `--no-reload` | 開発時のリロードを無効化 | `--no-reload` |

**補足**:

- `--ace-url` を指定した場合、`--ace-host` / `--ace-port` の指定は不要です（`--ace-url` が優先されます）
- `--llm-url` を指定した場合、`--llm-host` / `--llm-port` の指定は不要です（`--llm-url` が優先されます）

#### 使用例

```bash
# デフォルト設定で起動
python main.py

# ACE-Step APIを別サーバーに接続
python main.py --ace-host YOUR_ACE_HOST --ace-port 8001

# LLM APIを指定して起動（例: Ollama）
python main.py --llm-url http://localhost:11434/v1 --llm-model llama3

# 複数オプションを組み合わせ
python main.py --port 9000 --ace-url http://YOUR_ACE_HOST:8001 --llm-host YOUR_LLM_HOST --llm-port 11434
```

**優先順位**: コマンドラインオプション > .envファイル > デフォルト値

## 📁 ディレクトリ構造

```
ace_step_standalone/
├── main.py              # FastAPIメインアプリ
├── config.py            # 設定
├── requirements.txt     # 依存パッケージ
├── .env                 # 環境変数
├── start.sh             # 起動スクリプト
├── README.md            # このファイル
├── docs/
│   ├── EASY_MUSIC_GUIDE.md              # かんたん音楽生成ガイド
│   ├── ACE_STEP_1_5_STANDALONE_SPEC.md  # 設計仕様書
│   ├── ACE_STEP_API_DOCUMENTATION.md    # API詳細ドキュメント
│   └── ACE_STEP_AUDIO_TIPS.md           # 音声パラメータTips
├── routers/
│   ├── generate.py      # 音楽生成API
│   └── lyrics.py        # 作詞/タグ生成API
├── services/
│   ├── ace_step_client.py  # ACE-Step APIクライアント
│   └── llm_service.py      # LLMサービス
├── static/
│   ├── style.css        # スタイルシート
│   └── app.js           # フロントエンドJS
└── templates/
    └── index.html       # メインページ
```

## 🎵 使い方

1. **テーマを入力**: 曲のテーマやシナリオを自然言語で入力
2. **AI作詞**: 「AI作詞」ボタンで歌詞を自動生成
3. **タグ生成**: 「タグ生成」ボタンでジャンル・楽器タグを推奨
4. **パラメータ調整**: BPM、調、長さ、STEP、CFG、SEEDなどを設定
5. **音楽生成**: 「音楽を生成」ボタンでAI音楽を生成
6. **再生**: 生成完了後、ビジュアライザー付きプレイヤーで再生

## 🎛️ 音楽パラメータ

| パラメータ | 説明 | デフォルト | 範囲 |
|-----------|------|-----------|------|
| 長さ（秒） | 生成する音楽の長さ | 150 | 10-300 |
| BPM | テンポ | 120 | 30-300 |
| 調 | キースケール（34種類） | 自動 | C major〜B minor（#/b含む） |
| 拍子 | 拍子記号 | 4/4 | 2/2, 2/4, 3/4, 4/4, 6/8 等 |
| STEP | 推論ステップ数（多いほど高品質） | 60 | 1-200 |
| CFG | ガイダンススケール | 3.0 | 0.0-20.0 |
| SEED | 再現性のためのシード値 | ランダム | 任意の整数 |

> **Note**: Turboモデル使用時はSTEPが自動的に8に調整されます

## 🔌 API エンドポイント

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/generate` | POST | 音楽生成タスク作成 |
| `/api/status/{task_id}` | GET | タスクステータス確認 |
| `/api/audio` | GET | 音声ファイルプロキシ（CORS対応） |
| `/api/models` | GET | ACE-Stepモデル情報取得 |
| `/api/stats` | GET | ACE-Step統計情報取得 |
| `/api/lyrics` | POST | AI作詞 |
| `/api/tags` | POST | タグ生成 |
| `/api/full_generate` | POST | 歌詞+タグ一括生成 |
| `/api/languages` | GET | サポート言語一覧 |
| `/api/key_scales` | GET | サポートキースケール一覧 |
| `/api/health` | GET | ヘルスチェック |

## 🎨 機能

- **AI作詞**: LLMによる自動歌詞生成
- **タグ生成**: ジャンル・楽器タグの自動推奨
- **ビジュアライザー**: 再生中に音楽に合わせたカラフルなアニメーション表示
- **詳細設定**: CFG、SEED等の詳細パラメータをアコーディオンで設定
- **サーバー情報表示**: フッターに現在のモデル・キュー状態を表示

## 📄 ライセンス

MIT License

## 🌐 nginxリバースプロキシ設定

本番環境でnginxを使用する場合の設定例：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8888;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 音声ストリーミング対応
        proxy_buffering off;
        proxy_read_timeout 300s;
        
        # 音声ファイルサイズ上限
        client_max_body_size 100M;
    }
}
```

> **Note**: WebSocketは使用していないため、WS設定は不要です

