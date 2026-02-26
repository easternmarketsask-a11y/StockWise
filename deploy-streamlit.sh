#!/bin/bash

# StockWise Streamlit 应用部署脚本

echo "🚀 StockWise Streamlit 应用部署"

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

# 4. 使用 Streamlit Dockerfile 构建
echo "🔨 构建 Streamlit 应用镜像..."
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/stockwise:streamlit --dockerfile Dockerfile.streamlit .

# 5. 部署到 Cloud Run
echo "🌐 部署到 Cloud Run..."
gcloud run deploy stockwise-streamlit \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/stockwise:streamlit \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars CLOVER_API_KEY=${CLOVER_API_KEY} \
  --set-env-vars MERCHANT_ID=${MERCHANT_ID} \
  --set-env-vars GEMINI_API_KEY=${GEMINI_API_KEY} \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --port 8080

echo "✅ Streamlit 应用部署完成！"

# 6. 获取服务信息
SERVICE_URL=$(gcloud run services describe stockwise-streamlit --region us-central1 --format 'value(status.url)')
echo "🌐 应用地址: $SERVICE_URL"
echo "📊 查看日志: gcloud logs tail stockwise-streamlit --platform managed --region us-central1 --limit 50"
