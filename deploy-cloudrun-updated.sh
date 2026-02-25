#!/bin/bash

# Google Cloud Run 部署脚本 - 更新版本
# StockWise Enhanced - EasternMarket

echo "🚀 开始部署 StockWise Enhanced 到 Google Cloud Run..."

# 检查 gcloud CLI 是否安装
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI 未安装"
    echo "📥 请访问: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 设置项目变量 (请修改为你的实际配置)
PROJECT_ID="your-gcp-project-id"  # 🔧 请替换为你的 GCP 项目 ID
SERVICE_NAME="stockwise-enhanced"
REGION="us-central1"         # 可以修改为最近的区域

# 获取 API 凭据
read -p "请输入你的 Clover API Key: " CLOVER_API_KEY
read -p "请输入你的 Merchant ID: " MERCHANT_ID

echo "📦 使用 Cloud Run 专用 Dockerfile 构建镜像..."

# 1. 构建 Docker 镜像
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --project=${PROJECT_ID} \
  --timeout=1200

# 2. 部署到 Cloud Run
echo "🌐 部署到 Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars CLOVER_API_KEY=${CLOVER_API_KEY},MERCHANT_ID=${MERCHANT_ID} \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0

# 3. 获取服务 URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format 'value(status.url)')

echo "✅ 部署完成！"
echo "🌐 应用地址: ${SERVICE_URL}"
echo "📊 查看日志: gcloud logs tail ${SERVICE_NAME} --platform managed --region ${REGION}"
echo "🔄 更新部署: 重新运行此脚本"
echo ""
echo "🎉 StockWise Enhanced 新功能包括:"
echo "   • 📊 数据可视化图表"
echo "   • 🚨 库存预警系统" 
echo "   • 📈 销售趋势分析"
echo "   • 🌍 多语言支持 (中文/英文)"
echo "   • 📱 移动端优化"
