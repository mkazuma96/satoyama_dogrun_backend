import re
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import UploadFile
from config import settings

def validate_email(email: str) -> bool:
    """メールアドレスの形式を検証"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> bool:
    """パスワードの強度を検証"""
    if len(password) < settings.min_password_length:
        return False
    
    # 少なくとも1つの数字と1つの文字を含む
    has_digit = any(char.isdigit() for char in password)
    has_letter = any(char.isalpha() for char in password)
    
    return has_digit and has_letter

def validate_phone_number(phone: str) -> bool:
    """電話番号の形式を検証"""
    # 日本の電話番号形式（ハイフンありなし両対応）
    pattern = r'^(\+81|0)[0-9-]{9,}$'
    return re.match(pattern, phone) is not None

def generate_unique_filename(original_filename: str) -> str:
    """ユニークなファイル名を生成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    extension = original_filename.split('.')[-1] if '.' in original_filename else ''
    return f"{timestamp}_{unique_id}.{extension}"

def validate_file_upload(file: UploadFile) -> bool:
    """ファイルアップロードを検証"""
    # ファイルサイズの検証
    if hasattr(file, 'size') and file.size > settings.max_file_size:
        return False
    
    # ファイルタイプの検証
    if file.content_type not in settings.allowed_file_types:
        return False
    
    return True

def sanitize_filename(filename: str) -> str:
    """ファイル名をサニタイズ"""
    # 危険な文字を除去
    filename = re.sub(r'[^\w\-_\.]', '', filename)
    # パストラバーサル攻撃を防ぐ
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')
    return filename

def format_datetime(dt: datetime) -> str:
    """日時をフォーマット"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_date(dt: datetime) -> str:
    """日付をフォーマット"""
    return dt.strftime("%Y-%m-%d")

def calculate_age(birth_date: datetime) -> int:
    """年齢を計算"""
    today = datetime.now()
    age = today.year - birth_date.year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    return age

def is_vaccine_up_to_date(vaccination_date: datetime, months_valid: int = 12) -> bool:
    """ワクチンが有効期限内かチェック"""
    cutoff_date = datetime.now() - timedelta(days=months_valid * 30)
    return vaccination_date >= cutoff_date

def extract_hashtags(text: str) -> List[str]:
    """テキストからハッシュタグを抽出"""
    hashtags = re.findall(r'#\w+', text)
    return list(set(hashtags))  # 重複を除去

def truncate_text(text: str, max_length: int = 100) -> str:
    """テキストを指定長で切り詰め"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def generate_qr_code_data(user_id: int, dog_ids: List[int]) -> str:
    """QRコード用のデータを生成"""
    data = {
        "user_id": user_id,
        "dog_ids": dog_ids,
        "timestamp": datetime.now().isoformat(),
        "type": "dogrun_entry"
    }
    return str(data)

def validate_qr_code_data(data: str) -> Optional[dict]:
    """QRコードデータを検証"""
    try:
        import ast
        parsed_data = ast.literal_eval(data)
        required_keys = ["user_id", "dog_ids", "timestamp", "type"]
        
        if not all(key in parsed_data for key in required_keys):
            return None
        
        if parsed_data["type"] != "dogrun_entry":
            return None
        
        return parsed_data
    except (ValueError, SyntaxError):
        return None

def create_pagination_response(items: List, total: int, page: int, size: int) -> dict:
    """ページネーション用のレスポンスを作成"""
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
        "has_next": page * size < total,
        "has_prev": page > 1
    }

def log_activity(user_id: int, action: str, details: Optional[dict] = None):
    """アクティビティをログに記録"""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "user_id": user_id,
        "action": action,
        "details": details or {}
    }
    # 実際の実装ではログファイルやデータベースに記録
    print(f"Activity Log: {log_entry}")

def validate_breed(breed: str) -> bool:
    """犬種の妥当性を検証"""
    # 一般的な犬種リスト（簡略版）
    common_breeds = [
        "柴犬", "トイプードル", "チワワ", "ミニチュアダックスフンド",
        "ポメラニアン", "マルチーズ", "ヨークシャーテリア", "パピヨン",
        "ボーダーコリー", "ラブラドールレトリバー", "ゴールデンレトリバー",
        "シベリアンハスキー", "ドーベルマン", "ジャーマンシェパード",
        "その他"
    ]
    return breed in common_breeds

def validate_weight(weight: str) -> bool:
    """体重の妥当性を検証"""
    try:
        weight_value = float(weight.replace('kg', ''))
        return 0.1 <= weight_value <= 100.0  # 0.1kg〜100kg
    except (ValueError, AttributeError):
        return False 