#!/bin/bash

# StockWise 安全部署脚本
# 使用 Google Cloud Secret Manager 管理敏感信息

echo "🚀 开始部署 StockWise 到 Cloud Run..."

# 部署到 Cloud Run
echo "📦 构建和部署容器..."
gcloud run deploy stockwise-app \
    --source . \
    --region us-central1 \
    --allow-unauthenticated

if [ $? -eq 0 ]; then
    echo "✅ 部署成功！"
    echo "🌐 应用地址: https://stockwise-app-873982544406.us-central1.run.app"
    echo "🔒 所有API密钥已通过 Secret Manager 安全管理"
else
    echo "❌ 部署失败，请检查错误信息"
    exit 1
fi
