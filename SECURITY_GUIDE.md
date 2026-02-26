# 🔐 API Keys 安全配置指南

## 📋 概述

StockWise 提供了三种 API Keys 管理方式，从基础到企业级安全：

1. **基础方式** - `.env` 文件（适合开发环境）
2. **推荐方式** - 环境变量（适合 CI/CD）
3. **企业级** - Google Secret Manager（适合生产环境）

## 🔑 需要的 API Keys

- **Clover API Key**: `c7e0ed05-ecc2-0c33-25b1`
- **Merchant ID**: `SN4FE813EDA51`
- **Gemini API Key**: `AIzaSyD2orlisbm1SfbS3qH`

## 🛠️ 配置方法

### 方法 1: .env 文件（开发环境）

```bash
# 1. 创建 .env 文件
cp .env.example .env

# 2. 编辑 .env 文件，填入你的 API Keys
nano .env

# 3. 使用快速部署
./quick-deploy.sh
```

**优点**: 简单快速
**缺点**: 文件可能意外提交到版本控制

### 方法 2: 环境变量（推荐）

```bash
# 1. 导出环境变量
export CLOVER_API_KEY="your_key_here"
export MERCHANT_ID="your_merchant_id"  
export GEMINI_API_KEY="your_gemini_key"

# 2. 部署时传入
gcloud run deploy stockwise-app \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars CLOVER_API_KEY=${CLOVER_API_KEY} \
  --set-env-vars MERCHANT_ID=${MERCHANT_ID} \
  --set-env-vars GEMINI_API_KEY=${GEMINI_API_KEY}
```

**优点**: CI/CD 友好，不会意外提交
**缺点**: 需要每次部署时设置

### 方法 3: Google Secret Manager（生产环境推荐）

#### 初始化设置

```bash
# 1. 运行初始化脚本
./setup-secrets.sh
```

#### 安全部署

```bash
# 2. 使用安全部署脚本
./deploy-secure.sh
```

**优点**: 
- 🔒 企业级安全
- 🔄 自动轮换支持
- 👥 团队访问控制
- 📊 审计日志

**缺点**: 需要额外配置步骤

## 🔄 从现有部署迁移

如果你已经有硬编码 keys 的部署：

```bash
# 1. 重新部署（使用新脚本）
./deploy-secure.sh

# 2. 验证部署
gcloud run services describe eastern-market-api --region us-central1
```

## 🚨 安全最佳实践

### ✅ 推荐做法

- ✅ 使用 Secret Manager 管理生产环境 keys
- ✅ 定期轮换 API keys
- ✅ 使用最小权限原则
- ✅ 监控 API 使用情况
- ✅ 将 `.env` 添加到 `.gitignore`

### ❌ 避免做法

- ❌ 在代码中硬编码 keys
- ❌ 将 keys 提交到版本控制
- ❌ 在日志中打印 keys
- ❌ 在前端代码中使用 keys

## 🔍 验证配置

```bash
# 检查环境变量是否正确设置
gcloud run services describe eastern-market-api \
  --region us-central1 \
  --format "value(spec.template.spec.containers[0].env)"

# 检查 secrets 是否正确配置
gcloud secrets list --project=eastern-market-app
```

## 🆘 故障排除

### 常见问题

1. **"未找到 .env 文件"**
   - 解决: `cp .env.example .env` 并填入 keys

2. **"权限被拒绝"**
   - 解决: 检查 Secret Manager 权限设置

3. **"部署失败"**
   - 解决: 验证 keys 格式和有效性

### 获取帮助

```bash
# 查看 Cloud Run 日志
gcloud logging read "resource.type=cloud_run_revision" --limit 10

# 查看 Secret Manager 状态
gcloud secrets describe clover-api-key --project=eastern-market-app
```

---

**📞 如需帮助，请查看 [Cloud Run 指南](CLOUD_RUN_GUIDE.md) 或联系技术支持。**
