# Docker 部署快速启动脚本 (Windows PowerShell)

Write-Host "🐳 StockWise Docker 部署脚本" -ForegroundColor Green

# 检查 Docker 是否安装
try {
    docker --version | Out-Null
    Write-Host "✅ Docker 已安装" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker 未安装，请先安装 Docker Desktop" -ForegroundColor Red
    Write-Host "📥 下载地址: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# 设置环境变量（请修改为你的实际值）
$env:CLOVER_API_KEY = Read-Host "请输入你的 Clover API Key"
$env:MERCHANT_ID = Read-Host "请输入你的 Merchant ID"

# 构建镜像
Write-Host "📦 构建 Docker 镜像..." -ForegroundColor Blue
docker build -t stockwise:latest .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 镜像构建失败" -ForegroundColor Red
    exit 1
}

# 停止现有容器
Write-Host "🛑 停止现有容器..." -ForegroundColor Blue
docker stop stockwise 2>$null
docker rm stockwise 2>$null

# 运行新容器
Write-Host "🚀 启动新容器..." -ForegroundColor Blue
docker run -d --name stockwise -p 8501:8501 --restart unless-stopped -e CLOVER_API_KEY=$env:CLOVER_API_KEY -e MERCHANT_ID=$env:MERCHANT_ID stockwise:latest

# 检查容器状态
Write-Host "📊 检查容器状态..." -ForegroundColor Blue
Start-Sleep -Seconds 3
$containerStatus = docker ps --filter "name=stockwise" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

if ($containerStatus -match "stockwise") {
    Write-Host "✅ 容器启动成功！" -ForegroundColor Green
    Write-Host "🌐 访问地址: http://localhost:8501" -ForegroundColor Green
    Write-Host "📊 查看日志: docker logs -f stockwise" -ForegroundColor Blue
    Write-Host "🛑 停止容器: docker stop stockwise" -ForegroundColor Yellow
} else {
    Write-Host "❌ 容器启动失败" -ForegroundColor Red
    Write-Host "📝 查看错误日志:" -ForegroundColor Yellow
    docker logs stockwise
}

# 显示实时日志（可选）
$showLogs = Read-Host "是否查看实时日志? (y/n)"
if ($showLogs -eq "y") {
    docker logs -f stockwise
}
