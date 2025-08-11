from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from typing import List, Optional
import uvicorn
from datetime import datetime, date
import os
from dotenv import load_dotenv

from models import (
    Dog, Post, Comment, Event, Notice, Tag,
    UserCreate, UserResponse, DogCreate, DogResponse,
    PostCreate, PostResponse, CommentCreate, CommentResponse,
    EventResponse, NoticeResponse, TagResponse
)
from db_control.models import User as DbUser
from db_control.models import Dog as DbDog
from db_control.models import Post as DbPost
from db_control.models import Comment as DbComment
from db_control.models import Like as DbLike
from db_control.models import Hashtag as DbHashtag
from db_control.models import PostHashtag as DbPostHashtag
from database import engine, get_db
from auth import get_current_user, create_access_token, verify_password, get_password_hash
from schemas import (
    LoginRequest, RegisterRequest, CreatePostRequest, AddCommentRequest,
    AddDogRequest, UpdateUserProfileRequest, CalendarRequest,
    UserRegisterResponse,
    RegisterDbRequest, UpdateUserDbRequest, UserDbResponse,
    CreateDogDbRequest, UpdateDogDbRequest, DogDbResponse,
    CreatePostDbRequest, PostDbResponse, CreateCommentDbRequest, CommentDbResponse
)

load_dotenv()

app = FastAPI(
    title="里山ドッグラン API",
    description="里山ドッグランの管理システムAPI",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# データベース初期化（環境変数で制御）
from database import Base
if os.getenv("AUTO_CREATE_TABLES", "false").lower() == "true":
    Base.metadata.create_all(bind=engine)
# db_control のテーブル作成を個別に有効化（初回のみ true 推奨）
if os.getenv("AUTO_CREATE_DB_CONTROL_TABLES", "false").lower() == "true":
    from db_control.models import Base as DbBase
    DbBase.metadata.create_all(bind=engine)

# 認証関連
@app.post("/auth/register", response_model=UserDbResponse)
async def register(request: RegisterDbRequest, db=Depends(get_db)):
    """ユーザー登録"""
    # メールアドレスの重複チェック（db_control.models.User）
    existing_user = db.query(DbUser).filter(DbUser.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="このメールアドレスは既に登録されています")
    
    # ユーザー作成（db_control.models.User）
    from uuid import uuid4
    user = DbUser(
        id=str(uuid4()),
        email=request.email,
        password_hash=get_password_hash(request.password),
        last_name=request.last_name,
        first_name=request.first_name,
        address=request.address,
        phone_number=request.phone_number,
        prefecture=request.prefecture,
        city=request.city,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 新レスポンスで返却（idはUUID文字列）
    return UserDbResponse(
        id=user.id,
        email=user.email,
        last_name=user.last_name,
        first_name=user.first_name,
        address=user.address,
        phone_number=user.phone_number,
        prefecture=user.prefecture,
        city=user.city,
        created_at=user.created_at,
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

@app.post("/posts", response_model=PostDbResponse)
async def create_post(
    request: CreatePostDbRequest,
    current_user = Depends(get_current_user),
    db=Depends(get_db)
):
    """投稿作成 (db_control)"""
    from uuid import uuid4
    post = DbPost(
        id=str(uuid4()),
        user_id=current_user.id,
        content=request.content,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    # 画像/ハッシュタグは後続で対応
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
    exists = db.query(DbLike).filter(DbLike.post_id == post_id, DbLike.user_id == current_user.id).first()
    if not exists:
        from uuid import uuid4
        like = DbLike(id=str(uuid4()), post_id=post_id, user_id=current_user.id, created_at=datetime.utcnow())
        db.add(like)
        db.commit()
    return {"message": "いいねしました"}

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

# イベント関連
@app.get("/events", response_model=List[EventResponse])
async def get_events(db=Depends(get_db)):
    """イベント一覧取得"""
    events = db.query(Event).all()
    return [EventResponse.from_orm(event) for event in events]

@app.get("/calendar/{year}/{month}")
async def get_calendar(year: int, month: int):
    """カレンダー情報取得"""
    # 実際の実装ではデータベースから取得
    return {
        "year": year,
        "month": month,
        "days": []  # カレンダーの日付情報
    }

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)