#!/bin/bash

# StockWise Anthropic API 部署脚本
# 使用 ANTHROPIC_API_KEY 部署到 Cloud Run

echo "🚀 StockWise Anthropic API 部署脚本"

# 检查 gcloud CLI
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI 未安装"
    echo "📥 请访问: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 设置项目变量 (请修改为你的实际配置)
PROJECT_ID="your-gcp-project-id"  # 🔧 请替换为你的 GCP 项目 ID
SERVICE_NAME="stockwise-anthropic"
REGION="us-central1"

# 检查 .env 文件
if [ -f .env ]; then
    echo "🔑 从 .env 文件加载环境变量..."
    export $(grep -v '^#' .env | xargs)
    
    if [ -z "$CLOVER_API_KEY" ] || [ -z "$MERCHANT_ID" ] || [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "❌ .env 文件中缺少必要的 API Keys"
        echo "📋 请确保 .env 文件包含:"
        echo "   - CLOVER_API_KEY"
        echo "   - MERCHANT_ID" 
        echo "   - ANTHROPIC_API_KEY"
        exit 1
    fi
    
    echo "✅ API Keys 验证通过"
    echo "🤖 使用 Anthropic Claude AI"
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

# 2. 部署到 Cloud Run
echo "🌐 部署到 Cloud Run (使用 Anthropic API)..."
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars CLOVER_API_KEY=${CLOVER_API_KEY},MERCHANT_ID=${MERCHANT_ID},ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY} \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300

# 3. 获取服务 URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format 'value(status.url)')

echo "✅ Anthropic API 部署完成！"
echo "🌐 应用地址: ${SERVICE_URL}"
echo "🤖 AI 提供商: Anthropic Claude"
echo ""
echo "📊 管理命令:"
echo "   查看日志: gcloud logs tail ${SERVICE_NAME} --platform managed --region ${REGION}"
echo "   更新部署: gcloud run services update ${SERVICE_NAME} --platform managed --region ${REGION}"
echo "   删除服务: gcloud run services delete ${SERVICE_NAME} --platform managed --region ${REGION}"
