#!/bin/bash

# StockWise 强制部署最新代码脚本

echo "🚀 StockWise 强制部署最新代码"

# 1. 确保使用最新代码
echo "📥 拉取最新代码..."
git pull origin main

# 2. 检查当前提交
echo "📋 当前提交信息:"
git log --oneline -1

# 3. 加载环境变量
if [ -f .env ]; then
    echo "🔑 加载环境变量..."
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ 未找到 .env 文件，请创建并配置 API keys"
    exit 1
fi

# 4. 强制重新构建和部署
echo "🔨 强制重新构建..."
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/stockwise:latest .

echo "🌐 部署到 Cloud Run..."
gcloud run deploy stockwise \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/stockwise:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars CLOVER_API_KEY=${CLOVER_API_KEY} \
  --set-env-vars MERCHANT_ID=${MERCHANT_ID} \
  --set-env-vars GEMINI_API_KEY=${GEMINI_API_KEY} \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --force

echo "✅ 部署完成！"

# 5. 获取服务信息
SERVICE_URL=$(gcloud run services describe stockwise --region us-central1 --format 'value(status.url)')
echo "🌐 应用地址: $SERVICE_URL"
echo "📊 查看日志: gcloud logs tail stockwise --platform managed --region us-central1 --limit 50"
