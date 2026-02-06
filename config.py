"""
ACE-Step Standalone App Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional
import argparse


def parse_args():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(description="ACE-Step Standalone Web App")
    
    # サーバー設定
    parser.add_argument("--host", type=str, default=None, help="サーバーホスト (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=None, help="サーバーポート (default: 8888)")
    
    # ACE-Step API設定
    parser.add_argument("--ace-host", type=str, default=None, help="ACE-Step APIホスト (default: localhost)")
    parser.add_argument("--ace-port", type=int, default=None, help="ACE-Step APIポート (default: 8001)")
    parser.add_argument("--ace-url", type=str, default=None, help="ACE-Step API URL (例: http://YOUR_ACE_HOST:8001)")
    
    # LLM API設定
    parser.add_argument("--llm-host", type=str, default=None, help="LLM APIホスト (default: YOUR_LLM_HOST)")
    parser.add_argument("--llm-port", type=int, default=None, help="LLM APIポート (default: 64650)")
    parser.add_argument("--llm-url", type=str, default=None, help="LLM API URL (例: http://YOUR_LLM_HOST:64650/v1)")
    parser.add_argument("--llm-model", type=str, default=None, help="LLMモデル名")
    
    # その他
    parser.add_argument("--no-reload", action="store_true", help="自動リロードを無効化")
    
    return parser.parse_args()


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # ACE-Step API設定
    ace_step_api_url: str = "http://localhost:8001"
    ace_step_api_key: Optional[str] = None
    
    # LLM設定（作詞/タグ生成用）
    openai_base_url: str = "http://YOUR_LLM_HOST:64650/v1"
    openai_api_key: str = "YOUR_OPENAI_API_KEY"
    openai_chat_model: str = "gemma3:latest"
    
    # サーバー設定
    host: str = "0.0.0.0"
    port: int = 8888
    debug: bool = True
    
    # ポーリング設定
    poll_interval: float = 1.0  # 秒
    poll_timeout: float = 300.0  # 5分
    
    # 音声設定
    default_audio_duration: int = 60
    default_bpm: int = 120
    default_language: str = "ja"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def apply_args(self, args):
        """コマンドライン引数を適用"""
        # サーバー設定
        if args.host:
            self.host = args.host
        if args.port:
            self.port = args.port
        
        # ACE-Step API設定
        if args.ace_url:
            self.ace_step_api_url = args.ace_url
        elif args.ace_host or args.ace_port:
            # 現在のURLをパースしてホスト/ポートを更新
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(self.ace_step_api_url)
            host = args.ace_host or parsed.hostname or "localhost"
            port = args.ace_port or parsed.port or 8001
            self.ace_step_api_url = f"http://{host}:{port}"
        
        # LLM API設定
        if args.llm_url:
            self.openai_base_url = args.llm_url
        elif args.llm_host or args.llm_port:
            from urllib.parse import urlparse
            parsed = urlparse(self.openai_base_url)
            host = args.llm_host or parsed.hostname or "localhost"
            port = args.llm_port or parsed.port or 11434
            path = parsed.path or "/v1"
            self.openai_base_url = f"http://{host}:{port}{path}"
        
        if args.llm_model:
            self.openai_chat_model = args.llm_model
        
        # デバッグモード
        if args.no_reload:
            self.debug = False


# 設定インスタンス
settings = Settings()

# コマンドライン引数を適用（main実行時）
_args_applied = False

def apply_cli_args():
    """CLIから呼び出された場合に引数を適用"""
    global _args_applied
    if not _args_applied:
        try:
            args = parse_args()
            settings.apply_args(args)
            _args_applied = True
        except SystemExit:
            # argparseがヘルプ表示などで終了した場合
            raise
