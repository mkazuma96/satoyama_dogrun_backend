# backend/db_control/initialize_local_db.py

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ローカルSQLiteデータベースの設定
DATABASE_URL = "sqlite:///./satoyama_dogrun.db"

# SQLiteエンジン作成
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# db_control/models.pyからBaseとモデルをインポート
from models import Base, User, Dog

def init_local_db():
    """ローカルSQLiteデータベースにテーブルを作成"""
    print("ローカルSQLiteデータベースにテーブルを作成中...")
    
    # テーブル作成
    Base.metadata.create_all(bind=engine)
    
    print("✅ ローカルデータベースのテーブル作成完了")
    print(f"データベースファイル: {os.path.abspath('./satoyama_dogrun.db')}")
    
    # 作成されたテーブルを確認
    with engine.connect() as conn:
        result = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = result.fetchall()
        print(f"\n作成されたテーブル数: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")

if __name__ == "__main__":
    init_local_db() 