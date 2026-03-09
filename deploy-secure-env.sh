#!/bin/bash

# 安全部署脚本 - 使用环境变量方式
# StockWise - EasternMarket

echo "🚀 StockWise 安全部署脚本 (环境变量方式)"

# 检查 gcloud CLI 是否安装
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI 未安装"
    echo "📥 请访问: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 设置项目变量 (请修改为你的实际配置)
PROJECT_ID="stockwise-486801"  # 🔧 请替换为你的 GCP 项目 ID
SERVICE_NAME="stockwise"
REGION="us-central1"         # 可以修改为最近的区域

# 获取 API 凭据
if [ -f .env ]; then
    echo "🔑 从 .env 文件加载环境变量..."
    export $(grep -v '^#' .env | xargs)
    
    if [ -z "$CLOVER_API_KEY" ] || [ -z "$MERCHANT_ID" ]; then
        echo "❌ .env 文件中缺少必要的 API Keys"
        echo "📋 请确保 .env 文件包含:"
        echo "   - CLOVER_API_KEY"
        echo "   - MERCHANT_ID" 
        echo "   - ANTHROPIC_API_KEY 或 GEMINI_API_KEY (至少一个)"
        exit 1
    fi
    
    echo "✅ API Keys 验证通过"
else
    echo "❌ 未找到 .env 文件"
    echo "📋 请先创建 .env 文件:"
    echo "   cp .env.example .env"
    echo "   然后编辑 .env 文件填入你的 API Keys"
    exit 1
fi

# 1. 构建 Docker 镜像
echo "📦 构建 Docker 镜像..."
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME} --project=${PROJECT_ID}

# 2. 部署到 Cloud Run (使用环境变量)
echo "🌐 部署到 Cloud Run (使用环境变量)..."
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars CLOVER_API_KEY=${CLOVER_API_KEY},MERCHANT_ID=${MERCHANT_ID},ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-},GEMINI_API_KEY=${GEMINI_API_KEY:-} \
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
echo "🔐 API Keys 已通过环境变量安全管理"
echo ""
echo "📊 管理命令:"
echo "   查看日志: gcloud logs tail ${SERVICE_NAME} --platform managed --region ${REGION}"
echo "   更新部署: gcloud run services update ${SERVICE_NAME} --platform managed --region ${REGION}"
echo "   删除服务: gcloud run services delete ${SERVICE_NAME} --platform managed --region ${REGION}"
