from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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