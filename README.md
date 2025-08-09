# 里山ドッグラン - バックエンド

里山ドッグラン管理システムのバックエンド（FastAPI）です。

## 技術スタック

- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.8+
- **Database**: SQLite (開発) / PostgreSQL (本番)
- **ORM**: SQLAlchemy
- **Authentication**: JWT
- **Password Hashing**: bcrypt
- **Documentation**: Swagger UI

## プロジェクト構造

```
backend/
├── main.py              # FastAPI アプリケーション
├── models.py            # データベースモデル
├── auth.py              # 認証機能
├── database.py          # データベース設定
├── schemas.py           # Pydantic スキーマ
├── requirements.txt     # 依存関係
├── env.example          # 環境変数サンプル
└── satoyama_dogrun.db  # SQLite データベース
```

## セットアップ

### 1. 仮想環境の作成

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

```bash
cp env.example .env
```

`.env`ファイルを編集して、適切な値を設定：

```env
DATABASE_URL=sqlite:///./satoyama_dogrun.db
SECRET_KEY=your-secret-key-here-change-this-in-production
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 4. サーバーの起動

```bash
python main.py
```

バックエンドは `http://localhost:8000` で起動します。

## API ドキュメント

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## データベース

### SQLite (開発環境)

デフォルトでSQLiteを使用します。データベースファイルは自動的に作成されます。

### PostgreSQL (本番環境)

本番環境ではPostgreSQLを使用することを推奨します：

```env
DATABASE_URL=postgresql://user:password@localhost/satoyama_dogrun
```

## 認証

JWT（JSON Web Token）を使用した認証システムを実装しています。

### 認証フロー

1. **登録**: `POST /auth/register`
2. **ログイン**: `POST /auth/login`
3. **トークン検証**: 自動的にリクエストヘッダーで検証

### 保護されたエンドポイント

認証が必要なエンドポイントには `Depends(get_current_user)` を使用します。

## エラーハンドリング

- **HTTP 400**: バリデーションエラー
- **HTTP 401**: 認証エラー
- **HTTP 404**: リソースが見つからない
- **HTTP 500**: サーバーエラー

## 開発ガイドライン

### コードスタイル

- **PEP 8**: Python コーディング規約に従う
- **Type Hints**: すべての関数で型ヒントを使用
- **Docstrings**: 関数とクラスにドキュメントを記載

### データベース設計

- **正規化**: 適切な正規化を行う
- **インデックス**: 検索頻度の高いカラムにインデックスを設定
- **外部キー**: 適切な外部キー制約を設定

### セキュリティ

- **パスワードハッシュ**: bcrypt を使用
- **JWT**: 適切な有効期限を設定
- **CORS**: 許可されたオリジンのみアクセス可能
- **入力検証**: Pydantic を使用した厳密なバリデーション

## テスト

```bash
# 単体テスト
python -m pytest tests/

# カバレッジ
python -m pytest --cov=app tests/
```

## デプロイ

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 本番環境

```bash
# Gunicorn を使用
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## ライセンス

MIT License 