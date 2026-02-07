"""
LLM Service - 作詞・タグ生成サービス

OpenAI互換APIを使用した歌詞生成とタグ推奨
"""
import json
import re
from typing import Optional, Dict, Any, Tuple
from openai import AsyncOpenAI

from config import settings


# システムプロンプト: 作詞
LYRICS_GENERATE_SYSTEM_PROMPT = """You are a professional lyricist who creates song lyrics for AI music generation (ACE-Step).

CRITICAL OUTPUT RULES:
1. Start with a JSON metadata line, then output ONLY the lyrics with structure tags
2. Use structure tags: [intro], [verse], [chorus], [bridge], [outro], [inst] (for instrumental)
3. Do NOT include timestamps like (0:00-0:05) - ACE-Step does not use them
4. Do NOT include romanization in parentheses - write in the requested language ONLY
5. Write lyrics line by line, each line on its own

REQUIRED FIRST LINE FORMAT (JSON):
{"recommended_duration": 90, "parts": {"intro": 5, "verse1": 20, "chorus1": 25, "verse2": 20, "chorus2": 25, "outro": 5}}

- recommended_duration: Total song length in seconds (typically 60-180)
- parts: Estimated duration for each part in seconds

STRUCTURE GUIDELINES:
- [intro]: Keep short (1-2 lines) or use [inst] for instrumental (5-10 sec)
- [verse]: 4-6 lines per verse (15-25 sec)
- [chorus]: 4-6 lines, catchy and memorable (20-30 sec)
- [bridge]: Optional, 2-4 lines (10-15 sec)
- [outro]: Short ending, 1-2 lines or [inst] (5-10 sec)

STYLE GUIDELINES:
- Match the mood and genre specified
- Use natural, singable phrases
- If Japanese: Write only in Japanese (kanji/hiragana/katakana mix)
- If English: Write only in English
- Keep vocabulary natural for singing
"""

# システムプロンプト: タグ生成
TAGS_GENERATE_SYSTEM_PROMPT = """You are a music metadata expert. Based on the given lyrics and theme, generate appropriate music tags for AI music generation.

OUTPUT FORMAT (JSON only):
{
    "genre": "primary genre, secondary genre",
    "tags": "instrument1, instrument2, mood1, mood2, vocal type, tempo description",
    "bpm": 120,
    "key_scale": "C major"
}

TAG CATEGORIES:
- Genre: pop, rock, jazz, electronic, hip-hop, R&B, classical, folk, country, etc.
- Mood: upbeat, melancholic, energetic, calm, romantic, dark, hopeful, nostalgic
- Instruments: piano, guitar, drums, bass, strings, synth, brass, etc.
- Vocal: male voice, female voice, choir, falsetto, breathy, powerful
- Tempo: slow tempo, mid tempo, fast tempo, upbeat rhythm

GUIDELINES:
- Analyze the lyrics mood and theme
- Suggest appropriate instrumentation
- Match tempo to the emotional content
- Use 5-10 tags total
- BPM range: 60-180
"""


