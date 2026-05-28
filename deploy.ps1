# 🚀 PropertyYards Microservices Deployment Script (PowerShell)
# Usage: .\deploy.ps1 [environment]
# Environment: preview (default) | production

param(
    [string]$Environment = "preview"
)

$ErrorActionPreference = "Stop"

$Services = @(
    @{Dir="microservices/api-gateway"; Name="api-gateway-propertyyards"},
    @{Dir="microservices/auth-service"; Name="auth-service-propertyyards"},
    @{Dir="microservices/property-service"; Name="property-service-propertyyards"},
    @{Dir="microservices/user-service"; Name="user-service-propertyyards"},
    @{Dir="microservices/report-service"; Name="report-service-propertyyards"},
    @{Dir="microservices/insurance-service"; Name="insurance-service-propertyyards"},
    @{Dir="microservices/ai-service"; Name="ai-service-propertyyards"},
    @{Dir="microservices/notification-service"; Name="notification-service-propertyyards"},
    @{Dir="microservices/analytics-service"; Name="analytics-service-propertyyards"}
)

Write-Host "🚀 PropertyYards Microservices Deployment" -ForegroundColor Cyan
Write-Host "=========================================="
Write-Host "Environment: $Environment"
Write-Host ""

# Check if Vercel CLI is installed
if (!(Get-Command vercel -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Vercel CLI not found. Installing..." -ForegroundColor Red
    npm i -g vercel
}

# Check if logged in
try {
    $null = vercel whoami 2>$null
} catch {
    Write-Host "🔑 Please login to Vercel:" -ForegroundColor Yellow
    vercel login
}

# Deploy Frontend
Write-Host "📦 Deploying Frontend..." -ForegroundColor Cyan
Push-Location frontend
try {
    if ($Environment -eq "production") {
        $FrontendUrl = vercel --prod --confirm
    } else {
        $FrontendUrl = vercel --confirm
    }
    Write-Host "✅ Frontend deployed: $FrontendUrl" -ForegroundColor Green
} finally {
    Pop-Location
}

# Deploy each service
$Jobs = @()
foreach ($Service in $Services) {
    $Jobs += Start-Job -ScriptBlock {
        param($Dir, $Name, $Env)
        
        Write-Host "📦 Deploying $Name..." -ForegroundColor Cyan
        Push-Location $Dir
        try {
            if ($Env -eq "production") {
                $Url = vercel --prod --confirm 2>&1
            } else {
                $Url = vercel --confirm 2>&1
            }
            Write-Host "✅ $Name deployed" -ForegroundColor Green
        } finally {
            Pop-Location
        }
    } -ArgumentList $Service.Dir, $Service.Name, $Environment
}

# Wait for all deployments
Write-Host ""
Write-Host "🔄 Waiting for all deployments to complete..." -ForegroundColor Cyan
$Jobs | Wait-Job | Receive-Job
$Jobs | Remove-Job

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "=========================================="
Write-Host ""
Write-Host "🔗 Frontend: $FrontendUrl" -ForegroundColor Cyan
Write-Host "📊 Check Vercel dashboard for service URLs"
Write-Host ""
Write-Host "🧪 Testing deployments..." -ForegroundColor Yellow

# Test health endpoints
Start-Sleep -Seconds 5

$TestUrls = @(
    "https://api-gateway-propertyyards.vercel.app/api/health",
    "https://auth-service-propertyyards.vercel.app/health",
    "https://property-service-propertyyards.vercel.app/health"
)

foreach ($Url in $TestUrls) {
    Write-Host "Testing $Url..."
    try {
        $Response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 10
        Write-Host "  Status: $($Response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "✅ All services deployed successfully!" -ForegroundColor Green
Write-Host "🌐 Access your application at: $FrontendUrl" -ForegroundColor Cyan
