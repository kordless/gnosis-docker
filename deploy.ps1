# Gnosis Docker Deployment Script
# Single script for all deployment targets: local, staging, production

param(
    [string]$Target = "local",  # local, staging, production
    [string]$Tag = "latest",
    [switch]$Rebuild = $false,
    [switch]$WhatIf = $false,
    [switch]$SkipTests = $false,
    [string]$ProjectPath = ""   # Optional: Path to project to deploy
)

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
$projectName = "gnosis-docker"

Write-Host "=== Gnosis Docker Deployment ===" -ForegroundColor Cyan
Write-Host "Target: $Target" -ForegroundColor White
Write-Host "Tag: $Tag" -ForegroundColor White
Write-Host "Project Root: $projectRoot" -ForegroundColor Gray

# Validate target
$validTargets = @("local", "staging", "production")
if ($Target -notin $validTargets) {
    Write-Error "Invalid target '$Target'. Must be one of: local, staging, production"
}

# Create logs directory
$logsDir = Join-Path $projectRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

# Run tests if not skipped
if (-not $SkipTests) {
    Write-Host "`n=== Running Tests ===" -ForegroundColor Yellow
    if (-not $WhatIf) {
        Push-Location $projectRoot
        try {
            python -m pytest tests/ -v
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Tests failed. Use -SkipTests to bypass."
            }
            Write-Host "✓ Tests passed" -ForegroundColor Green
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "[WOULD RUN] python -m pytest tests/ -v" -ForegroundColor Magenta
    }
}

# Build configuration
$imageName = switch ($Target) {
    "local" { $projectName }
    "staging" { "$projectName-staging" }
    "production" { $projectName }
}

$fullImageName = "${imageName}:${Tag}"

Write-Host "`n=== Building Docker Image ===" -ForegroundColor Green
Write-Host "Image: $fullImageName" -ForegroundColor White

# Generate timestamp for log file
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logFile = Join-Path $logsDir "build_${Target}_${timestamp}.log"

# Build arguments
$buildArgs = @(
    "build",
    "-t", $fullImageName,
    "."
)

if ($Rebuild) {
    $buildArgs += "--no-cache"
    Write-Host "Rebuilding from scratch (--no-cache)" -ForegroundColor Yellow
}

$buildArgs += "--progress=plain"


Write-Host "Build log: $logFile" -ForegroundColor Gray

if (-not $WhatIf) {
    Push-Location $projectRoot
    try {
        # Initialize log file
        @"
Gnosis Docker Build Log
=====================
Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Target: $Target
Tag: $Tag
Image: $fullImageName
=====================

"@ | Out-File -FilePath $logFile -Encoding UTF8

        # Build the image
        & docker @buildArgs 2>&1 | Tee-Object -FilePath $logFile -Append
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Docker build failed"
        }
        
        Write-Host "✓ Build completed successfully" -ForegroundColor Green
    } finally {
        Pop-Location
    }
} else {
    Write-Host "[WOULD RUN] docker $($buildArgs -join ' ')" -ForegroundColor Magenta
}

# Deploy based on target
Write-Host "`n=== Deployment ===" -ForegroundColor Green

