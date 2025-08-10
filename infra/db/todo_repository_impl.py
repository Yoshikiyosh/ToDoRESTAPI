from datetime import datetime
from typing import List, Optional
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from domain.entities.todo import Todo
from domain.repositories.todo_repository import (
    TodoRepository, 
    TodoSearchParams, 
    TodoSearchResult
)
from infra.db.models import TodoModel


class SqlAlchemyTodoRepository(TodoRepository):
    """SQLAlchemy を使った TodoRepository の実装"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, todo: Todo) -> Todo:
        """ToDo を作成する"""
        # ID は None でなければならない（新規作成なので）
        if todo.id is not None:
            raise ValueError("ID should be None for new todos")
        
        # created_at, updated_at を現在時刻に設定
        now = datetime.utcnow()
        todo_with_timestamp = todo.update(created_at=now, updated_at=now)
        
        # モデルに変換
        todo_model = TodoModel.from_entity(todo_with_timestamp)
        todo_model.id = None  # 明示的に None に設定
        
        # DB に保存
        self.session.add(todo_model)
        await self.session.commit()
        await self.session.refresh(todo_model)
        
        return todo_model.to_entity()

    async def get_by_id(self, todo_id: int) -> Optional[Todo]:
        """ID で ToDo を取得する"""
        result = await self.session.execute(
            select(TodoModel).where(TodoModel.id == todo_id)
        )
        todo_model = result.scalar_one_or_none()
        
        if todo_model is None:
            return None
        
        return todo_model.to_entity()

    async def update(self, todo: Todo) -> Todo:
        """ToDo を更新する"""
        if todo.id is None:
            raise ValueError("Todo ID is required for update")
        
        # 既存のレコードを取得
        result = await self.session.execute(
            select(TodoModel).where(TodoModel.id == todo.id)
        )
        todo_model = result.scalar_one_or_none()
        
        if todo_model is None:
            raise ValueError(f"Todo with ID {todo.id} not found")
        
        # updated_at を現在時刻に設定
        updated_todo = todo.update(updated_at=datetime.utcnow())
        
        # モデルを更新
        todo_model.update_from_entity(updated_todo)
        
        await self.session.commit()
        await self.session.refresh(todo_model)
        
        return todo_model.to_entity()

    async def delete(self, todo_id: int) -> bool:
        """ToDo を削除する"""
        result = await self.session.execute(
            select(TodoModel).where(TodoModel.id == todo_id)
        )
        todo_model = result.scalar_one_or_none()
        
        if todo_model is None:
            return False
        
        await self.session.delete(todo_model)
        await self.session.commit()
        
        return True

    async def exists(self, todo_id: int) -> bool:
        """ToDo が存在するかチェックする"""
        result = await self.session.execute(
            select(func.count(TodoModel.id)).where(TodoModel.id == todo_id)
        )
        count = result.scalar()
        return count > 0

    async def search(self, params: TodoSearchParams) -> TodoSearchResult:
        """ToDo を検索する"""
        # ベースクエリ
        query = select(TodoModel)
        count_query = select(func.count(TodoModel.id))
        
        # 条件を構築
        conditions = []
        
        # is_done フィルタ
        if params.is_done is not None:
            conditions.append(TodoModel.is_done == params.is_done)
        
        # フリーテキスト検索
        if params.q:
            search_term = f"%{params.q}%"
            conditions.append(
                or_(
                    TodoModel.title.ilike(search_term),
                    TodoModel.description.ilike(search_term)
                )
            )
        
        # タグフィルタ
        if params.tags:
            # JSON配列内にタグが含まれるかチェック
            tag_conditions = []
            for tag in params.tags:
                # SQLiteのJSON関数を使用
                tag_conditions.append(
                    func.json_extract(TodoModel.tags, '$').like(f'%"{tag.lower()}"%')
                )
            conditions.append(and_(*tag_conditions))
        
        # 期限フィルタ
        if params.due_before:
            conditions.append(TodoModel.due_date <= params.due_before)
        
        if params.due_after:
            conditions.append(TodoModel.due_date >= params.due_after)
        
        # 条件を適用
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # 総件数を取得
        total_result = await self.session.execute(count_query)
        total_items = total_result.scalar()
        
        # ソートを適用
        sort_fields = params.get_sort_fields()
        for field_name, direction in sort_fields:
            if hasattr(TodoModel, field_name):
                column = getattr(TodoModel, field_name)
                if direction == "desc":
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
        
        # ページネーションを適用
        query = query.offset(params.offset).limit(params.page_size)
        
        # 実行
        result = await self.session.execute(query)
        todo_models = result.scalars().all()
        
        # エンティティに変換
        todos = [model.to_entity() for model in todo_models]
        
        return TodoSearchResult(
            items=todos,
            total_items=total_items,
            page=params.page,
            page_size=params.page_size
        )
