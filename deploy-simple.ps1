# Simple deployment script for StockWise with Anthropic API
Write-Host "Starting StockWise deployment..." -ForegroundColor Green

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "ERROR: .env file not found" -ForegroundColor Red
    exit 1
}

# Load environment variables
Get-Content .env | Where-Object { $_ -match "=" } | ForEach-Object {
    $name, $value = $_.Split('=', 2)
    [System.Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), "Process")
}

# Check required variables
if (-not $env:CLOVER_API_KEY -or -not $env:MERCHANT_ID -or -not $env:ANTHROPIC_API_KEY) {
    Write-Host "ERROR: Missing required API keys" -ForegroundColor Red
    exit 1
}

# Set your project ID here
$PROJECT_ID = "your-gcp-project-id"
$SERVICE_NAME = "stockwise-anthropic"

Write-Host "Building Docker image..." -ForegroundColor Blue
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME --project=$PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host "Deploying to Cloud Run..." -ForegroundColor Blue
    gcloud run deploy $SERVICE_NAME --image gcr.io/$PROJECT_ID/$SERVICE_NAME --platform managed --region us-central1 --allow-unauthenticated --set-env-vars "CLOVER_API_KEY=$env:CLOVER_API_KEY,MERCHANT_ID=$env:MERCHANT_ID,ANTHROPIC_API_KEY=$env:ANTHROPIC_API_KEY" --port 8080 --memory 512Mi --cpu 1 --timeout 300
    
    if ($LASTEXITCODE -eq 0) {
        $SERVICE_URL = gcloud run services describe $SERVICE_NAME --platform managed --region us-central1 --format 'value(status.url)'
        Write-Host "Deployment successful!" -ForegroundColor Green
        Write-Host "Application URL: $SERVICE_URL" -ForegroundColor Cyan
    } else {
        Write-Host "Deployment failed!" -ForegroundColor Red
    }
} else {
    Write-Host "Build failed!" -ForegroundColor Red
}
