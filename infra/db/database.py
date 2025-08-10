from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from infra.db.models import Base


class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        
        # 同期エンジン（テーブル作成用）
        self.sync_engine = create_engine(
            database_url.replace("sqlite+aiosqlite://", "sqlite:///"),
            echo=False
        )
        
        # 非同期エンジン
        self.async_engine = create_async_engine(
            database_url,
            echo=False
        )
        
        # セッションファクトリ
        self.async_session_factory = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    def create_tables(self):
        """テーブルを作成する"""
        Base.metadata.create_all(bind=self.sync_engine)

    def drop_tables(self):
        """テーブルを削除する（テスト用）"""
        Base.metadata.drop_all(bind=self.sync_engine)

    async def get_session(self) -> AsyncSession:
        """非同期セッションを取得する"""
        async with self.async_session_factory() as session:
            yield session

    async def close(self):
        """接続を閉じる"""
        await self.async_engine.dispose()


# グローバルなデータベース管理インスタンス
database_manager: DatabaseManager = None


def init_database(database_url: str) -> DatabaseManager:
    """データベースを初期化する"""
    global database_manager
    database_manager = DatabaseManager(database_url)
    database_manager.create_tables()
    return database_manager


def get_database_manager() -> DatabaseManager:
    """データベース管理インスタンスを取得する"""
    if database_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return database_manager
