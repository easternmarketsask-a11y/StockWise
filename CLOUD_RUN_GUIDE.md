# Google Cloud Run 部署指南
# StockWise EasternMarket

## 🚀 快速部署到 Google Cloud Run

### 📋 前置要求

1. **Google Cloud 账户**
   - 访问 [Google Cloud Console](https://console.cloud.google.com/)
   - 创建新项目或使用现有项目
   - 启用计费功能

2. **安装 Google Cloud CLI**
   ```bash
   # Windows
   # 下载并安装 Google Cloud SDK
   # https://cloud.google.com/sdk/docs/install
   
   # 验证安装
   gcloud --version
   ```

3. **启用必要的服务**
   ```bash
   # 启用 Cloud Run API
   gcloud services enable run.googleapis.com
   
   # 启用 Cloud Build API
   gcloud services enable cloudbuild.googleapis.com
   
   # 启用 Container Registry API
   gcloud services enable containerregistry.googleapis.com
   ```

### 🔧 部署步骤

#### 步骤1：配置 Google Cloud
```bash
# 登录 Google Cloud
gcloud auth login

# 设置项目 ID (替换为你的项目 ID)
gcloud config set project your-project-id

# 设置默认区域
gcloud config set run/region us-central1
```

#### 步骤2：部署应用
```bash
# 使用自动化脚本
./deploy-cloudrun.sh

# 或手动部署
gcloud builds submit --tag gcr.io/your-project-id/stockwise
gcloud run deploy stockwise --image gcr.io/your-project-id/stockwise --allow-unauthenticated
```

#### 步骤3：配置环境变量
```bash
# 设置 API 凭据
gcloud run services update stockwise \
  --set-env-vars CLOVER_API_KEY=your_api_key,MERCHANT_ID=your_merchant_id
```

### 🌐 访问应用

部署完成后，你会获得一个类似这样的 URL：
```
https://stockwise-xxxxx-xx.a.run.app
```

### 📊 管理和维护

#### 查看服务状态
```bash
gcloud run services describe stockwise
```

#### 查看日志
```bash
gcloud logs tail stockwise
```

#### 更新部署
```bash
# 重新构建和部署
gcloud builds submit --tag gcr.io/your-project-id/stockwise
gcloud run services update stockwise --image gcr.io/your-project-id/stockwise
```

#### 删除服务
```bash
gcloud run services delete stockwise
```

### 💰 成本估算

Cloud Run 的免费额度：
- **每月 180,000 vCPU-秒**
- **每月 1 GB 出站流量**
- **每月 360,000 内存-GB秒**

对于 StockWise 应用：
- **预估月成本**: $0-5 (取决于使用量)
- **内存**: 512Mi
- **CPU**: 1 vCPU
- **并发**: 最多 80 个请求

### 🔒 安全配置

#### 限制访问
```bash
# 仅允许特定用户访问
gcloud run services update stockwise \
  --no-allow-unauthenticated \
  --set-invocation-policy=allow-unauthenticated
```

#### 设置 IAM 权限
```bash
# 授予特定用户访问权限
gcloud run services add-iam-policy-binding stockwise \
  --member=user:example@gmail.com \
  --role=roles/run.invoker
```

### 📈 监控和告警

#### 设置监控
```bash
# 启用 Cloud Monitoring
gcloud monitoring services create stockwise

# 创建告警策略
gcloud alpha monitoring policies create \
  --notification-channels=your-channel-id \
  --condition-display-name="High Error Rate" \
  --condition-filter='metric.type="run.googleapis.com/request_count" resource.type="cloud_run_revision"'
```

### 🔄 CI/CD 集成

#### GitHub Actions 自动部署
```yaml
name: Deploy to Cloud Run
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Google Cloud
      uses: google-github-actions/setup-gcloud@v0.2.0
    - name: Deploy to Cloud Run
      run: |
        gcloud builds submit --tag gcr.io/$PROJECT_ID/stockwise
        gcloud run deploy stockwise --image gcr.io/$PROJECT_ID/stockwise --allow-unauthenticated
```

### 🛠️ 故障排除

#### 常见问题
1. **部署失败**: 检查项目权限和 API 启用状态
2. **访问错误**: 确认 `--allow-unauthenticated` 标志
3. **环境变量**: 使用 `gcloud run services update` 更新

#### 调试命令
```bash
# 查看详细错误信息
gcloud builds log --project=your-project-id $(gcloud builds list --limit=1 --format='value(ID)')

# 测试本地运行
docker build -f Dockerfile.cloudrun -t stockwise-cloudrun .
docker run -p 8080:8080 -e CLOVER_API_KEY=test -e MERCHANT_ID=test stockwise-cloudrun
```

### 📞 支持和文档

- **Google Cloud Run 文档**: https://cloud.google.com/run/docs
- **定价详情**: https://cloud.google.com/run/pricing
- **配额和限制**: https://cloud.google.com/run/quotas
