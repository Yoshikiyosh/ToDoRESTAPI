import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from domain.entities.todo import Todo
from domain.repositories.todo_repository import TodoSearchResult
from usecases.todo_service import TodoService


class TestTodoService:
    """TodoService のテスト"""
    
    @pytest.fixture
    def mock_repository(self):
        """モックリポジトリ"""
        return AsyncMock()
    
    @pytest.fixture
    def todo_service(self, mock_repository):
        """TodoService インスタンス"""
        return TodoService(mock_repository)
    
    @pytest.mark.asyncio
    async def test_create_todo_success(self, todo_service, mock_repository):
        """Todo 作成の成功テスト"""
        # モックの設定
        created_todo = Todo.create(title="Test Todo")
        created_todo.id = 1
        mock_repository.create.return_value = created_todo
        
        # 実行
        result = await todo_service.create_todo(
            title="Test Todo",
            description="Test Description",
            priority=1,
            tags=["work"]
        )
        
        # 検証
        assert result.id == 1
        assert result.title == "Test Todo"
        mock_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_todo_validation_error(self, todo_service, mock_repository):
        """Todo 作成のバリデーションエラーテスト"""
        # 空のタイトルでエラーが発生することを確認
        with pytest.raises(ValueError):
            await todo_service.create_todo(title="")
    
    @pytest.mark.asyncio
    async def test_get_todo_by_id_success(self, todo_service, mock_repository):
        """Todo 取得の成功テスト"""
        # モックの設定
        todo = Todo.create(title="Test Todo")
        todo.id = 1
        mock_repository.get_by_id.return_value = todo
        
        # 実行
        result = await todo_service.get_todo_by_id(1)
        
        # 検証
        assert result.id == 1
        assert result.title == "Test Todo"
        mock_repository.get_by_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_todo_by_id_not_found(self, todo_service, mock_repository):
        """Todo 取得の失敗テスト（存在しない）"""
        # モックの設定
        mock_repository.get_by_id.return_value = None
        
        # 実行
        result = await todo_service.get_todo_by_id(999)
        
        # 検証
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(999)
    
    @pytest.mark.asyncio
    async def test_update_todo_success(self, todo_service, mock_repository):
        """Todo 更新の成功テスト"""
        # モックの設定
        existing_todo = Todo.create(title="Original")
        existing_todo.id = 1
        
        updated_todo = existing_todo.update(title="Updated")
        
        mock_repository.get_by_id.return_value = existing_todo
        mock_repository.update.return_value = updated_todo
        
        # 実行
        result = await todo_service.update_todo(
            todo_id=1,
            title="Updated",
            priority=2
        )
        
        # 検証
        assert result.title == "Updated"
        mock_repository.get_by_id.assert_called_once_with(1)
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_todo_not_found(self, todo_service, mock_repository):
        """Todo 更新の失敗テスト（存在しない）"""
        # モックの設定
        mock_repository.get_by_id.return_value = None
        
        # 実行
        result = await todo_service.update_todo(
            todo_id=999,
            title="Updated"
        )
        
        # 検証
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(999)
        mock_repository.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_todo_success(self, todo_service, mock_repository):
        """Todo 削除の成功テスト"""
        # モックの設定
        mock_repository.delete.return_value = True
        
        # 実行
        result = await todo_service.delete_todo(1)
        
        # 検証
        assert result is True
        mock_repository.delete.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_delete_todo_not_found(self, todo_service, mock_repository):
        """Todo 削除の失敗テスト（存在しない）"""
        # モックの設定
        mock_repository.delete.return_value = False
        
        # 実行
        result = await todo_service.delete_todo(999)
        
        # 検証
        assert result is False
        mock_repository.delete.assert_called_once_with(999)
    
    @pytest.mark.asyncio
    async def test_mark_todo_as_done_success(self, todo_service, mock_repository):
        """Todo 完了状態変更の成功テスト"""
        # モックの設定
        todo = Todo.create(title="Test Todo")
        todo.id = 1
        
        done_todo = todo.mark_as_done()
        
        mock_repository.get_by_id.return_value = todo
        mock_repository.update.return_value = done_todo
        
        # 実行
        result = await todo_service.mark_todo_as_done(1)
        
        # 検証
        assert result.is_done is True
        mock_repository.get_by_id.assert_called_once_with(1)
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mark_todo_as_undone_success(self, todo_service, mock_repository):
        """Todo 未完了状態変更の成功テスト"""
        # モックの設定
        todo = Todo.create(title="Test Todo")
        todo.id = 1
        done_todo = todo.mark_as_done()
        undone_todo = done_todo.mark_as_undone()
        
        mock_repository.get_by_id.return_value = done_todo
        mock_repository.update.return_value = undone_todo
        
        # 実行
        result = await todo_service.mark_todo_as_undone(1)
        
        # 検証
        assert result.is_done is False
        mock_repository.get_by_id.assert_called_once_with(1)
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_tag_to_todo_success(self, todo_service, mock_repository):
        """Todo タグ追加の成功テスト"""
        # モックの設定
        todo = Todo.create(title="Test Todo", tags=["work"])
        todo.id = 1
        
        tagged_todo = todo.add_tag("urgent")
        
        mock_repository.get_by_id.return_value = todo
        mock_repository.update.return_value = tagged_todo
        
        # 実行
        result = await todo_service.add_tag_to_todo(1, "urgent")
        
        # 検証
        assert "urgent" in result.tags
        assert "work" in result.tags
        mock_repository.get_by_id.assert_called_once_with(1)
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_tag_from_todo_success(self, todo_service, mock_repository):
        """Todo タグ削除の成功テスト"""
        # モックの設定
        todo = Todo.create(title="Test Todo", tags=["work", "urgent"])
        todo.id = 1
        
        untagged_todo = todo.remove_tag("work")
        
        mock_repository.get_by_id.return_value = todo
        mock_repository.update.return_value = untagged_todo
        
        # 実行
        result = await todo_service.remove_tag_from_todo(1, "work")
        
        # 検証
        assert "work" not in result.tags
        assert "urgent" in result.tags
        mock_repository.get_by_id.assert_called_once_with(1)
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_todos_success(self, todo_service, mock_repository):
        """Todo 検索の成功テスト"""
        # モックの設定
        todos = [
            Todo.create(title="Todo 1"),
            Todo.create(title="Todo 2")
        ]
        
        search_result = TodoSearchResult(
            items=todos,
            total_items=2,
            page=1,
            page_size=20
        )
        
        mock_repository.search.return_value = search_result
        
        # 実行
        result = await todo_service.search_todos(
            page=1,
            page_size=20,
            is_done=False
        )
        
        # 検証
        assert len(result.items) == 2
        assert result.total_items == 2
        assert result.page == 1
        mock_repository.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_bulk_mark_as_done_success(self, todo_service, mock_repository):
        """一括完了状態変更の成功テスト"""
        # モックの設定
        todo1 = Todo.create(title="Todo 1")
        todo1.id = 1
        todo2 = Todo.create(title="Todo 2")
        todo2.id = 2
        
        done_todo1 = todo1.mark_as_done()
        done_todo2 = todo2.mark_as_done()
        
        mock_repository.get_by_id.side_effect = [todo1, todo2]
        mock_repository.update.side_effect = [done_todo1, done_todo2]
        
        # 実行
        result = await todo_service.bulk_mark_as_done([1, 2])
        
        # 検証
        assert result["updated"] == 2
        assert result["failed_ids"] == []
        assert mock_repository.get_by_id.call_count == 2
        assert mock_repository.update.call_count == 2
    
    @pytest.mark.asyncio
    async def test_bulk_mark_as_done_partial_failure(self, todo_service, mock_repository):
        """一括完了状態変更の部分失敗テスト"""
        # モックの設定
        todo1 = Todo.create(title="Todo 1")
        todo1.id = 1
        
        done_todo1 = todo1.mark_as_done()
        
        # 1つ目は成功、2つ目は存在しない
        mock_repository.get_by_id.side_effect = [todo1, None]
        mock_repository.update.return_value = done_todo1
        
        # 実行
        result = await todo_service.bulk_mark_as_done([1, 999])
        
        # 検証
        assert result["updated"] == 1
        assert result["failed_ids"] == [999]
    
    @pytest.mark.asyncio
    async def test_get_todos_count(self, todo_service, mock_repository):
        """Todo 総数取得のテスト"""
        # モックの設定
        search_result = TodoSearchResult(
            items=[],
            total_items=5,
            page=1,
            page_size=1
        )
        mock_repository.search.return_value = search_result
        
        # 実行
        result = await todo_service.get_todos_count()
        
        # 検証
        assert result == 5
        mock_repository.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_done_todos_count(self, todo_service, mock_repository):
        """完了 Todo 数取得のテスト"""
        # モックの設定
        search_result = TodoSearchResult(
            items=[],
            total_items=3,
            page=1,
            page_size=1
        )
        mock_repository.search.return_value = search_result
        
        # 実行
        result = await todo_service.get_done_todos_count()
        
        # 検証
        assert result == 3
        mock_repository.search.assert_called_once()
        # is_done=True で検索されることを確認
        call_args = mock_repository.search.call_args[0][0]
        assert call_args.is_done is True
    
    @pytest.mark.asyncio
    async def test_get_pending_todos_count(self, todo_service, mock_repository):
        """未完了 Todo 数取得のテスト"""
        # モックの設定
        search_result = TodoSearchResult(
            items=[],
            total_items=2,
            page=1,
            page_size=1
        )
        mock_repository.search.return_value = search_result
        
        # 実行
        result = await todo_service.get_pending_todos_count()
        
        # 検証
        assert result == 2
        mock_repository.search.assert_called_once()
        # is_done=False で検索されることを確認
        call_args = mock_repository.search.call_args[0][0]
        assert call_args.is_done is False
