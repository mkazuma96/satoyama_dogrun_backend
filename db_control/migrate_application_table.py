#!/usr/bin/env python3
"""
Applicationテーブルを更新して、新規申請時にユーザー情報を直接保存できるようにする
"""
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import pymysql

load_dotenv()

def get_mysql_connection():
    """MySQL接続情報を取得"""
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME")
    ssl_ca_path = os.getenv("SSL_CA_PATH")
    
    if not all([db_user, db_password, db_host, db_name]):
        raise ValueError("データベース接続情報が不足しています")
    
    # SSL証明書のパスを解決
    if ssl_ca_path and not os.path.isabs(ssl_ca_path):
        ssl_ca_path = os.path.join(os.path.dirname(__file__), ssl_ca_path)
    
    # 接続
    connection = pymysql.connect(
        host=db_host,
        port=int(db_port),
        user=db_user,
        password=db_password,
        database=db_name,
        ssl={'ca': ssl_ca_path} if ssl_ca_path else None,
        charset='utf8mb4'
    )
    
    return connection

def main():
    """メイン処理"""
    print("Applicationテーブルの更新を開始します...")
    
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # 1. 現在のカラムを確認
        cursor.execute("SHOW COLUMNS FROM applications")
        existing_columns = [col[0] for col in cursor.fetchall()]
        
        # 2. 新しいカラムを追加（存在しない場合のみ）
        columns_to_add = [
            # ユーザー情報を保存するカラム
            ("user_email", "VARCHAR(255)"),
            ("user_password_hash", "VARCHAR(255)"),
            ("user_last_name", "VARCHAR(50)"),
            ("user_first_name", "VARCHAR(50)"),
            ("user_phone", "VARCHAR(20)"),
            ("user_address", "VARCHAR(255)"),
            ("user_prefecture", "VARCHAR(50)"),
            ("user_city", "VARCHAR(50)"),
            ("user_postal_code", "VARCHAR(10)"),
            # 犬の追加情報
            ("dog_age", "INT"),
            ("dog_gender", "VARCHAR(10)")
        ]
        
        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                stmt = f"ALTER TABLE applications ADD COLUMN {col_name} {col_type}"
                cursor.execute(stmt)
                print(f"✅ カラム追加: {col_name}")
            else:
                print(f"⏭️  既存のカラム: {col_name}")
        
        # 3. user_idをNULL許可に変更（新規申請時はユーザーが存在しないため）
        try:
            cursor.execute("ALTER TABLE applications MODIFY COLUMN user_id VARCHAR(36)")
            print("✅ user_idをNULL許可に変更")
        except pymysql.err.OperationalError as e:
            print(f"ℹ️  user_id変更: {e}")
        
        # 4. インデックスを追加
        # 既存のインデックスを確認
        cursor.execute("SHOW INDEX FROM applications")
        existing_indexes = [row[2] for row in cursor.fetchall()]
        
        indexes_to_add = [
            ("idx_applications_user_email", "user_email"),
            ("idx_applications_status", "status"),
            ("idx_applications_created_at", "created_at")
        ]
        
        for idx_name, col_name in indexes_to_add:
            if idx_name not in existing_indexes:
                try:
                    stmt = f"CREATE INDEX {idx_name} ON applications({col_name})"
                    cursor.execute(stmt)
                    print(f"✅ インデックス作成: {idx_name}")
                except pymysql.err.OperationalError as e:
                    print(f"⚠️  インデックス作成エラー: {idx_name} - {e}")
            else:
                print(f"⏭️  既存のインデックス: {idx_name}")
        
        conn.commit()
        print("\n✅ Applicationテーブルの更新が完了しました")
        
        # 更新後のテーブル構造を確認
        cursor.execute("DESCRIBE applications")
        columns = cursor.fetchall()
        print("\n現在のテーブル構造:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()