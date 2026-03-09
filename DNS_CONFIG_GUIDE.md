# EasternMarket.ca DNS配置指南

## 🌐 域名配置步骤

### 步骤1：部署应用
```bash
# 使用新的域名部署脚本
cd d:\Market_App\StockWise\stockwise_final
chmod +x deploy-with-domain.sh
./deploy-with-domain.sh
```

### 步骤2：DNS配置

登录你的域名管理面板，添加以下记录：

#### 方案A：使用Google托管DNS (推荐)
```
Type: CNAME
Name: @ 
Value: ghs.googlehosted.com.
TTL: 3600
```

#### 方案B：使用A记录
```
Type: A
Name: @
Value: [需要获取Cloud Run负载均衡器IP]
TTL: 300
```

### 步骤3：验证配置

#### 检查域名映射状态
```bash
gcloud run domain-mappings list --region=us-central1
```

#### 检查SSL证书
```bash
gcloud run domain-mappings describe easternmarket.ca --region=us-central1
```

#### 测试访问
```bash
# 检查HTTP响应
curl -I https://easternmarket.ca

# 检查HTTPS重定向
curl -L https://easternmarket.ca
```

## 🔧 常见问题解决

### 问题1：DNS传播慢
- **等待时间**：通常5-15分钟，最长可能24小时
- **检查工具**：使用 `nslookup easternmarket.ca` 验证

### 问题2：SSL证书未生效
- **自动颁发**：Google会自动为验证域名颁发SSL证书
- **检查状态**：`gcloud run domain-mappings describe easternmarket.ca`

### 问题3：访问404错误
- **检查服务状态**：`gcloud run services describe stockwise --region=us-central1`
- **检查域名映射**：确认域名正确映射到服务

## 📋 域名管理命令

### 查看所有域名映射
```bash
gcloud run domain-mappings list --region=us-central1
```

### 删除域名映射
```bash
gcloud run domain-mappings delete easternmarket.ca --region=us-central1
```

### 更新域名映射
```bash
gcloud run domain-mappings update easternmarket.ca \
  --region=us-central1 \
  --service=stockwise
```

## 🚀 高级配置

### 子域名配置
```bash
# API子域名
gcloud run domain-mappings create stockwise \
  --domain=api.easternmarket.ca \
  --region=us-central1

# 管理后台子域名  
gcloud run domain-mappings create stockwise-admin \
  --domain=admin.easternmarket.ca \
  --region=us-central1
```

### 流量分配
```bash
# 分配流量到不同版本
gcloud run services update-traffic stockwise \
  --region=us-central1 \
  --to-revisions=stockwise-00001-abc=50,stockwise-00002-def=50
```

## 📞 支持资源

- **Google Cloud Run文档**: https://cloud.google.com/run/docs/mapping-custom-domains
- **DNS配置指南**: https://cloud.google.com/run/docs/mapping-custom-domains#steps
- **SSL证书管理**: https://cloud.google.com/run/docs/mapping-custom-domains#certificates

---

⚡ **完成后你的应用将可以通过 https://easternmarket.ca 永久访问！**
