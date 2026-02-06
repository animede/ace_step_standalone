"""
音楽生成エンドポイント
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio
import httpx

from services.ace_step_client import ace_step_client, TaskResult, SUPPORTED_LANGUAGES, SUPPORTED_KEY_SCALES
from config import settings

router = APIRouter(prefix="/api", tags=["generate"])


# =============================================================================
# Request/Response Models
# =============================================================================

class GenerateRequest(BaseModel):
    """音楽生成リクエスト"""
    prompt: str = Field(default="", description="音楽の説明（ジャンル、楽器、雰囲気など）")
    lyrics: str = Field(default="", description="歌詞（構造タグ付き）")
    thinking: bool = Field(default=True, description="LMで高品質生成")
    vocal_language: str = Field(default="ja", description="歌詞言語")
    audio_duration: int = Field(default=60, ge=10, le=300, description="生成時間（秒）")
    bpm: Optional[int] = Field(default=None, ge=30, le=300, description="テンポ")
    key_scale: Optional[str] = Field(default=None, description="調")
    time_signature: str = Field(default="4", description="拍子")
    batch_size: int = Field(default=1, ge=1, le=4, description="バッチサイズ")
    audio_format: str = Field(default="mp3", description="出力形式")
    seed: Optional[int] = Field(default=None, description="シード値")
    inference_steps: int = Field(default=60, ge=1, le=200, description="推論ステップ数")
    guidance_scale: float = Field(default=3.0, ge=0.0, le=20.0, description="CFGスケール")


class GenerateResponse(BaseModel):
    """音楽生成レスポンス"""
    task_id: str
    status: str
    message: str = ""


class TaskStatusResponse(BaseModel):
    """タスクステータスレスポンス"""
    task_id: str
    status: int  # 0=processing, 1=succeeded, 2=failed
    status_text: str
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class GenerateAndWaitRequest(GenerateRequest):
    """生成して完了を待つリクエスト"""
    timeout: float = Field(default=300.0, description="タイムアウト（秒）")


class GenerateAndWaitResponse(BaseModel):
    """生成完了レスポンス"""
    success: bool
    results: List[Dict[str, Any]] = []
    error: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/generate", response_model=GenerateResponse)
async def generate_music(request: GenerateRequest):
    """
    音楽生成タスクを作成
    
    タスクIDを返し、完了を待たない非同期処理
    """
    try:
        result = await ace_step_client.release_task(
            prompt=request.prompt,
            lyrics=request.lyrics,
            thinking=request.thinking,
            vocal_language=request.vocal_language,
            audio_duration=request.audio_duration,
            bpm=request.bpm,
            key_scale=request.key_scale,
            time_signature=request.time_signature,
            batch_size=request.batch_size,
            audio_format=request.audio_format,
            seed=request.seed,
            inference_steps=request.inference_steps,
            guidance_scale=request.guidance_scale
        )
        
        data = result.get("data", {})
        task_id = data.get("task_id", "")
        
        if not task_id:
            raise HTTPException(status_code=500, detail="Failed to create task")
        
        return GenerateResponse(
            task_id=task_id,
            status="queued",
            message="Task created successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    タスクステータスを取得
    """
    try:
        result = await ace_step_client.query_result([task_id])
        
        if result.get("code") != 200:
            raise HTTPException(status_code=500, detail=result.get("error", "API error"))
        
        data_list = result.get("data", [])
        if not data_list:
            return TaskStatusResponse(
                task_id=task_id,
                status=0,
                status_text="processing"
            )
        
        task_data = data_list[0]
        status = task_data.get("status", 0)
        
        status_map = {0: "processing", 1: "succeeded", 2: "failed"}
        status_text = status_map.get(status, "unknown")
        
        results = None
        error = None
        
        if status == 1:
            # 成功
            import json
            result_json = task_data.get("result", "[]")
            if isinstance(result_json, str):
                results = json.loads(result_json)
            else:
                results = result_json
            
            # URLを追加
            for r in results:
                if r.get("file"):
                    r["url"] = ace_step_client.get_audio_url(r["file"])
        
        elif status == 2:
            # 失敗
            error = task_data.get("result", "Unknown error")
        
        return TaskStatusResponse(
            task_id=task_id,
            status=status,
            status_text=status_text,
            results=results,
            error=error
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate_and_wait", response_model=GenerateAndWaitResponse)
async def generate_and_wait(request: GenerateAndWaitRequest):
    """
    音楽を生成し、完了まで待機
    
    同期的に結果を返す
    """
    try:
        # タスク作成
        result = await ace_step_client.release_task(
            prompt=request.prompt,
            lyrics=request.lyrics,
            thinking=request.thinking,
            vocal_language=request.vocal_language,
            audio_duration=request.audio_duration,
            bpm=request.bpm,
            key_scale=request.key_scale,
            time_signature=request.time_signature,
            batch_size=request.batch_size,
            audio_format=request.audio_format,
            seed=request.seed
        )
        
        data = result.get("data", {})
        task_id = data.get("task_id", "")
        
        if not task_id:
            return GenerateAndWaitResponse(
                success=False,
                error="Failed to create task"
            )
        
        # 完了を待機
        task_results = await ace_step_client.wait_for_completion(
            task_id=task_id,
            timeout=request.timeout
        )
        
        # 結果を整形
        results = []
        for tr in task_results:
            results.append({
                "url": tr.url,
                "file": tr.file,
                "prompt": tr.prompt,
                "lyrics": tr.lyrics,
                "metas": {
                    "bpm": tr.metas.bpm if tr.metas else None,
                    "duration": tr.metas.duration if tr.metas else None,
                    "keyscale": tr.metas.keyscale if tr.metas else None,
                },
                "seed": tr.seed_value
            })
        
        return GenerateAndWaitResponse(
            success=True,
            results=results
        )
    
    except TimeoutError as e:
        return GenerateAndWaitResponse(
            success=False,
            error=str(e)
        )
    except Exception as e:
        return GenerateAndWaitResponse(
            success=False,
            error=str(e)
        )


@router.get("/languages")
async def get_languages():
    """サポート言語一覧を取得"""
    return {"languages": SUPPORTED_LANGUAGES}


@router.get("/key_scales")
async def get_key_scales():
    """サポートキースケール一覧を取得"""
    return {"key_scales": SUPPORTED_KEY_SCALES}


@router.get("/health")
async def health_check():
    """ACE-Step APIのヘルスチェック"""
    try:
        result = await ace_step_client.health_check()
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/models")
async def get_models():
    """ACE-Step APIのモデル情報を取得"""
    try:
        result = await ace_step_client.get_models()
        data = result.get("data", {})
        return {
            "success": True,
            "models": data.get("models", []),
            "default_model": data.get("default_model", "unknown")
        }
    except Exception as e:
        return {"success": False, "error": str(e), "models": [], "default_model": "unknown"}


@router.get("/stats")
async def get_stats():
    """ACE-Step APIの統計情報を取得"""
    try:
        result = await ace_step_client.get_stats()
        data = result.get("data", {})
        return {
            "success": True,
            "jobs": data.get("jobs", {}),
            "queue_size": data.get("queue_size", 0),
            "avg_job_seconds": data.get("avg_job_seconds", 0)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/audio")
async def proxy_audio(path: str):
    """
    ACE-Step APIからの音声ファイルをプロキシ
    CORSの問題を回避するため
    """
    try:
        # ACE-Step APIのURLを構築
        audio_url = f"{settings.ace_step_api_url}/v1/audio?path={path}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(audio_url, timeout=60.0)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Audio not found")
            
            # Content-Typeを取得
            content_type = response.headers.get("content-type", "audio/mpeg")
            
            return StreamingResponse(
                iter([response.content]),
                media_type=content_type,
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(len(response.content))
                }
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch audio: {str(e)}")
