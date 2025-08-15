from pydantic import BaseModel
from typing import List, Optional, ForwardRef
from datetime import datetime, date
from enum import Enum

# ==== 管理者関連のスキーマ ====

class AdminRole(str, Enum):
    super_admin = "super_admin"
    admin = "admin"
    moderator = "moderator"

class ApplicationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class PostStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    reported = "reported"

class NoticeStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"

class NoticePriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"

# 管理者認証
class AdminLoginRequest(BaseModel):
    email: str
    password: str

class AdminUserResponse(BaseModel):
    id: str
    email: str
    last_name: str
    first_name: str
    role: AdminRole
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str
    admin_user: AdminUserResponse

# 管理者ユーザー
class AdminUserCreateRequest(BaseModel):
    email: str
    password: str
    last_name: str
    first_name: str
    role: AdminRole = AdminRole.admin

class AdminUserUpdateRequest(BaseModel):
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    role: Optional[AdminRole] = None
    is_active: Optional[bool] = None

# 申請管理
class ApplicationResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_email: str
    user_phone: str
    dog_name: str
    dog_breed: Optional[str] = None
    dog_weight: Optional[str] = None
    vaccine_certificate: Optional[str] = None
    request_date: Optional[date] = None
    request_time: Optional[str] = None
    status: ApplicationStatus
    admin_notes: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ApplicationUpdateRequest(BaseModel):
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None

# 管理者ログ
class AdminLogResponse(BaseModel):
    id: str
    admin_user_id: str
    admin_user_name: str
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# 投稿管理
class PostManagementResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    content: str
    status: PostStatus
    admin_notes: Optional[str] = None
    likes_count: int
    comments_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PostStatusUpdateRequest(BaseModel):
    status: PostStatus
    admin_notes: Optional[str] = None

# ユーザー管理（拡張）
class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    suspended_users: int
    new_users_this_month: int
    
class UserDetailResponse(BaseModel):
    id: str
    email: str
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    prefecture: Optional[str] = None
    city: Optional[str] = None
    is_active: bool = True
    is_suspended: bool = False
    dogs_count: int = 0
    posts_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserSuspendRequest(BaseModel):
    reason: str
    suspend_until: Optional[datetime] = None

# イベント管理
class EventCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: date
    start_time: str
    end_time: str
    location: str
    capacity: int
    fee: int = 0

class EventUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    capacity: Optional[int] = None
    fee: Optional[int] = None

class EventManagementResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    event_date: date
    start_time: str
    end_time: str
    location: str
    capacity: int
    current_participants: int
    fee: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EventStatsResponse(BaseModel):
    total_events: int
    upcoming_events: int
    past_events: int
    total_participants: int

class EventRegistrationResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    event_id: str
    dog_id: Optional[str] = None
    dog_name: Optional[str] = None
    registered_at: datetime
    
    class Config:
        from_attributes = True

# お知らせ管理
class NoticeCreateRequest(BaseModel):
    title: str
    content: str
    category: Optional[str] = None
    priority: NoticePriority = NoticePriority.normal
    expires_at: Optional[date] = None

class NoticeUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[NoticePriority] = None
    status: Optional[NoticeStatus] = None
    expires_at: Optional[date] = None

class NoticeManagementResponse(BaseModel):
    id: str
    title: str
    content: str
    category: Optional[str] = None
    priority: NoticePriority
    status: NoticeStatus
    posted_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[date] = None
    view_count: int = 0

    class Config:
        from_attributes = True

# 営業時間管理
class BusinessHourResponse(BaseModel):
    id: str
    day_of_week: int  # 0:日曜, 1:月曜, ..., 6:土曜
    is_open: bool
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    special_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BusinessHourUpdateRequest(BaseModel):
    is_open: bool
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    special_note: Optional[str] = None

class SpecialHolidayResponse(BaseModel):
    id: str
    holiday_date: date
    holiday_name: Optional[str] = None
    is_open: bool
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SpecialHolidayCreateRequest(BaseModel):
    holiday_date: date
    holiday_name: Optional[str] = None
    is_open: bool = False
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    note: Optional[str] = None

class SpecialHolidayUpdateRequest(BaseModel):
    holiday_name: Optional[str] = None
    is_open: Optional[bool] = None
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    note: Optional[str] = None

class TodayBusinessHoursResponse(BaseModel):
    date: date
    day_of_week: int
    day_name: str
    is_open: bool
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    special_note: Optional[str] = None
    is_holiday: bool
    holiday_name: Optional[str] = None

# 設定管理
class SystemSettingResponse(BaseModel):
    id: str
    setting_key: str
    setting_value: Optional[str] = None
    setting_type: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    is_public: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SystemSettingUpdateRequest(BaseModel):
    setting_value: str

class SystemSettingsCategoryResponse(BaseModel):
    category: str
    settings: List[SystemSettingResponse]

class SystemSettingsBackupResponse(BaseModel):
    backup_id: str
    created_at: datetime
    settings_count: int
    file_path: str

class SystemSettingsImportRequest(BaseModel):
    settings: dict

# 統計情報
class DashboardStatsResponse(BaseModel):
    total_users: int
    total_dogs: int
    pending_applications: int
    pending_posts: int
    total_events: int
    active_events: int
    total_notices: int
    published_notices: int

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
    created_at: Optional[datetime] = None

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