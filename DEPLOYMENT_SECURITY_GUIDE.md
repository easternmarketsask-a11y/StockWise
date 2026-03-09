# 🔐 StockWise 安全部署指南

## 📋 概述

本指南提供两种安全的部署方式，确保你的 API Keys 不会泄露：

1. **推荐方式** - 环境变量部署（平衡安全性和易用性）
2. **企业级方式** - Secret Manager 部署（最高安全级别）

## 🚀 方式 1: 环境变量部署（推荐）

### 前置要求
- Google Cloud 账户和项目
- Google Cloud CLI 已安装
- 有效的 API Keys

### 步骤 1: 准备环境变量文件

```bash
# 1. 复制模板
cp .env.example .env

# 2. 编辑 .env 文件，填入真实的 API Keys
nano .env
```

**.env 文件示例：**
```bash
# Clover API 配置
CLOVER_API_KEY=your_actual_clover_api_key
MERCHANT_ID=your_actual_merchant_id

# Google Gemini AI 配置  
GEMINI_API_KEY=your_actual_gemini_api_key

# 可选配置
API_TIMEOUT=30
CACHE_TTL=1800
```

### 步骤 2: 配置 Google Cloud

```bash
# 1. 登录 Google Cloud
gcloud auth login

# 2. 设置项目 ID（替换为你的项目）
gcloud config set project your-project-id

# 3. 设置默认区域
gcloud config set run/region us-central1
```

### 步骤 3: 安全部署

```bash
# 使用安全部署脚本
./deploy-secure-env.sh
```

**脚本会自动：**
- ✅ 验证 .env 文件存在
- ✅ 检查必要的 API Keys
- ✅ 构建 Docker 镜像
- ✅ 部署到 Cloud Run
- ✅ 安全设置环境变量

## 🔒 方式 2: Secret Manager 部署（企业级）

### 前置要求
- 启用 Secret Manager API
- 适当的 IAM 权限

### 步骤 1: 初始化 Secrets

```bash
# 运行安全初始化脚本
./setup-secrets.sh
```

**脚本会：**
- 🔐 安全创建 secrets
- 🔑 手动输入 API Keys（无硬编码）
- 🔓 配置访问权限

### 步骤 2: 部署应用

```bash
# 使用 Secret Manager 部署
./deploy-secure.sh
```

## 🛡️ 安全最佳实践

### ✅ 推荐做法
- ✅ 使用环境变量或 Secret Manager
- ✅ 将 `.env` 添加到 `.gitignore`
- ✅ 定期轮换 API Keys
- ✅ 监控 Cloud Run 日志
- ✅ 使用最小权限原则

### ❌ 避免做法
- ❌ 在代码中硬编码 API Keys
- ❌ 将 API Keys 提交到版本控制
- ❌ 在日志中打印敏感信息
- ❌ 在前端代码中使用 API Keys

## 📊 部署后管理

### 查看部署状态
```bash
# 查看服务详情
gcloud run services describe stockwise --region us-central1

# 查看日志
gcloud logs tail stockwise --region us-central1
```

### 更新部署
```bash
# 环境变量方式
./deploy-secure-env.sh

# Secret Manager 方式
./deploy-secure.sh
```

### 更新 API Keys
```bash
# 环境变量方式：编辑 .env 文件后重新部署
nano .env
./deploy-secure-env.sh

# Secret Manager 方式：更新 secret 版本
echo "new_key" | gcloud secrets versions add clover-api-key --data-file=-
```

## 🆘 故障排除

### 常见问题

1. **"未找到 .env 文件"**
   ```bash
   cp .env.example .env
   nano .env  # 填入 API Keys
   ```

2. **"权限被拒绝"**
   ```bash
   gcloud auth login
   gcloud config set project your-project-id
   ```

3. **"部署失败"**
   ```bash
   # 检查 API Keys 格式
   gcloud builds log --project=your-project-id $(gcloud builds list --limit=1 --format='value(ID)')
   ```

4. **"环境变量未生效"**
   ```bash
   # 验证环境变量
   gcloud run services describe stockwise --region us-central1 --format "value(spec.template.spec.containers[0].env)"
   ```

## 💰 成本估算

### Cloud Run 免费额度
- **每月 180,000 vCPU-秒**
- **每月 1 GB 出站流量**
- **每月 360,000 内存-GB秒**

### StockWise 预估成本
- **轻量使用**: $0-5/月
- **中等使用**: $5-20/月
- **重度使用**: $20-50/月

### Secret Manager 成本
- **每月 6 美元** (10,000 次访问)
- **额外访问**: $0.03/10,000 次

## 📞 获取帮助

- **Google Cloud Run 文档**: https://cloud.google.com/run/docs
- **Secret Manager 文档**: https://cloud.google.com/secret-manager
- **定价详情**: https://cloud.google.com/run/pricing

---

**🔐 记住：安全永远是第一优先级！**
