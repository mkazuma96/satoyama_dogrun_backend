from fastapi import HTTPException, status
from typing import Any, Dict, Optional

class SatoyamaDogrunException(Exception):
    """里山ドッグランアプリケーションの基底例外クラス"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(SatoyamaDogrunException):
    """バリデーションエラー"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

class AuthenticationError(SatoyamaDogrunException):
    """認証エラー"""
    
    def __init__(self, message: str = "認証に失敗しました"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class AuthorizationError(SatoyamaDogrunException):
    """認可エラー"""
    
    def __init__(self, message: str = "アクセス権限がありません"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )

class NotFoundError(SatoyamaDogrunException):
    """リソースが見つからないエラー"""
    
    def __init__(self, resource: str, resource_id: Any):
        super().__init__(
            message=f"{resource}が見つかりません (ID: {resource_id})",
            status_code=status.HTTP_404_NOT_FOUND
        )

class ConflictError(SatoyamaDogrunException):
    """競合エラー（重複など）"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )

class DatabaseError(SatoyamaDogrunException):
    """データベースエラー"""
    
    def __init__(self, message: str = "データベースエラーが発生しました"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class FileUploadError(SatoyamaDogrunException):
    """ファイルアップロードエラー"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

# 例外をHTTPExceptionに変換する関数
def raise_http_exception(exception: SatoyamaDogrunException) -> HTTPException:
    """カスタム例外をHTTPExceptionに変換"""
    return HTTPException(
        status_code=exception.status_code,
        detail={
            "message": exception.message,
            "details": exception.details
        }
    ) 