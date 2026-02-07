# ACE-Step 1.5 Standalone Web App

A standalone web application for AI music generation.

## 📦 Installation

### Requirements

- OS: Linux
- Python 3.10+
- pip

### 1. Clone (or place) the repository

```bash
cd /home/animede/gm_song
git clone <repository_url> ace_step_standalone
# or use an existing directory
cd ace_step_standalone
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables (optional)

```bash
cp .env.example .env
# Edit .env to customize settings
```

## 🚀 Quick Start

### 1. Activate the virtual environment

```bash
cd /home/animede/gm_song/ace_step_standalone
source .venv/bin/activate
```

### 2. Run the app

```bash
python main.py
```

Or:

```bash
./start.sh
```

### 3. Open in your browser

http://localhost:8888

## 📋 Prerequisites

- **ACE-Step 1.5 API Server** must be running at `localhost:8001`
- **LLM API** (for lyrics/tags generation) must be available

#### 🌐 REST API Server

```bash
uv run acestep-api
```

## 🔧 Configuration

### Environment variables (.env)

You can override settings via a `.env` file:

```env
# ACE-Step API
ACE_STEP_API_URL=http://localhost:8001

# LLM API
OPENAI_BASE_URL=http://YOUR_LLM_HOST:YOUR_LLM_PORT/v1
OPENAI_CHAT_MODEL=gemma3:latest

# Web app server
PORT=8888
```

### Command-line options

You can also override settings with CLI options:

```bash
python main.py [options]
```

| Option | Description | Example |
|---|---|---|
| `--host HOST` | Web app host | `--host 0.0.0.0` |
| `--port PORT` | Web app port | `--port 9000` |
| `--ace-host HOST` | ACE-Step API host | `--ace-host YOUR_ACE_HOST` |
| `--ace-port PORT` | ACE-Step API port | `--ace-port 8001` |
| `--ace-url URL` | Full ACE-Step API URL | `--ace-url http://YOUR_ACE_HOST:8001` |
| `--llm-host HOST` | LLM API host | `--llm-host YOUR_LLM_HOST` |
| `--llm-port PORT` | LLM API port (Ollama default: 11434) | `--llm-port 11434` |
| `--llm-url URL` | Full LLM API URL (e.g., Ollama) | `--llm-url http://localhost:11434/v1` |
| `--llm-model MODEL` | LLM model name | `--llm-model gemma3:latest` |
| `--no-reload` | Disable auto-reload | `--no-reload` |

Notes:

- If you set `--ace-url`, you do not need `--ace-host` / `--ace-port` (the URL takes precedence).
- If you set `--llm-url`, you do not need `--llm-host` / `--llm-port` (the URL takes precedence).

Examples:

```bash
# Run with defaults
python main.py

# Connect to a remote ACE-Step API
python main.py --ace-host YOUR_ACE_HOST --ace-port 8001

# Connect to a specific LLM API (example: Ollama)
python main.py --llm-url http://localhost:11434/v1 --llm-model llama3

# Combine options
python main.py --port 9000 --ace-url http://YOUR_ACE_HOST:8001 --llm-host YOUR_LLM_HOST --llm-port 11434
```

Priority: CLI options > `.env` > defaults

## 📁 Directory Structure

```text
ace_step_standalone/
├── main.py              # FastAPI app entry
├── config.py            # Settings / CLI parsing
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
├── start.sh             # Startup script
├── README.md            # Japanese README
├── README_EN.md         # English README
├── docs/
│   ├── EASY_MUSIC_GUIDE.md
│   ├── ACE_STEP_1_5_STANDALONE_SPEC.md
│   ├── ACE_STEP_API_DOCUMENTATION.md
│   └── ACE_STEP_AUDIO_TIPS.md
├── routers/
│   ├── generate.py      # Music generation API
│   └── lyrics.py        # Lyrics/tags API
├── services/
│   ├── ace_step_client.py
│   └── llm_service.py
├── static/
│   ├── style.css
│   └── app.js
└── templates/
    └── index.html
```

## 🎵 How to Use

1. Enter a theme/scenario in natural language
2. Click **AI Lyrics** to generate lyrics
3. Click **Tag Generation** to get genre/tags suggestions
4. Adjust parameters (BPM, key, duration, steps/CFG/seed, etc.)
5. Click **Generate Music**
6. After completion, play the result in the built-in player

## 🎛️ Music Parameters

| Parameter | Description | Default | Range |
|---|---|---:|---|
| Duration (sec) | Generated audio length | 150 | 10–300 |
| BPM | Tempo | 120 | 30–300 |
| Key | Key scale (34 types) | Auto | C major – B minor (incl. #/b) |
| Time signature | Meter | 4/4 | 2/2, 2/4, 3/4, 4/4, 6/8, ... |
| STEP | Inference steps (higher = better, slower) | 60 | 1–200 |
| CFG | Guidance scale | 3.0 | 0.0–20.0 |
| SEED | Seed for reproducibility | Random | Any integer |

> Note: When using Turbo models, STEP is automatically adjusted to 8.

## 🔌 API Endpoints

| Endpoint | Method | Description |
|---|---:|---|
| `/api/generate` | POST | Create a music generation task |
| `/api/status/{task_id}` | GET | Check task status |
| `/api/audio` | GET | Audio proxy (CORS workaround) |
| `/api/models` | GET | Get ACE-Step model info |
| `/api/stats` | GET | Get ACE-Step stats |
| `/api/lyrics` | POST | AI lyrics generation |
| `/api/tags` | POST | Tag generation |
| `/api/full_generate` | POST | Lyrics + tags in one call |
| `/api/languages` | GET | Supported languages |
| `/api/key_scales` | GET | Supported key scales |
| `/api/health` | GET | Health check |

## 🎨 Features

- AI lyrics generation via LLM
- Genre/tag suggestions
- Built-in visualizer during playback
- Advanced settings (CFG/SEED, etc.) via accordion UI
- Footer shows current model/queue status

## 📄 License

MIT License
