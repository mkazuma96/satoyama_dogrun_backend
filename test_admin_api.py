#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理者API動作テストスクリプト
"""

import requests
import json
import time
from datetime import datetime

# API設定
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@satoyama-dogrun.com"
ADMIN_PASSWORD = "admin2025!"

def print_test_result(test_name, success, response=None, error=None):
    """テスト結果を表示"""
    if success:
        print(f"✅ {test_name}: 成功")
        if response:
            print(f"   レスポンス: {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    data = response.json()
                    print(f"   データ: {json.dumps(data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"   データ: {response.text}")
    else:
        print(f"❌ {test_name}: 失敗")
        if error:
            print(f"   エラー: {error}")
        if response:
            print(f"   レスポンス: {response.status_code}")
            print(f"   内容: {response.text}")

def test_admin_login():
    """管理者ログインテスト"""
    print("\n🔐 管理者ログインテスト")
    
    try:
        response = requests.post(
            f"{BASE_URL}/admin/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            admin_user = data.get("admin_user")
            
            print_test_result("管理者ログイン", True, response)
            print(f"   アクセストークン: {access_token[:20]}...")
            print(f"   管理者名: {admin_user.get('last_name')} {admin_user.get('first_name')}")
            print(f"   権限: {admin_user.get('role')}")
            
            return access_token
        else:
            print_test_result("管理者ログイン", False, response)
            return None
            
    except Exception as e:
        print_test_result("管理者ログイン", False, error=str(e))
        return None

def test_admin_me(access_token):
    """管理者情報取得テスト"""
    print("\n👤 管理者情報取得テスト")
    
    try:
        response = requests.get(
            f"{BASE_URL}/admin/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_test_result("管理者情報取得", True, response)
            print(f"   管理者ID: {data.get('id')}")
            print(f"   メール: {data.get('email')}")
            print(f"   権限: {data.get('role')}")
        else:
            print_test_result("管理者情報取得", False, response)
            
    except Exception as e:
        print_test_result("管理者情報取得", False, error=str(e))

def test_dashboard_stats(access_token):
    """ダッシュボード統計テスト"""
    print("\n📊 ダッシュボード統計テスト")
    
    try:
        response = requests.get(
            f"{BASE_URL}/admin/dashboard/stats",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_test_result("ダッシュボード統計取得", True, response)
            print(f"   総ユーザー数: {data.get('total_users')}")
            print(f"   総犬数: {data.get('total_dogs')}")
            print(f"   承認待ち申請: {data.get('pending_applications')}")
            print(f"   承認待ち投稿: {data.get('pending_posts')}")
        else:
            print_test_result("ダッシュボード統計取得", False, response)
            
    except Exception as e:
        print_test_result("ダッシュボード統計取得", False, error=str(e))

def test_applications(access_token):
    """申請管理テスト"""
    print("\n📝 申請管理テスト")
    
    try:
        response = requests.get(
            f"{BASE_URL}/admin/applications",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_test_result("申請一覧取得", True, response)
            print(f"   申請数: {len(data)}")
            
            if data:
                app = data[0]
                print(f"   最初の申請:")
                print(f"     - ID: {app.get('id')}")
                print(f"     - ユーザー名: {app.get('user_name')}")
                print(f"     - 犬の名前: {app.get('dog_name')}")
                print(f"     - ステータス: {app.get('status')}")
        else:
            print_test_result("申請一覧取得", False, response)
            
    except Exception as e:
        print_test_result("申請一覧取得", False, error=str(e))

def test_posts_management(access_token):
    """投稿管理テスト"""
    print("\n📄 投稿管理テスト")
    
    try:
        response = requests.get(
            f"{BASE_URL}/admin/posts",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_test_result("投稿一覧取得（管理者用）", True, response)
            print(f"   投稿数: {len(data)}")
            
            if data:
                post = data[0]
                print(f"   最初の投稿:")
                print(f"     - ID: {post.get('id')}")
                print(f"     - ユーザー名: {post.get('user_name')}")
                print(f"     - ステータス: {post.get('status')}")
                print(f"     - いいね数: {post.get('likes_count')}")
                print(f"     - コメント数: {post.get('comments_count')}")
        else:
            print_test_result("投稿一覧取得（管理者用）", False, response)
            
    except Exception as e:
        print_test_result("投稿一覧取得（管理者用）", False, error=str(e))

def test_unauthorized_access():
    """認証なしアクセステスト"""
    print("\n🚫 認証なしアクセステスト")
    
    try:
        # 認証なしでダッシュボード統計にアクセス
        response = requests.get(f"{BASE_URL}/admin/dashboard/stats")
        
        if response.status_code == 401:
            print_test_result("認証なしアクセス拒否", True, response)
        else:
            print_test_result("認証なしアクセス拒否", False, response, 
                            error="認証なしでもアクセスできてしまいました")
            
    except Exception as e:
        print_test_result("認証なしアクセステスト", False, error=str(e))

def test_invalid_token():
    """無効なトークンテスト"""
    print("\n🔒 無効なトークンテスト")
    
    try:
        # 無効なトークンでダッシュボード統計にアクセス
        response = requests.get(
            f"{BASE_URL}/admin/dashboard/stats",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        if response.status_code == 401:
            print_test_result("無効なトークン拒否", True, response)
        else:
            print_test_result("無効なトークン拒否", False, response,
                            error="無効なトークンでもアクセスできてしまいました")
            
    except Exception as e:
        print_test_result("無効なトークンテスト", False, error=str(e))

def main():
    """メイン関数"""
    print("🚀 里山ドッグラン管理者API動作テスト開始")
    print(f"📅 テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 テスト対象URL: {BASE_URL}")
    
    # バックエンドの起動確認
    print("\n🔍 バックエンド接続確認中...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ バックエンドに接続できました")
        else:
            print("⚠️  バックエンドは起動していますが、予期しないレスポンスです")
    except requests.exceptions.ConnectionError:
        print("❌ バックエンドに接続できません。バックエンドが起動しているか確認してください。")
        print("   起動コマンド: python main.py")
        return
    except Exception as e:
        print(f"❌ 接続確認中にエラーが発生しました: {e}")
        return
    
    # 管理者ログインテスト
    access_token = test_admin_login()
    
    if not access_token:
        print("\n❌ 管理者ログインに失敗したため、以降のテストをスキップします")
        return
    
    # 各種APIテスト
    test_admin_me(access_token)
    test_dashboard_stats(access_token)
    test_applications(access_token)
    test_posts_management(access_token)
    
    # セキュリティテスト
    test_unauthorized_access()
    test_invalid_token()
    
    print("\n🎉 管理者API動作テスト完了！")
    print(f"📅 テスト完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
