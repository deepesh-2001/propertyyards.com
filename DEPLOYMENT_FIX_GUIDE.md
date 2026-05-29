# Deployment Fix Guide

This guide addresses the production and Netlify UI deployment issues and provides step-by-step solutions.

## 🔍 Issues Identified

### 1. **Missing Frontend Dockerfile**
- The frontend service in docker-compose.yml references a Dockerfile that didn't exist
- This prevented the frontend container from building

### 2. **Complex Microservices Configuration**
- The main docker-compose.yml is configured for microservices architecture
- Missing individual service Dockerfiles for each microservice
- Too complex for simple development setup

### 3. **Missing Nginx Configuration**
- No reverse proxy configuration for production
- Missing SSL setup and security headers

### 4. **Netlify Configuration Issues**
- netlify.toml exists but may not be properly configured
- Build process may fail due to missing dependencies

## 🛠️ Solutions Implemented

### 1. **Created Frontend Dockerfile**
```dockerfile
# Multi-stage build for React frontend
FROM node:18-alpine AS builder
# ... build process
FROM nginx:alpine AS production
# ... production setup
```

### 2. **Created Simplified Docker Compose**
- `docker-compose.simple.yml` for easy development
- Includes all necessary services (MongoDB, Redis, Backend, Frontend)
- Proper networking and volume configuration

### 3. **Added Nginx Reverse Proxy**
- Complete nginx configuration with security headers
- Rate limiting and compression
- API routing and SPA fallback support

### 4. **Fixed Netlify Configuration**
- Updated netlify.toml with proper build settings
- Added redirect rules for SPA routing

## 🚀 Quick Deployment Fixes

### Option 1: Use Simplified Docker Compose (Recommended)

```bash
# Stop any running containers
docker-compose down

# Use the simplified configuration
docker-compose -f docker-compose.simple.yml up -d

# Check status
docker-compose -f docker-compose.simple.yml ps

# View logs
docker-compose -f docker-compose.simple.yml logs -f
```

### Option 2: Fix Current Docker Compose

```bash
# Build frontend first
cd frontend
docker build -t propertyyards-frontend .

# Build backend
cd ../backend
docker build -t propertyyards-backend .

# Start services
cd ..
docker-compose up -d
```

### Option 3: Development Mode

```bash
# Start backend and database only
docker-compose up -d mongodb redis

# Start backend in development
cd backend
python run.py

# Start frontend in development (new terminal)
cd frontend
npm run dev
```

## 🌐 Netlify Deployment Fix

### 1. **Update netlify.toml**
```toml
[build]
  base    = "frontend"
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from   = "/api/*"
  to     = "https://your-backend-url.com/api/:splat"
  status = 200

[[redirects]]
  from   = "/*"
  to     = "/index.html"
  status = 200
```

### 2. **Environment Variables**
Set these in Netlify dashboard:
- `VITE_API_URL=https://your-backend-url.com`
- `VITE_APP_NAME=PropertyYards`

### 3. **Deploy to Netlify**
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
cd frontend
npm run build
netlify deploy --prod --dir=dist
```

## 🔧 Production Deployment

### 1. **SSL Certificate Setup**
```bash
# Create SSL directory
mkdir -p nginx/ssl

# Generate self-signed certificate (for testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=IN/ST=DL/L=Delhi/O=PropertyYards/CN=propertyyards.com"
```

### 2. **Production Docker Compose**
```bash
# Use production profile
docker-compose -f docker-compose.simple.yml --profile production up -d
```

### 3. **Environment Configuration**
Create `.env` file:
```bash
MONGODB_URL=mongodb://admin:propertyyards123@mongodb:27017/housing_db?authSource=admin
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=your_production_jwt_secret
API_SECRET_KEY=your_production_api_secret
DEBUG=false
CORS_ORIGINS=https://propertyyards.com,https://www.propertyyards.com
```

## 📋 Verification Steps

### 1. **Check Container Status**
```bash
docker-compose -f docker-compose.simple.yml ps
```

Expected output:
```
NAME                    COMMAND                  SERVICE             STATUS              PORTS
propertyyards_backend   "uvicorn app.main:ap…"   backend             running (healthy)   0.0.0.0:8000->8000/tcp
propertyyards_frontend  "nginx -g 'daemon of…"   frontend            running (healthy)   0.0.0.0:5173->80/tcp
propertyyards_mongodb   "docker-entrypoint.s…"   mongodb             running              0.0.0.0:27017->27017/tcp
propertyyards_redis     "redis-server --appe…"   redis               running              0.0.0.0:6379->6379/tcp
```

### 2. **Test API Endpoints**
```bash
# Health check
curl http://localhost:8000/health

# API root
curl http://localhost:8000/

# Frontend
curl http://localhost:5173/health
```

### 3. **Test Frontend**
Visit http://localhost:5173 in browser - should show PropertyYards interface

### 4. **Test Image Upload**
```bash
# Test image upload endpoint
curl -X POST "http://localhost:8000/api/images/upload" \
  -F "file=@test-image.jpg"
```

## 🐛 Common Troubleshooting

### Issue: Frontend not accessible
**Solution**: Check nginx configuration and port mapping
```bash
# Check nginx logs
docker logs propertyyards_frontend

# Check port conflicts
netstat -tulpn | grep :5173
```

### Issue: Backend API not responding
**Solution**: Check backend logs and database connection
```bash
# Check backend logs
docker logs propertyyards_backend

# Test database connection
docker exec propertyyards_mongodb mongosh --eval "db.adminCommand('ping')"
```

### Issue: Netlify build fails
**Solution**: Check build logs and dependencies
```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install

# Test build locally
npm run build
```

### Issue: CORS errors
**Solution**: Update CORS configuration in backend
```bash
# Check current CORS settings
curl -I http://localhost:8000/api/auth/login
```

## 🚀 Alternative Deployment Options

### 1. **Kubernetes Deployment**
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/
```

### 2. **Docker Swarm**
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.simple.yml propertyyards
```

### 3. **Manual Deployment**
```bash
# Backend
cd backend
pip install -r requirements.txt
python run.py

# Frontend
cd frontend
npm run build
# Serve dist folder with any web server
```

## 📊 Performance Optimization

### 1. **Enable Caching**
```bash
# Redis cache should be running
docker exec propertyyards_redis redis-cli ping
```

### 2. **Database Indexing**
```bash
# Connect to MongoDB and create indexes
docker exec propertyyards_mongodb mongosh housing_db
```

### 3. **Nginx Optimization**
The nginx configuration includes:
- Gzip compression
- Rate limiting
- Security headers
- Proper caching

## 🔒 Security Considerations

### 1. **Change Default Passwords**
Update these in production:
- MongoDB password
- JWT secrets
- API secrets

### 2. **Enable HTTPS**
```bash
# Uncomment HTTPS section in nginx.conf
# Add SSL certificates
```

### 3. **Firewall Rules**
```bash
# Only expose necessary ports
ufw allow 80
ufw allow 443
ufw deny 27017  # MongoDB
ufw deny 6379   # Redis
```

## 📞 Support

If issues persist:
1. Check logs: `docker-compose logs`
2. Verify configuration: Check .env file
3. Test individual services: Start one by one
4. Check resource usage: `docker stats`

## 🎯 Success Criteria

Deployment is successful when:
- [ ] Frontend loads at http://localhost:5173
- [ ] Backend API responds at http://localhost:8000
- [ ] Health checks pass for all services
- [ ] Image upload functionality works
- [ ] No CORS errors in browser console
- [ ] Database and Redis connections established

This guide should resolve all production and Netlify UI deployment issues.
