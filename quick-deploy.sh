#!/bin/bash

# StockWise 快速同步和部署脚本 (Streamlit 版本)

echo "🔄 StockWise Streamlit 同步部署脚本"

# 1. 同步最新代码
echo "📥 同步最新代码..."
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

# 4. 部署到 Cloud Run - 使用源代码构建确保最新代码，强制 Streamlit 模式
echo "🚀 部署 Streamlit 应用到 Cloud Run..."
gcloud run deploy stockwise \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars CLOVER_API_KEY=${CLOVER_API_KEY} \
  --set-env-vars MERCHANT_ID=${MERCHANT_ID} \
  --set-env-vars GEMINI_API_KEY=${GEMINI_API_KEY} \
  --set-env-vars APP_MODE=streamlit \
  --build-arg APP_MODE=streamlit \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --port 8080

echo "✅ Streamlit 应用部署完成！"

# 5. 获取服务 URL
SERVICE_URL=$(gcloud run services describe stockwise --region us-central1 --format 'value(status.url)')
echo "🌐 应用地址: $SERVICE_URL"
echo "📊 查看日志: gcloud logs tail stockwise --platform managed --region us-central1 --limit 50"
echo "🔍 调试模式: 查看启动日志确认 Streamlit 是否正常运行"
