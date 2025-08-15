#!/usr/bin/env python3
"""
営業時間管理・システム設定テーブルの作成マイグレーション

このスクリプトは以下のテーブルを作成します：
1. business_hours - 営業時間管理
2. special_holidays - 特別休業日管理
3. system_settings - システム設定管理
"""

import os
import sys
from datetime import datetime, time
from uuid import uuid4
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from db_control.models import Base, BusinessHour, SpecialHoliday, SystemSetting
from database import engine, SessionLocal

load_dotenv()


def create_tables():
    """新しいテーブルを作成"""
    print("=== 管理テーブル作成開始 ===")
    
    try:
        # テーブル作成
        Base.metadata.create_all(
            bind=engine,
            tables=[
                BusinessHour.__table__,
                SpecialHoliday.__table__,
                SystemSetting.__table__
            ]
        )
        print("✅ テーブル作成完了:")
        print("  - business_hours")
        print("  - special_holidays")
        print("  - system_settings")
        
    except Exception as e:
        print(f"❌ テーブル作成エラー: {e}")
        return False
    
    return True


def insert_initial_business_hours():
    """営業時間の初期データを挿入"""
    session = SessionLocal()
    
    try:
        # 既存データチェック
        existing_count = session.query(BusinessHour).count()
        if existing_count > 0:
            print(f"⚠️ business_hours テーブルに既存データがあります ({existing_count}件)")
            return True
        
        # 初期データ（通常の営業時間）
        business_hours = [
            # 日曜日（0）
            BusinessHour(
                id=str(uuid4()),
                day_of_week=0,
                is_open=True,
                open_time=time(9, 0),
                close_time=time(17, 0),
                special_note="日曜日は通常営業",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            # 月曜日（1）- 定休日
            BusinessHour(
                id=str(uuid4()),
                day_of_week=1,
                is_open=False,
                open_time=None,
                close_time=None,
                special_note="定休日",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            # 火曜日（2）
            BusinessHour(
                id=str(uuid4()),
                day_of_week=2,
                is_open=True,
                open_time=time(9, 0),
                close_time=time(17, 0),
                special_note=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            # 水曜日（3）
            BusinessHour(
                id=str(uuid4()),
                day_of_week=3,
                is_open=True,
                open_time=time(9, 0),
                close_time=time(17, 0),
                special_note=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            # 木曜日（4）
            BusinessHour(
                id=str(uuid4()),
                day_of_week=4,
                is_open=True,
                open_time=time(9, 0),
                close_time=time(17, 0),
                special_note=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            # 金曜日（5）
            BusinessHour(
                id=str(uuid4()),
                day_of_week=5,
                is_open=True,
                open_time=time(9, 0),
                close_time=time(17, 0),
                special_note=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            # 土曜日（6）
            BusinessHour(
                id=str(uuid4()),
                day_of_week=6,
                is_open=True,
                open_time=time(9, 0),
                close_time=time(18, 0),
                special_note="土曜日は18時まで営業",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
        ]
        
        session.bulk_save_objects(business_hours)
        session.commit()
        print(f"✅ 営業時間の初期データを挿入しました ({len(business_hours)}件)")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 営業時間データ挿入エラー: {e}")
        return False
    finally:
        session.close()
    
    return True


def insert_initial_system_settings():
    """システム設定の初期データを挿入"""
    session = SessionLocal()
    
    try:
        # 既存データチェック
        existing_count = session.query(SystemSetting).count()
        if existing_count > 0:
            print(f"⚠️ system_settings テーブルに既存データがあります ({existing_count}件)")
            return True
        
        # 初期設定データ
        settings = [
            # 一般設定
            SystemSetting(
                id=str(uuid4()),
                setting_key="site_name",
                setting_value="里山ドッグラン",
                setting_type="string",
                category="general",
                description="サイト名",
                is_public=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            SystemSetting(
                id=str(uuid4()),
                setting_key="max_dogs_per_user",
                setting_value="5",
                setting_type="number",
                category="general",
                description="ユーザーあたりの最大登録犬数",
                is_public=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            SystemSetting(
                id=str(uuid4()),
                setting_key="max_dogs_in_park",
                setting_value="20",
                setting_type="number",
                category="general",
                description="同時入場可能な最大犬数",
                is_public=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            SystemSetting(
                id=str(uuid4()),
                setting_key="reservation_required",
                setting_value="false",
                setting_type="boolean",
                category="general",
                description="事前予約の必須化",
                is_public=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            # メンテナンス設定
            SystemSetting(
                id=str(uuid4()),
                setting_key="maintenance_mode",
                setting_value="false",
                setting_type="boolean",
                category="maintenance",
                description="メンテナンスモード",
                is_public=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            SystemSetting(
                id=str(uuid4()),
                setting_key="maintenance_message",
                setting_value="システムメンテナンス中です。しばらくお待ちください。",
                setting_type="string",
                category="maintenance",
                description="メンテナンス時の表示メッセージ",
                is_public=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            # 通知設定
            SystemSetting(
                id=str(uuid4()),
                setting_key="notification_email",
                setting_value="admin@satoyama-dogrun.jp",
                setting_type="string",
                category="notification",
                description="管理者通知メールアドレス",
                is_public=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            SystemSetting(
                id=str(uuid4()),
                setting_key="enable_email_notifications",
                setting_value="true",
                setting_type="boolean",
                category="notification",
                description="メール通知の有効化",
                is_public=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            # 料金設定
            SystemSetting(
                id=str(uuid4()),
                setting_key="admission_fee",
                setting_value="500",
                setting_type="number",
                category="fee",
                description="入場料（円）",
                is_public=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            SystemSetting(
                id=str(uuid4()),
                setting_key="monthly_pass_fee",
                setting_value="3000",
                setting_type="number",
                category="fee",
                description="月額パス料金（円）",
                is_public=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
        ]
        
        session.bulk_save_objects(settings)
        session.commit()
        print(f"✅ システム設定の初期データを挿入しました ({len(settings)}件)")
        
    except Exception as e:
        session.rollback()
        print(f"❌ システム設定データ挿入エラー: {e}")
        return False
    finally:
        session.close()
    
    return True


def verify_tables():
    """テーブルの作成を確認"""
    session = SessionLocal()
    
    try:
        # 各テーブルの件数を確認
        business_hours_count = session.query(BusinessHour).count()
        special_holidays_count = session.query(SpecialHoliday).count()
        system_settings_count = session.query(SystemSetting).count()
        
        print("\n=== テーブル確認 ===")
        print(f"business_hours: {business_hours_count}件")
        print(f"special_holidays: {special_holidays_count}件")
        print(f"system_settings: {system_settings_count}件")
        
    except Exception as e:
        print(f"❌ テーブル確認エラー: {e}")
        return False
    finally:
        session.close()
    
    return True


def main():
    """メイン処理"""
    print("\n========================================")
    print("管理テーブル作成マイグレーション開始")
    print("========================================\n")
    
    # 1. テーブル作成
    if not create_tables():
        print("\n❌ マイグレーション失敗")
        sys.exit(1)
    
    # 2. 初期データ挿入
    print("\n=== 初期データ挿入 ===")
    if not insert_initial_business_hours():
        print("⚠️ 営業時間データの挿入に失敗しました")
    
    if not insert_initial_system_settings():
        print("⚠️ システム設定データの挿入に失敗しました")
    
    # 3. 確認
    if not verify_tables():
        print("\n⚠️ テーブル確認に失敗しました")
    
    print("\n✅ マイグレーション完了!")
    print("========================================\n")


if __name__ == "__main__":
    main()