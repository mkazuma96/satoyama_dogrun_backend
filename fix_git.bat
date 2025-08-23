@echo off
cd /d "C:\Users\kmats\OneDrive\デスクトップ\satoyamadogrun-main\backend"
git add .
git commit -m "修正: インポートエラー解決 - schemasからの正しいインポート"
git push origin main
echo "デプロイ完了"
pause

