import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient

from main import app
from infra.db.database import init_database, get_database_manager
from infra.db.models import Base
from configs.settings import Settings, get_settings


# テスト用設定
test_settings = Settings(
    database_url="sqlite+aiosqlite:///:memory:",
    debug=True
)


def get_test_settings():
    return test_settings


# テスト用設定で上書き
app.dependency_overrides[get_settings] = get_test_settings


@pytest.fixture(scope="session")
def event_loop():
    """セッションスコープのイベントループ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """テスト用データベースエンジン"""
    engine = create_async_engine(
        test_settings.database_url,
        echo=False
    )
    
    # テーブル作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # クリーンアップ
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """テスト用データベースセッション"""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def client() -> TestClient:
    """テスト用 FastAPI クライアント"""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """テスト用非同期 HTTP クライアント"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
