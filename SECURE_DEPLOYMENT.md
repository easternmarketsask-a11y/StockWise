# StockWise 安全部署指南

## 🔐 安全架构

StockWise 现在使用 Google Cloud Secret Manager 管理所有敏感信息，确保 API 密钥安全。

### 存储的密钥
- `clover-api-key` - Clover POS API 密钥
- `merchant-id` - Clover 商户 ID  
- `anthropic-api-key` - Anthropic AI 密钥
- `gemini-api-key` - Google Gemini AI 密钥（可选）

## 🚀 一键部署

### 方法 1: 使用部署脚本
```bash
# Linux/Mac
./deploy_secure.sh

# Windows PowerShell
./deploy_secure.ps1
```

### 方法 2: 直接命令
```bash
gcloud run deploy stockwise-app --source . --region us-central1 --allow-unauthenticated
```

## 🔧 密钥管理

### 更新 API 密钥
```bash
# 更新 Clover API 密钥
echo "your-new-clover-api-key" | gcloud secrets versions add clover-api-key --data-file=-

# 更新 Anthropic API 密钥  
echo "your-new-anthropic-api-key" | gcloud secrets versions add anthropic-api-key --data-file=-

# 更新 Gemini API 密钥
echo "your-new-gemini-api-key" | gcloud secrets versions add gemini-api-key --data-file=-
```

### 查看密钥状态
```bash
gcloud secrets list
gcloud secrets versions list clover-api-key
```

## 📋 部署检查清单

- [ ] 代码已提交到 Git
- [ ] Secret Manager 中的密钥是最新的
- [ ] 运行部署命令
- [ ] 访问 https://stockwise-app-873982544406.us-central1.run.app 验证功能
- [ ] 测试 "🔄 同步Clover商品" 功能

## 🛡️ 安全优势

1. **零暴露**: API 密钥不在环境变量中暴露
2. **集中管理**: 所有敏感信息在 Secret Manager 中统一管理
3. **访问控制**: 基于角色的权限管理
4. **审计日志**: 完整的密钥访问记录
5. **自动轮换**: 支持密钥自动轮换

## 🔄 回滚

如需回滚到之前版本：
```bash
gcloud run services update-traffic stockwise-app --region us-central1 --to-revisions stockwise-app-00070-grd=100
```

## 📞 支持

如遇到部署问题：
1. 检查 Secret Manager 权限
2. 查看 Cloud Build 日志
3. 验证 Cloud Run 服务状态
