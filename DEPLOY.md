# StockWise 部署指南

## 🚀 快速部署

StockWise 使用 Google Cloud Run 进行部署，一键部署脚本已准备好。

### 前置要求

1. **安装 Google Cloud SDK**
   ```bash
   # Windows
   # 下载并安装 Google Cloud SDK
   # 运行 gcloud init 配置项目
   ```

2. **配置环境变量**
   ```bash
   # 复制环境变量模板
   cp .env.example .env
   
   # 编辑 .env 文件，填入真实的API密钥
   # CLOVER_API_KEY=your_real_clover_api_key
   # MERCHANT_ID=your_real_merchant_id
   # ANTHROPIC_API_KEY=your_anthropic_api_key  # 可选
   # GEMINI_API_KEY=your_gemini_api_key        # 可选
   ```

### 一键部署

```powershell
# Windows PowerShell
.\deploy.ps1
```

脚本会自动：
- ✅ 验证环境配置
- ✅ 构建 Docker 镜像
- ✅ 部署到 Cloud Run
- ✅ 配置环境变量
- ✅ 返回应用地址

## 📋 部署信息

- **项目ID:** stockwise-486801
- **服务名:** stockwise-app
- **区域:** us-central1
- **端口:** 8080
- **内存:** 512Mi
- **超时:** 300秒

## 🔧 手动部署（可选）

如果需要手动部署：

```bash
# 1. 构建 Docker 镜像
gcloud builds submit --tag gcr.io/stockwise-486801/stockwise-app --project=stockwise-486801

# 2. 部署到 Cloud Run
gcloud run deploy stockwise-app \
    --image gcr.io/stockwise-486801/stockwise-app \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "CLOVER_API_KEY=your_key,MERCHANT_ID=your_id,ANTHROPIC_API_KEY=your_key" \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300
```

## 📱 访问应用

部署完成后，脚本会输出应用地址，格式类似：
```
https://stockwise-app-xxxxxx.us-central1.run.app
```

## 🛠️ 常用命令

```bash
# 查看应用日志
gcloud logs tail stockwise-app --platform managed --region us-central1

# 更新部署
gcloud run services update stockwise-app --platform managed --region us-central1

# 查看服务状态
gcloud run services describe stockwise-app --platform managed --region us-central1

# 删除服务（如需）
gcloud run services delete stockwise-app --platform managed --region us-central1
```

## 🔒 环境变量说明

| 变量名 | 必需 | 说明 |
|--------|------|------|
| `CLOVER_API_KEY` | ✅ | Clover POS API 密钥 |
| `MERCHANT_ID` | ✅ | Clover 商户 ID |
| `ANTHROPIC_API_KEY` | ❌ | Anthropic Claude AI 密钥 |
| `GEMINI_API_KEY` | ❌ | Google Gemini AI 密钥 |

**注意：** 至少需要配置一个 AI API 密钥才能使用 AI 功能。

## 🐛 故障排除

### 常见问题

1. **"未找到 gcloud CLI"**
   - 确保已安装 Google Cloud SDK
   - 重启 PowerShell 或重新打开终端

2. **"API密钥验证失败"**
   - 检查 .env 文件中的密钥是否为真实值
   - 确保没有 `your_` 前缀的占位符

3. **"构建失败"**
   - 检查网络连接
   - 确保项目 ID 正确

4. **"部署失败"**
   - 检查 Cloud Run 配额
   - 确保区域可用

### 获取帮助

```bash
# 查看 Cloud Run 日志
gcloud logs tail stockwise-app --platform managed --region us-central1 --limit 50

# 查看构建日志
gcloud builds list --project=stockwise-486801 --limit 5
```

## 📈 监控

部署后可以通过以下方式监控：

1. **Google Cloud Console** - 查看服务状态和指标
2. **Cloud Logging** - 查看应用日志
3. **Cloud Monitoring** - 监控性能指标

---

**版本：** 2.2.0  
**更新日期：** 2026年3月10日  
**部署方式：** Google Cloud Run
