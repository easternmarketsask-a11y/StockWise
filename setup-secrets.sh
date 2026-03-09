#!/bin/bash

# Google Secret Manager 配置脚本
# 用于安全管理 StockWise API Keys

echo "🔐 配置 Google Secret Manager..."

# 检查 gcloud CLI 是否安装
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI 未安装"
    echo "📥 请访问: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 设置项目变量
PROJECT_ID="eastern-market-app"
REGION="us-central1"

echo "📋 将创建以下 secrets:"
echo "- clover-api-key"
echo "- merchant-id" 
echo "- gemini-api-key"

# 创建 secrets
echo "🔑 创建 Clover API Key secret..."
gcloud secrets create clover-api-key --replication-policy="automatic" --project=${PROJECT_ID}

echo "🏪 创建 Merchant ID secret..."
gcloud secrets create merchant-id --replication-policy="automatic" --project=${PROJECT_ID}

echo "🤖 创建 Gemini API Key secret..."
gcloud secrets create gemini-api-key --replication-policy="automatic" --project=${PROJECT_ID}

echo "📝 添加 secret values..."
echo "请手动输入你的 API Keys:"
read -s -p "Clover API Key: " CLOVER_KEY
echo ""
read -s -p "Merchant ID: " MERCHANT_ID_VALUE
echo ""
read -s -p "Gemini API Key: " GEMINI_KEY
echo ""

echo "$CLOVER_KEY" | gcloud secrets versions add clover-api-key --data-file=- --project=${PROJECT_ID}
echo "$MERCHANT_ID_VALUE" | gcloud secrets versions add merchant-id --data-file=- --project=${PROJECT_ID}
echo "$GEMINI_KEY" | gcloud secrets versions add gemini-api-key --data-file=- --project=${PROJECT_ID}

echo "✅ Secrets 创建完成！"

# 授予 Cloud Run 服务账号访问权限
SERVICE_ACCOUNT="$(gcloud run services describe eastern-market-api --region=${REGION} --format='value(spec.template.spec.serviceAccountName)')"

if [ -n "$SERVICE_ACCOUNT" ]; then
    echo "🔓 授予 Cloud Run 服务账号访问权限..."
    gcloud secrets add-iam-policy-binding clover-api-key --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor" --project=${PROJECT_ID}
    gcloud secrets add-iam-policy-binding merchant-id --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor" --project=${PROJECT_ID}
    gcloud secrets add-iam-policy-binding gemini-api-key --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor" --project=${PROJECT_ID}
    echo "✅ 权限配置完成！"
else
    echo "⚠️  未找到服务账号，请手动配置权限"
fi

echo ""
echo "📖 使用方法:"
echo "1. 在 Cloud Run 部署时添加以下参数:"
echo "   --set-secrets=CLOVER_API_KEY=clover-api-key:latest"
echo "   --set-secrets=MERCHANT_ID=merchant-id:latest"
echo "   --set-secrets=GEMINI_API_KEY=gemini-api-key:latest"
echo ""
echo "2. 查看 secrets:"
echo "   gcloud secrets list --project=${PROJECT_ID}"
