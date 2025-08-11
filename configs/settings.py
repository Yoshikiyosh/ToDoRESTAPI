import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # アプリケーション基本設定
    app_name: str = Field(default="Level2 ToDo API", description="アプリケーション名")
    app_version: str = Field(default="1.0.0", description="アプリケーションバージョン")
    debug: bool = Field(default=False, description="デバッグモード")
    
    # データベース設定
    database_url: str = Field(
        default=f"sqlite+aiosqlite:///{str(Path(__file__).parent.parent / 'data' / 'todos.db').replace(chr(92), '/')}",
        description="データベース接続URL"
    )
    
    # API設定
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 プレフィックス")
    allowed_hosts: list[str] = Field(default=["*"], description="許可されたホスト")
    
    # CORS設定
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="CORS許可オリジン"
    )
    cors_allow_credentials: bool = Field(default=True, description="CORS認証情報許可")
    cors_allow_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        description="CORS許可メソッド"
    )
    cors_allow_headers: list[str] = Field(default=["*"], description="CORS許可ヘッダ")
    
    # ページネーション設定
    default_page_size: int = Field(default=20, description="デフォルトページサイズ")
    max_page_size: int = Field(default=100, description="最大ページサイズ")
    
    # レート制限設定（将来の拡張用）
    rate_limit_enabled: bool = Field(default=False, description="レート制限有効化")
    rate_limit_requests: int = Field(default=100, description="レート制限リクエスト数")
    rate_limit_window: int = Field(default=60, description="レート制限時間窓（秒）")
    
    # ログ設定
    log_level: str = Field(default="INFO", description="ログレベル")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="ログフォーマット"
    )
    
    # セキュリティ設定（将来の拡張用）
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="秘密キー"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="アクセストークン有効期限（分）"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # 環境変数のプレフィックス
        env_prefix = "TODO_API_"


# 設定インスタンス
settings = Settings()


def get_settings() -> Settings:
    """設定を取得する"""
    return settings
