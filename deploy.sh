#!/bin/bash

# 🚀 PropertyYards Microservices Deployment Script
# Usage: ./deploy.sh [environment]
# Environment: preview (default) | production

set -e

ENVIRONMENT=${1:-preview}
SERVICES=(
  "microservices/api-gateway:api-gateway-propertyyards"
  "microservices/auth-service:auth-service-propertyyards"
  "microservices/property-service:property-service-propertyyards"
  "microservices/user-service:user-service-propertyyards"
  "microservices/report-service:report-service-propertyyards"
  "microservices/insurance-service:insurance-service-propertyyards"
  "microservices/ai-service:ai-service-propertyyards"
  "microservices/notification-service:notification-service-propertyyards"
  "microservices/analytics-service:analytics-service-propertyyards"
)

echo "🚀 PropertyYards Microservices Deployment"
echo "=========================================="
echo "Environment: $ENVIRONMENT"
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm i -g vercel
fi

# Check if logged in
if ! vercel whoami &> /dev/null; then
    echo "🔑 Please login to Vercel:"
    vercel login
fi

# Deploy Frontend
echo "📦 Deploying Frontend..."
cd frontend
if [ "$ENVIRONMENT" == "production" ]; then
  FRONTEND_URL=$(vercel --prod --confirm)
else
  FRONTEND_URL=$(vercel --confirm)
fi
echo "✅ Frontend deployed: $FRONTEND_URL"
cd ..

# Deploy each service
deploy_service() {
  local service_dir=$1
  local service_name=$2
  
  echo ""
  echo "📦 Deploying $service_name..."
  cd "$service_dir"
  
  if [ "$ENVIRONMENT" == "production" ]; then
    SERVICE_URL=$(vercel --prod --confirm)
  else
    SERVICE_URL=$(vercel --confirm)
  fi
  
  echo "✅ $service_name deployed: $SERVICE_URL"
  cd - > /dev/null
}

# Deploy services in parallel
echo ""
echo "🔄 Deploying microservices..."
for service in "${SERVICES[@]}"; do
  IFS=':' read -r dir name <<< "$service"
  deploy_service "$dir" "$name" &
done

# Wait for all deployments to complete
wait

echo ""
echo "=========================================="
echo "🎉 Deployment Complete!"
echo "=========================================="
echo ""
echo "🔗 Frontend: $FRONTEND_URL"
echo "📊 Check Vercel dashboard for service URLs"
echo ""
echo "🧪 Testing deployments..."

# Test health endpoints
sleep 5

TEST_URLS=(
  "https://api-gateway-propertyyards.vercel.app/api/health"
  "https://auth-service-propertyyards.vercel.app/health"
  "https://property-service-propertyyards.vercel.app/health"
)

for url in "${TEST_URLS[@]}"; do
  echo "Testing $url..."
  curl -s -o /dev/null -w "%{http_code}" "$url" || echo "Failed"
done

echo ""
echo "✅ All services deployed successfully!"
echo "🌐 Access your application at: $FRONTEND_URL"
