#!/bin/bash

# StockWise FastAPI 快速部署脚本

echo "🔄 StockWise FastAPI 部署脚本"

 SERVICE_NAME=${SERVICE_NAME:-${1:-stockwise}}

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

# 4. 部署到 Cloud Run - FastAPI 应用
echo "🚀 部署 FastAPI 应用到 Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars CLOVER_API_KEY=${CLOVER_API_KEY} \
  --set-env-vars MERCHANT_ID=${MERCHANT_ID} \
  --set-env-vars GEMINI_API_KEY=${GEMINI_API_KEY} \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --port 8080

echo "✅ FastAPI 应用部署完成！"

# 5. 获取服务 URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region us-central1 --format 'value(status.url)')
LATEST_REVISION=$(gcloud run services describe ${SERVICE_NAME} --region us-central1 --format 'value(status.latestReadyRevisionName)')
IMAGE=$(gcloud run services describe ${SERVICE_NAME} --region us-central1 --format 'value(spec.template.spec.containers[0].image)')
echo "🌐 应用地址: $SERVICE_URL"
echo "🧾 Latest Revision: $LATEST_REVISION"
echo "🖼️  Image: $IMAGE"
echo "📊 API 文档: $SERVICE_URL/docs"
echo "📊 查看日志: gcloud logs tail ${SERVICE_NAME} --platform managed --region us-central1 --limit 50"
