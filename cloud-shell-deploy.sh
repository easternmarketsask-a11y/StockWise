#!/bin/bash

# StockWise Anthropic API - Cloud Shell 高效部署命令
# 复制以下命令到 Google Cloud Shell 执行

echo "=== StockWise Cloud Shell 部署命令 ==="
echo ""

# 1. 设置项目变量 (请替换为你的实际值)
echo "# 1. 设置环境变量"
echo "export PROJECT_ID=\"your-gcp-project-id\""
echo "export SERVICE_NAME=\"stockwise-anthropic\""
echo "export REGION=\"us-central1\""
echo ""

# 2. 设置API密钥 (请替换为你的实际值)
echo "# 2. 设置API密钥"
echo "export CLOVER_API_KEY=\"your_clover_api_key_here\""
echo "export MERCHANT_ID=\"your_merchant_id_here\""
echo "export ANTHROPIC_API_KEY=\"your_anthropic_api_key_here\""
echo ""

# 3. 一键部署命令
echo "# 3. 一键构建和部署"
echo "gcloud builds submit --tag gcr.io/\${PROJECT_ID}/\${SERVICE_NAME} --project=\${PROJECT_ID} && \\"
echo "gcloud run deploy \${SERVICE_NAME} \\"
echo "  --image gcr.io/\${PROJECT_ID}/\${SERVICE_NAME} \\"
echo "  --platform managed \\"
echo "  --region \${REGION} \\"
echo "  --allow-unauthenticated \\"
echo "  --set-env-vars \"CLOVER_API_KEY=\${CLOVER_API_KEY},MERCHANT_ID=\${MERCHANT_ID},ANTHROPIC_API_KEY=\${ANTHROPIC_API_KEY}\" \\"
echo "  --port 8080 \\"
echo "  --memory 512Mi \\"
echo "  --cpu 1 \\"
echo "  --timeout 300"
echo ""

# 4. 获取服务URL
echo "# 4. 获取服务地址"
echo "gcloud run services describe \${SERVICE_NAME} --platform managed --region \${REGION} --format 'value(status.url)'"
echo ""

# 5. 快速验证
echo "# 5. 验证部署"
echo "curl -s \"\$(gcloud run services describe \${SERVICE_NAME} --platform managed --region \${REGION} --format 'value(status.url)')/health\" | jq ."
echo ""

echo "=== 完整复制版本 ==="
echo ""
echo "# 设置项目信息"
echo "PROJECT_ID=\"your-gcp-project-id\""
echo "SERVICE_NAME=\"stockwise-anthropic\""
echo "REGION=\"us-central1\""
echo ""
echo "# 设置API密钥"
echo "CLOVER_API_KEY=\"your_clover_api_key_here\""
echo "MERCHANT_ID=\"your_merchant_id_here\""
echo "ANTHROPIC_API_KEY=\"your_anthropic_api_key_here\""
echo ""
echo "# 构建和部署"
echo "gcloud builds submit --tag gcr.io/\${PROJECT_ID}/\${SERVICE_NAME} --project=\${PROJECT_ID}"
echo "gcloud run deploy \${SERVICE_NAME} --image gcr.io/\${PROJECT_ID}/\${SERVICE_NAME} --platform managed --region \${REGION} --allow-unauthenticated --set-env-vars \"CLOVER_API_KEY=\${CLOVER_API_KEY},MERCHANT_ID=\${MERCHANT_ID},ANTHROPIC_API_KEY=\${ANTHROPIC_API_KEY}\" --port 8080 --memory 512Mi --cpu 1 --timeout 300"
echo ""
echo "# 获取URL"
echo "gcloud run services describe \${SERVICE_NAME} --platform managed --region \${REGION} --format 'value(status.url)'"
