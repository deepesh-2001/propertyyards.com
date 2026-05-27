#!/bin/bash

# Housing Platform - Quick Start Script

set -e

echo "🏠 Housing Platform - Starting Services"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Start services
echo ""
echo "📦 Starting Docker Compose services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Initialize database
echo ""
echo "🗄️ Initializing database..."
docker-compose exec -T backend python app/init_db.py

echo ""
echo "✅ All services started successfully!"
echo ""
echo "🌐 Access the application at:"
echo "  - Frontend: http://localhost:5173"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - ReDoc: http://localhost:8000/redoc"
echo ""
echo "📝 Demo Credentials:"
echo "  - Admin: admin@housing.com / admin@housing123"
echo "  - Seller: seller@housing.com / seller@housing123"
echo "  - Buyer: buyer@housing.com / buyer@housing123"
echo ""
echo "📜 Logs:"
echo "  - View all: docker-compose logs -f"
echo "  - Backend: docker-compose logs -f backend"
echo "  - Frontend: docker-compose logs -f frontend"
echo ""
echo "🛑 Stop services: docker-compose down"

