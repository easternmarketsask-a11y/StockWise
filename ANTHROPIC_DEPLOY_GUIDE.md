# StockWise Anthropic API 快速部署指南

## 🚀 快速部署到 Cloud Run

### 前置条件
1. 已安装 Google Cloud CLI
2. 已创建 GCP 项目并启用了 Cloud Run 和 Cloud Build API
3. 已在 `.env` 文件中配置了 `ANTHROPIC_API_KEY`

### 部署步骤

#### Windows 用户 (PowerShell)
```powershell
# 1. 修改项目ID
$PROJECT_ID = "your-gcp-project-id"

# 2. 运行部署脚本
cd d:\Market_App\StockWise\stockwise_final
.\deploy-anthropic.ps1
```

#### Linux/Mac 用户 (Bash)
```bash
# 1. 修改项目ID
export PROJECT_ID="your-gcp-project-id"

# 2. 运行部署脚本
cd d:\Market_App\StockWise\stockwise_final
chmod +x deploy-anthropic.sh
./deploy-anthropic.sh
```

### 🔧 手动部署 (如果脚本失败)

```bash
# 1. 设置环境变量
export CLOVER_API_KEY="your_clover_api_key"
export MERCHANT_ID="your_merchant_id"
export ANTHROPIC_API_KEY="your_anthropic_api_key"

# 2. 构建镜像
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/stockwise-anthropic

# 3. 部署到 Cloud Run
gcloud run deploy stockwise-anthropic \
  --image gcr.io/YOUR_PROJECT_ID/stockwise-anthropic \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "CLOVER_API_KEY=$CLOVER_API_KEY,MERCHANT_ID=$MERCHANT_ID,ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300
```

### 🎯 验证部署

部署完成后，访问返回的URL，检查：
- 首页正常加载
- `/health` 端点返回状态
- `/api/system/status` 显示 `ai_provider: "anthropic"`

### 🤖 AI 功能测试

在应用的"🤖 智能管理"标签页：
1. 输入商品名称（如 "Fuji Apple"）
2. 设置价格
3. 点击"生成分类"或"生成描述"
4. 验证返回结果来自 Anthropic Claude

### 📊 监控和管理

```bash
# 查看日志
gcloud logs tail stockwise-anthropic --platform managed --region us-central1

# 更新部署
gcloud run services update stockwise-anthropic --platform managed --region us-central1

# 删除服务
gcloud run services delete stockwise-anthropic --platform managed --region us-central1
```

### 🔒 安全提示

- API Keys 通过环境变量安全传递
- 建议使用 Secret Manager 进行生产环境管理
- 定期轮换 API Keys

### 🆘 故障排除

1. **构建失败**: 检查 `Dockerfile` 和 `requirements.txt`
2. **部署失败**: 验证 GCP 权限和配额
3. **AI 功能异常**: 检查 `ANTHROPIC_API_KEY` 有效性
4. **Clover API 错误**: 验证 `CLOVER_API_KEY` 和 `MERCHANT_ID`

### 📈 性能优化

- 默认配置: 512Mi 内存, 1 CPU
- 可根据需要调整: `--memory 1Gi --cpu 2`
- 设置并发: `--max-concurrency 10`
