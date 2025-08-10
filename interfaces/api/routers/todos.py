from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.todo import Todo
from usecases.todo_service import TodoService
from infra.db.database import get_database_manager
from infra.db.todo_repository_impl import SqlAlchemyTodoRepository
from interfaces.api.schemas import (
    TodoCreate, TodoUpdate, TodoOut, TodoSearchParams,
    PagedTodoResponse, ErrorResponse, ErrorDetail,
    BulkTodoOperation, BulkTodoResponse, TodoStats
)

router = APIRouter(prefix="/api/v1/todos", tags=["todos"])


async def get_todo_service():
    """TodoService の依存性注入"""
    db_manager = get_database_manager()
    async for session in db_manager.get_session():
        repository = SqlAlchemyTodoRepository(session)
        yield TodoService(repository)


@router.get("", response_model=PagedTodoResponse)
async def list_todos(
    page: int = Query(default=1, ge=1, description="ページ番号"),
    page_size: int = Query(default=20, ge=1, le=100, description="ページサイズ"),
    sort: Optional[str] = Query(default=None, description="ソート条件"),
    is_done: Optional[bool] = Query(default=None, description="完了状態フィルタ"),
    q: Optional[str] = Query(default=None, description="フリーテキスト検索"),
    tag: List[str] = Query(default=[], description="タグフィルタ"),
    due_before: Optional[datetime] = Query(default=None, description="期限前フィルタ"),
    due_after: Optional[datetime] = Query(default=None, description="期限後フィルタ"),
    todo_service: TodoService = Depends(get_todo_service)
):
    """ToDo 一覧取得（検索・ページング・ソート対応）"""
    try:
        result = await todo_service.search_todos(
            page=page,
            page_size=page_size,
            sort=sort,
            is_done=is_done,
            q=q,
            tags=tag,
            due_before=due_before,
            due_after=due_after
        )
        
        return PagedTodoResponse(
            items=[TodoOut.model_validate(todo.__dict__) for todo in result.items],
            page=result.page,
            page_size=result.page_size,
            total_items=result.total_items,
            total_pages=result.total_pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.create(
                code="INTERNAL_ERROR",
                message="Internal server error"
            ).model_dump()
        )


@router.post("", response_model=TodoOut, status_code=201)
async def create_todo(
    todo_data: TodoCreate,
    response: Response,
    todo_service: TodoService = Depends(get_todo_service)
):
    """ToDo 作成"""
    try:
        created_todo = await todo_service.create_todo(
            title=todo_data.title,
            description=todo_data.description,
            priority=todo_data.priority,
            due_date=todo_data.due_date,
            tags=todo_data.tags
        )
        
        # Location ヘッダを設定
        response.headers["Location"] = f"/api/v1/todos/{created_todo.id}"
        
        return TodoOut.model_validate(created_todo.__dict__)
    
    except ValueError as e:
        # バリデーションエラー
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse.create(
                code="VALIDATION_ERROR",
                message=str(e),
                details=[ErrorDetail(field="general", reason=str(e))]
            ).model_dump()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.create(
                code="INTERNAL_ERROR",
                message="Internal server error"
            ).model_dump()
        )


@router.get("/{todo_id}", response_model=TodoOut)
async def get_todo(
    todo_id: int,
    todo_service: TodoService = Depends(get_todo_service)
):
    """ToDo 取得（単体）"""
    try:
        todo = await todo_service.get_todo_by_id(todo_id)
        
        if todo is None:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse.create(
                    code="NOT_FOUND",
                    message="todo not found"
                ).model_dump()
            )
        
        return TodoOut.model_validate(todo.__dict__)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.create(
                code="INTERNAL_ERROR",
                message="Internal server error"
            ).model_dump()
        )


