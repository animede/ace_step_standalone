"""
ACE-Step 1.5 Standalone Web Application

FastAPIベースの音楽生成Webアプリ
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import settings
from routers import generate, lyrics

# =============================================================================
# Application Setup
# =============================================================================

app = FastAPI(
    title="ACE-Step 1.5 Music Generator",
    description="AI音楽生成Webアプリケーション",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイル
app.mount("/static", StaticFiles(directory="static"), name="static")

# テンプレート
templates = Jinja2Templates(directory="templates")


# =============================================================================
# Routers
# =============================================================================

app.include_router(generate.router)
app.include_router(lyrics.router)


# =============================================================================
# Pages
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """メインページ"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "ACE-Step 1.5 Music Generator"
    })


@app.get("/api")
async def api_info():
    """API情報"""
    return {
        "name": "ACE-Step Standalone API",
        "version": "1.0.0",
        "endpoints": {
            "generate": {
                "POST /api/generate": "音楽生成タスク作成",
                "GET /api/status/{task_id}": "タスクステータス確認",
                "POST /api/generate_and_wait": "音楽生成（完了待ち）",
            },
            "lyrics": {
                "POST /api/lyrics": "AI作詞",
                "POST /api/tags": "タグ生成",
                "POST /api/full_generate": "歌詞+タグ一括生成",
            },
            "utility": {
                "GET /api/languages": "サポート言語一覧",
                "GET /api/key_scales": "サポートキースケール一覧",
                "GET /api/health": "ヘルスチェック",
            }
        }
    }


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    from config import apply_cli_args, settings
    
    # コマンドライン引数を適用
    apply_cli_args()
    
    print(f"🎵 ACE-Step Standalone starting on http://{settings.host}:{settings.port}")
    print(f"   ACE-Step API: {settings.ace_step_api_url}")
    print(f"   LLM API: {settings.openai_base_url}")
    print(f"   LLM Model: {settings.openai_chat_model}")
    print()
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
