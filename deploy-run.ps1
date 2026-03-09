# StockWise Cloud Run 快速部署
Write-Host "🚀 StockWise Cloud Run 部署开始" -ForegroundColor Green

$PROJECT_ID = "stockwise-486801"
$SERVICE_NAME = "stockwise-app"
$REGION = "us-central1"

Write-Host "📋 项目配置:" -ForegroundColor Yellow
Write-Host "   项目ID: $PROJECT_ID" -ForegroundColor White
Write-Host "   服务名: $SERVICE_NAME" -ForegroundColor White
Write-Host "   区域: $REGION" -ForegroundColor White

# 检查 .env 文件
if (-not (Test-Path .env)) {
    Write-Host "❌ 未找到 .env 文件" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 找到 .env 文件" -ForegroundColor Green

# 设置环境变量
$envContent = Get-Content .env | Where-Object { $_ -notmatch '^#' -and $_.Trim() -ne '' }
foreach ($line in $envContent) {
    $key, $value = $line.Split('=', 2)
    [System.Environment]::SetEnvironmentVariable($key.Trim(), $value.Trim(), "Process")
}

Write-Host "🔑 API Keys 已加载" -ForegroundColor Green

# 构建 Docker 镜像
Write-Host "📦 构建 Docker 镜像..." -ForegroundColor Blue
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME --project=$PROJECT_ID

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 构建失败" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 镜像构建成功" -ForegroundColor Green

# 准备环境变量
$envVars = "CLOVER_API_KEY=$($env:CLOVER_API_KEY),MERCHANT_ID=$($env:MERCHANT_ID)"

if ($env:ANTHROPIC_API_KEY) {
    $envVars += ",ANTHROPIC_API_KEY=$($env:ANTHROPIC_API_KEY)"
    Write-Host "🤖 使用 Anthropic Claude AI" -ForegroundColor Cyan
} elseif ($env:GEMINI_API_KEY) {
    $envVars += ",GEMINI_API_KEY=$($env:GEMINI_API_KEY)"
    Write-Host "🤖 使用 Google Gemini AI" -ForegroundColor Cyan
}

# 部署到 Cloud Run
Write-Host "🌐 部署到 Cloud Run..." -ForegroundColor Blue
gcloud run deploy $SERVICE_NAME --image gcr.io/$PROJECT_ID/$SERVICE_NAME --platform managed --region $REGION --allow-unauthenticated --set-env-vars $envVars --port 8080 --memory 512Mi --cpu 1 --timeout 300

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 部署失败" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 部署成功" -ForegroundColor Green

# 获取服务 URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)'

Write-Host ""
Write-Host "🎉 部署完成！" -ForegroundColor Green
Write-Host "🌐 应用地址: $SERVICE_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 常用命令:" -ForegroundColor Yellow
Write-Host "   查看日志: gcloud logs tail $SERVICE_NAME --platform managed --region $REGION" -ForegroundColor White
Write-Host "   更新部署: gcloud run services update $SERVICE_NAME --platform managed --region $REGION" -ForegroundColor White
