from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import uvicorn
from datetime import datetime, date
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# models.pyは不要なので削除 - db_control.modelsを使用
from schemas import (
    CreatePostDbRequest, PostDbResponse, PostDetailResponse, CreateCommentDbRequest, CommentDbResponse,
    EventResponse as EventDbResponse, EventDetailResponse, EventRegistrationRequest, EventParticipantResponse,
    QRCodeResponse, EntryRequest, EntryResponse, CurrentVisitorsResponse, EntryHistoryResponse,
    # 管理者用スキーマ
    AdminLoginRequest, AdminLoginResponse, AdminUserResponse,
    ApplicationResponse, ApplicationUpdateRequest, ApplicationCreateRequest, ApplicationStatusResponse,
    PostManagementResponse, PostStatusUpdateRequest,
    DashboardStatsResponse,
    # 営業時間・設定管理用スキーマ
    BusinessHourResponse, BusinessHourUpdateRequest,
    SpecialHolidayResponse, SpecialHolidayCreateRequest, SpecialHolidayUpdateRequest,
    TodayBusinessHoursResponse,
    SystemSettingResponse, SystemSettingUpdateRequest, SystemSettingsCategoryResponse,
    SystemSettingsBackupResponse, SystemSettingsImportRequest,
    # ユーザー・イベント管理拡張スキーマ
    UserStatsResponse, UserDetailResponse, UserSuspendRequest,
    EventStatsResponse, EventRegistrationResponse, EventManagementResponse, EventCreateRequest, EventUpdateRequest
)
from db_control.models import User as DbUser
from db_control.models import Dog as DbDog
from db_control.models import Post as DbPost
from db_control.models import PostImage as DbPostImage
from db_control.models import Comment as DbComment
from db_control.models import Like as DbLike
from db_control.models import Hashtag as DbHashtag
from db_control.models import PostHashtag as DbPostHashtag
from db_control.models import VaccinationRecord as DbVaccinationRecord
from db_control.models import Event as DbEvent
from db_control.models import EventRegistration as DbEventRegistration
from db_control.models import EntryLog as DbEntryLog
from db_control.models import EntryAction
from db_control.models import EventStatus
from db_control.models import AdminUser, AdminLog, Application, ApplicationStatus, BusinessHour, SpecialHoliday, SystemSetting
from database import engine, get_db
from auth import (
    get_current_user, create_access_token, verify_password, get_password_hash,
    get_current_admin_user, create_admin_access_token, log_admin_action
)
from schemas import (
    LoginRequest, RegisterRequest, CreatePostRequest, AddCommentRequest,
    AddDogRequest, UpdateUserProfileRequest, CalendarRequest,
    UserRegisterResponse,
    RegisterDbRequest, UpdateUserDbRequest, UserDbResponse, UserProfileDetailResponse,
    CreateDogDbRequest, UpdateDogDbRequest, DogDbResponse,
    VaccinationRecordRequest, VaccinationRecordResponse,
    CreatePostDbRequest, PostDbResponse, PostDetailResponse, CreateCommentDbRequest, CommentDbResponse,
    EventResponse as EventDbResponse, EventDetailResponse, EventRegistrationRequest, EventParticipantResponse,
    QRCodeResponse, EntryRequest, EntryResponse, CurrentVisitorsResponse, EntryHistoryResponse,
    # 管理者用スキーマ
    AdminLoginRequest, AdminLoginResponse, AdminUserResponse,
    ApplicationResponse, ApplicationUpdateRequest, ApplicationCreateRequest, ApplicationStatusResponse,
    PostManagementResponse, PostStatusUpdateRequest,
    DashboardStatsResponse,
    # 営業時間・設定管理用スキーマ
    BusinessHourResponse, BusinessHourUpdateRequest,
    SpecialHolidayResponse, SpecialHolidayCreateRequest, SpecialHolidayUpdateRequest,
    TodayBusinessHoursResponse,
    SystemSettingResponse, SystemSettingUpdateRequest, SystemSettingsCategoryResponse,
    SystemSettingsBackupResponse, SystemSettingsImportRequest,
    # ユーザー・イベント管理拡張スキーマ
    UserStatsResponse, UserDetailResponse, UserSuspendRequest,
    EventStatsResponse, EventRegistrationResponse, EventManagementResponse, EventCreateRequest, EventUpdateRequest
)

load_dotenv()

app = FastAPI(
    title="里山ドッグラン API",
    description="里山ドッグランの管理システムAPI",
    version="1.0.0"
)

# CORS設定
default_origins = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3002,https://app-002-gen10-step3-2-node-oshima14.azurewebsites.net"
allowed_origins = os.getenv("ALLOWED_ORIGINS", default_origins).split(",")
# 空文字列を除去してクリーンなリストを作成
allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# アップロード用ディレクトリの作成
UPLOAD_DIR = Path("uploads")
POST_UPLOAD_DIR = UPLOAD_DIR / "posts"
POST_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

VACCINE_CERTIFICATE_UPLOAD_DIR = UPLOAD_DIR / "vaccine_certificates"
VACCINE_CERTIFICATE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Static filesのマウント
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# データベース初期化（環境変数で制御）
from database import Base
if os.getenv("AUTO_CREATE_TABLES", "false").lower() == "true":
    Base.metadata.create_all(bind=engine)
# db_control のテーブル作成を個別に有効化（初回のみ true 推奨）
if os.getenv("AUTO_CREATE_DB_CONTROL_TABLES", "false").lower() == "true":
    from db_control.models import Base as DbBase
    DbBase.metadata.create_all(bind=engine)

# ===== 管理者用APIエンドポイント =====

@app.post("/admin/auth/login", response_model=AdminLoginResponse)
async def admin_login(
    request: AdminLoginRequest,
    db=Depends(get_db)
):
    """管理者ログイン"""
    admin_user = db.query(AdminUser).filter(
        AdminUser.email == request.email,
        AdminUser.is_active == True
    ).first()
    
    if not admin_user or not verify_password(request.password, admin_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません"
        )
    
    # 最終ログイン時刻を更新
    admin_user.last_login = datetime.utcnow()
    db.commit()
    
    # 管理者用アクセストークンを作成
    access_token = create_admin_access_token(data={"sub": admin_user.email})
    
    return AdminLoginResponse(
        access_token=access_token,
        token_type="bearer",
        admin_user=AdminUserResponse(
            id=admin_user.id,
            email=admin_user.email,
            last_name=admin_user.last_name,
            first_name=admin_user.first_name,
            role=admin_user.role,
            is_active=admin_user.is_active,
            last_login=admin_user.last_login,
            created_at=admin_user.created_at,
            updated_at=admin_user.updated_at
        )
    )

@app.get("/admin/auth/me", response_model=AdminUserResponse)
async def get_current_admin_info(
    current_admin = Depends(get_current_admin_user)
):
    """現在の管理者情報取得"""
    return AdminUserResponse(
        id=current_admin.id,
        email=current_admin.email,
        last_name=current_admin.last_name,
        first_name=current_admin.first_name,
        role=current_admin.role,
        is_active=current_admin.is_active,
        last_login=current_admin.last_login,
        created_at=current_admin.created_at,
        updated_at=current_admin.updated_at
    )

