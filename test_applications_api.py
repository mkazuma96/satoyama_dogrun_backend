#!/usr/bin/env python3
"""
利用申請管理APIのテストスクリプト
"""

import requests
import json
from datetime import datetime

# APIのベースURL
BASE_URL = "http://localhost:8000"

# テスト用の管理者認証情報
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"

def login_admin():
    """管理者としてログイン"""
    response = requests.post(
        f"{BASE_URL}/admin/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        print("✅ Admin login successful")
        return data["access_token"]
    else:
        print(f"❌ Admin login failed: {response.status_code}")
        print(response.json())
        return None

def test_get_applications(token):
    """申請一覧の取得をテスト"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n📋 Testing GET /admin/applications")
    response = requests.get(f"{BASE_URL}/admin/applications", headers=headers)
    
    if response.status_code == 200:
        applications = response.json()
        print(f"✅ Retrieved {len(applications)} applications")
        
        # 各申請の詳細を表示
        for app in applications[:3]:  # 最初の3件のみ表示
            print(f"  - ID: {app['id']}")
            print(f"    User: {app['user_name']} ({app['user_email']})")
            print(f"    Dog: {app['dog_name']}")
            print(f"    Status: {app['status']}")
            if app.get('rejection_reason'):
                print(f"    Rejection Reason: {app['rejection_reason']}")
        
        return applications
    else:
        print(f"❌ Failed to get applications: {response.status_code}")
        print(response.json())
        return []

def test_get_application_stats(token):
    """申請統計の取得をテスト"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n📊 Testing GET /admin/applications/stats")
    response = requests.get(f"{BASE_URL}/admin/applications/stats", headers=headers)
    
    if response.status_code == 200:
        stats = response.json()
        print("✅ Retrieved application statistics:")
        print(f"  - Total: {stats['total']}")
        print(f"  - Pending: {stats['pending']}")
        print(f"  - Approved: {stats['approved']}")
        print(f"  - Rejected: {stats['rejected']}")
        print(f"  - Today: {stats['today']}")
        return stats
    else:
        print(f"❌ Failed to get stats: {response.status_code}")
        print(response.json())
        return None

def test_approve_application(token, application_id):
    """申請の承認をテスト"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n✅ Testing PUT /admin/applications/{application_id}/approve")
    response = requests.put(
        f"{BASE_URL}/admin/applications/{application_id}/approve",
        headers=headers,
        json={"admin_notes": "テスト承認 - " + datetime.now().isoformat()}
    )
    
    if response.status_code == 200:
        print(f"✅ Application {application_id} approved successfully")
        return True
    else:
        print(f"❌ Failed to approve application: {response.status_code}")
        print(response.json())
        return False

def test_reject_application(token, application_id):
    """申請の却下をテスト"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n❌ Testing PUT /admin/applications/{application_id}/reject")
    response = requests.put(
        f"{BASE_URL}/admin/applications/{application_id}/reject",
        headers=headers,
        json={
            "admin_notes": "テスト却下 - " + datetime.now().isoformat(),
            "rejection_reason": "ワクチン証明書の有効期限が切れています"
        }
    )
    
    if response.status_code == 200:
        print(f"✅ Application {application_id} rejected successfully")
        return True
    else:
        print(f"❌ Failed to reject application: {response.status_code}")
        print(response.json())
        return False

def main():
    """メインテスト関数"""
    print("🧪 Starting Application Management API Test")
    print("=" * 50)
    
    # 管理者としてログイン
    token = login_admin()
    if not token:
        print("Cannot proceed without admin token")
        return
    
    # 申請一覧を取得
    applications = test_get_applications(token)
    
    # 申請統計を取得
    stats = test_get_application_stats(token)
    
    # pending状態の申請があれば、承認・却下テスト
    pending_apps = [app for app in applications if app['status'] == 'pending']
    
    if len(pending_apps) >= 2:
        # 1つ目を承認
        test_approve_application(token, pending_apps[0]['id'])
        
        # 2つ目を却下
        test_reject_application(token, pending_apps[1]['id'])
        
        # 再度一覧を取得して確認
        print("\n📋 Verifying changes...")
        test_get_applications(token)
        test_get_application_stats(token)
    elif len(pending_apps) == 1:
        print("\n⚠️ Only one pending application found, testing approval only")
        test_approve_application(token, pending_apps[0]['id'])
    else:
        print("\n⚠️ No pending applications to test approval/rejection")
    
    print("\n" + "=" * 50)
    print("✅ Application Management API Test Complete!")

if __name__ == "__main__":
    main()