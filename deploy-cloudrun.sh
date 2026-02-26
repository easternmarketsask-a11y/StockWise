#!/bin/bash

# Google Cloud Run 部署脚本
# StockWise - EasternMarket

echo "🚀 开始部署 StockWise 到 Google Cloud Run..."

# 检查 gcloud CLI 是否安装
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI 未安装"
    echo "📥 请访问: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 设置项目变量 (请修改为你的实际配置)
PROJECT_ID="your-gcp-project-id"  # 🔧 请替换为你的 GCP 项目 ID
SERVICE_NAME="stockwise"
REGION="us-central1"         # 可以修改为最近的区域

# 获取 API 凭据
if [ -f .env ]; then
    echo "🔑 从 .env 文件加载环境变量..."
    export $(grep -v '^#' .env | xargs)
    CLOVER_API_KEY=${CLOVER_API_KEY}
    MERCHANT_ID=${MERCHANT_ID}
    GEMINI_API_KEY=${GEMINI_API_KEY}
else
    echo "❌ 未找到 .env 文件，请手动输入 API 凭据"
    read -p "请输入你的 Clover API Key: " CLOVER_API_KEY
    read -p "请输入你的 Merchant ID: " MERCHANT_ID
    read -p "请输入你的 Gemini API Key: " GEMINI_API_KEY
fi

# 1. 构建 Docker 镜像
echo "📦 构建 Docker 镜像..."
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME} --project=${PROJECT_ID}

# 2. 部署到 Cloud Run
echo "🌐 部署到 Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars CLOVER_API_KEY=${CLOVER_API_KEY},MERCHANT_ID=${MERCHANT_ID},GEMINI_API_KEY=${GEMINI_API_KEY} \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300

# 3. 获取服务 URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format 'value(status.url)')

echo "✅ 部署完成！"
echo "🌐 应用地址: ${SERVICE_URL}"
echo "📊 查看日志: gcloud logs tail ${SERVICE_NAME} --platform managed --region ${REGION}"
echo "🔄 更新部署: gcloud run services update ${SERVICE_NAME} --platform managed --region ${REGION}"
