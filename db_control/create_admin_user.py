# backend/db_control/create_admin_user.py

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from uuid import uuid4

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db_control.models import Base, AdminUser, AdminRole
from auth import get_password_hash

# データベース接続設定
DB_HOST = os.getenv("DB_HOST", "rdbs-002-gen10-step3-2-oshima14.mysql.database.azure.com")
DB_USER = os.getenv("DB_USER", "tech0gen10student")
DB_PASSWORD = os.getenv("DB_PASSWORD", "vY7JZNfU")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "satoyama_dogrun")
SSL_CA_PATH = os.getenv("SSL_CA_PATH", "DigiCertGlobalRootCA.crt.pem")

def create_database_engine():
    """データベースエンジンを作成"""
    if SSL_CA_PATH and os.path.exists(SSL_CA_PATH):
        database_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        engine = create_engine(
            database_url,
            echo=True,
            connect_args={
                "ssl": {"ca": SSL_CA_PATH, "check_hostname": False},
                "connect_timeout": 30,
                "read_timeout": 30,
                "write_timeout": 30,
            }
        )
    else:
        # SSL証明書がない場合はSQLiteを使用
        database_url = "sqlite:///./satoyama_dogrun.db"
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            echo=True
        )
    
    return engine

def create_admin_user():
    """管理者ユーザーを作成"""
    print("管理者ユーザー作成スクリプトを開始します...")
    
    # データベースエンジン作成
    engine = create_database_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # テーブル作成
    print("テーブルを作成中...")
    Base.metadata.create_all(bind=engine)
    
    # セッション作成
    db = SessionLocal()
    
    try:
        # 既存の管理者ユーザーをチェック
        existing_admin = db.query(AdminUser).filter(
            AdminUser.email == "admin@satoyama-dogrun.com"
        ).first()
        
        if existing_admin:
            print("管理者ユーザーは既に存在します。")
            print(f"ID: {existing_admin.id}")
            print(f"Email: {existing_admin.email}")
            print(f"Role: {existing_admin.role}")
            return
        
        # 管理者ユーザーを作成
        admin_user = AdminUser(
            id=str(uuid4()),
            email="admin@satoyama-dogrun.com",
            password_hash=get_password_hash("admin2025!"),
            last_name="里山",
            first_name="管理者",
            role=AdminRole.super_admin,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ 管理者ユーザーを作成しました！")
        print(f"ID: {admin_user.id}")
        print(f"Email: {admin_user.email}")
        print(f"Password: admin2025!")
        print(f"Role: {admin_user.role}")
        print(f"Created: {admin_user.created_at}")
        
        # 追加の管理者ユーザーも作成
        moderator_user = AdminUser(
            id=str(uuid4()),
            email="moderator@satoyama-dogrun.com",
            password_hash=get_password_hash("moderator2025!"),
            last_name="里山",
            first_name="モデレーター",
            role=AdminRole.moderator,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(moderator_user)
        db.commit()
        
        print("\n✅ モデレーターユーザーも作成しました！")
        print(f"Email: {moderator_user.email}")
        print(f"Password: moderator2025!")
        print(f"Role: {moderator_user.role}")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
