# StockWise 简化部署脚本
Write-Host "🚀 开始部署 StockWise 到 Cloud Run" -ForegroundColor Green

$PROJECT_ID = "stockwise-486801"
$SERVICE_NAME = "stockwise-anthropic"
$REGION = "us-central1"

# 检查环境变量
Write-Host "🔑 检查环境变量..." -ForegroundColor Yellow
if (-not (Test-Path .env)) {
    Write-Host "❌ 未找到 .env 文件" -ForegroundColor Red
    exit 1
}

# 读取环境变量
Get-Content .env | Where-Object { $_ -notmatch '^#' -and $_.Trim() -ne '' } | ForEach-Object {
    $key, $value = $_.Split('=', 2)
    [System.Environment]::SetEnvironmentVariable($key.Trim(), $value.Trim(), "Process")
}

if (-not $env:CLOVER_API_KEY -or -not $env:MERCHANT_ID -or -not $env:ANTHROPIC_API_KEY) {
    Write-Host "❌ 缺少必要的 API Keys" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 环境变量验证通过" -ForegroundColor Green

# 构建镜像
Write-Host "📦 构建 Docker 镜像..." -ForegroundColor Blue
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME --project=$PROJECT_ID

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 构建失败" -ForegroundColor Red
    exit 1
}

# 部署到 Cloud Run
Write-Host "🌐 部署到 Cloud Run..." -ForegroundColor Blue
gcloud run deploy $SERVICE_NAME --image gcr.io/$PROJECT_ID/$SERVICE_NAME --platform managed --region $REGION --allow-unauthenticated --set-env-vars "CLOVER_API_KEY=$env:CLOVER_API_KEY,MERCHANT_ID=$env:MERCHANT_ID,ANTHROPIC_API_KEY=$env:ANTHROPIC_API_KEY" --port 8080 --memory 512Mi --cpu 1 --timeout 300

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 部署失败" -ForegroundColor Red
    exit 1
}

# 获取服务 URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)'

Write-Host "✅ 部署完成！" -ForegroundColor Green
Write-Host "🌐 应用地址: $SERVICE_URL" -ForegroundColor Cyan
Write-Host "🤖 AI 提供商: Anthropic Claude" -ForegroundColor Cyan
