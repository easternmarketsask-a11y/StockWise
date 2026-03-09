# StockWise Cloud Run 部署脚本
Write-Host "🚀 开始部署 StockWise 到 Google Cloud Run..." -ForegroundColor Green

# 设置项目变量
$PROJECT_ID = "stockwise-486801"
$SERVICE_NAME = "stockwise-app"
$REGION = "us-central1"

# 检查 gcloud CLI
try {
    gcloud version | Out-Null
    Write-Host "✅ Google Cloud CLI 已安装" -ForegroundColor Green
} catch {
    Write-Host "❌ Google Cloud CLI 未安装" -ForegroundColor Red
    Write-Host "📥 请访问: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# 检查 .env 文件
if (Test-Path .env) {
    Write-Host "🔑 从 .env 文件加载环境变量..." -ForegroundColor Yellow
    
    # 读取 .env 文件
    $envContent = Get-Content .env | Where-Object { $_ -notmatch '^#' -and $_.Trim() -ne '' }
    foreach ($line in $envContent) {
        $key, $value = $line.Split('=', 2)
        [System.Environment]::SetEnvironmentVariable($key.Trim(), $value.Trim(), "Process")
    }
    
    if (-not $env:CLOVER_API_KEY -or -not $env:MERCHANT_ID) {
        Write-Host "❌ .env 文件中缺少必要的 API Keys" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ API Keys 验证通过" -ForegroundColor Green
} else {
    Write-Host "❌ 未找到 .env 文件" -ForegroundColor Red
    exit 1
}

# 1. 构建 Docker 镜像
Write-Host "📦 构建 Docker 镜像..." -ForegroundColor Blue
try {
    gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME --project=$PROJECT_ID
    Write-Host "✅ 镜像构建成功" -ForegroundColor Green
} catch {
    Write-Host "❌ 构建失败" -ForegroundColor Red
    exit 1
}

# 2. 部署到 Cloud Run
Write-Host "🌐 部署到 Cloud Run..." -ForegroundColor Blue
$envVars = "CLOVER_API_KEY=$($env:CLOVER_API_KEY),MERCHANT_ID=$($env:MERCHANT_ID)"

if ($env:ANTHROPIC_API_KEY) {
    $envVars += ",ANTHROPIC_API_KEY=$($env:ANTHROPIC_API_KEY)"
    Write-Host "🤖 使用 Anthropic Claude AI" -ForegroundColor Cyan
} elseif ($env:GEMINI_API_KEY) {
    $envVars += ",GEMINI_API_KEY=$($env:GEMINI_API_KEY)"
    Write-Host "🤖 使用 Google Gemini AI" -ForegroundColor Cyan
}

try {
    gcloud run deploy $SERVICE_NAME `
      --image gcr.io/$PROJECT_ID/$SERVICE_NAME `
      --platform managed `
      --region $REGION `
      --allow-unauthenticated `
      --set-env-vars $envVars `
      --port 8080 `
      --memory 512Mi `
      --cpu 1 `
      --timeout 300
      
    Write-Host "✅ 部署成功" -ForegroundColor Green
} catch {
    Write-Host "❌ 部署失败" -ForegroundColor Red
    exit 1
}

# 3. 获取服务 URL
try {
    $SERVICE_URL = gcloud run services describe $SERVICE_NAME `
      --platform managed `
      --region $REGION `
      --format 'value(status.url)'

    Write-Host "✅ 部署完成！" -ForegroundColor Green
    Write-Host "🌐 应用地址: $SERVICE_URL" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📊 管理命令:" -ForegroundColor Yellow
    Write-Host "   查看日志: gcloud logs tail $SERVICE_NAME --platform managed --region $REGION" -ForegroundColor White
    Write-Host "   更新部署: gcloud run services update $SERVICE_NAME --platform managed --region $REGION" -ForegroundColor White
} catch {
    Write-Host "❌ 获取服务 URL 失败" -ForegroundColor Red
}
