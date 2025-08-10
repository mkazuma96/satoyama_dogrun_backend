# backend/db_control/test_connection.py

import os
import pymysql
from dotenv import load_dotenv

# 1) .env を読み込む
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # backend/
load_dotenv(os.path.join(BASE_DIR, ".env"))

# 2) 環境変数取得
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = int(os.getenv("DB_PORT", "3306"))
DB_NAME     = os.getenv("DB_NAME")
SSL_CA_PATH = os.getenv("SSL_CA_PATH")

# 3) SSL_CA_PATH の絶対パス化
if SSL_CA_PATH and not os.path.isabs(SSL_CA_PATH):
    SSL_CA_PATH = os.path.join(os.path.dirname(__file__), SSL_CA_PATH)

print(f"接続情報:")
print(f"Host: {DB_HOST}")
print(f"Port: {DB_PORT}")
print(f"Database: {DB_NAME}")
print(f"User: {DB_USER}")
print(f"SSL CA Path: {SSL_CA_PATH}")
print(f"SSL CA exists: {os.path.exists(SSL_CA_PATH) if SSL_CA_PATH else 'Not specified'}")

try:
    # 4) 接続テスト
    print("\n接続テスト中...")
    
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
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30
    )
    
    print("✅ 接続成功!")
    
    # 5) 簡単なクエリテスト
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"MySQL Version: {version[0]}")
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"既存のテーブル数: {len(tables)}")
        if tables:
            print("テーブル一覧:")
            for table in tables:
                print(f"  - {table[0]}")
    
    connection.close()
    print("✅ 接続テスト完了")
    
except Exception as e:
    print(f"❌ 接続エラー: {e}")
    print(f"エラータイプ: {type(e).__name__}")
    
    # より詳細なエラー情報
    if "timed out" in str(e).lower():
        print("\n💡 タイムアウトエラーの可能性:")
        print("1. Azure MySQLのファイアウォール設定を確認してください")
        print("2. 現在のIPアドレスが許可リストに含まれているか確認してください")
        print("3. Azure PortalでMySQLサーバーの状態を確認してください")
    
    elif "ssl" in str(e).lower():
        print("\n💡 SSLエラーの可能性:")
        print("1. SSL証明書ファイルが正しくダウンロードされているか確認してください")
        print("2. SSL設定を無効にしてテストしてみてください")
    
    elif "access denied" in str(e).lower():
        print("\n💡 アクセス拒否エラーの可能性:")
        print("1. ユーザー名とパスワードが正しいか確認してください")
        print("2. データベース名が正しいか確認してください")
        print("3. ユーザーに適切な権限が付与されているか確認してください") 