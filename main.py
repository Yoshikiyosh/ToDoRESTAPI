import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from configs.settings import get_settings
from infra.db.database import init_database
from interfaces.api.routers.todos import router as todos_router
from interfaces.api.exception_handlers import (
    validation_exception_handler,
    pydantic_validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

# 設定を取得
settings = get_settings()

# ログ設定
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format=settings.log_format
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """FastAPI アプリケーションを作成する"""
    
    # FastAPI アプリケーション作成
    app = FastAPI(
        title=settings.app_name,
        description="Clean Architecture による ToDo REST API の実装",
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # CORS ミドルウェア設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # 例外ハンドラー登録
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    # ルーター登録
    app.include_router(todos_router)
    
    return app


# アプリケーション作成
app = create_app()


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時イベント"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # データベース初期化
    try:
        init_database(settings.database_url)
        logger.info(f"Database initialized: {settings.database_url}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時イベント"""
    logger.info(f"Shutting down {settings.app_name}")
    
    # データベース接続を閉じる
    try:
        from infra.db.database import get_database_manager
        db_manager = get_database_manager()
        await db_manager.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "api": "/api/v1/todos"
    }


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
