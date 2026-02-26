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

# 3. 加载环境变量
if [ -f .env ]; then
    echo "🔑 加载环境变量..."
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ 未找到 .env 文件，请创建并配置 API keys"
    exit 1
fi

# 4. 部署到 Cloud Run
echo "🚀 部署到 Cloud Run..."
gcloud run deploy stockwise-app \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars CLOVER_MERCHANT_ID=${MERCHANT_ID} \
  --set-env-vars CLOVER_API_KEY=${CLOVER_API_KEY} \
  --set-env-vars GEMINI_API_KEY=${GEMINI_API_KEY}

echo "✅ 部署完成！"

# 4. 获取服务 URL
SERVICE_URL=$(gcloud run services describe stockwise-app --region us-central1 --format 'value(status.url)')
echo "🌐 应用地址: $SERVICE_URL"
