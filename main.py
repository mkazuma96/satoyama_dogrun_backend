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
    User, Dog, Post, Comment, Event, Notice, Tag,
    UserCreate, UserResponse, DogCreate, DogResponse,
    PostCreate, PostResponse, CommentCreate, CommentResponse,
    EventResponse, NoticeResponse, TagResponse
)
from database import engine, get_db
from auth import get_current_user, create_access_token, verify_password, get_password_hash
from schemas import (
    LoginRequest, RegisterRequest, CreatePostRequest, AddCommentRequest,
    AddDogRequest, UpdateUserProfileRequest, CalendarRequest
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

# データベース初期化
from database import Base
Base.metadata.create_all(bind=engine)

# 認証関連
@app.post("/auth/register", response_model=UserResponse)
async def register(request: RegisterRequest, db=Depends(get_db)):
    """ユーザー登録"""
    # メールアドレスの重複チェック
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="このメールアドレスは既に登録されています")
    
    # ユーザー作成
    user = User(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        address=request.address,
        phone_number=request.phone_number,
        imabari_residency=request.imabari_residency
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)

@app.post("/auth/login")
async def login(request: LoginRequest, db=Depends(get_db)):
    """ログイン"""
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが正しくありません")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/forgot-password")
async def forgot_password(email: str, db=Depends(get_db)):
    """パスワードリセット"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    # 実際の実装ではメール送信処理を行う
    return {"message": "パスワードリセットメールを送信しました"}

# ユーザー関連
@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """現在のユーザー情報取得"""
    return UserResponse.from_orm(current_user)

@app.put("/users/profile", response_model=UserResponse)
async def update_user_profile(
    request: UpdateUserProfileRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """ユーザープロフィール更新"""
    current_user.full_name = request.full_name
    current_user.address = request.address
    current_user.phone_number = request.phone_number
    current_user.imabari_residency = request.imabari_residency
    
    db.commit()
    db.refresh(current_user)
    return UserResponse.from_orm(current_user)

# 犬のプロフィール関連
@app.get("/dogs", response_model=List[DogResponse])
async def get_user_dogs(current_user: User = Depends(get_current_user), db=Depends(get_db)):
    """ユーザーの犬一覧取得"""
    dogs = db.query(Dog).filter(Dog.owner_id == current_user.id).all()
    return [DogResponse.from_orm(dog) for dog in dogs]

@app.post("/dogs", response_model=DogResponse)
async def add_dog(
    request: AddDogRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """犬の登録"""
    dog = Dog(
        name=request.name,
        breed=request.breed,
        weight=request.weight,
        personality=request.personality,
        last_vaccination_date=request.last_vaccination_date,
        owner_id=current_user.id
    )
    db.add(dog)
    db.commit()
    db.refresh(dog)
    return DogResponse.from_orm(dog)

@app.put("/dogs/{dog_id}", response_model=DogResponse)
async def update_dog(
    dog_id: int,
    request: DogCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """犬の情報更新"""
    dog = db.query(Dog).filter(Dog.id == dog_id, Dog.owner_id == current_user.id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="犬が見つかりません")
    
    dog.name = request.name
    dog.breed = request.breed
    dog.weight = request.weight
    dog.personality = request.personality
    dog.last_vaccination_date = request.last_vaccination_date
    
    db.commit()
    db.refresh(dog)
    return DogResponse.from_orm(dog)

@app.delete("/dogs/{dog_id}")
async def delete_dog(
    dog_id: int,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """犬の削除"""
    dog = db.query(Dog).filter(Dog.id == dog_id, Dog.owner_id == current_user.id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="犬が見つかりません")
    
    db.delete(dog)
    db.commit()
    return {"message": "削除しました"}

# 投稿関連
@app.get("/posts", response_model=List[PostResponse])
async def get_posts(
    tag: Optional[str] = None,
    search: Optional[str] = None,
    db=Depends(get_db)
):
    """投稿一覧取得"""
    query = db.query(Post)
    
    if tag and tag != "all":
        query = query.filter(Post.tag == tag)
    
    if search:
        query = query.filter(Post.content.contains(search))
    
    posts = query.order_by(Post.created_at.desc()).all()
    return [PostResponse.from_orm(post) for post in posts]

@app.post("/posts", response_model=PostResponse)
async def create_post(
    request: CreatePostRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """投稿作成"""
    post = Post(
        content=request.content,
        tag=request.category,
        hashtags=request.hashtags,
        user_id=current_user.id
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return PostResponse.from_orm(post)

@app.post("/posts/{post_id}/like")
async def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """投稿にいいね"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="投稿が見つかりません")
    
    # いいねの処理（実際の実装では中間テーブルを使用）
    post.likes += 1
    db.commit()
    return {"message": "いいねしました"}

@app.post("/posts/{post_id}/comments", response_model=CommentResponse)
async def add_comment(
    post_id: int,
    request: CommentCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """コメント追加"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="投稿が見つかりません")
    
    comment = Comment(
        text=request.text,
        post_id=post_id,
        user_id=current_user.id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return CommentResponse.from_orm(comment)

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
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """ドッグラン入場"""
    # 実際の実装では入場処理を行う
    return {"message": "入場しました", "dog_ids": dog_ids}

@app.post("/entry/exit")
async def exit_dog_run(current_user: User = Depends(get_current_user)):
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