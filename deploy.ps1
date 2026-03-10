# StockWise Cloud Run 部署脚本
Write-Host "🚀 StockWise Cloud Run 部署开始" -ForegroundColor Green

# 配置
$PROJECT_ID = "stockwise-486801"
$SERVICE_NAME = "stockwise-app"
$REGION = "us-central1"

# 检查 gcloud
$gcloud = (Get-Command gcloud.cmd -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
if (-not $gcloud) {
    $gcloud = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
}
if (-not (Test-Path $gcloud)) {
    Write-Host "❌ 未找到 gcloud CLI，请安装 Google Cloud SDK" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 项目配置: $PROJECT_ID | $SERVICE_NAME | $REGION" -ForegroundColor Cyan

# 检查 .env 文件
if (-not (Test-Path .env)) {
    Write-Host "❌ 未找到 .env 文件" -ForegroundColor Red
    exit 1
}

# 加载环境变量
Get-Content .env | Where-Object { $_ -notmatch '^#' -and $_.Trim() -ne '' } | ForEach-Object {
    $key, $value = $_.Split('=', 2)
    [System.Environment]::SetEnvironmentVariable($key.Trim(), $value.Trim(), "Process")
}

# 验证必需的API密钥
if (-not $env:CLOVER_API_KEY -or $env:CLOVER_API_KEY -like 'your_*') {
    Write-Host "❌ 请在 .env 中配置真实的 CLOVER_API_KEY" -ForegroundColor Red
    exit 1
}
if (-not $env:MERCHANT_ID -or $env:MERCHANT_ID -like 'your_*') {
    Write-Host "❌ 请在 .env 中配置真实的 MERCHANT_ID" -ForegroundColor Red
    exit 1
}

Write-Host "✅ API密钥验证通过" -ForegroundColor Green

# 构建Docker镜像
Write-Host "📦 构建Docker镜像..." -ForegroundColor Blue
& $gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME --project=$PROJECT_ID --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 构建失败" -ForegroundColor Red
    exit 1
}

# 准备环境变量
$envVars = "CLOVER_API_KEY=$($env:CLOVER_API_KEY),MERCHANT_ID=$($env:MERCHANT_ID)"
if ($env:ANTHROPIC_API_KEY) {
    $envVars += ",ANTHROPIC_API_KEY=$($env:ANTHROPIC_API_KEY)"
    Write-Host "🤖 使用 Anthropic Claude AI" -ForegroundColor Cyan
} elseif ($env:GEMINI_API_KEY) {
    $envVars += ",GEMINI_API_KEY=$($env:GEMINI_API_KEY)"
    Write-Host "🤖 使用 Google Gemini AI" -ForegroundColor Cyan
}

# 部署到Cloud Run
Write-Host "🚀 部署到 Cloud Run..." -ForegroundColor Blue
& $gcloud run deploy $SERVICE_NAME `
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --set-env-vars $envVars `
    --port 8080 `
    --memory 512Mi `
    --cpu 1 `
    --timeout 300 `
    --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 部署失败" -ForegroundColor Red
    exit 1
}

# 获取服务URL
$SERVICE_URL = & $gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)' --quiet

Write-Host ""
Write-Host "🎉 部署成功！" -ForegroundColor Green
Write-Host "🌐 应用地址: $SERVICE_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 常用命令:" -ForegroundColor Yellow
Write-Host "   查看日志: gcloud logs tail $SERVICE_NAME --platform managed --region $REGION" -ForegroundColor White
Write-Host "   更新部署: gcloud run services update $SERVICE_NAME --platform managed --region $REGION" -ForegroundColor White
