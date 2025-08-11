from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
import re


@dataclass
class Todo:
    """ToDo エンティティ
    
    ビジネスルールとデータの整合性を保証する
    """
    id: Optional[int]
    title: str
    description: Optional[str]
    is_done: bool
    priority: int
    due_date: Optional[datetime]
    tags: List[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    def __post_init__(self):
        """作成時の検証とデータ正規化"""
        self._validate_and_normalize()

    def _validate_and_normalize(self):
        """データ検証と正規化"""
        # title の検証と正規化
        if not self.title or not self.title.strip():
            raise ValueError("title is required and cannot be empty")
        
        self.title = self.title.strip()
        if len(self.title) > 200:
            raise ValueError("title must be 200 characters or less")

        # description の検証
        if self.description and len(self.description) > 2000:
            raise ValueError("description must be 2000 characters or less")

        # priority の検証
        if not isinstance(self.priority, int) or self.priority < 0 or self.priority > 5:
            raise ValueError("priority must be an integer between 0 and 5")

        # tags の正規化
        if self.tags:
            normalized_tags = []
            for tag in self.tags:
                if not tag or not tag.strip():
                    continue
                normalized_tag = tag.strip().lower()
                if len(normalized_tag) > 30:
                    raise ValueError("tag must be 30 characters or less")
                if normalized_tag not in normalized_tags:
                    normalized_tags.append(normalized_tag)
            self.tags = normalized_tags
        else:
            self.tags = []

        if len(self.tags) > 20:
            raise ValueError("maximum 20 tags allowed")

        # due_date の検証（新規作成時は created_at がまだ設定されていない場合があるのでスキップ）
        if (self.due_date and self.created_at and 
            self.id is not None and  # 既存のTodoの場合のみチェック
            self.due_date < self.created_at):
            # 仕様では警告として扱うオプションもあるが、ここでは例外として扱う
            raise ValueError("due_date cannot be before created_at")

    def update(self, **kwargs) -> "Todo":
        """ToDo を更新して新しいインスタンスを返す（不変性保証）"""
        # 現在の値をベースに更新
        updated_data = {
            "id": self.id,
            "title": kwargs.get("title", self.title),
            "description": kwargs.get("description", self.description),
            "is_done": kwargs.get("is_done", self.is_done),
            "priority": kwargs.get("priority", self.priority),
            "due_date": kwargs.get("due_date", self.due_date),
            "tags": kwargs.get("tags", self.tags.copy()),
            "created_at": self.created_at,
            "updated_at": kwargs.get("updated_at", datetime.utcnow())
        }
        
        return Todo(**updated_data)

    def mark_as_done(self) -> "Todo":
        """完了状態にする"""
        return self.update(is_done=True, updated_at=datetime.utcnow())

    def mark_as_undone(self) -> "Todo":
        """未完了状態にする"""
        return self.update(is_done=False, updated_at=datetime.utcnow())

    def add_tag(self, tag: str) -> "Todo":
        """タグを追加する"""
        new_tags = self.tags.copy()
        normalized_tag = tag.strip().lower()
        
        if normalized_tag and normalized_tag not in new_tags:
            new_tags.append(normalized_tag)
        
        return self.update(tags=new_tags, updated_at=datetime.utcnow())

    def remove_tag(self, tag: str) -> "Todo":
        """タグを削除する"""
        new_tags = self.tags.copy()
        normalized_tag = tag.strip().lower()
        
        if normalized_tag in new_tags:
            new_tags.remove(normalized_tag)
        
        return self.update(tags=new_tags, updated_at=datetime.utcnow())

    @classmethod
    def create(
        cls,
        title: str,
        description: Optional[str] = None,
        priority: int = 0,
        due_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None
    ) -> "Todo":
        """新しい ToDo を作成する"""
        now = datetime.utcnow()
        return cls(
            id=None,
            title=title,
            description=description,
            is_done=False,
            priority=priority,
            due_date=due_date,
            tags=tags or [],
            created_at=now,
            updated_at=now
        )
