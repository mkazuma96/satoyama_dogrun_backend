# backend/db_control/connect_MySQL.py

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# 1) .env を読み込む
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # backend/
load_dotenv(os.path.join(BASE_DIR, ".env"))

# 2) 環境変数取得
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT")
DB_NAME     = os.getenv("DB_NAME")
SSL_CA_PATH = os.getenv("SSL_CA_PATH")

# 3) SSL_CA_PATH の絶対パス化（相対パス指定でも動くように）
if SSL_CA_PATH and not os.path.isabs(SSL_CA_PATH):
    # このファイル(connect_MySQL.py)がある db_control/ フォルダ基点で解決
    SSL_CA_PATH = os.path.join(os.path.dirname(__file__), SSL_CA_PATH)

# 4) 接続 URL 組み立て（SSL設定を追加）
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    "?charset=utf8mb4&ssl_mode=VERIFY_IDENTITY"
)

# 5) connect_args に SSL CA とタイムアウト設定を渡す
connect_args = {
    "ssl": {
        "ca": SSL_CA_PATH,
        "check_hostname": False
    },
    "connect_timeout": 30,
    "read_timeout": 30,
    "write_timeout": 30
}

# 6) エンジン生成
engine = create_engine(
    DATABASE_URL,
    echo=True,         # SQL をログ出力
    pool_pre_ping=True,
    pool_recycle=3600,  # 1時間でコネクションをリサイクル
    connect_args=connect_args
)
