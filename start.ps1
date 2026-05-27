# Housing Platform - Quick Start Script for Windows
# Run with: .\start.ps1

Write-Host "🏠 Housing Platform - Starting Services" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if Docker Compose is available
try {
    docker-compose --version | Out-Null
} catch {
    Write-Host "❌ Docker Compose is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Docker Desktop first: https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}

# Start services
Write-Host ""
Write-Host "📦 Starting Docker Compose services..." -ForegroundColor Green

docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Docker Compose services started" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start Docker Compose services" -ForegroundColor Red
    exit 1
}

# Wait for services
Write-Host ""
Write-Host "⏳ Waiting for services to be ready (10 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Initialize database
Write-Host ""
Write-Host "🗄️ Initializing database..." -ForegroundColor Green
docker-compose exec -T backend python app/init_db.py

Write-Host ""
Write-Host "✅ All services started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access the application at:" -ForegroundColor Cyan
Write-Host "  - Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - ReDoc: http://localhost:8000/redoc" -ForegroundColor White
Write-Host ""
Write-Host "📝 Demo Credentials:" -ForegroundColor Cyan
Write-Host "  - Admin: admin@housing.com / admin@housing123" -ForegroundColor White
Write-Host "  - Seller: seller@housing.com / seller@housing123" -ForegroundColor White
Write-Host "  - Buyer: buyer@housing.com / buyer@housing123" -ForegroundColor White
Write-Host ""
Write-Host "📜 Logs:" -ForegroundColor Cyan
Write-Host "  View all: docker-compose logs -f" -ForegroundColor White
Write-Host "  Backend: docker-compose logs -f backend" -ForegroundColor White
Write-Host "  Frontend: docker-compose logs -f frontend" -ForegroundColor White
Write-Host ""
Write-Host "🛑 Stop services: docker-compose down" -ForegroundColor Yellow