@router.patch("/{todo_id}", response_model=TodoOut)
async def update_todo(
    todo_id: int,
    todo_data: TodoUpdate,
    todo_service: TodoService = Depends(get_todo_service)
):
    """ToDo 更新（部分）"""
    try:
        # 更新データを辞書に変換（None 値は除外）
        update_fields = todo_data.model_dump(exclude_unset=True)
        
        updated_todo = await todo_service.update_todo(
            todo_id=todo_id,
            **update_fields
        )
        
        if updated_todo is None:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse.create(
                    code="NOT_FOUND",
                    message="todo not found"
                ).model_dump()
            )
        
        return TodoOut.model_validate(updated_todo.__dict__)
    
    except HTTPException:
        raise
    except ValueError as e:
        # バリデーションエラー
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse.create(
                code="VALIDATION_ERROR",
                message=str(e),
                details=[ErrorDetail(field="general", reason=str(e))]
            ).model_dump()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.create(
                code="INTERNAL_ERROR",
                message="Internal server error"
            ).model_dump()
        )


@router.put("/{todo_id}", response_model=TodoOut)
async def replace_todo(
    todo_id: int,
    todo_data: TodoCreate,
    todo_service: TodoService = Depends(get_todo_service)
):
    """ToDo 置換（全体更新）"""
    try:
        # 既存の ToDo が存在するかチェック
        existing_todo = await todo_service.get_todo_by_id(todo_id)
        
        if existing_todo is None:
            # 新規作成（upsert）
            created_todo = await todo_service.create_todo(
                title=todo_data.title,
                description=todo_data.description,
                priority=todo_data.priority,
                due_date=todo_data.due_date,
                tags=todo_data.tags
            )
            return TodoOut.model_validate(created_todo.__dict__)
        else:
            # 全体更新
            updated_todo = await todo_service.update_todo(
                todo_id=todo_id,
                title=todo_data.title,
                description=todo_data.description,
                is_done=todo_data.is_done,
                priority=todo_data.priority,
                due_date=todo_data.due_date,
                tags=todo_data.tags
            )
            return TodoOut.model_validate(updated_todo.__dict__)
    
    except ValueError as e:
        # バリデーションエラー
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse.create(
                code="VALIDATION_ERROR",
                message=str(e),
                details=[ErrorDetail(field="general", reason=str(e))]
            ).model_dump()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.create(
                code="INTERNAL_ERROR",
                message="Internal server error"
            ).model_dump()
        )


@router.delete("/{todo_id}", status_code=204)
async def delete_todo(
    todo_id: int,
    todo_service: TodoService = Depends(get_todo_service)
):
    """ToDo 削除"""
    try:
        deleted = await todo_service.delete_todo(todo_id)
        
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse.create(
                    code="NOT_FOUND",
                    message="todo not found"
                ).model_dump()
            )
        
        return Response(status_code=204)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.create(
                code="INTERNAL_ERROR",
                message="Internal server error"
            ).model_dump()
        )


@router.patch(":bulk", response_model=BulkTodoResponse)
async def bulk_update_todos(
    operation: BulkTodoOperation,
    todo_service: TodoService = Depends(get_todo_service)
):
    """一括操作"""
    try:
        if operation.op == "mark_done":
            result = await todo_service.bulk_mark_as_done(operation.ids)
        else:
            # mark_undone の場合（将来の拡張）
            result = {"updated": 0, "failed_ids": operation.ids}
        
        return BulkTodoResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.create(
                code="INTERNAL_ERROR",
                message="Internal server error"
            ).model_dump()
        )


@router.get("/stats/summary", response_model=TodoStats)
async def get_todo_stats(
    todo_service: TodoService = Depends(get_todo_service)
):
    """ToDo 統計情報取得"""
    try:
        total = await todo_service.get_todos_count()
        done = await todo_service.get_done_todos_count()
        pending = await todo_service.get_pending_todos_count()
        
        return TodoStats(
            total=total,
            done=done,
            pending=pending,
            completion_rate=0.0  # model_validator で計算される
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.create(
                code="INTERNAL_ERROR",
                message="Internal server error"
            ).model_dump()
        )
