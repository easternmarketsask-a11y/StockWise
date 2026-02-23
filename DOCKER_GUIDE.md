# Docker 安装和部署指南
# StockWise 容器化部署完整流程

## 🔧 第一步：安装 Docker

### Windows 安装 Docker Desktop
1. 访问 [Docker Desktop 官网](https://www.docker.com/products/docker-desktop/)
2. 下载 Docker Desktop for Windows
3. 运行安装程序，重启计算机
4. 启动 Docker Desktop

### 验证安装
```powershell
docker --version
docker-compose --version
```

## 🐳 第二步：构建和部署

### 方法1：使用脚本自动部署
```powershell
# 设置环境变量
$env:CLOVER_API_KEY="你的API密钥"
$env:MERCHANT_ID="你的商户ID"

# 运行部署脚本
.\docker-deploy.sh
```

### 方法2：手动部署
```powershell
# 1. 构建镜像
docker build -t stockwise:latest .

# 2. 运行容器
docker run -d `
  --name stockwise `
  -p 8501:8501 `
  --restart unless-stopped `
  -e CLOVER_API_KEY="你的API密钥" `
  -e MERCHANT_ID="你的商户ID" `
  stockwise:latest
```

## 🌐 第三步：验证部署

### 检查容器状态
```powershell
docker ps
```

### 查看日志
```powershell
docker logs stockwise
```

### 访问应用
- 本地访问：http://localhost:8501
- 局域网访问：http://你的IP:8501

## 🔄 第四步：容器管理

### 停止容器
```powershell
docker stop stockwise
```

### 启动容器
```powershell
docker start stockwise
```

### 重新构建
```powershell
docker stop stockwise
docker rm stockwise
docker build -t stockwise:latest .
docker run -d --name stockwise -p 8501:8501 --restart unless-stopped -e CLOVER_API_KEY="你的API密钥" -e MERCHANT_ID="你的商户ID" stockwise:latest
```

## 🚀 生产环境部署

### 使用 docker-compose（推荐）
```powershell
# 创建生产环境配置
docker-compose -f docker-compose.yml up -d
```

### 配置反向代理（Nginx）
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 监控和维护

### 设置健康检查
```powershell
docker exec stockwise curl -f http://localhost:8501
```

### 备份数据
```powershell
docker exec stockwise tar -czf /backup/stockwise-backup.tar.gz /app
```

## 🔒 安全配置

### 防火墙设置
```powershell
# 仅允许特定IP访问
New-NetFirewallRule -DisplayName "StockWise" -Direction Inbound -Protocol TCP -LocalPort 8501 -RemoteAddress <允许的IP>
```

### SSL/TLS 配置
建议使用反向代理（如 Nginx）来处理 HTTPS

## 📞 故障排除

### 常见问题
1. **端口冲突**：修改 docker-compose.yml 中的端口映射
2. **权限问题**：确保 Docker 服务正在运行
3. **环境变量**：检查 .env 文件配置

### 调试命令
```powershell
# 进入容器
docker exec -it stockwise /bin/bash

# 查看实时日志
docker logs -f stockwise

# 检查资源使用
docker stats stockwise
```
