# Setup script for Docker Desktop on Windows with WSL2
Write-Host "Setting up Docker Desktop for Gnosis Docker..." -ForegroundColor Green

# Check if Docker Desktop is running
$dockerProcess = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
if (-not $dockerProcess) {
    Write-Host "Docker Desktop is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

Write-Host "`nIMPORTANT: Docker Desktop Configuration" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Please ensure Docker Desktop is configured with these settings:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Open Docker Desktop Settings" -ForegroundColor White
Write-Host "2. Go to 'General' tab" -ForegroundColor White
Write-Host "3. Enable 'Expose daemon on tcp://localhost:2375 without TLS'" -ForegroundColor White
Write-Host "   (Note: Only enable this for local development!)" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Go to 'Resources' -> 'WSL Integration'" -ForegroundColor White
Write-Host "5. Enable integration with your default WSL2 distro" -ForegroundColor White
Write-Host ""
Write-Host "6. Click 'Apply & Restart'" -ForegroundColor White
Write-Host ""

# Test Docker connection
Write-Host "Testing Docker connection..." -ForegroundColor Cyan
try {
    docker version | Out-Null
    Write-Host "✓ Docker CLI is working" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker CLI is not working properly" -ForegroundColor Red
}

# Test TCP endpoint
Write-Host "`nTesting TCP endpoint..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:2375/version" -Method GET -UseBasicParsing -ErrorAction Stop
    Write-Host "✓ Docker TCP endpoint is accessible" -ForegroundColor Green
    $version = ($response.Content | ConvertFrom-Json).Version
    Write-Host "  Docker version: $version" -ForegroundColor Gray
} catch {
    Write-Host "✗ Docker TCP endpoint is NOT accessible" -ForegroundColor Red
    Write-Host "  Please enable 'Expose daemon on tcp://localhost:2375' in Docker Desktop settings" -ForegroundColor Yellow
}

Write-Host "`nSetup check complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Ensure Docker Desktop settings are configured as shown above" -ForegroundColor White
Write-Host "2. Run: docker-compose up --build" -ForegroundColor White
Write-Host "3. The service will be available at: http://localhost:5680" -ForegroundColor White
