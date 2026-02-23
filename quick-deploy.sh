#!/bin/bash

# StockWise 快速同步和部署脚本

echo "🔄 StockWise 同步部署脚本"

# 1. 同步代码
echo "📥 同步最新代码..."
git pull origin main

# 2. 检查是否有代码更改
if git diff --quiet HEAD~1 HEAD -- .; then
    echo "ℹ️  没有代码更改，跳过部署"
    exit 0
fi

# 3. 部署到 Cloud Run
echo "🚀 部署到 Cloud Run..."
gcloud run deploy stockwise-app \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars CLOVER_MERCHANT_ID=SN4FE813EDA51 \
  --set-env-vars CLOVER_API_KEY=c7e0ed05-ecc2-0c33-25b1 \
  --set-env-vars GEMINI_API_KEY=AIzaSyD2orlisbm1SfbS3qH

echo "✅ 部署完成！"

# 4. 获取服务 URL
SERVICE_URL=$(gcloud run services describe stockwise-app --region us-central1 --format 'value(status.url)')
echo "🌐 应用地址: $SERVICE_URL"
