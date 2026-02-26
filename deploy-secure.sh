#!/bin/bash

# 使用 Secret Manager 的安全部署脚本

echo "🚀 StockWise 安全部署脚本 (使用 Secret Manager)"

# 设置项目变量
PROJECT_ID="eastern-market-app"
SERVICE_NAME="eastern-market-api"
REGION="us-central1"

# 1. 构建 Docker 镜像
echo "📦 构建 Docker 镜像..."
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME} --project=${PROJECT_ID}

# 2. 部署到 Cloud Run (使用 Secret Manager)
echo "🌐 部署到 Cloud Run (使用 Secret Manager)..."
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-secrets=CLOVER_API_KEY=clover-api-key:latest \
  --set-secrets=MERCHANT_ID=merchant-id:latest \
  --set-secrets=GEMINI_API_KEY=gemini-api-key:latest \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300

# 3. 获取服务 URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format 'value(status.url)')

echo "✅ 安全部署完成！"
echo "🌐 应用地址: ${SERVICE_URL}"
echo "🔐 API Keys 已通过 Secret Manager 安全管理"
