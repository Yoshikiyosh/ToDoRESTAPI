from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import uuid


class TodoBase(BaseModel):
    """ToDo の基本スキーマ"""
    title: str = Field(..., min_length=1, max_length=200, description="ToDo のタイトル")
    description: Optional[str] = Field(None, max_length=2000, description="ToDo の説明")
    is_done: bool = Field(default=False, description="完了状態")
    priority: int = Field(default=0, ge=0, le=5, description="優先度 (0-5)")
    due_date: Optional[datetime] = Field(None, description="期限日時")
    tags: List[str] = Field(default_factory=list, description="タグリスト")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('title is required and cannot be empty')
        return v.strip()

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if not v:
            return []
        
        if len(v) > 20:
            raise ValueError('maximum 20 tags allowed')
        
        normalized_tags = []
        for tag in v:
            if not tag or not tag.strip():
                continue
            normalized_tag = tag.strip().lower()
            if len(normalized_tag) > 30:
                raise ValueError('tag must be 30 characters or less')
            if normalized_tag not in normalized_tags:
                normalized_tags.append(normalized_tag)
        
        return normalized_tags


class TodoCreate(TodoBase):
    """ToDo 作成リクエストスキーマ"""
    # is_done は作成時には指定しない（常に False）
    is_done: bool = Field(default=False, description="完了状態（作成時は常に false）")


class TodoUpdate(BaseModel):
    """ToDo 更新リクエストスキーマ（部分更新）"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="ToDo のタイトル")
    description: Optional[str] = Field(None, max_length=2000, description="ToDo の説明")
    is_done: Optional[bool] = Field(None, description="完了状態")
    priority: Optional[int] = Field(None, ge=0, le=5, description="優先度 (0-5)")
    due_date: Optional[datetime] = Field(None, description="期限日時")
    tags: Optional[List[str]] = Field(None, description="タグリスト")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('title cannot be empty')
            return v.strip()
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if v is None:
            return v
        
        if len(v) > 20:
            raise ValueError('maximum 20 tags allowed')
        
        normalized_tags = []
        for tag in v:
            if not tag or not tag.strip():
                continue
            normalized_tag = tag.strip().lower()
            if len(normalized_tag) > 30:
                raise ValueError('tag must be 30 characters or less')
            if normalized_tag not in normalized_tags:
                normalized_tags.append(normalized_tag)
        
        return normalized_tags


class TodoOut(TodoBase):
    """ToDo レスポンススキーマ"""
    id: int = Field(..., description="ToDo の ID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    class Config:
        from_attributes = True


class TodoSearchParams(BaseModel):
    """ToDo 検索パラメータスキーマ"""
    page: int = Field(default=1, ge=1, description="ページ番号")
    page_size: int = Field(default=20, ge=1, le=100, description="ページサイズ")
    sort: Optional[str] = Field(None, description="ソート条件")
    is_done: Optional[bool] = Field(None, description="完了状態フィルタ")
    q: Optional[str] = Field(None, description="フリーテキスト検索")
    tag: Optional[List[str]] = Field(default_factory=list, description="タグフィルタ")
    due_before: Optional[datetime] = Field(None, description="期限前フィルタ")
    due_after: Optional[datetime] = Field(None, description="期限後フィルタ")


class PagedTodoResponse(BaseModel):
    """ページ付き ToDo レスポンススキーマ"""
    items: List[TodoOut] = Field(..., description="ToDo リスト")
    page: int = Field(..., description="現在のページ番号")
    page_size: int = Field(..., description="ページサイズ")
    total_items: int = Field(..., description="総件数")
    total_pages: int = Field(..., description="総ページ数")


class ErrorDetail(BaseModel):
    """エラー詳細スキーマ"""
    field: str = Field(..., description="エラーが発生したフィールド")
    reason: str = Field(..., description="エラーの理由")


class ErrorResponse(BaseModel):
    """エラーレスポンススキーマ"""
    error: dict[str, Any] = Field(..., description="エラー情報")

    @classmethod
    def create(
        cls,
        code: str,
        message: str,
        details: List[ErrorDetail] = None,
        trace_id: str = None
    ) -> "ErrorResponse":
        """エラーレスポンスを作成する"""
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        
        return cls(
            error={
                "code": code,
                "message": message,
                "details": details or [],
                "trace_id": trace_id
            }
        )


class BulkTodoOperation(BaseModel):
    """一括操作リクエストスキーマ"""
    op: str = Field(..., description="操作種別 (mark_done, mark_undone)")
    ids: List[int] = Field(..., min_length=1, description="対象 ToDo ID リスト")

    @field_validator('op')
    @classmethod
    def validate_op(cls, v):
        allowed_ops = ["mark_done", "mark_undone"]
        if v not in allowed_ops:
            raise ValueError(f'op must be one of {allowed_ops}')
        return v


class BulkTodoResponse(BaseModel):
    """一括操作レスポンススキーマ"""
    updated: int = Field(..., description="更新された件数")
    failed_ids: List[int] = Field(..., description="失敗した ToDo ID リスト")


class TodoStats(BaseModel):
    """ToDo 統計スキーマ"""
    total: int = Field(..., description="総 ToDo 数")
    done: int = Field(..., description="完了 ToDo 数")
    pending: int = Field(..., description="未完了 ToDo 数")
    completion_rate: float = Field(..., description="完了率 (0.0-1.0)")

    @model_validator(mode='after')
    def calculate_completion_rate(self):
        if self.total == 0:
            self.completion_rate = 0.0
        else:
            self.completion_rate = self.done / self.total
        return self
