#!/bin/bash

# PropertyYards Deployment Script
# This script handles deployment of the PropertyYards platform

set -e

# Configuration
PROJECT_NAME="propertyyards"
ENVIRONMENT="${ENVIRONMENT:-development}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-docker.io/propertyyards}"
BACKEND_IMAGE="${DOCKER_REGISTRY}/backend:latest"
FRONTEND_IMAGE="${DOCKER_REGISTRY}/frontend:latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check environment file
    if [ ! -f ".env" ]; then
        log_warning ".env file not found, creating from template"
        cp .env.example .env
        log_warning "Please edit .env file with your configuration"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build images
build_images() {
    log_info "Building Docker images..."
    
    # Build backend image
    log_info "Building backend image..."
    docker build -t $BACKEND_IMAGE ../backend/
    
    # Build frontend image
    log_info "Building frontend image..."
    docker build -t $FRONTEND_IMAGE ../frontend/
    
    log_success "Images built successfully"
}

# Push images to registry
push_images() {
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "Pushing images to registry..."
        
        docker push $BACKEND_IMAGE
        docker push $FRONTEND_IMAGE
        
        log_success "Images pushed successfully"
    else
        log_info "Skipping image push for non-production environment"
    fi
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    
    # Determine compose file
    case $ENVIRONMENT in
        "production")
            COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
            ;;
        "staging")
            COMPOSE_FILES="-f docker-compose.yml -f docker-compose.staging.yml"
            ;;
        *)
            COMPOSE_FILES="-f docker-compose.yml -f docker-compose.dev.yml"
            ;;
    esac
    
    # Pull latest images
    log_info "Pulling latest images..."
    docker-compose $COMPOSE_FILES pull
    
    # Deploy services
    log_info "Starting services..."
    docker-compose $COMPOSE_FILES up -d
    
    log_success "Services deployed successfully"
}

# Wait for services to be healthy
wait_for_health() {
    log_info "Waiting for services to be healthy..."
    
    # Wait for backend
    log_info "Waiting for backend service..."
    timeout 60 bash -c 'until curl -f http://localhost:8000/health; do sleep 2; done'
    
    # Wait for frontend
    log_info "Waiting for frontend service..."
    timeout 60 bash -c 'until curl -f http://localhost:5173; do sleep 2; done'
    
    log_success "All services are healthy"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Wait for MongoDB to be ready
    log_info "Waiting for MongoDB..."
    timeout 60 bash -c 'until docker exec propertyyards_mongodb_primary_1 mongosh --eval "db.adminCommand(\"ping\")"; do sleep 2; done'
    
    # Run migrations (if any)
    # docker exec propertyyards_backend_1 python -m app.migrate
    
    log_success "Database migrations completed"
}

# Setup monitoring
setup_monitoring() {
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "Setting up monitoring..."
        
        # Create monitoring directories
        mkdir -p monitoring/prometheus monitoring/grafana monitoring/elasticsearch
        
        # Setup Prometheus configuration
        if [ ! -f "monitoring/prometheus/prometheus.yml" ]; then
            cp prometheus/prometheus.yml monitoring/prometheus/
        fi
        
        # Setup Grafana dashboards
        if [ ! -d "monitoring/grafana/dashboards" ]; then
            cp -r grafana/dashboards monitoring/grafana/
        fi
        
        log_success "Monitoring setup completed"
    fi
}

# Backup data before deployment
backup_data() {
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "Creating backup before deployment..."
        
        # Create backup directory
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p $BACKUP_DIR
        
        # Backup MongoDB
        docker exec propertyyards_mongodb_primary_1 mongodump --out /tmp/backup
        docker cp propertyyards_mongodb_primary_1:/tmp/backup $BACKUP_DIR/mongodb
        
        # Backup Redis (if needed)
        docker exec propertyyards_redis_1 redis-cli BGSAVE
        docker cp propertyyards_redis_1:/data/dump.rdb $BACKUP_DIR/redis.rdb
        
        log_success "Backup created: $BACKUP_DIR"
    fi
}

# Cleanup old resources
cleanup() {
    log_info "Cleaning up old resources..."
    
    # Remove unused Docker images
    docker image prune -f
    
    # Remove unused volumes (be careful in production)
    if [ "$ENVIRONMENT" != "production" ]; then
        docker volume prune -f
    fi
    
    # Remove old backups (keep last 7 days)
    if [ -d "backups" ]; then
        find backups -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    fi
    
    log_success "Cleanup completed"
}

# Show deployment status
show_status() {
    log_info "Deployment status:"
    echo
    
    # Show running containers
    echo "Running containers:"
    docker-compose ps
    echo
    
    # Show service URLs
    echo "Service URLs:"
    echo "  Frontend: http://localhost:5173"
    echo "  Backend API: http://localhost:8000"
    echo "  API Documentation: http://localhost:8000/docs"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "  Grafana: http://localhost:3000"
        echo "  Prometheus: http://localhost:9090"
        echo "  Kibana: http://localhost:5601"
    fi
    
    echo
}

# Rollback function
rollback() {
    log_warning "Rolling back to previous deployment..."
    
    # Get previous image tags
    PREVIOUS_BACKEND_IMAGE=$(docker images --format "table {{.Repository}}:{{.Tag}}" | grep propertyyards/backend | sed -n '2p')
    PREVIOUS_FRONTEND_IMAGE=$(docker images --format "table {{.Repository}}:{{.Tag}}" | grep propertyyards/frontend | sed -n '2p')
    
    if [ -z "$PREVIOUS_BACKEND_IMAGE" ] || [ -z "$PREVIOUS_FRONTEND_IMAGE" ]; then
        log_error "No previous images found for rollback"
        exit 1
    fi
    
    # Update compose file with previous images
    sed -i "s|image: $BACKEND_IMAGE|image: $PREVIOUS_BACKEND_IMAGE|g" docker-compose.yml
    sed -i "s|image: $FRONTEND_IMAGE|image: $PREVIOUS_FRONTEND_IMAGE|g" docker-compose.yml
    
    # Redeploy
    deploy_services
    wait_for_health
    
    log_success "Rollback completed"
}

# Main deployment function
deploy() {
    log_info "Starting deployment for $ENVIRONMENT environment..."
    
    check_prerequisites
    
    if [ "$ENVIRONMENT" = "production" ]; then
        backup_data
    fi
    
    build_images
    push_images
    deploy_services
    wait_for_health
    run_migrations
    setup_monitoring
    cleanup
    show_status
    
    log_success "Deployment completed successfully!"
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "build")
        build_images
        ;;
    "push")
        push_images
        ;;
    "status")
        show_status
        ;;
    "rollback")
        rollback
        ;;
    "cleanup")
        cleanup
        ;;
    "backup")
        backup_data
        ;;
    *)
        echo "Usage: $0 {deploy|build|push|status|rollback|cleanup|backup}"
        echo "  deploy   - Full deployment (default)"
        echo "  build    - Build Docker images only"
        echo "  push     - Push images to registry only"
        echo "  status   - Show deployment status"
        echo "  rollback - Rollback to previous deployment"
        echo "  cleanup  - Clean up old resources"
        echo "  backup   - Create data backup"
        exit 1
        ;;
esac