switch ($Target) {
    "local" {
        Write-Host "Deploying locally with docker-compose..." -ForegroundColor White
        
        if (-not $WhatIf) {
            Push-Location $projectRoot
            try {
                # Stop existing containers
                Write-Host "Stopping existing containers..." -ForegroundColor Yellow
                & docker compose down
                
                # Start services
                Write-Host "Starting services..." -ForegroundColor White
                & docker compose up -d
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✓ Services started successfully" -ForegroundColor Green
                    Write-Host "✓ API available at: http://localhost:5680" -ForegroundColor Cyan
                    Write-Host ""
                    Write-Host "Useful commands:" -ForegroundColor Yellow
                    Write-Host "  View logs:     docker compose logs -f gnosis-docker" -ForegroundColor Gray
                    Write-Host "  Stop services: docker compose down" -ForegroundColor Gray
                    Write-Host "  Restart:       docker compose restart" -ForegroundColor Gray
                    
                    # Wait and health check
                    Write-Host "`nWaiting for service to start..." -ForegroundColor White
                    Start-Sleep -Seconds 3
                    
                    try {
                        $response = Invoke-WebRequest -Uri "http://localhost:5680/health" -UseBasicParsing -TimeoutSec 5
                        if ($response.StatusCode -eq 200) {
                            Write-Host "✓ Health check passed!" -ForegroundColor Green
                        }
                    } catch {
                        Write-Host "⚠ Health check failed - service may still be starting" -ForegroundColor Yellow
                    }
                }
            } finally {
                Pop-Location
            }
        } else {
            Write-Host "[WOULD RUN] docker compose down" -ForegroundColor Magenta
            Write-Host "[WOULD RUN] docker compose up -d" -ForegroundColor Magenta
        }
    }
    
    "staging" {
        Write-Host "Staging deployment (Google Cloud Run)" -ForegroundColor White
        
        # Load staging environment variables
        $envFile = Join-Path $projectRoot ".env.staging"
        if (-not (Test-Path $envFile)) {
            Write-Error "Staging environment file not found: $envFile"
        }
        
        # Read project ID from .env.staging
        $envContent = Get-Content $envFile -Raw
        if ($envContent -match 'GCP_PROJECT_ID=(.*)') {
            $projectId = $Matches[1].Trim()
        } else {
            Write-Error "GCP_PROJECT_ID not found in .env.staging"
        }
        
        $gcrImage = "gcr.io/$projectId/${imageName}:${Tag}"
        
        if (-not $WhatIf) {
            # Tag and push
            Write-Host "`nTagging image for GCR..." -ForegroundColor White
            & docker tag $fullImageName $gcrImage
            
            Write-Host "Configuring Docker auth..." -ForegroundColor White
            & gcloud auth configure-docker --quiet
            
            Write-Host "Pushing to GCR..." -ForegroundColor Yellow
            & docker push $gcrImage
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Image pushed to GCR" -ForegroundColor Green
                
                # Deploy to Cloud Run
                Write-Host "`nDeploying to Cloud Run (staging)..." -ForegroundColor White
                & gcloud run deploy $projectName-staging `
                    --image $gcrImage `
                    --platform managed `
                    --region us-central1 `
                    --memory 1Gi `
                    --cpu 1 `
                    --timeout 300 `
                    --concurrency 80 `
                    --port 5680 `
                    --env-vars-file $envFile `
                    --no-allow-unauthenticated `
                    --project $projectId
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✓ Deployed to Cloud Run (staging)" -ForegroundColor Green
                }
            }
        } else {
            Write-Host "[WOULD RUN] docker tag $fullImageName $gcrImage" -ForegroundColor Magenta
            Write-Host "[WOULD RUN] gcloud auth configure-docker" -ForegroundColor Magenta
            Write-Host "[WOULD RUN] docker push $gcrImage" -ForegroundColor Magenta
            Write-Host "[WOULD RUN] gcloud run deploy ..." -ForegroundColor Magenta
        }
    }
    
    "production" {
        Write-Host "Production deployment (Google Cloud Run)" -ForegroundColor White
        
        # Require explicit confirmation
        if (-not $WhatIf) {
            $confirm = Read-Host "Deploy to PRODUCTION? Type 'DEPLOY' to confirm"
            if ($confirm -ne "DEPLOY") {
                Write-Host "Production deployment cancelled" -ForegroundColor Yellow
                return
            }
        }
        
        # Similar to staging but with production config
        $envFile = Join-Path $projectRoot ".env.production"
        if (-not (Test-Path $envFile)) {
            Write-Error "Production environment file not found: $envFile"
        }
        
        # Read project ID
        $envContent = Get-Content $envFile -Raw
        if ($envContent -match 'GCP_PROJECT_ID=(.*)') {
            $projectId = $Matches[1].Trim()
        } else {
            Write-Error "GCP_PROJECT_ID not found in .env.production"
        }
        
        $gcrImage = "gcr.io/$projectId/${imageName}:${Tag}"
        
        if (-not $WhatIf) {
            # Tag and push
            & docker tag $fullImageName $gcrImage
            & gcloud auth configure-docker --quiet
            & docker push $gcrImage
            
            if ($LASTEXITCODE -eq 0) {
                # Deploy with production settings
                & gcloud run deploy $projectName `
                    --image $gcrImage `
                    --platform managed `
                    --region us-central1 `
                    --memory 2Gi `
                    --cpu 2 `
                    --timeout 300 `
                    --concurrency 100 `
                    --max-instances 10 `
                    --port 5680 `
                    --env-vars-file $envFile `
                    --no-allow-unauthenticated `
                    --project $projectId
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✓ Deployed to Cloud Run (production)" -ForegroundColor Green
                }
            }
        } else {
            Write-Host "[WOULD CONFIRM] Production deployment" -ForegroundColor Magenta
            Write-Host "[WOULD RUN] Full production deployment" -ForegroundColor Magenta
        }
    }
}

# Special project deployment feature
if ($ProjectPath) {
    Write-Host "`n=== Project Deployment ===" -ForegroundColor Cyan
    Write-Host "Deploying project: $ProjectPath" -ForegroundColor White
    
    if (-not $WhatIf) {
        # Call the API to trigger project build
        $body = @{
            project_path = $ProjectPath
            target = $Target
        } | ConvertTo-Json
        
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:5680/api/projects/deploy" `
                -Method Post `
                -ContentType "application/json" `
                -Body $body
            
            Write-Host "✓ Project deployment triggered" -ForegroundColor Green
            Write-Host $response.message -ForegroundColor White
        } catch {
            Write-Error "Failed to trigger project deployment: $_"
        }
    } else {
        Write-Host "[WOULD CALL] POST /api/projects/deploy" -ForegroundColor Magenta
    }
}

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green

if ($WhatIf) {
    Write-Host "*** DRY RUN COMPLETE - No changes made ***" -ForegroundColor Red
}
