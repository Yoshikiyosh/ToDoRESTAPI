from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from interfaces.api.schemas import ErrorResponse, ErrorDetail


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """バリデーションエラーハンドラ"""
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # 'body' を除外
        details.append(ErrorDetail(
            field=field or "general",
            reason=error["msg"]
        ))
    
    error_response = ErrorResponse.create(
        code="VALIDATION_ERROR",
        message="Invalid request",
        details=details
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.model_dump()
    )


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Pydantic バリデーションエラーハンドラ"""
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        details.append(ErrorDetail(
            field=field or "general",
            reason=error["msg"]
        ))
    
    error_response = ErrorResponse.create(
        code="VALIDATION_ERROR",
        message="Validation failed",
        details=details
    )
    
    return JSONResponse(
        status_code=400,
        content=error_response.model_dump()
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP例外ハンドラ"""
    # すでにエラーレスポンス形式の場合はそのまま返す
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    
    # 通常の HTTPException の場合
    error_response = ErrorResponse.create(
        code="HTTP_ERROR",
        message=str(exc.detail)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception):
    """一般的な例外ハンドラ"""
    error_response = ErrorResponse.create(
        code="INTERNAL_ERROR",
        message="Internal server error"
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )
