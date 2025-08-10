from datetime import datetime
from typing import List, Optional

from domain.entities.todo import Todo
from domain.repositories.todo_repository import (
    TodoRepository, 
    TodoSearchParams, 
    TodoSearchResult
)


class TodoService:
    """ToDo に関するビジネスロジックを含むサービス"""
    
    def __init__(self, todo_repository: TodoRepository):
        self.todo_repository = todo_repository

    async def create_todo(
        self,
        title: str,
        description: Optional[str] = None,
        priority: int = 0,
        due_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None
    ) -> Todo:
        """新しい ToDo を作成する
        
        Args:
            title: タイトル
            description: 説明
            priority: 優先度 (0-5)
            due_date: 期限
            tags: タグリスト
            
        Returns:
            作成された ToDo
            
        Raises:
            ValueError: バリデーションエラー
        """
        # ドメインエンティティを作成（バリデーションが実行される）
        todo = Todo.create(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            tags=tags
        )
        
        # リポジトリに保存
        return await self.todo_repository.create(todo)

    async def get_todo_by_id(self, todo_id: int) -> Optional[Todo]:
        """ID で ToDo を取得する
        
        Args:
            todo_id: ToDo の ID
            
        Returns:
            Todo エンティティ、存在しない場合は None
        """
        return await self.todo_repository.get_by_id(todo_id)

    async def update_todo(
        self,
        todo_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        is_done: Optional[bool] = None,
        priority: Optional[int] = None,
        due_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Todo]:
        """ToDo を更新する
        
        Args:
            todo_id: 更新する ToDo の ID
            title: 新しいタイトル
            description: 新しい説明
            is_done: 完了状態
            priority: 新しい優先度
            due_date: 新しい期限
            tags: 新しいタグリスト
            
        Returns:
            更新された ToDo、存在しない場合は None
            
        Raises:
            ValueError: バリデーションエラー
        """
        # 既存の ToDo を取得
        existing_todo = await self.todo_repository.get_by_id(todo_id)
        if existing_todo is None:
            return None
        
        # 更新データを準備
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description
        if is_done is not None:
            update_data["is_done"] = is_done
        if priority is not None:
            update_data["priority"] = priority
        if due_date is not None:
            update_data["due_date"] = due_date
        if tags is not None:
            update_data["tags"] = tags
        
        # 更新を実行（バリデーションが実行される）
        updated_todo = existing_todo.update(**update_data)
        
        # リポジトリに保存
        return await self.todo_repository.update(updated_todo)

    async def delete_todo(self, todo_id: int) -> bool:
        """ToDo を削除する
        
        Args:
            todo_id: 削除する ToDo の ID
            
        Returns:
            削除できた場合 True、存在しなかった場合 False
        """
        return await self.todo_repository.delete(todo_id)

    async def mark_todo_as_done(self, todo_id: int) -> Optional[Todo]:
        """ToDo を完了状態にする
        
        Args:
            todo_id: 完了状態にする ToDo の ID
            
        Returns:
            更新された ToDo、存在しない場合は None
        """
        existing_todo = await self.todo_repository.get_by_id(todo_id)
        if existing_todo is None:
            return None
        
        completed_todo = existing_todo.mark_as_done()
        return await self.todo_repository.update(completed_todo)

    async def mark_todo_as_undone(self, todo_id: int) -> Optional[Todo]:
        """ToDo を未完了状態にする
        
        Args:
            todo_id: 未完了状態にする ToDo の ID
            
        Returns:
            更新された ToDo、存在しない場合は None
        """
        existing_todo = await self.todo_repository.get_by_id(todo_id)
        if existing_todo is None:
            return None
        
        uncompleted_todo = existing_todo.mark_as_undone()
        return await self.todo_repository.update(uncompleted_todo)

    async def add_tag_to_todo(self, todo_id: int, tag: str) -> Optional[Todo]:
        """ToDo にタグを追加する
        
        Args:
            todo_id: タグを追加する ToDo の ID
            tag: 追加するタグ
            
        Returns:
            更新された ToDo、存在しない場合は None
        """
        existing_todo = await self.todo_repository.get_by_id(todo_id)
        if existing_todo is None:
            return None
        
        tagged_todo = existing_todo.add_tag(tag)
        return await self.todo_repository.update(tagged_todo)

    async def remove_tag_from_todo(self, todo_id: int, tag: str) -> Optional[Todo]:
        """ToDo からタグを削除する
        
        Args:
            todo_id: タグを削除する ToDo の ID
            tag: 削除するタグ
            
        Returns:
            更新された ToDo、存在しない場合は None
        """
        existing_todo = await self.todo_repository.get_by_id(todo_id)
        if existing_todo is None:
            return None
        
        untagged_todo = existing_todo.remove_tag(tag)
        return await self.todo_repository.update(untagged_todo)

    async def search_todos(
        self,
        page: int = 1,
        page_size: int = 20,
        sort: Optional[str] = None,
        is_done: Optional[bool] = None,
        q: Optional[str] = None,
        tags: Optional[List[str]] = None,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None
    ) -> TodoSearchResult:
        """ToDo を検索する
        
        Args:
            page: ページ番号
            page_size: ページサイズ
            sort: ソート条件
            is_done: 完了状態フィルタ
            q: フリーテキスト検索
            tags: タグフィルタ
            due_before: 期限前フィルタ
            due_after: 期限後フィルタ
            
        Returns:
            検索結果
        """
        params = TodoSearchParams(
            page=page,
            page_size=page_size,
            sort=sort,
            is_done=is_done,
            q=q,
            tags=tags,
            due_before=due_before,
            due_after=due_after
        )
        
        return await self.todo_repository.search(params)

    async def bulk_mark_as_done(self, todo_ids: List[int]) -> dict:
        """複数の ToDo を一括で完了状態にする
        
        Args:
            todo_ids: 完了状態にする ToDo の ID リスト
            
        Returns:
            結果統計
        """
        updated_count = 0
        failed_ids = []
        
        for todo_id in todo_ids:
            try:
                result = await self.mark_todo_as_done(todo_id)
                if result is not None:
                    updated_count += 1
                else:
                    failed_ids.append(todo_id)
            except Exception:
                failed_ids.append(todo_id)
        
        return {
            "updated": updated_count,
            "failed_ids": failed_ids
        }

    async def get_todos_count(self) -> int:
        """ToDo の総数を取得する"""
        params = TodoSearchParams(page=1, page_size=1)
        result = await self.todo_repository.search(params)
        return result.total_items

    async def get_done_todos_count(self) -> int:
        """完了した ToDo の数を取得する"""
        params = TodoSearchParams(page=1, page_size=1, is_done=True)
        result = await self.todo_repository.search(params)
        return result.total_items

    async def get_pending_todos_count(self) -> int:
        """未完了の ToDo の数を取得する"""
        params = TodoSearchParams(page=1, page_size=1, is_done=False)
        result = await self.todo_repository.search(params)
        return result.total_items
