# Azure MySQL接続問題解決ガイド

## 現在の状況
- ローカルSQLiteデータベース: ✅ 正常に動作
- Azure MySQLデータベース: ❌ 接続タイムアウト

## 問題の原因
Azure MySQLのファイアウォール設定で、現在のIPアドレス `111.188.120.193` が許可リストに含まれていない可能性があります。

## 解決手順

### 1. Azure Portalでファイアウォール設定を確認・更新

1. Azure Portal (https://portal.azure.com) にログイン
2. MySQLサーバー `rdbs-002-gen10-step3-2-oshima14` を検索
3. 「セキュリティ」→「ネットワーク」を選択
4. 「ファイアウォール規則」で以下を確認・追加：
   - 名前: `Local Development`
   - 開始IP: `111.188.120.193`
   - 終了IP: `111.188.120.193`

### 2. 接続テスト

ファイアウォール設定を更新後、以下のコマンドで接続をテスト：

```bash
cd backend/db_control
python test_connection.py
```

### 3. テーブル作成

接続が成功したら、以下のコマンドでテーブルを作成：

```bash
python initialize_db.py
```

## 代替案

### 一時的にローカルSQLiteを使用

Azure接続が解決するまで、ローカルSQLiteデータベースを使用できます：

```bash
# ローカルデータベースにテーブル作成
python initialize_local_db.py

# アプリケーションでローカルデータベースを使用
# .envファイルで DATABASE_URL=sqlite:///./satoyama_dogrun.db に設定
```

### データベース移行

Azure接続が確立された後、ローカルデータからAzureにデータを移行できます。

## トラブルシューティング

### 接続タイムアウトが続く場合
1. ネットワーク接続を確認
2. Azure MySQLサーバーの状態を確認
3. ファイアウォール設定を再確認
4. 別のネットワーク（モバイルホットスポットなど）でテスト

### SSL証明書エラーの場合
1. SSL証明書ファイルが正しくダウンロードされているか確認
2. `certs/DigiCertGlobalRootCA.crt.pem` ファイルのサイズを確認（1338バイトである必要があります）

### アクセス拒否エラーの場合
1. ユーザー名とパスワードを確認
2. データベース名を確認
3. ユーザー権限を確認

## 現在の設定

### 環境変数 (.env)
```
DB_USER='tech0gen10student'
DB_PASSWORD='vY7JZNfU'
DB_HOST='rdbs-002-gen10-step3-2-oshima14.mysql.database.azure.com'
DB_PORT='3306'
DB_NAME='satoyama_dogrun'
SSL_CA_PATH=certs/DigiCertGlobalRootCA.crt.pem
```

### 作成済みテーブル（ローカル）
- `users` - ユーザー情報
- `dogs` - 犬の情報

## 次のステップ
1. Azure Portalでファイアウォール設定を更新
2. 接続テストを実行
3. 成功したらテーブル作成を実行
4. アプリケーションでAzure MySQLを使用 