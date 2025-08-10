from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any

from domain.entities.todo import Todo


class TodoSearchParams:
    """ToDo 検索パラメータ"""
    
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
        sort: Optional[str] = None,
        is_done: Optional[bool] = None,
        q: Optional[str] = None,
        tags: Optional[List[str]] = None,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None
    ):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), 100)
        self.sort = sort
        self.is_done = is_done
        self.q = q
        self.tags = tags or []
        self.due_before = due_before
        self.due_after = due_after

    @property
    def offset(self) -> int:
        """ページネーションのオフセット値"""
        return (self.page - 1) * self.page_size

    def get_sort_fields(self) -> List[tuple]:
        """ソートフィールドを解析
        
        Returns:
            List of (field_name, direction) tuples
            direction is 'asc' or 'desc'
        """
        if not self.sort:
            return [("created_at", "desc")]
        
        fields = []
        for field in self.sort.split(","):
            field = field.strip()
            if field.startswith("-"):
                fields.append((field[1:], "desc"))
            else:
                fields.append((field, "asc"))
        
        return fields


class TodoSearchResult:
    """ToDo 検索結果"""
    
    def __init__(
        self,
        items: List[Todo],
        total_items: int,
        page: int,
        page_size: int
    ):
        self.items = items
        self.total_items = total_items
        self.page = page
        self.page_size = page_size

    @property
    def total_pages(self) -> int:
        """総ページ数"""
        if self.page_size == 0:
            return 0
        return (self.total_items + self.page_size - 1) // self.page_size


class TodoRepository(ABC):
    """ToDo リポジトリの抽象インターフェース"""

    @abstractmethod
    async def create(self, todo: Todo) -> Todo:
        """ToDo を作成する
        
        Args:
            todo: 作成する ToDo エンティティ
            
        Returns:
            作成された ToDo（ID が設定される）
        """
        pass

    @abstractmethod
    async def get_by_id(self, todo_id: int) -> Optional[Todo]:
        """ID で ToDo を取得する
        
        Args:
            todo_id: ToDo の ID
            
        Returns:
            Todo エンティティ、存在しない場合は None
        """
        pass

    @abstractmethod
    async def update(self, todo: Todo) -> Todo:
        """ToDo を更新する
        
        Args:
            todo: 更新する ToDo エンティティ
            
        Returns:
            更新された ToDo
            
        Raises:
            ValueError: Todo が存在しない場合
        """
        pass

    @abstractmethod
    async def delete(self, todo_id: int) -> bool:
        """ToDo を削除する
        
        Args:
            todo_id: 削除する ToDo の ID
            
        Returns:
            削除できた場合 True、存在しなかった場合 False
        """
        pass

    @abstractmethod
    async def search(self, params: TodoSearchParams) -> TodoSearchResult:
        """ToDo を検索する
        
        Args:
            params: 検索パラメータ
            
        Returns:
            検索結果
        """
        pass

    @abstractmethod
    async def exists(self, todo_id: int) -> bool:
        """ToDo が存在するかチェックする
        
        Args:
            todo_id: チェックする ToDo の ID
            
        Returns:
            存在する場合 True
        """
        pass
