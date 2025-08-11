from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date

# 認証関連
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    address: str
    phone_number: str
    imabari_residency: str

# ユーザー関連
class UpdateUserProfileRequest(BaseModel):
    full_name: str
    address: str
    phone_number: str
    imabari_residency: str

# 犬のプロフィール関連
class AddDogRequest(BaseModel):
    name: str
    breed: str
    weight: str
    personality: List[str]
    last_vaccination_date: str

# 投稿関連
class CreatePostRequest(BaseModel):
    content: str
    category: str
    hashtags: Optional[str] = None

class AddCommentRequest(BaseModel):
    text: str

# 入場関連
class CalendarRequest(BaseModel):
    year: int
    month: int

# レスポンス用
class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class MessageResponse(BaseModel):
    message: str 

# 新スキーマ: ユーザー登録レスポンス（db_control.models.User に合わせて ID を文字列に）
class UserRegisterResponse(BaseModel):
    id: str
    email: str
    full_name: str
    address: str
    phone_number: str
    imabari_residency: str
    created_at: datetime

# ==== db_control 準拠のユーザースキーマ ====
class RegisterDbRequest(BaseModel):
    email: str
    password: str
    last_name: str
    first_name: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    prefecture: Optional[str] = None
    city: Optional[str] = None

class UpdateUserDbRequest(BaseModel):
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    prefecture: Optional[str] = None
    city: Optional[str] = None

class UserDbResponse(BaseModel):
    id: str
    email: str
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    prefecture: Optional[str] = None
    city: Optional[str] = None
    created_at: datetime

# ==== db_control 準拠の犬スキーマ ====
class CreateDogDbRequest(BaseModel):
    name: str
    breed: Optional[str] = None
    birthday_at: date
    gender: Optional[str] = None
    personality: Optional[str] = None
    likes: Optional[str] = None
    avatar_url: Optional[str] = None

class UpdateDogDbRequest(BaseModel):
    name: Optional[str] = None
    breed: Optional[str] = None
    birthday_at: Optional[date] = None
    gender: Optional[str] = None
    personality: Optional[str] = None
    likes: Optional[str] = None
    avatar_url: Optional[str] = None

class DogDbResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    breed: Optional[str] = None
    birthday_at: date
    gender: Optional[str] = None
    personality: Optional[str] = None
    likes: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# ==== db_control 準拠の投稿・コメント・いいねスキーマ ====
class CreatePostDbRequest(BaseModel):
    content: str
    images: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None

class PostDbResponse(BaseModel):
    id: str
    user_id: str
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    comments_count: int
    likes_count: int

class CreateCommentDbRequest(BaseModel):
    content: str

class CommentDbResponse(BaseModel):
    id: str
    post_id: str
    user_id: str
    content: str
    created_at: datetime