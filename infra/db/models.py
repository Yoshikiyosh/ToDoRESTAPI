from datetime import datetime
from typing import List

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from domain.entities.todo import Todo


Base = declarative_base()


class TodoModel(Base):
    """ToDo テーブルモデル"""
    
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_done = Column(Boolean, nullable=False, default=False)
    priority = Column(Integer, nullable=False, default=0)
    due_date = Column(DateTime, nullable=True)
    tags = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def to_entity(self) -> Todo:
        """SQLAlchemy モデルから Domain エンティティに変換"""
        return Todo(
            id=self.id,
            title=self.title,
            description=self.description,
            is_done=self.is_done,
            priority=self.priority,
            due_date=self.due_date,
            tags=self.tags or [],
            created_at=self.created_at,
            updated_at=self.updated_at
        )

    @classmethod
    def from_entity(cls, todo: Todo) -> "TodoModel":
        """Domain エンティティから SQLAlchemy モデルに変換"""
        return cls(
            id=todo.id,
            title=todo.title,
            description=todo.description,
            is_done=todo.is_done,
            priority=todo.priority,
            due_date=todo.due_date,
            tags=todo.tags,
            created_at=todo.created_at,
            updated_at=todo.updated_at
        )

    def update_from_entity(self, todo: Todo) -> None:
        """既存のモデルを Domain エンティティで更新"""
        self.title = todo.title
        self.description = todo.description
        self.is_done = todo.is_done
        self.priority = todo.priority
        self.due_date = todo.due_date
        self.tags = todo.tags
        self.updated_at = todo.updated_at or datetime.utcnow()
