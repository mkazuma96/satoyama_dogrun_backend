#!/usr/bin/env python3
"""
申請テーブルにrejection_reasonカラムを追加するマイグレーションスクリプト
"""

import os
import pymysql
from dotenv import load_dotenv

# .envファイルを読み込み
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# 環境変数から接続情報を取得
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_NAME = os.getenv("DB_NAME")
SSL_CA_PATH = os.getenv("SSL_CA_PATH")

# SSL証明書のパスを絶対パスに変換
if SSL_CA_PATH and not os.path.isabs(SSL_CA_PATH):
    SSL_CA_PATH = os.path.join(os.path.dirname(__file__), SSL_CA_PATH)

def migrate():
    """rejection_reasonカラムを追加"""
    
    # PyMySQLで直接接続
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        ssl={'ca': SSL_CA_PATH}
    )
    
    try:
        with conn.cursor() as cursor:
            # まず、カラムが既に存在するか確認
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = 'applications' 
                AND COLUMN_NAME = 'rejection_reason'
            """, (DB_NAME,))
            
            result = cursor.fetchone()
            
            if result is None:
                # カラムが存在しない場合のみ追加
                print("Adding rejection_reason column to applications table...")
                cursor.execute("""
                    ALTER TABLE applications 
                    ADD COLUMN rejection_reason TEXT
                """)
                conn.commit()
                print("Migration completed successfully!")
            else:
                print("rejection_reason column already exists. Skipping migration.")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()