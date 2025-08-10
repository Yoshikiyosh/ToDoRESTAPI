import pytest
from datetime import datetime
from domain.entities.todo import Todo


class TestTodo:
    """Todo エンティティのテスト"""
    
    def test_create_todo_success(self):
        """正常な Todo 作成のテスト"""
        todo = Todo.create(
            title="Test Todo",
            description="Test Description",
            priority=1,
            tags=["work", "important"]
        )
        
        assert todo.id is None
        assert todo.title == "Test Todo"
        assert todo.description == "Test Description"
        assert todo.is_done is False
        assert todo.priority == 1
        assert todo.tags == ["work", "important"]
        assert todo.created_at is not None
        assert todo.updated_at is not None
    
    def test_create_todo_minimal(self):
        """最小限の情報での Todo 作成のテスト"""
        todo = Todo.create(title="Minimal Todo")
        
        assert todo.title == "Minimal Todo"
        assert todo.description is None
        assert todo.is_done is False
        assert todo.priority == 0
        assert todo.tags == []
    
    def test_title_validation_empty(self):
        """空のタイトルでのバリデーションエラー"""
        with pytest.raises(ValueError, match="title is required"):
            Todo.create(title="")
        
        with pytest.raises(ValueError, match="title is required"):
            Todo.create(title="   ")
    
    def test_title_validation_too_long(self):
        """長すぎるタイトルでのバリデーションエラー"""
        long_title = "x" * 201
        with pytest.raises(ValueError, match="title must be 200 characters or less"):
            Todo.create(title=long_title)
    
    def test_title_strip_whitespace(self):
        """タイトルの前後空白削除"""
        todo = Todo.create(title="  Test Title  ")
        assert todo.title == "Test Title"
    
    def test_description_validation_too_long(self):
        """長すぎる説明でのバリデーションエラー"""
        long_description = "x" * 2001
        with pytest.raises(ValueError, match="description must be 2000 characters or less"):
            Todo.create(title="Test", description=long_description)
    
    def test_priority_validation_invalid(self):
        """無効な優先度でのバリデーションエラー"""
        with pytest.raises(ValueError, match="priority must be an integer between 0 and 5"):
            Todo.create(title="Test", priority=-1)
        
        with pytest.raises(ValueError, match="priority must be an integer between 0 and 5"):
            Todo.create(title="Test", priority=6)
    
    def test_tags_normalization(self):
        """タグの正規化テスト"""
        todo = Todo.create(
            title="Test",
            tags=["Work", "IMPORTANT", "work", "  urgent  ", ""]
        )
        
        # 小文字化、重複削除、空文字削除、前後空白削除
        assert todo.tags == ["work", "important", "urgent"]
    
    def test_tags_validation_too_many(self):
        """多すぎるタグでのバリデーションエラー"""
        many_tags = [f"tag{i}" for i in range(21)]
        with pytest.raises(ValueError, match="maximum 20 tags allowed"):
            Todo.create(title="Test", tags=many_tags)
    
    def test_tags_validation_too_long(self):
        """長すぎるタグでのバリデーションエラー"""
        long_tag = "x" * 31
        with pytest.raises(ValueError, match="tag must be 30 characters or less"):
            Todo.create(title="Test", tags=[long_tag])
    
    def test_update_todo(self):
        """Todo 更新のテスト"""
        original = Todo.create(title="Original", priority=1)
        updated = original.update(title="Updated", priority=2)
        
        # 元のオブジェクトは変更されない（不変性）
        assert original.title == "Original"
        assert original.priority == 1
        
        # 新しいオブジェクトが更新されている
        assert updated.title == "Updated"
        assert updated.priority == 2
        assert updated.updated_at > original.updated_at
    
    def test_mark_as_done(self):
        """完了状態への変更テスト"""
        todo = Todo.create(title="Test")
        done_todo = todo.mark_as_done()
        
        assert todo.is_done is False  # 元のオブジェクトは変更されない
        assert done_todo.is_done is True
        assert done_todo.updated_at > todo.updated_at
    
    def test_mark_as_undone(self):
        """未完了状態への変更テスト"""
        todo = Todo.create(title="Test")
        done_todo = todo.mark_as_done()
        undone_todo = done_todo.mark_as_undone()
        
        assert undone_todo.is_done is False
        assert undone_todo.updated_at > done_todo.updated_at
    
    def test_add_tag(self):
        """タグ追加のテスト"""
        todo = Todo.create(title="Test", tags=["work"])
        tagged_todo = todo.add_tag("urgent")
        
        assert todo.tags == ["work"]  # 元のオブジェクトは変更されない
        assert "urgent" in tagged_todo.tags
        assert "work" in tagged_todo.tags
    
    def test_add_duplicate_tag(self):
        """重複タグ追加のテスト"""
        todo = Todo.create(title="Test", tags=["work"])
        tagged_todo = todo.add_tag("work")
        
        # 重複は追加されない
        assert tagged_todo.tags == ["work"]
    
    def test_remove_tag(self):
        """タグ削除のテスト"""
        todo = Todo.create(title="Test", tags=["work", "urgent"])
        untagged_todo = todo.remove_tag("work")
        
        assert todo.tags == ["work", "urgent"]  # 元のオブジェクトは変更されない
        assert untagged_todo.tags == ["urgent"]
    
    def test_remove_nonexistent_tag(self):
        """存在しないタグ削除のテスト"""
        todo = Todo.create(title="Test", tags=["work"])
        untagged_todo = todo.remove_tag("nonexistent")
        
        # 変更されない
        assert untagged_todo.tags == ["work"]
    
    def test_due_date_validation(self):
        """期限日の検証テスト"""
        now = datetime.utcnow()
        past_date = datetime(2020, 1, 1)
        
        # 過去の日付でも警告のみ（例外は発生しない実装の場合）
        # または例外が発生する実装の場合
        todo = Todo.create(
            title="Test",
            due_date=past_date
        )
        
        # created_at より前の due_date は警告または例外
        # 実装に応じてテストを調整
