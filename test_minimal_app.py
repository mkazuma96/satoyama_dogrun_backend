#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小限のFastAPIアプリ起動テスト
"""

import uvicorn
from fastapi import FastAPI

# 最小限のアプリケーション
app = FastAPI(title="テスト用API")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 最小限のFastAPIアプリを起動中...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
