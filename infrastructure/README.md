# PropertyYards Infrastructure

Infrastructure as Code for PropertyYards real estate platform including Docker Compose configurations, Kubernetes manifests, deployment scripts, and monitoring setup.

## Overview

This repository contains all infrastructure configurations needed to deploy and manage the PropertyYards platform across different environments (development, staging, production).

## Architecture

### Microservices Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (MongoDB)     │
│   Port: 5173    │    │   Port: 8000    │    │   Port: 27017   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │      Cache      │
                       │    (Redis)      │
                       │   Port: 6379    │
                       └─────────────────┘
```

### Infrastructure Components
- **Load Balancer**: Nginx reverse proxy
- **API Gateway**: Nginx with SSL termination
- **Database**: MongoDB replica set
- **Cache**: Redis cluster
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **CI/CD**: GitHub Actions
- **Container Registry**: Docker Hub / GitHub Container Registry

## Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- kubectl (for Kubernetes)
- Helm 3.0+ (optional)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/propertyyards-infrastructure.git
   cd propertyyards-infrastructure
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Verify services**
   ```bash
   # Check service status
   docker-compose ps

   # View logs
   docker-compose logs -f

   # Access services
   # Frontend: http://localhost:5173
   # Backend API: http://localhost:8000
   # API Docs: http://localhost:8000/docs
   ```

## Configuration

### Environment Variables

```bash
# Application Configuration
COMPOSE_PROJECT_NAME=propertyyards
ENVIRONMENT=development

# Database Configuration
MONGO_ROOT_PASSWORD=your_secure_password
MONGO_REPLICA_SET_NAME=rs0
MONGO_DATABASE=housing_db

# Redis Configuration
REDIS_PASSWORD=your_redis_password
REDIS_CLUSTER_ENABLED=false

# Backend Configuration
BACKEND_IMAGE=propertyyards/backend:latest
BACKEND_PORT=8000
JWT_SECRET_KEY=your_jwt_secret
API_SECRET_KEY=your_api_secret

# Frontend Configuration
FRONTEND_IMAGE=propertyyards/frontend:latest
FRONTEND_PORT=5173
API_BASE_URL=http://localhost:8000/api

# Nginx Configuration
NGINX_PORT=80
NGINX_SSL_PORT=443
SSL_CERT_PATH=./certs/cert.pem
SSL_KEY_PATH=./certs/key.pem

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=admin_password

# Logging
ELASTICSEARCH_PORT=9200
KIBANA_PORT=5601
LOGSTASH_PORT=5044
```

## Services

### Development Services

#### Backend Service
```yaml
backend:
  build: ../backend
  ports:
    - "8000:8000"
  environment:
    - MONGODB_URL=mongodb://mongodb_primary:27017/housing_db
    - REDIS_URL=redis://redis:6379/0
  depends_on:
    - mongodb_primary
    - redis
  volumes:
    - ../backend:/app
  restart: unless-stopped
```

#### Frontend Service
```yaml
frontend:
  build: ../frontend
  ports:
    - "5173:5173"
  environment:
    - VITE_API_BASE_URL=http://localhost:8000/api
  depends_on:
    - backend
  volumes:
    - ../frontend:/app
  restart: unless-stopped
```

#### Database Services
```yaml
mongodb_primary:
  image: mongo:7
  ports:
    - "27017:27017"
  environment:
    - MONGO_INITDB_ROOT_USERNAME=admin
    - MONGO_INITDB_ROOT_PASSWORD=${MONGO_ROOT_PASSWORD}
  volumes:
    - mongodb_primary_data:/data/db
  restart: unless-stopped

redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  command: redis-server --requirepass ${REDIS_PASSWORD}
  volumes:
    - redis_data:/data
  restart: unless-stopped
```

### Production Services

#### Load Balancer (Nginx)
```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:5173;
}

