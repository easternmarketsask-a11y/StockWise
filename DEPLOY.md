# StockWise Cloud Run 部署指南

## 部署前准备

1. 安装 Google Cloud SDK: https://cloud.google.com/sdk/docs/install
2. 登录 Google Cloud:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. 启用必要 API:
   ```bash
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com
   ```

## 部署方式

### 方式一：使用 gcloud 命令直接部署（推荐）

```bash
cd d:\Market_App\StockWise\stockwise_final

# 设置环境变量
$env:CLOVER_API_KEY = "your_clover_api_key"
$env:MERCHANT_ID = "your_merchant_id"

# 提交构建并部署到 Cloud Run
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/stockwise-api

gcloud run deploy stockwise-api `
  --image gcr.io/YOUR_PROJECT_ID/stockwise-api `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --set-env-vars "CLOVER_API_KEY=$env:CLOVER_API_KEY,MERCHANT_ID=$env:MERCHANT_ID,ENVIRONMENT=production" `
  --port 8080
```

### 方式二：使用 Cloud Build 配置文件

已创建 `cloudbuild.yaml`，运行：

```bash
gcloud builds submit --config cloudbuild.yaml
```

### 方式三：Docker 本地测试

```bash
# 构建镜像
docker build -t stockwise-api .

# 运行容器
docker run -p 8080:8080 -e CLOVER_API_KEY=xxx -e MERCHANT_ID=xxx stockwise-api
```

## 部署后验证

访问: `https://stockwise-api-xxx-uc.a.run.app`

API 端点:
- `/` - 首页 (HTML)
- `/health` - 健康检查
- `/api/products` - 商品列表
- `/api/sales/search` - 销量查询
- `/api/sales/export` - 导出30天数据
- `/docs` - Swagger 文档

## 环境变量

必需:
- `CLOVER_API_KEY` - Clover API 密钥
- `MERCHANT_ID` - 商户 ID

AI 配置 (至少一个):
- `ANTHROPIC_API_KEY` - Anthropic Claude API 密钥 (推荐)
- `GEMINI_API_KEY` - Google Gemini API 密钥 (备选)

可选:
- `ENVIRONMENT` - 环境标识 (production/development)
- `PORT` - 服务端口 (默认 8080)

### Anthropic API 部署 (推荐)

如果你已配置 `ANTHROPIC_API_KEY`，使用以下命令：

**PowerShell (Windows):**
```powershell
cd d:\Market_App\StockWise\stockwise_final
.\deploy-anthropic.ps1
```

**Bash (Linux/Mac):**
```bash
cd d:\Market_App\StockWise\stockwise_final
chmod +x deploy-anthropic.sh
./deploy-anthropic.sh
```

**手动 gcloud 命令:**
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/stockwise-anthropic

gcloud run deploy stockwise-anthropic `
  --image gcr.io/YOUR_PROJECT_ID/stockwise-anthropic `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --set-env-vars "CLOVER_API_KEY=$env:CLOVER_API_KEY,MERCHANT_ID=$env:MERCHANT_ID,ANTHROPIC_API_KEY=$env:ANTHROPIC_API_KEY" `
  --port 8080
```

## 其他部署平台

### Railway (https://railway.app)
1. 连接 GitHub 仓库
2. 设置环境变量
3. 自动部署

### Render (https://render.com)
1. 创建 Web Service
2. 选择 Docker 部署
3. 设置环境变量

### 阿里云/腾讯云容器服务
使用提供的 Dockerfile 构建镜像后推送至相应容器仓库。
