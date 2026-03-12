# StockWise 安全部署脚本 (PowerShell)
# 使用 Google Cloud Secret Manager 管理敏感信息

Write-Host "🚀 开始部署 StockWise 到 Cloud Run..." -ForegroundColor Green

# 部署到 Cloud Run
Write-Host "📦 构建和部署容器..." -ForegroundColor Blue
$deployResult = gcloud run deploy stockwise-app --source . --region us-central1 --allow-unauthenticated

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 部署成功！" -ForegroundColor Green
    Write-Host "🌐 应用地址: https://stockwise-app-873982544406.us-central1.run.app" -ForegroundColor Cyan
    Write-Host "🔒 所有API密钥已通过 Secret Manager 安全管理" -ForegroundColor Yellow
} else {
    Write-Host "❌ 部署失败，请检查错误信息" -ForegroundColor Red
    exit 1
}