class LLMService:
    """LLMサービス - 作詞・タグ生成"""
    
    def __init__(
        self,
        base_url: str = None,
        api_key: str = None,
        model: str = None
    ):
        # NOTE:
        # `llm_service` is instantiated at import time. CLI args / .env may be
        # applied later (e.g., when running via uvicorn which re-imports
        # `main:app`). Therefore, we keep only optional overrides here and
        # lazily create (or recreate) the client per-request based on the
        # latest `settings`.
        self._base_url_override = base_url
        self._api_key_override = api_key
        self._model_override = model

        self._client: Optional[AsyncOpenAI] = None
        self._client_base_url: Optional[str] = None
        self._client_api_key: Optional[str] = None

    def _effective_base_url(self) -> str:
        return self._base_url_override or settings.openai_base_url

    def _effective_api_key(self) -> str:
        return self._api_key_override or settings.openai_api_key

    def _effective_model(self) -> str:
        return self._model_override or settings.openai_chat_model

    def _ensure_client(self) -> None:
        base_url = self._effective_base_url()
        api_key = self._effective_api_key()
        if (
            self._client is None
            or self._client_base_url != base_url
            or self._client_api_key != api_key
        ):
            self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)
            self._client_base_url = base_url
            self._client_api_key = api_key
    
    async def chat(
        self,
        user_message: str,
        system_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.8
    ) -> str:
        """
        LLMにチャットリクエストを送信
        
        Args:
            user_message: ユーザーメッセージ
            system_prompt: システムプロンプト
            max_tokens: 最大トークン数
            temperature: 温度
        
        Returns:
            LLMの応答
        """
        self._ensure_client()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        completion = await self._client.chat.completions.create(
            model=self._effective_model(),
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return completion.choices[0].message.content
    
    async def generate_lyrics(
        self,
        theme: str,
        genre: str = "",
        language: str = "Japanese",
        mood: str = ""
    ) -> Dict[str, Any]:
        """
        歌詞を生成
        
        Args:
            theme: 曲のテーマ/シナリオ
            genre: ジャンル
            language: 言語
            mood: ムード
        
        Returns:
            {
                "lyrics": str,  # 構造タグ付き歌詞
                "recommended_duration": int,  # 推奨秒数
                "parts": dict  # パート別秒数
            }
        """
        prompt = f"""Create lyrics for the following:
Theme: {theme}
Genre: {genre or 'any'}
Language: {language}
Mood: {mood or 'match the theme'}

Generate complete song lyrics with structure tags."""
        
        response = await self.chat(
            user_message=prompt,
            system_prompt=LYRICS_GENERATE_SYSTEM_PROMPT,
            temperature=0.85
        )
        
        return self._parse_lyrics_response(response)
    
    def _parse_lyrics_response(self, response: str) -> Dict[str, Any]:
        """歌詞レスポンスをパース"""
        lines = response.strip().split("\n")
        
        # 最初の行からJSONメタデータを抽出
        metadata = {
            "recommended_duration": 90,
            "parts": {}
        }
        lyrics_start = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("{") and "recommended_duration" in line:
                try:
                    metadata = json.loads(line)
                    lyrics_start = i + 1
                    break
                except json.JSONDecodeError:
                    pass
        
        # 歌詞部分を抽出
        lyrics = "\n".join(lines[lyrics_start:]).strip()
        
        return {
            "lyrics": lyrics,
            "recommended_duration": metadata.get("recommended_duration", 90),
            "parts": metadata.get("parts", {})
        }
    
    async def generate_tags(
        self,
        lyrics: str = "",
        theme: str = "",
        language: str = "Japanese"
    ) -> Dict[str, Any]:
        """
        歌詞/テーマからタグを生成
        
        Args:
            lyrics: 歌詞
            theme: テーマ
            language: 言語
        
        Returns:
            {
                "genre": str,
                "tags": str,
                "bpm": int,
                "key_scale": str
            }
        """
        content = []
        if theme:
            content.append(f"Theme: {theme}")
        if lyrics:
            content.append(f"Lyrics:\n{lyrics[:1000]}")  # 長すぎる場合は切り詰め
        content.append(f"Language: {language}")
        
        prompt = "\n\n".join(content) + "\n\nGenerate music tags in JSON format."
        
        response = await self.chat(
            user_message=prompt,
            system_prompt=TAGS_GENERATE_SYSTEM_PROMPT,
            temperature=0.7
        )
        
        return self._parse_tags_response(response)
    
    def _parse_tags_response(self, response: str) -> Dict[str, Any]:
        """タグレスポンスをパース"""
        # JSONを抽出
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        
        if json_match:
            try:
                data = json.loads(json_match.group())
                return {
                    "genre": data.get("genre", "pop"),
                    "tags": data.get("tags", ""),
                    "bpm": data.get("bpm", 120),
                    "key_scale": data.get("key_scale", "C major")
                }
            except json.JSONDecodeError:
                pass
        
        # パース失敗時のデフォルト
        return {
            "genre": "pop",
            "tags": "piano, emotional",
            "bpm": 120,
            "key_scale": "C major"
        }
    
    async def generate_full(
        self,
        theme: str,
        genre: str = "",
        language: str = "Japanese",
        mood: str = ""
    ) -> Dict[str, Any]:
        """
        歌詞とタグを一括生成
        
        Args:
            theme: テーマ
            genre: ジャンル
            language: 言語
            mood: ムード
        
        Returns:
            歌詞とタグの両方を含む辞書
        """
        # 歌詞生成
        lyrics_result = await self.generate_lyrics(
            theme=theme,
            genre=genre,
            language=language,
            mood=mood
        )
        
        # タグ生成
        tags_result = await self.generate_tags(
            lyrics=lyrics_result["lyrics"],
            theme=theme,
            language=language
        )
        
        return {
            **lyrics_result,
            **tags_result
        }


# シングルトンインスタンス
llm_service = LLMService()
