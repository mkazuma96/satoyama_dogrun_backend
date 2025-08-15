from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# 優先度:
# 1) Azure MySQL 向け環境変数 (DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME) が揃っていれば MySQL(SSL) を使用
# 2) それ以外は DATABASE_URL を使用（未設定なら SQLite デフォルト）

def _build_mysql_engine_from_env():
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    ssl_ca_path = os.getenv("SSL_CA_PATH")

    if not all([db_user, db_password, db_host, db_port, db_name]):
        return None

    # 相対パス指定でも動くように db_control/ 基点で解決
    if ssl_ca_path and not os.path.isabs(ssl_ca_path):
        ssl_ca_path = os.path.join(os.path.dirname(__file__), "db_control", ssl_ca_path)

    database_url = (
        f"mysql+pymysql://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    )

    # PyMySQL は URL の ssl_mode を受け付けないため、SSL は connect_args で指定する
    connect_args = {
        "connect_timeout": 30,
        "read_timeout": 30,
        "write_timeout": 30,
    }
    if ssl_ca_path:
        connect_args["ssl"] = {"ca": ssl_ca_path}

    return create_engine(
        database_url,
        echo=True,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args=connect_args,
    )


# 1) MySQL (Azure) 優先
engine = _build_mysql_engine_from_env()

if engine is None:
    # 2) DATABASE_URL（デフォルトは SQLite）
    database_url = os.getenv("DATABASE_URL", "sqlite:///./satoyama_dogrun.db")
    if database_url.startswith("sqlite"):
        engine = create_engine(database_url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 現段階では既存API互換のため、Base は従来通りの宣言ベースを公開
# db_control/models.py 採用への切替時に、以下を
#   from db_control.models import Base
# に変更する
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()