import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from infra.db.models import Base


class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        
        # データベースファイルのディレクトリを作成
        if database_url.startswith("sqlite"):
            # SQLiteのパスを抽出（Windows/Unix両対応）
            db_path = database_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
            
            # Windows drive letter対応 (C:/path/to/file)
            if len(db_path) > 1 and db_path[1] == ':':
                db_path = db_path
            elif db_path.startswith("./"):
                db_path = db_path[2:]
            
            # Pathオブジェクトに変換してディレクトリを作成
            db_path_obj = Path(db_path)
            db_dir = db_path_obj.parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # データベースファイルを事前に作成してテスト
            try:
                import sqlite3
                test_conn = sqlite3.connect(str(db_path_obj))
                test_conn.close()
            except Exception as e:
                raise RuntimeError(f"Failed to create database file: {e}")
        
        # 同期エンジン（テーブル作成用）
        # WindowsでもUnixでも動作するように調整
        if database_url.startswith("sqlite+aiosqlite:///"):
            # 絶対パス（Windows: C:/ Unix: /）を正しく処理
            db_path_part = database_url.replace("sqlite+aiosqlite:///", "")
            if len(db_path_part) > 1 and db_path_part[1] == ':':
                # Windows絶対パス (C:/...)
                sync_url = f"sqlite:///{db_path_part}"
            else:
                # 相対パスまたはUnix絶対パス
                sync_url = f"sqlite:///{db_path_part}"
        else:
            sync_url = database_url.replace("sqlite+aiosqlite://", "sqlite:///")
        
        self.sync_engine = create_engine(
            sync_url,
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
