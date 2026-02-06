"""
作詞・タグ生成エンドポイント
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from services.llm_service import llm_service

router = APIRouter(prefix="/api", tags=["lyrics"])


# =============================================================================
# Request/Response Models
# =============================================================================

class LyricsGenerateRequest(BaseModel):
    """作詞リクエスト"""
    theme: str = Field(..., description="曲のテーマ/シナリオ")
    genre: str = Field(default="", description="ジャンル")
    language: str = Field(default="Japanese", description="言語")
    mood: str = Field(default="", description="ムード")


class LyricsGenerateResponse(BaseModel):
    """作詞レスポンス"""
    success: bool
    lyrics: str = ""
    recommended_duration: int = 90
    parts: Dict[str, int] = {}
    error: Optional[str] = None


class TagsGenerateRequest(BaseModel):
    """タグ生成リクエスト"""
    lyrics: str = Field(default="", description="歌詞")
    theme: str = Field(default="", description="テーマ")
    language: str = Field(default="Japanese", description="言語")


class TagsGenerateResponse(BaseModel):
    """タグ生成レスポンス"""
    success: bool
    genre: str = ""
    tags: str = ""
    bpm: int = 120
    key_scale: str = "C major"
    error: Optional[str] = None


class FullGenerateRequest(BaseModel):
    """歌詞+タグ一括生成リクエスト"""
    theme: str = Field(..., description="曲のテーマ/シナリオ")
    genre: str = Field(default="", description="ジャンル")
    language: str = Field(default="Japanese", description="言語")
    mood: str = Field(default="", description="ムード")


class FullGenerateResponse(BaseModel):
    """歌詞+タグ一括生成レスポンス"""
    success: bool
    lyrics: str = ""
    recommended_duration: int = 90
    parts: Dict[str, int] = {}
    genre: str = ""
    tags: str = ""
    bpm: int = 120
    key_scale: str = "C major"
    error: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/lyrics", response_model=LyricsGenerateResponse)
async def generate_lyrics(request: LyricsGenerateRequest):
    """
    AI作詞
    
    テーマから歌詞を生成
    """
    try:
        result = await llm_service.generate_lyrics(
            theme=request.theme,
            genre=request.genre,
            language=request.language,
            mood=request.mood
        )
        
        return LyricsGenerateResponse(
            success=True,
            lyrics=result["lyrics"],
            recommended_duration=result["recommended_duration"],
            parts=result["parts"]
        )
    
    except Exception as e:
        return LyricsGenerateResponse(
            success=False,
            error=str(e)
        )


@router.post("/tags", response_model=TagsGenerateResponse)
async def generate_tags(request: TagsGenerateRequest):
    """
    タグ生成
    
    歌詞/テーマからジャンル・タグを推奨
    """
    try:
        result = await llm_service.generate_tags(
            lyrics=request.lyrics,
            theme=request.theme,
            language=request.language
        )
        
        return TagsGenerateResponse(
            success=True,
            genre=result["genre"],
            tags=result["tags"],
            bpm=result["bpm"],
            key_scale=result["key_scale"]
        )
    
    except Exception as e:
        return TagsGenerateResponse(
            success=False,
            error=str(e)
        )


@router.post("/full_generate", response_model=FullGenerateResponse)
async def full_generate(request: FullGenerateRequest):
    """
    歌詞+タグ一括生成
    
    テーマから歌詞とタグを一括生成
    """
    try:
        result = await llm_service.generate_full(
            theme=request.theme,
            genre=request.genre,
            language=request.language,
            mood=request.mood
        )
        
        return FullGenerateResponse(
            success=True,
            lyrics=result["lyrics"],
            recommended_duration=result["recommended_duration"],
            parts=result["parts"],
            genre=result["genre"],
            tags=result["tags"],
            bpm=result["bpm"],
            key_scale=result["key_scale"]
        )
    
    except Exception as e:
        return FullGenerateResponse(
            success=False,
            error=str(e)
        )
