# StockWise Anthropic API 部署脚本 (PowerShell)
# 使用 ANTHROPIC_API_KEY 部署到 Cloud Run

Write-Host "🚀 StockWise Anthropic API 部署脚本" -ForegroundColor Green

# 设置项目变量 (请修改为你的实际配置)
$PROJECT_ID = "stockwise-486801"  # 🔧 请替换为你的 GCP 项目 ID
$SERVICE_NAME = "stockwise-anthropic"
$REGION = "us-central1"

# 检查 .env 文件
if (Test-Path .env) {
    Write-Host "🔑 从 .env 文件加载环境变量..." -ForegroundColor Yellow
    
    # 读取 .env 文件
    $envContent = Get-Content .env | Where-Object { $_ -notmatch '^#' -and $_.Trim() -ne '' }
    foreach ($line in $envContent) {
        $key, $value = $line.Split('=', 2)
        [System.Environment]::SetEnvironmentVariable($key.Trim(), $value.Trim(), "Process")
    }
    
    if (-not $env:CLOVER_API_KEY -or -not $env:MERCHANT_ID -or -not $env:ANTHROPIC_API_KEY) {
        Write-Host "❌ .env 文件中缺少必要的 API Keys" -ForegroundColor Red
        Write-Host "📋 请确保 .env 文件包含:" -ForegroundColor Yellow
        Write-Host "   - CLOVER_API_KEY" -ForegroundColor White
        Write-Host "   - MERCHANT_ID" -ForegroundColor White
        Write-Host "   - ANTHROPIC_API_KEY" -ForegroundColor White
        exit 1
    }
    
    Write-Host "✅ API Keys 验证通过" -ForegroundColor Green
    Write-Host "🤖 使用 Anthropic Claude AI" -ForegroundColor Cyan
} else {
    Write-Host "❌ 未找到 .env 文件" -ForegroundColor Red
    Write-Host "📋 请先创建 .env 文件:" -ForegroundColor Yellow
    Write-Host "   cp .env.example .env" -ForegroundColor White
    Write-Host "   然后编辑 .env 文件填入你的 API Keys" -ForegroundColor White
    exit 1
}

# 1. 构建 Docker 镜像
Write-Host "📦 构建 Docker 镜像..." -ForegroundColor Blue
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME --project=$PROJECT_ID

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 构建失败" -ForegroundColor Red
    exit 1
}

# 2. 部署到 Cloud Run
Write-Host "🌐 部署到 Cloud Run (使用 Anthropic API)..." -ForegroundColor Blue
gcloud run deploy $SERVICE_NAME `
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --set-env-vars "CLOVER_API_KEY=$env:CLOVER_API_KEY,MERCHANT_ID=$env:MERCHANT_ID,ANTHROPIC_API_KEY=$env:ANTHROPIC_API_KEY" `
  --port 8080 `
  --memory 512Mi `
  --cpu 1 `
  --timeout 300

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 部署失败" -ForegroundColor Red
    exit 1
}

# 3. 获取服务 URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME `
  --platform managed `
  --region $REGION `
  --format 'value(status.url)'

Write-Host "✅ Anthropic API 部署完成！" -ForegroundColor Green
Write-Host "🌐 应用地址: $SERVICE_URL" -ForegroundColor Cyan
Write-Host "🤖 AI 提供商: Anthropic Claude" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 管理命令:" -ForegroundColor Yellow
Write-Host "   查看日志: gcloud logs tail $SERVICE_NAME --platform managed --region $REGION" -ForegroundColor White
Write-Host "   更新部署: gcloud run services update $SERVICE_NAME --platform managed --region $REGION" -ForegroundColor White
Write-Host "   删除服务: gcloud run services delete $SERVICE_NAME --platform managed --region $REGION" -ForegroundColor White
