#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from dotenv import load_dotenv
import pymysql

# プロジェクトルートをパスに追加
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

def check_table_schema():
    """テーブルのスキーマを確認"""
    # 環境変数から接続情報を取得
    DB_HOST = os.getenv("DB_HOST")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_NAME = os.getenv("DB_NAME")
    SSL_CA_PATH = os.getenv("SSL_CA_PATH")
    
    if SSL_CA_PATH and not os.path.isabs(SSL_CA_PATH):
        SSL_CA_PATH = os.path.join(os.path.dirname(__file__), SSL_CA_PATH)
    
    print("データベース接続情報:")
    print(f"Host: {DB_HOST}")
    print(f"Database: {DB_NAME}")
    print(f"User: {DB_USER}")
    print(f"SSL CA: {SSL_CA_PATH}")
    
    try:
        # SSL設定
        ssl_config = {}
        if SSL_CA_PATH and os.path.exists(SSL_CA_PATH):
            ssl_config = {
                "ca": SSL_CA_PATH,
                "check_hostname": False
            }
        
        # 接続
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            ssl=ssl_config,
            connect_timeout=30
        )
        
        print("\n✅ 接続成功!")
        
        with connection.cursor() as cursor:
            # 全テーブル一覧を表示
            print("\n=== 全テーブル一覧 ===")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            for table in tables:
                print(f"  - {table[0]}")
            
            # eventsテーブルの構造を確認
            print("\n=== eventsテーブルの構造 ===")
            cursor.execute("DESCRIBE events")
            columns = cursor.fetchall()
            for column in columns:
                print(f"  {column[0]} | {column[1]} | {column[2]} | {column[3]} | {column[4]} | {column[5]}")
            
            # postsテーブルの構造を確認
            print("\n=== postsテーブルの構造 ===")
            cursor.execute("DESCRIBE posts")
            columns = cursor.fetchall()
            for column in columns:
                print(f"  {column[0]} | {column[1]} | {column[2]} | {column[3]} | {column[4]} | {column[5]}")
            
            # usersテーブルの構造を確認
            print("\n=== usersテーブルの構造 ===")
            cursor.execute("DESCRIBE users")
            columns = cursor.fetchall()
            for column in columns:
                print(f"  {column[0]} | {column[1]} | {column[2]} | {column[3]} | {column[4]} | {column[5]}")
            
            # announcementsテーブルの構造を確認
            print("\n=== announcementsテーブルの構造 ===")
            cursor.execute("DESCRIBE announcements")
            columns = cursor.fetchall()
            for column in columns:
                print(f"  {column[0]} | {column[1]} | {column[2]} | {column[3]} | {column[4]} | {column[5]}")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_table_schema()
