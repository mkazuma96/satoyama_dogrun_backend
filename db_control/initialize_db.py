# backend/db_control/initialize_db.py

from connect_MySQL import engine
from models import Base

def init_db():
    # Azure MySQL 側にテーブルを一括作成
    Base.metadata.create_all(bind=engine)
    print("All tables created.")

if __name__ == "__main__":
    init_db()