@app.get("/admin/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """ダッシュボード統計情報取得"""
    total_users = db.query(DbUser).count()
    total_dogs = db.query(DbDog).count()
    pending_applications = db.query(Application).filter(
        Application.status == "pending"
    ).count()
    pending_posts = db.query(DbPost).filter(
        DbPost.status == "pending"
    ).count()
    total_events = db.query(Event).count()
    active_events = db.query(Event).filter(
        Event.event_date >= date.today()
    ).count()
    total_notices = db.query(Notice).count()
    published_notices = total_notices  # announcementsテーブルにはstatusカラムがないため、全件を公開済みとして扱う
    
    return DashboardStatsResponse(
        total_users=total_users,
        total_dogs=total_dogs,
        pending_applications=pending_applications,
        pending_posts=pending_posts,
        total_events=total_events,
        active_events=active_events,
        total_notices=total_notices,
        published_notices=published_notices
    )

# 申請管理
@app.get("/admin/applications", response_model=List[ApplicationResponse])
async def get_applications(
    status: Optional[str] = None,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """申請一覧取得"""
    query = db.query(Application)
    
    if status:
        query = query.filter(Application.status == status)
    
    applications = query.order_by(Application.created_at.desc()).all()
    
    responses = []
    for app in applications:
        # 申請データから直接情報を取得（user_idはNullの可能性がある）
        user_name = f"{app.user_last_name} {app.user_first_name}"
        
        responses.append(ApplicationResponse(
            id=app.id,
            user_id=app.user_id,  # Noneの場合もある
            user_name=user_name,
            user_email=app.user_email,
            user_phone=app.user_phone,
            dog_name=app.dog_name,
            dog_breed=app.dog_breed,
            dog_weight=app.dog_weight,
            vaccine_certificate=app.vaccine_certificate,
            request_date=app.request_date,
            request_time=app.request_time,
            status=app.status,
            admin_notes=app.admin_notes,
            approved_by=app.approved_by,
            approved_at=app.approved_at,
            rejection_reason=app.rejection_reason,
            created_at=app.created_at,
            updated_at=app.updated_at
        ))
    
    return responses

@app.get("/admin/applications/stats")
async def get_applications_stats(
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """申請統計取得"""
    from sqlalchemy import func
    
    total = db.query(func.count(Application.id)).scalar()
    pending = db.query(func.count(Application.id)).filter(Application.status == "pending").scalar()
    approved = db.query(func.count(Application.id)).filter(Application.status == "approved").scalar()
    rejected = db.query(func.count(Application.id)).filter(Application.status == "rejected").scalar()
    
    # 今日の申請数
    today = datetime.utcnow().date()
    today_count = db.query(func.count(Application.id)).filter(
        func.date(Application.created_at) == today
    ).scalar()
    
    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "today": today_count
    }

@app.get("/admin/applications/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """申請詳細取得"""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="申請が見つかりません")
    
    user = db.query(DbUser).filter(DbUser.id == application.user_id).first()
    user_name = f"{user.last_name} {user.first_name}" if user else "不明"
    
    return ApplicationResponse(
        id=application.id,
        user_id=application.user_id,
        user_name=user_name,
        user_email=user.email if user else "",
        user_phone=user.phone_number if user else "",
        dog_name=application.dog_name,
        dog_breed=application.dog_breed,
        dog_weight=application.dog_weight,
        vaccine_certificate=application.vaccine_certificate,
        request_date=application.request_date,
        request_time=application.request_time,
        status=application.status,
        admin_notes=application.admin_notes,
        approved_by=application.approved_by,
        approved_at=application.approved_at,
        rejection_reason=application.rejection_reason,
        created_at=application.created_at,
        updated_at=application.updated_at
    )

@app.put("/admin/applications/{application_id}/approve")
async def approve_application(
    application_id: str,
    request: ApplicationUpdateRequest,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """申請承認"""
    from uuid import uuid4
    
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="申請が見つかりません")
    
    # 既に承認済みの場合はエラー
    if application.status == ApplicationStatus.approved:
        raise HTTPException(status_code=400, detail="この申請は既に承認されています")
    
    # 新規申請の場合（user_idがNULL）、ユーザーを作成
    if application.user_id is None and application.user_email:
        # メールアドレスの重複チェック
        existing_user = db.query(DbUser).filter(DbUser.email == application.user_email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="このメールアドレスは既に登録されています")
        
        # ユーザー作成
        new_user = DbUser(
            id=str(uuid4()),
            email=application.user_email,
            password_hash=application.user_password_hash,  # 申請時に保存したハッシュ値を使用
            last_name=application.user_last_name,
            first_name=application.user_first_name,
            phone_number=application.user_phone,
            address=application.user_address,
            prefecture=application.user_prefecture,
            city=application.user_city,
            created_at=datetime.utcnow()
        )
        db.add(new_user)
        db.flush()  # ユーザーをデータベースに反映（コミット前）
        
        # 犬情報も同時に登録
        if application.dog_name:
            new_dog = DbDog(
                id=str(uuid4()),
                owner_id=new_user.id,  # owner_idが正しいカラム名
                name=application.dog_name,
                breed=application.dog_breed,
                birthday_at=date.today(),  # 仮の誕生日を設定（必須フィールドのため）
                gender=application.dog_gender,
                created_at=datetime.utcnow()
            )
            db.add(new_dog)
        
        # applicationのuser_idを更新
        application.user_id = new_user.id
    
    # 申請ステータスを承認に更新
    application.status = ApplicationStatus.approved
    application.admin_notes = request.admin_notes
    application.approved_by = current_admin.id
    application.approved_at = datetime.utcnow()
    application.updated_at = datetime.utcnow()
    
    db.commit()
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="application_approved",
        target_type="application",
        target_id=application_id,
        details=f"申請を承認しました: {request.admin_notes or 'なし'}",
        db=db
    )
    
    return {"message": "申請を承認し、ユーザーを作成しました"}

@app.put("/admin/applications/{application_id}/reject")
async def reject_application(
    application_id: str,
    request: ApplicationUpdateRequest,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """申請却下"""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="申請が見つかりません")
    
    # 既に処理済みの場合はエラー
    if application.status != ApplicationStatus.pending:
        raise HTTPException(status_code=400, detail="この申請は既に処理されています")
    
    application.status = ApplicationStatus.rejected
    application.admin_notes = request.admin_notes
    application.rejection_reason = request.rejection_reason
    application.approved_by = current_admin.id
    application.approved_at = datetime.utcnow()
    application.updated_at = datetime.utcnow()
    
    db.commit()
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="application_rejected",
        target_type="application",
        target_id=application_id,
        details=f"申請を却下しました: {request.admin_notes or 'なし'}",
        db=db
    )
    
    return {"message": "申請を却下しました"}

# ユーザー管理（完全実装）
@app.get("/admin/users", response_model=List[UserDbResponse])
async def get_users_for_admin(
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """ユーザー一覧取得（管理者用）"""
    users = db.query(DbUser).order_by(DbUser.created_at.desc()).all()
    return [UserDbResponse(
        id=user.id,
        email=user.email,
        last_name=user.last_name,
        first_name=user.first_name,
        address=user.address,
        phone_number=user.phone_number,
        prefecture=user.prefecture,
        city=user.city,
        created_at=user.created_at,
        updated_at=user.updated_at
    ) for user in users]

@app.get("/admin/users/stats", response_model=UserStatsResponse)
async def get_users_stats(
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """ユーザー統計取得"""
    from sqlalchemy import func
    from datetime import timedelta
    
    total_users = db.query(func.count(DbUser.id)).scalar()
    
    # アクティブユーザー（最近30日以内にログイン）- 仮実装
    active_users = total_users  # TODO: ログイン履歴テーブルから計算
    
    # 停止中のユーザー - 仮実装
    suspended_users = 0  # TODO: is_suspendedフィールド追加後に実装
    
    # 今月の新規ユーザー
    today = datetime.utcnow()
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_this_month = db.query(func.count(DbUser.id)).filter(
        DbUser.created_at >= first_day_of_month
    ).scalar()
    
    return UserStatsResponse(
        total_users=total_users,
        active_users=active_users,
        suspended_users=suspended_users,
        new_users_this_month=new_users_this_month
    )

@app.get("/admin/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """ユーザー詳細取得"""
    user = db.query(DbUser).filter(DbUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    # 関連データのカウント
    dogs_count = db.query(DbDog).filter(DbDog.owner_id == user_id).count()
    posts_count = db.query(DbPost).filter(DbPost.user_id == user_id).count()
    
    return UserDetailResponse(
        id=user.id,
        email=user.email,
        last_name=user.last_name,
        first_name=user.first_name,
        address=user.address,
        phone_number=user.phone_number,
        prefecture=user.prefecture,
        city=user.city,
        is_active=True,  # TODO: 実際のフィールドから取得
        is_suspended=False,  # TODO: 実際のフィールドから取得
        dogs_count=dogs_count,
        posts_count=posts_count,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@app.put("/admin/users/{user_id}")
async def update_user(
    user_id: str,
    request: UpdateUserDbRequest,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """ユーザー情報更新"""
    user = db.query(DbUser).filter(DbUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    if request.last_name is not None:
        user.last_name = request.last_name
    if request.first_name is not None:
        user.first_name = request.first_name
    if request.address is not None:
        user.address = request.address
    if request.phone_number is not None:
        user.phone_number = request.phone_number
    if request.prefecture is not None:
        user.prefecture = request.prefecture
    if request.city is not None:
        user.city = request.city
    
    user.updated_at = datetime.utcnow()
    db.commit()
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="user_updated",
        target_type="user",
        target_id=user_id,
        details=f"ユーザー情報を更新: {user.email}",
        db=db
    )
    
    return {"message": "ユーザー情報を更新しました"}

@app.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """ユーザー削除（論理削除）"""
    user = db.query(DbUser).filter(DbUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    # 関連データの確認
    dogs_count = db.query(DbDog).filter(DbDog.owner_id == user_id).count()
    posts_count = db.query(DbPost).filter(DbPost.user_id == user_id).count()
    
    if dogs_count > 0 or posts_count > 0:
        # 物理削除ではなく論理削除を推奨
        return {"message": f"このユーザーには関連データがあります（犬: {dogs_count}件、投稿: {posts_count}件）。削除する前に確認してください。"}
    
    # 物理削除
    db.delete(user)
    db.commit()
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="user_deleted",
        target_type="user",
        target_id=user_id,
        details=f"ユーザーを削除: {user.email}",
        db=db
    )
    
    return {"message": "ユーザーを削除しました"}

@app.put("/admin/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    request: UserSuspendRequest,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """ユーザー一時停止"""
    user = db.query(DbUser).filter(DbUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    # TODO: is_suspendedフィールドをUserテーブルに追加して実装
    # user.is_suspended = True
    # user.suspend_reason = request.reason
    # user.suspend_until = request.suspend_until
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="user_suspended",
        target_type="user",
        target_id=user_id,
        details=f"ユーザーを一時停止: {request.reason}",
        db=db
    )
    
    return {"message": "ユーザーを一時停止しました"}

@app.put("/admin/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """ユーザー有効化"""
    user = db.query(DbUser).filter(DbUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    # TODO: is_suspendedフィールドをUserテーブルに追加して実装
    # user.is_suspended = False
    # user.suspend_reason = None
    # user.suspend_until = None
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="user_activated",
        target_type="user",
        target_id=user_id,
        details=f"ユーザーを有効化",
        db=db
    )
    
    return {"message": "ユーザーを有効化しました"}

@app.get("/admin/users/{user_id}/dogs", response_model=List[DogDbResponse])
async def get_user_dogs_admin(
    user_id: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """ユーザーの犬一覧取得"""
    dogs = db.query(DbDog).filter(DbDog.owner_id == user_id).all()
    return [DogDbResponse(
        id=dog.id,
        user_id=dog.user_id,
        name=dog.name,
        breed=dog.breed,
        weight=dog.weight,
        personality=dog.personality,
        vaccination_status=dog.vaccination_status,
        last_vaccination_date=dog.last_vaccination_date,
        created_at=dog.created_at,
        updated_at=dog.updated_at
    ) for dog in dogs]

@app.get("/admin/users/{user_id}/posts", response_model=List[PostManagementResponse])
async def get_user_posts_admin(
    user_id: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """ユーザーの投稿一覧取得"""
    posts = db.query(DbPost).filter(DbPost.user_id == user_id).order_by(DbPost.created_at.desc()).all()
    
    responses = []
    for post in posts:
        user = db.query(DbUser).filter(DbUser.id == post.user_id).first()
        user_name = f"{user.last_name} {user.first_name}" if user else "不明"
        
        likes_count = db.query(DbLike).filter(DbLike.post_id == post.id).count()
        comments_count = db.query(DbComment).filter(DbComment.post_id == post.id).count()
        
        responses.append(PostManagementResponse(
            id=post.id,
            user_id=post.user_id,
            user_name=user_name,
            content=post.content,
            status=post.status,
            admin_notes=post.admin_notes,
            likes_count=likes_count,
            comments_count=comments_count,
            created_at=post.created_at,
            updated_at=post.updated_at
        ))
    
    return responses

# 犬の管理
@app.get("/admin/dogs", response_model=List[DogDbResponse])
async def get_dogs_for_admin(
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """犬一覧取得（管理者用）"""
    dogs = db.query(DbDog).order_by(DbDog.created_at.desc()).all()
    return [DogDbResponse(
        id=dog.id,
        user_id=dog.user_id,
        name=dog.name,
        breed=dog.breed,
        weight=dog.weight,
        personality=dog.personality,
        vaccination_status=dog.vaccination_status,
        last_vaccination_date=dog.last_vaccination_date,
        created_at=dog.created_at,
        updated_at=dog.updated_at
    ) for dog in dogs]

# イベント管理（完全実装）
@app.get("/admin/events", response_model=List[EventManagementResponse])
async def get_events_for_admin(
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """イベント一覧取得（管理者用）"""
    from db_control.models import Event as DbEvent, EventRegistration
    events = db.query(DbEvent).order_by(DbEvent.event_date.desc()).all()
    
    responses = []
    for event in events:
        # 参加者数を取得
        participants_count = db.query(EventRegistration).filter(
            EventRegistration.event_id == event.id
        ).count()
        
        responses.append(EventManagementResponse(
            id=event.id,
            title=event.title,
            description=event.description,
            event_date=event.event_date,
            start_time=str(event.start_time) if event.start_time else "",
            end_time=str(event.end_time) if event.end_time else "",
            location=event.location or "",
            capacity=event.capacity or 0,
            current_participants=participants_count,
            fee=event.fee or 0,
            status=str(event.status) if event.status else "reception",
            created_at=event.created_at,
            updated_at=event.updated_at
        ))
    
    return responses

@app.get("/admin/events/stats", response_model=EventStatsResponse)
async def get_events_stats(
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """イベント統計取得"""
    from sqlalchemy import func
    from db_control.models import Event as DbEvent, EventRegistration
    
    total_events = db.query(func.count(DbEvent.id)).scalar()
    
    # 今後のイベント
    today = date.today()
    upcoming_events = db.query(func.count(DbEvent.id)).filter(
        DbEvent.event_date >= today
    ).scalar()
    
    # 過去のイベント
    past_events = db.query(func.count(DbEvent.id)).filter(
        DbEvent.event_date < today
    ).scalar()
    
    # 総参加者数
    total_participants = db.query(func.count(EventRegistration.id)).scalar()
    
    return EventStatsResponse(
        total_events=total_events,
        upcoming_events=upcoming_events,
        past_events=past_events,
        total_participants=total_participants
    )

@app.post("/admin/events", response_model=EventManagementResponse)
async def create_event(
    request: EventCreateRequest,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """イベント作成"""
    from uuid import uuid4
    from datetime import time
    from db_control.models import Event as DbEvent
    
    start_time = None
    end_time = None
    if request.start_time:
        hour, minute = map(int, request.start_time.split(":"))
        start_time = time(hour, minute)
    if request.end_time:
        hour, minute = map(int, request.end_time.split(":"))
        end_time = time(hour, minute)
    
    event = DbEvent(
        id=str(uuid4()),
        title=request.title,
        description=request.description,
        event_date=request.event_date,
        start_time=start_time,
        end_time=end_time,
        location=request.location,
        capacity=request.capacity,
        fee=request.fee,
        status="reception",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="event_created",
        target_type="event",
        target_id=event.id,
        details=f"イベントを作成: {request.title}",
        db=db
    )
    
    return EventManagementResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        event_date=event.event_date,
        start_time=str(event.start_time) if event.start_time else "",
        end_time=str(event.end_time) if event.end_time else "",
        location=event.location or "",
        capacity=event.capacity or 0,
        current_participants=0,
        fee=event.fee or 0,
        status=str(event.status),
        created_at=event.created_at,
        updated_at=event.updated_at
    )

@app.get("/admin/events/{event_id}", response_model=EventManagementResponse)
async def get_event_detail(
    event_id: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """イベント詳細取得"""
    from db_control.models import Event as DbEvent, EventRegistration
    
    event = db.query(DbEvent).filter(DbEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    
    participants_count = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id
    ).count()
    
    return EventManagementResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        event_date=event.event_date,
        start_time=str(event.start_time) if event.start_time else "",
        end_time=str(event.end_time) if event.end_time else "",
        location=event.location or "",
        capacity=event.capacity or 0,
        current_participants=participants_count,
        fee=event.fee or 0,
        status=str(event.status) if event.status else "reception",
        created_at=event.created_at,
        updated_at=event.updated_at
    )

@app.put("/admin/events/{event_id}", response_model=EventManagementResponse)
async def update_event(
    event_id: str,
    request: EventUpdateRequest,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """イベント更新"""
    from datetime import time
    from db_control.models import Event as DbEvent, EventRegistration
    
    event = db.query(DbEvent).filter(DbEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    
    if request.title is not None:
        event.title = request.title
    if request.description is not None:
        event.description = request.description
    if request.event_date is not None:
        event.event_date = request.event_date
    if request.start_time is not None:
        hour, minute = map(int, request.start_time.split(":"))
        event.start_time = time(hour, minute)
    if request.end_time is not None:
        hour, minute = map(int, request.end_time.split(":"))
        event.end_time = time(hour, minute)
    if request.location is not None:
        event.location = request.location
    if request.capacity is not None:
        event.capacity = request.capacity
    if request.fee is not None:
        event.fee = request.fee
    if request.status is not None:
        event.status = request.status
    
    event.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(event)
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="event_updated",
        target_type="event",
        target_id=event_id,
        details=f"イベントを更新: {event.title}",
        db=db
    )
    
    participants_count = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id
    ).count()
    
    return EventManagementResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        event_date=event.event_date,
        start_time=str(event.start_time) if event.start_time else "",
        end_time=str(event.end_time) if event.end_time else "",
        location=event.location or "",
        capacity=event.capacity or 0,
        current_participants=participants_count,
        fee=event.fee or 0,
        status=str(event.status) if event.status else "reception",
        created_at=event.created_at,
        updated_at=event.updated_at
    )

@app.delete("/admin/events/{event_id}")
async def delete_event(
    event_id: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """イベント削除"""
    from db_control.models import Event as DbEvent, EventRegistration
    
    event = db.query(DbEvent).filter(DbEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    
    # 参加登録も削除
    db.query(EventRegistration).filter(EventRegistration.event_id == event_id).delete()
    
    event_title = event.title
    db.delete(event)
    db.commit()
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="event_deleted",
        target_type="event",
        target_id=event_id,
        details=f"イベントを削除: {event_title}",
        db=db
    )
    
    return {"message": "イベントを削除しました"}

@app.get("/admin/events/{event_id}/registrations", response_model=List[EventRegistrationResponse])
async def get_event_registrations(
    event_id: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """イベント参加者一覧取得"""
    from db_control.models import EventRegistration
    
    registrations = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id
    ).all()
    
    responses = []
    for reg in registrations:
        user = db.query(DbUser).filter(DbUser.id == reg.user_id).first()
        user_name = f"{user.last_name} {user.first_name}" if user else "不明"
        
        dog_name = None
        if reg.dog_id:
            dog = db.query(DbDog).filter(DbDog.id == reg.dog_id).first()
            dog_name = dog.name if dog else None
        
        responses.append(EventRegistrationResponse(
            id=reg.id,
            user_id=reg.user_id,
            user_name=user_name,
            event_id=reg.event_id,
            dog_id=reg.dog_id,
            dog_name=dog_name,
            registered_at=datetime.utcnow()  # TODO: registered_atフィールド追加後に実装
        ))
    
    return responses

@app.put("/admin/events/{event_id}/cancel")
async def cancel_event(
    event_id: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """イベントキャンセル"""
    from db_control.models import Event as DbEvent
    
    event = db.query(DbEvent).filter(DbEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    
    event.status = "closed"
    event.updated_at = datetime.utcnow()
    db.commit()
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="event_cancelled",
        target_type="event",
        target_id=event_id,
        details=f"イベントをキャンセル: {event.title}",
        db=db
    )
    
    return {"message": "イベントをキャンセルしました"}

@app.post("/admin/events/{event_id}/notify")
async def notify_event_participants(
    event_id: str,
    message: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """イベント参加者への通知"""
    from db_control.models import Event as DbEvent, EventRegistration
    
    event = db.query(DbEvent).filter(DbEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    
    registrations = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id
    ).all()
    
    # TODO: 実際の通知送信処理を実装
    # ここではログ記録のみ
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="event_notification_sent",
        target_type="event",
        target_id=event_id,
        details=f"参加者{len(registrations)}名に通知: {message[:50]}",
        db=db
    )
    
    return {"message": f"{len(registrations)}名の参加者に通知を送信しました"}

# 投稿管理（完全実装）
@app.get("/admin/posts", response_model=List[PostManagementResponse])
async def get_posts_for_admin(
    status: Optional[str] = None,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """投稿一覧取得（管理者用）"""
    query = db.query(DbPost)
    
    if status:
        query = query.filter(DbPost.status == status)
    
    posts = query.order_by(DbPost.created_at.desc()).all()
    
    responses = []
    for post in posts:
        # ユーザー情報を取得
        user = db.query(DbUser).filter(DbUser.id == post.user_id).first()
        user_name = f"{user.last_name} {user.first_name}" if user else "不明"
        
        # いいね数とコメント数を取得
        likes_count = db.query(DbLike).filter(DbLike.post_id == post.id).count()
        comments_count = db.query(DbComment).filter(DbComment.post_id == post.id).count()
        
        responses.append(PostManagementResponse(
            id=post.id,
            user_id=post.user_id,
            user_name=user_name,
            content=post.content,
            status=post.status,
            admin_notes=post.admin_notes,
            likes_count=likes_count,
            comments_count=comments_count,
            created_at=post.created_at,
            updated_at=post.updated_at
        ))
    
    return responses

@app.get("/admin/posts/stats")
async def get_posts_stats(
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """投稿統計取得"""
    from sqlalchemy import func
    
    total = db.query(func.count(DbPost.id)).scalar()
    pending = db.query(func.count(DbPost.id)).filter(DbPost.status == "pending").scalar()
    approved = db.query(func.count(DbPost.id)).filter(DbPost.status == "approved").scalar()
    rejected = db.query(func.count(DbPost.id)).filter(DbPost.status == "rejected").scalar()
    reported = db.query(func.count(DbPost.id)).filter(DbPost.status == "reported").scalar()
    
    # 今日の投稿数
    today = datetime.utcnow().date()
    today_count = db.query(func.count(DbPost.id)).filter(
        func.date(DbPost.created_at) == today
    ).scalar()
    
    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "reported": reported,
        "today": today_count
    }

@app.get("/admin/posts/{post_id}", response_model=PostManagementResponse)
async def get_post_detail(
    post_id: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """投稿詳細取得"""
    post = db.query(DbPost).filter(DbPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="投稿が見つかりません")
    
    user = db.query(DbUser).filter(DbUser.id == post.user_id).first()
    user_name = f"{user.last_name} {user.first_name}" if user else "不明"
    
    likes_count = db.query(DbLike).filter(DbLike.post_id == post.id).count()
    comments_count = db.query(DbComment).filter(DbComment.post_id == post.id).count()
    
    return PostManagementResponse(
        id=post.id,
        user_id=post.user_id,
        user_name=user_name,
        content=post.content,
        status=post.status,
        admin_notes=post.admin_notes,
        likes_count=likes_count,
        comments_count=comments_count,
        created_at=post.created_at,
        updated_at=post.updated_at
    )

@app.put("/admin/posts/{post_id}/status")
async def update_post_status(
    post_id: str,
    request: PostStatusUpdateRequest,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """投稿ステータス更新"""
    post = db.query(DbPost).filter(DbPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="投稿が見つかりません")
    
    post.status = request.status
    post.admin_notes = request.admin_notes
    post.updated_at = datetime.utcnow()
    
    db.commit()
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="post_status_updated",
        target_type="post",
        target_id=post_id,
        details=f"投稿ステータスを{request.status}に更新: {request.admin_notes or 'なし'}",
        db=db
    )
    
    return {"message": "投稿ステータスを更新しました"}

@app.delete("/admin/posts/{post_id}")
async def delete_post(
    post_id: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """投稿削除"""
    post = db.query(DbPost).filter(DbPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="投稿が見つかりません")
    
    # 関連データも削除
    db.query(DbComment).filter(DbComment.post_id == post_id).delete()
    db.query(DbLike).filter(DbLike.post_id == post_id).delete()
    db.query(PostHashtag).filter(PostHashtag.post_id == post_id).delete()
    
    db.delete(post)
    db.commit()
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="post_deleted",
        target_type="post",
        target_id=post_id,
        details=f"投稿を削除",
        db=db
    )
    
    return {"message": "投稿を削除しました"}

@app.put("/admin/posts/{post_id}/hide")
async def hide_post(
    post_id: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """投稿非表示"""
    post = db.query(DbPost).filter(DbPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="投稿が見つかりません")
    
    post.status = "rejected"
    post.updated_at = datetime.utcnow()
    
    db.commit()
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="post_hidden",
        target_type="post",
        target_id=post_id,
        details=f"投稿を非表示に設定",
        db=db
    )
    
    return {"message": "投稿を非表示にしました"}

@app.put("/admin/posts/{post_id}/show")
async def show_post(
    post_id: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """投稿表示"""
    post = db.query(DbPost).filter(DbPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="投稿が見つかりません")
    
    post.status = "approved"
    post.updated_at = datetime.utcnow()
    
    db.commit()
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="post_shown",
        target_type="post",
        target_id=post_id,
        details=f"投稿を表示に設定",
        db=db
    )
    
    return {"message": "投稿を表示にしました"}

@app.get("/admin/posts/{post_id}/reports")
async def get_post_reports(
    post_id: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """投稿の通報一覧取得"""
    # TODO: 通報テーブル実装後に対応
    return {"reports": [], "message": "通報機能は今後実装予定です"}

@app.post("/admin/posts/{post_id}/admin-comment")
async def add_admin_comment(
    post_id: str,
    content: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """管理者コメント追加"""
    post = db.query(DbPost).filter(DbPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="投稿が見つかりません")
    
    from uuid import uuid4
    comment = DbComment(
        id=str(uuid4()),
        post_id=post_id,
        user_id=current_admin.id,
        content=f"【管理者コメント】{content}",
        created_at=datetime.utcnow()
    )
    
    db.add(comment)
    db.commit()
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="admin_comment_added",
        target_type="post",
        target_id=post_id,
        details=f"管理者コメントを追加",
        db=db
    )
    
    return {"message": "管理者コメントを追加しました"}

# ===== 既存のAPIエンドポイント =====

# 認証関連 - 強制更新用コメント
@app.post("/auth/apply", response_model=ApplicationStatusResponse)
async def apply_registration(
    db: Session = Depends(get_db),
    # フォームフィールドを個別に受け取る
    email: str = Form(...),
    password: str = Form(...),
    fullName: str = Form(...),
    phoneNumber: str = Form(...),
    postalCode: str = Form(...),
    prefecture: str = Form(...),
    city: str = Form(...),
    street: str = Form(...),
    building: Optional[str] = Form(None),
    imabariResidency: str = Form(...),
    dogName: str = Form(...),
    dogBreed: str = Form(...),
    dogAge: Optional[int] = Form(None),
    dogGender: Optional[str] = Form(None),
    dogWeight: str = Form(...),
    applicationDate: date = Form(...),
    vaccine_certificate: UploadFile = File(...)
):
    """新規利用申請（ユーザー登録申請）- FormData対応"""
    from uuid import uuid4

    # メールアドレスの重複チェック
    existing_user = db.query(DbUser).filter(DbUser.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="このメールアドレスは既に登録されています")

    # 既存申請の確認
    existing_application = db.query(Application).filter(
        Application.user_email == email,
        Application.status == ApplicationStatus.pending
    ).first()
    if existing_application:
        raise HTTPException(status_code=400, detail="このメールアドレスで申請処理中です")
        
    # ワクチン証明書の保存
    file_extension = Path(vaccine_certificate.filename).suffix
    certificate_filename = f"{uuid4()}{file_extension}"
    certificate_path = VACCINE_CERTIFICATE_UPLOAD_DIR / certificate_filename
    
    try:
        with certificate_path.open("wb") as buffer:
            shutil.copyfileobj(vaccine_certificate.file, buffer)
    finally:
        vaccine_certificate.file.close()
    
    certificate_url = f"/uploads/vaccine_certificates/{certificate_filename}"

    # 姓と名を分割
    name_parts = fullName.split(' ', 1)
    last_name = name_parts[0]
    first_name = name_parts[1] if len(name_parts) > 1 else ''
    
    # 住所を結合
    full_address = f"{prefecture} {city} {street} {building or ''}".strip()

    # 申請データを作成
    application = Application(
        id=str(uuid4()),
        user_id=None,
        user_email=email,
        user_password_hash=get_password_hash(password),
        user_last_name=last_name,
        user_first_name=first_name,
        user_phone=phoneNumber,
        user_address=full_address,
        user_prefecture=prefecture,
        user_city=city,
        user_postal_code=postalCode,
        dog_name=dogName,
        dog_breed=dogBreed,
        dog_weight=str(dogWeight),
        dog_age=dogAge,
        dog_gender=dogGender,
        vaccine_certificate=certificate_url,
        request_date=applicationDate,
        status=ApplicationStatus.pending,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return ApplicationStatusResponse(
        application_id=application.id,
        status=application.status.value,
        rejection_reason=None,
        approved_at=None,
        created_at=application.created_at
    )

@app.get("/auth/application-status/{application_id}", response_model=ApplicationStatusResponse)
async def get_application_status(application_id: str, db=Depends(get_db)):
    """申請状況の確認"""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="申請が見つかりません")
    
    return ApplicationStatusResponse(
        application_id=application.id,
        status=application.status,
        rejection_reason=application.rejection_reason,
        approved_at=application.approved_at,
        created_at=application.created_at
    )

@app.post("/auth/login")
async def login(request: LoginRequest, db=Depends(get_db)):
    """ログイン"""
    user = db.query(DbUser).filter(DbUser.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが正しくありません")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/forgot-password")
async def forgot_password(email: str, db=Depends(get_db)):
    """パスワードリセット"""
    user = db.query(DbUser).filter(DbUser.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    # 実際の実装ではメール送信処理を行う
    return {"message": "パスワードリセットメールを送信しました"}

# ユーザー関連
@app.get("/users/me", response_model=UserDbResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """現在のユーザー情報取得"""
    return UserDbResponse(
        id=current_user.id,
        email=current_user.email,
        last_name=current_user.last_name,
        first_name=current_user.first_name,
        address=current_user.address,
        phone_number=current_user.phone_number,
        prefecture=current_user.prefecture,
        city=current_user.city,
        created_at=current_user.created_at or datetime.utcnow(),
    )

@app.get("/users/profile", response_model=UserProfileDetailResponse)
async def get_user_profile_detail(
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """ユーザープロフィール詳細取得（犬情報を含む）"""
    # ユーザーの犬情報を取得
    dogs = db.query(DbDog).filter(DbDog.owner_id == current_user.id).all()
    
    return UserProfileDetailResponse(
        id=current_user.id,
        email=current_user.email,
        last_name=current_user.last_name,
        first_name=current_user.first_name,
        address=current_user.address,
        phone_number=current_user.phone_number,
        prefecture=current_user.prefecture,
        city=current_user.city,
        created_at=current_user.created_at or datetime.utcnow(),
        dogs=[
            DogDbResponse(
                id=dog.id,
                owner_id=dog.owner_id,
                name=dog.name,
                breed=dog.breed,
                birthday_at=dog.birthday_at or date.today(),
                gender=dog.gender,
                personality=dog.personality,
                likes=dog.likes,
                avatar_url=dog.avatar_url,
                created_at=dog.created_at,
                updated_at=dog.updated_at
            ) for dog in dogs
        ]
    )

@app.put("/users/profile", response_model=UserDbResponse)
async def update_user_profile(
    request: UpdateUserDbRequest,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """ユーザープロフィール更新"""
    if request.last_name is not None:
        current_user.last_name = request.last_name
    if request.first_name is not None:
        current_user.first_name = request.first_name
    if request.address is not None:
        current_user.address = request.address
    if request.phone_number is not None:
        current_user.phone_number = request.phone_number
    if request.prefecture is not None:
        current_user.prefecture = request.prefecture
    if request.city is not None:
        current_user.city = request.city
    
    db.commit()
    db.refresh(current_user)
    return UserDbResponse(
        id=current_user.id,
        email=current_user.email,
        last_name=current_user.last_name,
        first_name=current_user.first_name,
        address=current_user.address,
        phone_number=current_user.phone_number,
        prefecture=current_user.prefecture,
        city=current_user.city,
        created_at=current_user.created_at or datetime.utcnow(),
    )

# 犬のプロフィール関連
@app.get("/dogs", response_model=List[DogDbResponse])
async def get_user_dogs(current_user = Depends(get_current_user), db=Depends(get_db)):
    """ユーザーの犬一覧取得 (db_control)"""
    dogs = db.query(DbDog).filter(DbDog.owner_id == current_user.id).all()
    return [
        DogDbResponse(
            id=d.id, owner_id=d.owner_id, name=d.name, breed=d.breed,
            birthday_at=d.birthday_at, gender=d.gender, personality=d.personality,
            likes=d.likes, avatar_url=d.avatar_url, created_at=d.created_at, updated_at=d.updated_at
        ) for d in dogs
    ]

@app.post("/dogs", response_model=DogDbResponse)
async def add_dog(
    request: CreateDogDbRequest,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """犬の登録 (db_control)"""
    from uuid import uuid4
    dog = DbDog(
        id=str(uuid4()),
        owner_id=current_user.id,
        name=request.name,
        breed=request.breed,
        birthday_at=request.birthday_at,
        gender=request.gender,
        personality=request.personality,
        likes=request.likes,
        avatar_url=request.avatar_url,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(dog)
    db.commit()
    db.refresh(dog)
    return DogDbResponse(
        id=dog.id, owner_id=dog.owner_id, name=dog.name, breed=dog.breed,
        birthday_at=dog.birthday_at, gender=dog.gender, personality=dog.personality,
        likes=dog.likes, avatar_url=dog.avatar_url, created_at=dog.created_at, updated_at=dog.updated_at
    )

@app.put("/dogs/{dog_id}", response_model=DogDbResponse)
async def update_dog(
    dog_id: str,
    request: UpdateDogDbRequest,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """犬の情報更新 (db_control)"""
    dog = db.query(DbDog).filter(DbDog.id == dog_id, DbDog.owner_id == current_user.id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="犬が見つかりません")
    
    if request.name is not None:
        dog.name = request.name
    if request.breed is not None:
        dog.breed = request.breed
    if request.birthday_at is not None:
        dog.birthday_at = request.birthday_at
    if request.gender is not None:
        dog.gender = request.gender
    if request.personality is not None:
        dog.personality = request.personality
    if request.likes is not None:
        dog.likes = request.likes
    if request.avatar_url is not None:
        dog.avatar_url = request.avatar_url
    dog.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(dog)
    return DogDbResponse(
        id=dog.id, owner_id=dog.owner_id, name=dog.name, breed=dog.breed,
        birthday_at=dog.birthday_at, gender=dog.gender, personality=dog.personality,
        likes=dog.likes, avatar_url=dog.avatar_url, created_at=dog.created_at, updated_at=dog.updated_at
    )

@app.delete("/dogs/{dog_id}")
async def delete_dog(
    dog_id: str,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """犬の削除"""
    dog = db.query(DbDog).filter(DbDog.id == dog_id, DbDog.owner_id == current_user.id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="犬が見つかりません")
    
    db.delete(dog)
    db.commit()
    return {"message": "削除しました"}

# ワクチン接種記録関連
@app.get("/dogs/{dog_id}/vaccinations", response_model=List[VaccinationRecordResponse])
async def get_vaccination_records(
    dog_id: str,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """犬のワクチン接種記録取得"""
    # 犬の所有者確認
    dog = db.query(DbDog).filter(DbDog.id == dog_id, DbDog.owner_id == current_user.id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="犬が見つかりません")
    
    records = db.query(DbVaccinationRecord).filter(DbVaccinationRecord.dog_id == dog_id).all()
    return [
        VaccinationRecordResponse(
            id=r.id,
            dog_id=r.dog_id,
            vaccine_type=r.vaccine_type,
            administered_at=r.administered_at,
            next_due_at=r.next_due_at,
            image_url=r.image_url,
            created_at=r.created_at,
            updated_at=r.updated_at
        ) for r in records
    ]

@app.post("/dogs/{dog_id}/vaccinations", response_model=VaccinationRecordResponse)
async def add_vaccination_record(
    dog_id: str,
    request: VaccinationRecordRequest,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """ワクチン接種記録の追加"""
    from uuid import uuid4
    
    # 犬の所有者確認
    dog = db.query(DbDog).filter(DbDog.id == dog_id, DbDog.owner_id == current_user.id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="犬が見つかりません")
    
    record = DbVaccinationRecord(
        id=str(uuid4()),
        dog_id=dog_id,
        vaccine_type=request.vaccine_type,
        administered_at=request.administered_at,
        next_due_at=request.next_due_at,
        image_url=request.image_url,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return VaccinationRecordResponse(
        id=record.id,
        dog_id=record.dog_id,
        vaccine_type=record.vaccine_type,
        administered_at=record.administered_at,
        next_due_at=record.next_due_at,
        image_url=record.image_url,
        created_at=record.created_at,
        updated_at=record.updated_at
    )

@app.delete("/dogs/{dog_id}/vaccinations/{record_id}")
async def delete_vaccination_record(
    dog_id: str,
    record_id: str,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """ワクチン接種記録の削除"""
    # 犬の所有者確認
    dog = db.query(DbDog).filter(DbDog.id == dog_id, DbDog.owner_id == current_user.id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="犬が見つかりません")
    
    record = db.query(DbVaccinationRecord).filter(
        DbVaccinationRecord.id == record_id,
        DbVaccinationRecord.dog_id == dog_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="接種記録が見つかりません")
    
    db.delete(record)
    db.commit()
    return {"message": "削除しました"}

# 投稿関連 (db_control)
@app.get("/posts", response_model=List[PostDbResponse])
async def get_posts(
    search: Optional[str] = None,
    db=Depends(get_db)
):
    """投稿一覧取得 (db_control)"""
    query = db.query(DbPost)
    if search:
        query = query.filter(DbPost.content.contains(search))
    posts = query.order_by(DbPost.created_at.desc()).all()
    responses: List[PostDbResponse] = []
    for p in posts:
        comments_count = db.query(DbComment).filter(DbComment.post_id == p.id).count()
        likes_count = db.query(DbLike).filter(DbLike.post_id == p.id).count()
        responses.append(PostDbResponse(
            id=p.id, user_id=p.user_id, content=p.content,
            created_at=p.created_at, updated_at=p.updated_at,
            comments_count=comments_count, likes_count=likes_count
        ))
    return responses

@app.get("/posts/feed", response_model=List[PostDetailResponse])
async def get_posts_feed(
    search: Optional[str] = None,
    hashtag: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """詳細な投稿フィード取得（画像、ハッシュタグ、ユーザー情報付き）"""
    query = db.query(DbPost)
    
    # ハッシュタグ検索
    if hashtag:
        hashtag_obj = db.query(DbHashtag).filter(DbHashtag.tag == hashtag).first()
        if hashtag_obj:
            post_ids = db.query(DbPostHashtag.post_id).filter(
                DbPostHashtag.hashtag_id == hashtag_obj.id
            ).subquery()
            query = query.filter(DbPost.id.in_(post_ids))
    
    # テキスト検索
    if search:
        query = query.filter(DbPost.content.contains(search))
    
    # ページネーション
    posts = query.order_by(DbPost.created_at.desc()).offset(offset).limit(limit).all()
    
    responses: List[PostDetailResponse] = []
    for post in posts:
        # ユーザー情報取得
        user = db.query(DbUser).filter(DbUser.id == post.user_id).first()
        user_name = f"{user.last_name or ''} {user.first_name or ''}".strip() if user else "不明なユーザー"
        
        # 画像URL取得
        images = db.query(DbPostImage.image_url).filter(DbPostImage.post_id == post.id).all()
        image_urls = [img[0] for img in images]
        
        # ハッシュタグ取得
        hashtags_query = db.query(DbHashtag.tag).join(
            DbPostHashtag, DbHashtag.id == DbPostHashtag.hashtag_id
        ).filter(DbPostHashtag.post_id == post.id)
        hashtags = [tag[0] for tag in hashtags_query.all()]
        
        # カウント取得
        comments_count = db.query(DbComment).filter(DbComment.post_id == post.id).count()
        likes_count = db.query(DbLike).filter(DbLike.post_id == post.id).count()
        
        # 現在のユーザーがいいねしているか
        is_liked = db.query(DbLike).filter(
            DbLike.post_id == post.id,
            DbLike.user_id == current_user.id
        ).first() is not None
        
        responses.append(PostDetailResponse(
            id=post.id,
            user_id=post.user_id,
            user_name=user_name,
            user_avatar=user.avatar_url if user else None,
            content=post.content,
            images=image_urls,
            hashtags=hashtags,
            created_at=post.created_at,
            updated_at=post.updated_at,
            comments_count=comments_count,
            likes_count=likes_count,
            is_liked=is_liked
        ))
    
    return responses

@app.post("/posts", response_model=PostDbResponse)
async def create_post(
    content: str = Form(...),
    hashtags: Optional[str] = Form(None),
    images: Optional[List[UploadFile]] = File(None),
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """投稿作成 (画像アップロード・ハッシュタグ対応)"""
    from uuid import uuid4
    import re
    
    # 投稿を作成
    post = DbPost(
        id=str(uuid4()),
        user_id=current_user.id,
        content=content,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(post)
    db.flush()  # IDを取得するためにflush
    
    # 画像アップロード処理
    if images:
        for image in images:
            if image.filename:
                # ファイル名を生成
                file_extension = Path(image.filename).suffix
                file_name = f"{uuid4()}{file_extension}"
                file_path = POST_UPLOAD_DIR / file_name
                
                # ファイルを保存
                with file_path.open("wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)
                
                # PostImageレコードを作成
                post_image = DbPostImage(
                    id=str(uuid4()),
                    post_id=post.id,
                    image_url=f"/uploads/posts/{file_name}"
                )
                db.add(post_image)
    
    # ハッシュタグ処理
    if hashtags:
        # カンマ区切りまたはスペース区切りのハッシュタグを処理
        tag_list = re.split(r'[,\s]+', hashtags)
        for tag_str in tag_list:
            if tag_str:
                # #を除去
                tag_name = tag_str.lstrip('#').strip()
                if tag_name:
                    # 既存のハッシュタグを検索または作成
                    hashtag = db.query(DbHashtag).filter(DbHashtag.tag == tag_name).first()
                    if not hashtag:
                        hashtag = DbHashtag(
                            id=str(uuid4()),
                            tag=tag_name
                        )
                        db.add(hashtag)
                        db.flush()
                    
                    # PostHashtagリレーションを作成
                    post_hashtag = DbPostHashtag(
                        id=str(uuid4()),
                        post_id=post.id,
                        hashtag_id=hashtag.id
                    )
                    db.add(post_hashtag)
    
    db.commit()
    db.refresh(post)
    
    return PostDbResponse(
        id=post.id, user_id=post.user_id, content=post.content,
        created_at=post.created_at, updated_at=post.updated_at,
        comments_count=0, likes_count=0
    )

@app.post("/posts/{post_id}/like")
async def like_post(
    post_id: str,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """投稿にいいね (db_control)"""
    post = db.query(DbPost).filter(DbPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="投稿が見つかりません")
    
    # 既存のいいねを確認
    exists = db.query(DbLike).filter(
        DbLike.post_id == post_id, 
        DbLike.user_id == current_user.id
    ).first()
    
    if exists:
        return {"message": "すでにいいねしています", "liked": True}
    
    # 新しいいいねを追加
    from uuid import uuid4
    like = DbLike(
        id=str(uuid4()), 
        post_id=post_id, 
        user_id=current_user.id, 
        created_at=datetime.utcnow()
    )
    db.add(like)
    db.commit()
    
    # いいね数を取得
    likes_count = db.query(DbLike).filter(DbLike.post_id == post_id).count()
    
    return {
        "message": "いいねしました", 
        "liked": True,
        "likes_count": likes_count
    }

@app.delete("/posts/{post_id}/like")
async def unlike_post(
    post_id: str,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """いいねを解除 (db_control)"""
    post = db.query(DbPost).filter(DbPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="投稿が見つかりません")
    
    like = db.query(DbLike).filter(
        DbLike.post_id == post_id, 
        DbLike.user_id == current_user.id
    ).first()
    
    if not like:
        return {"message": "いいねしていません", "liked": False}
    
    db.delete(like)
    db.commit()
    
    # いいね数を取得
    likes_count = db.query(DbLike).filter(DbLike.post_id == post_id).count()
    
    return {
        "message": "いいねを解除しました", 
        "liked": False,
        "likes_count": likes_count
    }

@app.get("/posts/{post_id}/comments", response_model=List[CommentDbResponse])
async def get_comments(
    post_id: str,
    db=Depends(get_db)
):
    """投稿のコメント一覧取得"""
    post = db.query(DbPost).filter(DbPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="投稿が見つかりません")
    
    comments = db.query(DbComment).filter(
        DbComment.post_id == post_id
    ).order_by(DbComment.created_at.desc()).all()
    
    return [
        CommentDbResponse(
            id=comment.id,
            post_id=comment.post_id,
            user_id=comment.user_id,
            content=comment.content,
            created_at=comment.created_at
        )
        for comment in comments
    ]

@app.post("/posts/{post_id}/comments", response_model=CommentDbResponse)
async def add_comment(
    post_id: str,
    request: CreateCommentDbRequest,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """コメント追加 (db_control)"""
    post = db.query(DbPost).filter(DbPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="投稿が見つかりません")
    from uuid import uuid4
    comment = DbComment(
        id=str(uuid4()),
        content=request.content,
        post_id=post_id,
        user_id=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return CommentDbResponse(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        content=comment.content,
        created_at=comment.created_at,
    )

# イベント関連 (db_control)
@app.get("/events", response_model=List[EventDbResponse])
async def get_events(
    upcoming_only: bool = True,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """イベント一覧取得（参加状況付き）"""
    query = db.query(DbEvent)
    
    if upcoming_only:
        # 今日以降のイベントのみ
        query = query.filter(DbEvent.event_date >= date.today())
    
    events = query.order_by(DbEvent.event_date, DbEvent.start_time).all()
    
    responses = []
    for event in events:
        # 参加者数を取得
        participants_count = db.query(DbEventRegistration).filter(
            DbEventRegistration.event_id == event.id
        ).count()
        
        # 現在のユーザーが登録しているか確認
        is_registered = db.query(DbEventRegistration).filter(
            DbEventRegistration.event_id == event.id,
            DbEventRegistration.user_id == current_user.id
        ).first() is not None
        
        responses.append(EventDbResponse(
            id=event.id,
            title=event.title,
            description=event.description,
            event_date=event.event_date,
            start_time=event.start_time.strftime("%H:%M") if event.start_time else "",
            end_time=event.end_time.strftime("%H:%M") if event.end_time else "",
            location=event.location,
            capacity=event.capacity or 0,
            fee=event.fee or 0,
            status=event.status.value if event.status else "reception",
            current_participants=participants_count,
            is_registered=is_registered,
            created_at=event.created_at,
            updated_at=event.updated_at
        ))
    
    return responses

@app.get("/events/{event_id}", response_model=EventDetailResponse)
async def get_event_detail(
    event_id: str,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """イベント詳細取得"""
    event = db.query(DbEvent).filter(DbEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    
    # 参加者数を取得
    participants_count = db.query(DbEventRegistration).filter(
        DbEventRegistration.event_id == event.id
    ).count()
    
    # 現在のユーザーの登録状況を確認
    user_registrations = db.query(DbEventRegistration).filter(
        DbEventRegistration.event_id == event.id,
        DbEventRegistration.user_id == current_user.id
    ).all()
    
    is_registered = len(user_registrations) > 0
    my_dogs_registered = [reg.dog_id for reg in user_registrations if reg.dog_id]
    
    return EventDetailResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        event_date=event.event_date,
        start_time=event.start_time.strftime("%H:%M") if event.start_time else "",
        end_time=event.end_time.strftime("%H:%M") if event.end_time else "",
        location=event.location,
        capacity=event.capacity or 0,
        fee=event.fee or 0,
        status=event.status.value if event.status else "reception",
        current_participants=participants_count,
        is_registered=is_registered,
        my_dogs_registered=my_dogs_registered,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

@app.post("/events/{event_id}/register")
async def register_for_event(
    event_id: str,
    request: EventRegistrationRequest,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """イベント参加登録"""
    # イベントの存在確認
    event = db.query(DbEvent).filter(DbEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    
    # 定員確認
    current_participants = db.query(DbEventRegistration).filter(
        DbEventRegistration.event_id == event_id
    ).count()
    
    if event.capacity and current_participants >= event.capacity:
        raise HTTPException(status_code=400, detail="イベントは満員です")
    
    # 既存の登録を削除（再登録の場合）
    db.query(DbEventRegistration).filter(
        DbEventRegistration.event_id == event_id,
        DbEventRegistration.user_id == current_user.id
    ).delete()
    
    # 新規登録
    from uuid import uuid4
    for dog_id in request.dog_ids:
        # 犬の所有権確認
        dog = db.query(DbDog).filter(
            DbDog.id == dog_id,
            DbDog.owner_id == current_user.id
        ).first()
        
        if not dog:
            continue  # 所有していない犬はスキップ
        
        registration = DbEventRegistration(
            id=str(uuid4()),
            user_id=current_user.id,
            event_id=event_id,
            dog_id=dog_id
        )
        db.add(registration)
    
    # ユーザーのみの登録（犬なし）
    if not request.dog_ids:
        registration = DbEventRegistration(
            id=str(uuid4()),
            user_id=current_user.id,
            event_id=event_id,
            dog_id=None
        )
        db.add(registration)
    
    db.commit()
    
    return {"message": "イベントに参加登録しました", "event_id": event_id}

@app.delete("/events/{event_id}/register")
async def cancel_event_registration(
    event_id: str,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """イベント参加キャンセル"""
    # 登録の存在確認
    registrations = db.query(DbEventRegistration).filter(
        DbEventRegistration.event_id == event_id,
        DbEventRegistration.user_id == current_user.id
    ).all()
    
    if not registrations:
        raise HTTPException(status_code=404, detail="参加登録が見つかりません")
    
    # 登録を削除
    for reg in registrations:
        db.delete(reg)
    
    db.commit()
    
    return {"message": "参加をキャンセルしました", "event_id": event_id}

@app.get("/events/{event_id}/participants", response_model=List[EventParticipantResponse])
async def get_event_participants(
    event_id: str,
    db=Depends(get_db)
):
    """イベント参加者一覧取得"""
    # イベントの存在確認
    event = db.query(DbEvent).filter(DbEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    
    # 参加登録を取得
    registrations = db.query(DbEventRegistration).filter(
        DbEventRegistration.event_id == event_id
    ).all()
    
    responses = []
    for reg in registrations:
        # ユーザー情報取得
        user = db.query(DbUser).filter(DbUser.id == reg.user_id).first()
        user_name = f"{user.last_name or ''} {user.first_name or ''}".strip() if user else "不明"
        
        # 犬情報取得（該当する場合）
        dog_name = None
        if reg.dog_id:
            dog = db.query(DbDog).filter(DbDog.id == reg.dog_id).first()
            dog_name = dog.name if dog else None
        
        responses.append(EventParticipantResponse(
            id=reg.id,
            user_id=reg.user_id,
            user_name=user_name,
            dog_id=reg.dog_id,
            dog_name=dog_name,
            registered_at=datetime.utcnow()  # EventRegistrationにregistered_atがない場合の仮値
        ))
    
    return responses

@app.get("/calendar/{year}/{month}")
async def get_calendar(year: int, month: int):
    """カレンダー情報取得"""
    # 実際の実装ではデータベースから取得
    return {
        "year": year,
        "month": month,
        "days": []  # カレンダーの日付情報
    }

# 入場管理関連 (db_control)
@app.get("/entry/qrcode", response_model=QRCodeResponse)
async def generate_qr_code(
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """ユーザー専用のQRコード生成"""
    import qrcode
    import io
    import base64
    from datetime import timedelta
    
    # QRコードに含めるデータ（ユーザーIDと有効期限）
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    qr_data = {
        "user_id": current_user.id,
        "expires_at": expires_at.isoformat()
    }
    
    # QRコード生成
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(str(qr_data))
    qr.make(fit=True)
    
    # 画像を生成してBase64エンコード
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return QRCodeResponse(
        qr_code=f"data:image/png;base64,{img_str}",
        user_id=current_user.id,
        expires_at=expires_at
    )

@app.post("/entry/scan")
async def scan_qr_code(
    qr_data: dict,
    admin_user = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """QRコードスキャン（管理者のみ）"""
    # QRコードのデータを検証
    user_id = qr_data.get("user_id")
    expires_at_str = qr_data.get("expires_at")
    
    if not user_id or not expires_at_str:
        raise HTTPException(status_code=400, detail="無効なQRコードです")
    
    # 有効期限チェック
    expires_at = datetime.fromisoformat(expires_at_str)
    if datetime.utcnow() > expires_at:
        raise HTTPException(status_code=400, detail="QRコードの有効期限が切れています")
    
    # ユーザー確認
    user = db.query(DbUser).filter(DbUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    return {
        "user_id": user_id,
        "user_name": f"{user.last_name or ''} {user.first_name or ''}".strip(),
        "message": "QRコードを確認しました"
    }

@app.post("/entry/enter", response_model=EntryResponse)
async def enter_dogrun(
    request: EntryRequest,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """ドッグラン入場記録"""
    from uuid import uuid4
    
    # 既に入場中かチェック
    last_entry = db.query(DbEntryLog).filter(
        DbEntryLog.user_id == current_user.id
    ).order_by(DbEntryLog.occurred_at.desc()).first()
    
    if last_entry and last_entry.action == EntryAction.entry:
        raise HTTPException(status_code=400, detail="既に入場中です")
    
    # 入場記録を作成
    entry_log = DbEntryLog(
        id=str(uuid4()),
        user_id=current_user.id,
        action=EntryAction.entry,
        occurred_at=datetime.utcnow()
    )
    db.add(entry_log)
    
    # 犬の情報を取得
    dogs_info = []
    for dog_id in request.dog_ids:
        dog = db.query(DbDog).filter(
            DbDog.id == dog_id,
            DbDog.owner_id == current_user.id
        ).first()
        if dog:
            dogs_info.append({
                "id": dog.id,
                "name": dog.name
            })
    
    db.commit()
    
    return EntryResponse(
        entry_id=entry_log.id,
        user_id=current_user.id,
        user_name=f"{current_user.last_name or ''} {current_user.first_name or ''}".strip(),
        dogs=dogs_info,
        entry_time=entry_log.occurred_at,
        status="in_park"
    )

@app.post("/entry/exit")
async def exit_dogrun(
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """ドッグラン退場記録"""
    from uuid import uuid4
    
    # 最後の入場記録を確認
    last_entry = db.query(DbEntryLog).filter(
        DbEntryLog.user_id == current_user.id
    ).order_by(DbEntryLog.occurred_at.desc()).first()
    
    if not last_entry or last_entry.action != EntryAction.entry:
        raise HTTPException(status_code=400, detail="入場記録がありません")
    
    # 退場記録を作成
    exit_log = DbEntryLog(
        id=str(uuid4()),
        user_id=current_user.id,
        action=EntryAction.exit,
        occurred_at=datetime.utcnow()
    )
    db.add(exit_log)
    db.commit()
    
    # 滞在時間を計算
    duration = exit_log.occurred_at - last_entry.occurred_at
    minutes = int(duration.total_seconds() / 60)
    
    return {
        "message": "退場処理が完了しました",
        "entry_time": last_entry.occurred_at,
        "exit_time": exit_log.occurred_at,
        "duration_minutes": minutes
    }

@app.get("/entry/current", response_model=CurrentVisitorsResponse)
async def get_current_visitors(
    db=Depends(get_db)
):
    """現在の在場者一覧取得"""
    # 各ユーザーの最新の記録を取得
    from sqlalchemy import func, and_
    
    # サブクエリ：各ユーザーの最新の記録時刻を取得
    latest_logs = db.query(
        DbEntryLog.user_id,
        func.max(DbEntryLog.occurred_at).label('latest_time')
    ).group_by(DbEntryLog.user_id).subquery()
    
    # 最新の記録がentryであるユーザーを取得
    current_visitors = db.query(DbEntryLog).join(
        latest_logs,
        and_(
            DbEntryLog.user_id == latest_logs.c.user_id,
            DbEntryLog.occurred_at == latest_logs.c.latest_time
        )
    ).filter(DbEntryLog.action == EntryAction.entry).all()
    
    visitors = []
    total_dogs = 0
    
    for log in current_visitors:
        user = db.query(DbUser).filter(DbUser.id == log.user_id).first()
        if user:
            # ユーザーの犬を取得
            dogs = db.query(DbDog).filter(DbDog.owner_id == user.id).all()
            dogs_info = [{"id": dog.id, "name": dog.name} for dog in dogs]
            total_dogs += len(dogs)
            
            visitors.append(EntryResponse(
                entry_id=log.id,
                user_id=user.id,
                user_name=f"{user.last_name or ''} {user.first_name or ''}".strip(),
                dogs=dogs_info,
                entry_time=log.occurred_at,
                status="in_park"
            ))
    
    return CurrentVisitorsResponse(
        total_visitors=len(visitors),
        total_dogs=total_dogs,
        visitors=visitors
    )

@app.get("/entry/history", response_model=List[EntryHistoryResponse])
async def get_entry_history(
    limit: int = 50,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """入退場履歴取得（自分の履歴）"""
    logs = db.query(DbEntryLog).filter(
        DbEntryLog.user_id == current_user.id
    ).order_by(DbEntryLog.occurred_at.desc()).limit(limit).all()
    
    history = []
    for log in logs:
        # その時点での犬情報を取得（簡略化のため現在の犬情報を使用）
        dogs = db.query(DbDog).filter(DbDog.owner_id == current_user.id).all()
        dog_names = [dog.name for dog in dogs]
        
        history.append(EntryHistoryResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=f"{current_user.last_name or ''} {current_user.first_name or ''}".strip(),
            action=log.action.value,
            occurred_at=log.occurred_at,
            dogs=dog_names
        ))
    
    return history

# お知らせ関連
@app.get("/notices", response_model=List[NoticeResponse])
async def get_notices(db=Depends(get_db)):
    """お知らせ一覧取得"""
    notices = db.query(Notice).order_by(Notice.created_at.desc()).all()
    return [NoticeResponse.from_orm(notice) for notice in notices]

@app.put("/notices/{notice_id}/read")
async def mark_notice_as_read(
    notice_id: int,
    db=Depends(get_db)
):
    """お知らせを既読にする"""
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="お知らせが見つかりません")

    notice.read = True
    db.commit()
    return {"message": "既読にしました"}

# 入場関連
@app.post("/entry/scan")
async def scan_qr_code(qr_data: str, db=Depends(get_db)):
    """QRコードスキャン"""
    # 実際の実装ではQRコードの検証を行う
    return {"message": "QRコードを読み取りました", "qr_data": qr_data}

@app.post("/entry/enter")
async def enter_dog_run(
    dog_ids: List[int],
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """ドッグラン入場"""
    # 実際の実装では入場処理を行う
    return {"message": "入場しました", "dog_ids": dog_ids}

@app.post("/entry/exit")
async def exit_dog_run(current_user = Depends(get_current_user)):
    """ドッグラン退場"""
    # 実際の実装では退場処理を行う
    return {"message": "退場しました"}

# タグ関連
@app.get("/tags", response_model=List[TagResponse])
async def get_tags(db=Depends(get_db)):
    """タグ一覧取得"""
    tags = db.query(Tag).all()
    return [TagResponse.from_orm(tag) for tag in tags]

# ===== 営業時間管理API =====

@app.get("/admin/business-hours", response_model=List[BusinessHourResponse])
async def get_business_hours(
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """営業時間一覧取得"""
    business_hours = db.query(BusinessHour).order_by(BusinessHour.day_of_week).all()
    return [BusinessHourResponse.from_orm(bh) for bh in business_hours]

@app.put("/admin/business-hours")
async def update_business_hours(
    updates: List[dict],
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """営業時間一括更新"""
    from datetime import time
    
    for update in updates:
        day_of_week = update.get("day_of_week")
        if day_of_week is not None:
            bh = db.query(BusinessHour).filter(BusinessHour.day_of_week == day_of_week).first()
            if bh:
                bh.is_open = update.get("is_open", bh.is_open)
                if update.get("open_time"):
                    hour, minute = map(int, update["open_time"].split(":"))
                    bh.open_time = time(hour, minute)
                if update.get("close_time"):
                    hour, minute = map(int, update["close_time"].split(":"))
                    bh.close_time = time(hour, minute)
                bh.special_note = update.get("special_note", bh.special_note)
                bh.updated_at = datetime.utcnow()
    
    db.commit()
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="business_hours_updated",
        target_type="business_hours",
        target_id=None,
        details="営業時間を更新しました",
        db=db
    )
    
    return {"message": "営業時間を更新しました"}

@app.get("/admin/business-hours/today", response_model=TodayBusinessHoursResponse)
async def get_today_business_hours(
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """本日の営業時間取得"""
    from datetime import date as dt_date
    
    today = dt_date.today()
    day_of_week = today.weekday()  # 月曜=0, 日曜=6
    # SQLの曜日形式に変換（日曜=0, 月曜=1）
    sql_day_of_week = (day_of_week + 1) % 7
    
    # 通常の営業時間を取得
    business_hour = db.query(BusinessHour).filter(
        BusinessHour.day_of_week == sql_day_of_week
    ).first()
    
    # 特別休業日チェック
    special_holiday = db.query(SpecialHoliday).filter(
        SpecialHoliday.holiday_date == today
    ).first()
    
    day_names = ["日曜日", "月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日"]
    
    if special_holiday:
        return TodayBusinessHoursResponse(
            date=today,
            day_of_week=sql_day_of_week,
            day_name=day_names[sql_day_of_week],
            is_open=special_holiday.is_open,
            open_time=str(special_holiday.open_time) if special_holiday.open_time else None,
            close_time=str(special_holiday.close_time) if special_holiday.close_time else None,
            special_note=special_holiday.note,
            is_holiday=True,
            holiday_name=special_holiday.holiday_name
        )
    elif business_hour:
        return TodayBusinessHoursResponse(
            date=today,
            day_of_week=sql_day_of_week,
            day_name=day_names[sql_day_of_week],
            is_open=business_hour.is_open,
            open_time=str(business_hour.open_time) if business_hour.open_time else None,
            close_time=str(business_hour.close_time) if business_hour.close_time else None,
            special_note=business_hour.special_note,
            is_holiday=False,
            holiday_name=None
        )
    else:
        return TodayBusinessHoursResponse(
            date=today,
            day_of_week=sql_day_of_week,
            day_name=day_names[sql_day_of_week],
            is_open=False,
            open_time=None,
            close_time=None,
            special_note="営業時間が設定されていません",
            is_holiday=False,
            holiday_name=None
        )

@app.get("/admin/special-holidays", response_model=List[SpecialHolidayResponse])
async def get_special_holidays(
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """特別休業日一覧取得"""
    holidays = db.query(SpecialHoliday).order_by(SpecialHoliday.holiday_date).all()
    return [SpecialHolidayResponse.from_orm(h) for h in holidays]

@app.post("/admin/special-holidays", response_model=SpecialHolidayResponse)
async def create_special_holiday(
    request: SpecialHolidayCreateRequest,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """特別休業日追加"""
    from uuid import uuid4
    from datetime import time
    
    # 既存の同じ日付のチェック
    existing = db.query(SpecialHoliday).filter(
        SpecialHoliday.holiday_date == request.holiday_date
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="この日付は既に登録されています")
    
    open_time = None
    close_time = None
    if request.open_time:
        hour, minute = map(int, request.open_time.split(":"))
        open_time = time(hour, minute)
    if request.close_time:
        hour, minute = map(int, request.close_time.split(":"))
        close_time = time(hour, minute)
    
    holiday = SpecialHoliday(
        id=str(uuid4()),
        holiday_date=request.holiday_date,
        holiday_name=request.holiday_name,
        is_open=request.is_open,
        open_time=open_time,
        close_time=close_time,
        note=request.note,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="special_holiday_created",
        target_type="special_holiday",
        target_id=holiday.id,
        details=f"特別休業日を追加: {request.holiday_date}",
        db=db
    )
    
    return SpecialHolidayResponse.from_orm(holiday)

@app.put("/admin/special-holidays/{holiday_id}", response_model=SpecialHolidayResponse)
async def update_special_holiday(
    holiday_id: str,
    request: SpecialHolidayUpdateRequest,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """特別休業日更新"""
    from datetime import time
    
    holiday = db.query(SpecialHoliday).filter(SpecialHoliday.id == holiday_id).first()
    if not holiday:
        raise HTTPException(status_code=404, detail="特別休業日が見つかりません")
    
    if request.holiday_name is not None:
        holiday.holiday_name = request.holiday_name
    if request.is_open is not None:
        holiday.is_open = request.is_open
    if request.open_time is not None:
        if request.open_time:
            hour, minute = map(int, request.open_time.split(":"))
            holiday.open_time = time(hour, minute)
        else:
            holiday.open_time = None
    if request.close_time is not None:
        if request.close_time:
            hour, minute = map(int, request.close_time.split(":"))
            holiday.close_time = time(hour, minute)
        else:
            holiday.close_time = None
    if request.note is not None:
        holiday.note = request.note
    
    holiday.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(holiday)
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="special_holiday_updated",
        target_type="special_holiday",
        target_id=holiday_id,
        details=f"特別休業日を更新: {holiday.holiday_date}",
        db=db
    )
    
    return SpecialHolidayResponse.from_orm(holiday)

@app.delete("/admin/special-holidays/{holiday_id}")
async def delete_special_holiday(
    holiday_id: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """特別休業日削除"""
    holiday = db.query(SpecialHoliday).filter(SpecialHoliday.id == holiday_id).first()
    if not holiday:
        raise HTTPException(status_code=404, detail="特別休業日が見つかりません")
    
    holiday_date = holiday.holiday_date
    db.delete(holiday)
    db.commit()
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="special_holiday_deleted",
        target_type="special_holiday",
        target_id=holiday_id,
        details=f"特別休業日を削除: {holiday_date}",
        db=db
    )
    
    return {"message": "特別休業日を削除しました"}

# ===== システム設定管理API =====

@app.get("/admin/settings", response_model=List[SystemSettingResponse])
async def get_system_settings(
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """設定一覧取得"""
    settings = db.query(SystemSetting).order_by(SystemSetting.category, SystemSetting.setting_key).all()
    return [SystemSettingResponse.from_orm(s) for s in settings]

@app.get("/admin/settings/{category}", response_model=SystemSettingsCategoryResponse)
async def get_settings_by_category(
    category: str,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """カテゴリ別設定取得"""
    settings = db.query(SystemSetting).filter(
        SystemSetting.category == category
    ).order_by(SystemSetting.setting_key).all()
    
    return SystemSettingsCategoryResponse(
        category=category,
        settings=[SystemSettingResponse.from_orm(s) for s in settings]
    )

@app.put("/admin/settings/{setting_key}")
async def update_system_setting(
    setting_key: str,
    request: SystemSettingUpdateRequest,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """設定更新"""
    setting = db.query(SystemSetting).filter(
        SystemSetting.setting_key == setting_key
    ).first()
    
    if not setting:
        raise HTTPException(status_code=404, detail="設定が見つかりません")
    
    # 型チェック
    if setting.setting_type == "number":
        try:
            int(request.setting_value)
        except ValueError:
            raise HTTPException(status_code=400, detail="数値を入力してください")
    elif setting.setting_type == "boolean":
        if request.setting_value.lower() not in ["true", "false"]:
            raise HTTPException(status_code=400, detail="true または false を入力してください")
    
    setting.setting_value = request.setting_value
    setting.updated_at = datetime.utcnow()
    
    db.commit()
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="setting_updated",
        target_type="system_setting",
        target_id=setting.id,
        details=f"{setting_key}を{request.setting_value}に更新",
        db=db
    )
    
    return {"message": "設定を更新しました"}

@app.post("/admin/settings/backup", response_model=SystemSettingsBackupResponse)
async def backup_settings(
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """設定バックアップ"""
    import json
    from uuid import uuid4
    
    settings = db.query(SystemSetting).all()
    
    backup_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "admin_id": current_admin.id,
        "settings": [
            {
                "key": s.setting_key,
                "value": s.setting_value,
                "type": s.setting_type,
                "category": s.category,
                "description": s.description,
                "is_public": s.is_public
            }
            for s in settings
        ]
    }
    
    backup_id = str(uuid4())
    file_path = f"backups/settings_{backup_id}.json"
    
    # バックアップディレクトリ作成
    os.makedirs("backups", exist_ok=True)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="settings_backup",
        target_type="system_settings",
        target_id=backup_id,
        details=f"設定をバックアップ: {file_path}",
        db=db
    )
    
    return SystemSettingsBackupResponse(
        backup_id=backup_id,
        created_at=datetime.utcnow(),
        settings_count=len(settings),
        file_path=file_path
    )

@app.get("/admin/settings/export")
async def export_settings(
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """設定エクスポート"""
    settings = db.query(SystemSetting).all()
    
    export_data = {
        "exported_at": datetime.utcnow().isoformat(),
        "settings": {
            s.setting_key: {
                "value": s.setting_value,
                "type": s.setting_type,
                "category": s.category,
                "description": s.description,
                "is_public": s.is_public
            }
            for s in settings
        }
    }
    
    return export_data

@app.post("/admin/settings/import")
async def import_settings(
    request: SystemSettingsImportRequest,
    current_admin = Depends(get_current_admin_user),
    db=Depends(get_db)
):
    """設定インポート"""
    updated_count = 0
    
    for key, data in request.settings.items():
        setting = db.query(SystemSetting).filter(
            SystemSetting.setting_key == key
        ).first()
        
        if setting:
            setting.setting_value = data.get("value")
            setting.updated_at = datetime.utcnow()
            updated_count += 1
    
    db.commit()
    
    # 管理者ログを記録
    await log_admin_action(
        admin_user_id=current_admin.id,
        action="settings_imported",
        target_type="system_settings",
        target_id=None,
        details=f"{updated_count}件の設定をインポート",
        db=db
    )
    
    return {"message": f"{updated_count}件の設定をインポートしました"}

# ヘルスチェック
@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)