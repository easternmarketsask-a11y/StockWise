#!/bin/bash

# Google Cloud Run 部署脚本 - 包含域名配置
# StockWise - EasternMarket
# 域名: easternmarket.ca

echo "🚀 开始部署 StockWise 到 Google Cloud Run..."

# 检查 gcloud CLI 是否安装
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI 未安装"
    echo "📥 请访问: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 设置项目变量 (请修改为你的实际配置)
PROJECT_ID="stockwise-486801"  # 🔧 已更新为你的 GCP 项目 ID
SERVICE_NAME="stockwise"
REGION="us-central1"
DOMAIN_NAME="easternmarket.ca"

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
echo "🌐 临时地址: ${SERVICE_URL}"
echo "📊 查看日志: gcloud logs tail ${SERVICE_NAME} --platform managed --region ${REGION}"

# 4. 配置自定义域名
echo ""
echo "🌐 配置自定义域名: ${DOMAIN_NAME}"

# 创建域名映射
echo "🔧 创建域名映射..."
gcloud run domain-mappings create ${SERVICE_NAME} \
  --domain=${DOMAIN_NAME} \
  --region=${REGION} \
  --service=${SERVICE_NAME}

echo "✅ 域名配置完成！"
echo "🌐 固定访问地址: https://${DOMAIN_NAME}"
echo ""
echo "📋 重要 - DNS配置步骤:"
echo "1. 登录你的域名管理面板 (如 GoDaddy, Namecheap等)"
echo "2. 添加以下DNS记录:"
echo "   Type: CNAME"
echo "   Name: @"
echo "   Value: ghs.googlehosted.com."
echo "   TTL: 3600"
echo ""
echo "3. 等待DNS传播 (通常5-15分钟)"
echo "4. 验证域名: curl -I https://${DOMAIN_NAME}"
echo ""
echo "🔍 检查域名映射状态:"
echo "gcloud run domain-mappings list --region=${REGION}"
echo ""
echo "📊 查看SSL证书状态:"
echo "gcloud run domain-mappings describe ${DOMAIN_NAME} --region=${REGION}"