server {
    listen 80;
    server_name propertyyards.com www.propertyyards.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name propertyyards.com www.propertyyards.com;

    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;

    # Frontend routes
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API routes
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Deployment

### Docker Compose Deployment

#### Development Environment
```bash
# Start development services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Production Environment
```bash
# Start production services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale backend=3

# Update services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment

#### Prerequisites
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

#### Deploy to Kubernetes
```bash
# Create namespace
kubectl create namespace propertyyards

# Apply configurations
kubectl apply -f k8s/namespaces/
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/
kubectl apply -f k8s/volumes/
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress/

# Check deployment
kubectl get pods -n propertyyards
kubectl get services -n propertyyards
kubectl get ingress -n propertyyards
```

#### Helm Deployment
```bash
# Add Helm repository
helm repo add propertyyards https://charts.propertyyards.com
helm repo update

# Install chart
helm install propertyyards propertyyards/propertyyards \
  --namespace propertyyards \
  --create-namespace \
  --set environment=production \
  --set backend.replicas=3 \
  --set frontend.replicas=2

# Upgrade deployment
helm upgrade propertyyards propertyyards/propertyyards \
  --namespace propertyyards \
  --set backend.image.tag=v1.2.0
```

## Monitoring

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']

  - job_name: 'mongodb'
    static_configs:
      - targets: ['mongodb-exporter:9216']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Grafana Dashboards

Pre-configured dashboards:
- **System Overview**: CPU, memory, disk usage
- **Application Metrics**: Request rate, response time, error rate
- **Database Performance**: MongoDB operations, connections, replication
- **Cache Performance**: Redis operations, memory usage, hit rate

### Alerting Rules

```yaml
# alerts.yml
groups:
  - name: propertyyards
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
```

## Logging

### ELK Stack Configuration

#### Elasticsearch
```yaml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
  environment:
    - discovery.type=single-node
    - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
  ports:
    - "9200:9200"
  volumes:
    - elasticsearch_data:/usr/share/elasticsearch/data
```

#### Logstash
```ruby
# logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "backend" {
    json {
      source => "message"
    }
  }
  
  date {
    match => [ "timestamp", "ISO8601" ]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "propertyyards-%{+YYYY.MM.dd}"
  }
}
```

#### Kibana
```yaml
kibana:
  image: docker.elastic.co/kibana/kibana:8.11.0
  environment:
    - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
  ports:
    - "5601:5601"
  depends_on:
    - elasticsearch
```

## Security

### SSL/TLS Configuration

```bash
# Generate self-signed certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/key.pem \
  -out certs/cert.pem \
  -subj "/C=IN/ST=DL/L=Delhi/O=PropertyYards/CN=propertyyards.com"

# Or use Let's Encrypt
certbot certonly --standalone -d propertyyards.com -d www.propertyyards.com
```

### Network Security

```yaml
# Docker network configuration
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
  database:
    driver: bridge
    internal: true

# Service network assignment
services:
  nginx:
    networks:
      - frontend
      - backend
  
  backend:
    networks:
      - backend
      - database
  
  mongodb:
    networks:
      - database
```

### Firewall Rules

```bash
# UFW configuration
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw deny 27017/tcp  # MongoDB (internal only)
ufw deny 6379/tcp   # Redis (internal only)
ufw enable
```

## Backup & Recovery

### Database Backup

```bash
#!/bin/bash
# backup-mongodb.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mongodb"
CONTAINER_NAME="propertyyards_mongodb_primary_1"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
docker exec $CONTAINER_NAME mongodump \
  --host localhost:27017 \
  --db housing_db \
  --out /tmp/backup

# Copy backup from container
docker cp $CONTAINER_NAME:/tmp/backup $BACKUP_DIR/mongodb_$DATE

# Compress backup
tar -czf $BACKUP_DIR/mongodb_$DATE.tar.gz -C $BACKUP_DIR mongodb_$DATE

# Remove uncompressed backup
rm -rf $BACKUP_DIR/mongodb_$DATE

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "mongodb_*.tar.gz" -mtime +7 -delete

echo "Backup completed: mongodb_$DATE.tar.gz"
```

### Restore Database

```bash
#!/bin/bash
# restore-mongodb.sh

BACKUP_FILE=$1
CONTAINER_NAME="propertyyards_mongodb_primary_1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

# Extract backup
tar -xzf $BACKUP_FILE -C /tmp/

# Copy to container
docker cp /tmp/mongodb_* $CONTAINER_NAME:/tmp/restore/

# Perform restore
docker exec $CONTAINER_NAME mongorestore \
  --host localhost:27017 \
  --db housing_db \
  --drop \
  /tmp/restore/housing_db

echo "Restore completed from: $BACKUP_FILE"
```

## Performance Optimization

### Database Optimization

```javascript
// MongoDB indexes
db.properties.createIndex({ "location.city": 1, "price": 1 })
db.properties.createIndex({ "title": "text", "description": "text" })
db.users.createIndex({ "email": 1 }, { unique: true })
db.transactions.createIndex({ "created_at": -1 })
```

### Redis Configuration

```conf
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Nginx Optimization

```nginx
# Performance settings
worker_processes auto;
worker_connections 1024;

# Gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript;

# Caching
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## Troubleshooting

### Common Issues

#### Service Not Starting
```bash
# Check logs
docker-compose logs <service_name>

# Check port conflicts
netstat -tulpn | grep <port>

# Check resource usage
docker stats
```

#### Database Connection Issues
```bash
# Test MongoDB connection
docker exec -it mongodb_primary mongosh --eval "db.adminCommand('ping')"

# Check replica set status
docker exec -it mongodb_primary mongosh --eval "rs.status()"

# Test Redis connection
docker exec -it redis redis-cli ping
```

#### Performance Issues
```bash
# Check resource usage
docker stats --no-stream

# Monitor database queries
docker exec mongodb_primary mongosh --eval "db.setProfilingLevel(2)"
docker exec mongodb_primary mongosh --eval "db.system.profile.find().limit(5).sort({ts:-1}).pretty()"

# Check cache hit rate
docker exec redis redis-cli info stats | grep keyspace
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to production
        run: |
          docker-compose -f docker-compose.prod.yml pull
          docker-compose -f docker-compose.prod.yml up -d
        env:
          DOCKER_HOST: ${{ secrets.DOCKER_HOST }}
          DOCKER_TLS_VERIFY: 1
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make infrastructure changes
4. Test configurations locally
5. Update documentation
6. Submit Pull Request

### Infrastructure Changes Checklist
- [ ] Update Docker Compose files
- [ ] Update Kubernetes manifests
- [ ] Update environment variables
- [ ] Test in development environment
- [ ] Update documentation
- [ ] Add monitoring and logging
- [ ] Security review

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [Infrastructure Docs](./docs)
- **Issues**: [GitHub Issues](https://github.com/your-org/propertyyards-infrastructure/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/propertyyards-infrastructure/discussions)

## Related Repositories

- [Backend Repository](https://github.com/your-org/propertyyards-backend)
- [Frontend Repository](https://github.com/your-org/propertyyards-frontend)
- [Documentation Repository](https://github.com/your-org/propertyyards-docs)
