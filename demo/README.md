# PropertyYards Platform Demo

This is a comprehensive demonstration of the PropertyYards real estate platform showcasing all implemented features including image upload, rewards system, security, and caching.

## 🚀 Demo Features

### 1. **Image Upload System**
- **Multiple Image Formats**: JPG, PNG, GIF, WebP, BMP support
- **Automatic Processing**: Resize, optimize, and create thumbnails
- **Smart Compression**: Quality optimization for web
- **Storage Management**: Organized file structure with originals, thumbnails, and medium sizes
- **Batch Upload**: Upload multiple images at once

### 2. **Rewards & Commission System**
- **0.1% Commission**: Automatic commission on all transactions
- **Points Conversion**: Convert points to wallet credit, bank transfer, or gift cards
- **Tier System**: Bronze, Silver, Gold, Platinum, Diamond tiers with benefits
- **Referral Program**: Earn points from referrals
- **Conversion History**: Track all conversions and earnings

### 3. **Advanced Security**
- **Threat Detection**: SQL injection, XSS, path traversal protection
- **Rate Limiting**: Per-endpoint rate limiting
- **IP Blocking**: Automatic blocking of suspicious IPs
- **Input Validation**: Comprehensive input sanitization
- **Admin Protection**: IP whitelisting for admin endpoints

### 4. **High-Performance Caching**
- **Multi-Layer Caching**: Application, Redis, and database caching
- **Cache Warming**: Preload frequently accessed data
- **Intelligent Invalidation**: Smart cache dependency management
- **Performance Monitoring**: Real-time cache metrics and alerts

### 5. **Property Management**
- **CRUD Operations**: Create, read, update, delete properties
- **Advanced Search**: Filter by location, price, type, amenities
- **Image Gallery**: Multiple images per property with automatic optimization
- **Analytics**: Property views, favorites, and inquiry tracking

## 🛠️ Quick Start Demo

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.8+ (for backend development)

### 1. **Clone and Setup**
```bash
git clone https://github.com/your-org/propertyyards-demo.git
cd propertyyards-demo
```

### 2. **Start All Services**
```bash
# Start the complete demo stack
docker-compose up -d

# View service status
docker-compose ps
```

### 3. **Access Demo Applications**

#### Backend API Demo
- **API Base**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

#### Frontend Demo
- **Web Application**: http://localhost:5173
- **Property Browse**: http://localhost:5173/properties
- **User Dashboard**: http://localhost:5173/dashboard

#### Monitoring & Admin
- **Grafana Dashboard**: http://localhost:3000 (admin/admin123)
- **Prometheus Metrics**: http://localhost:9090
- **Cache Monitor**: http://localhost:8000/api/cache/metrics

## 📱 Demo Scenarios

### Scenario 1: Image Upload Demo
```bash
# Test image upload via API
curl -X POST "http://localhost:8000/api/images/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@demo-image.jpg"

# View uploaded image
curl "http://localhost:8000/api/images/files/originals/IMAGE_ID"
```

### Scenario 2: Rewards System Demo
```bash
# Get user wallet
curl "http://localhost:8000/api/rewards/wallet" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Convert points to cash
curl -X POST "http://localhost:8000/api/rewards/convert-points" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"points": 1000, "conversion_type": "wallet_credit"}'
```

### Scenario 3: Security Testing Demo
```bash
# Test rate limiting (should be blocked after 5 attempts)
for i in {1..6}; do
  curl -X POST "http://localhost:8000/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}'
done

# Test threat detection (should be blocked)
curl "http://localhost:8000/api/properties?search='; DROP TABLE users; --"
```

## 🎯 Interactive Demo Guide

### Step 1: User Registration & Login
1. Visit http://localhost:5173/register
2. Create a new account
3. Verify email (automatic in demo)
4. Login to access dashboard

### Step 2: Property Management
1. Navigate to http://localhost:5173/properties
2. Click "Add Property"
3. Fill property details
4. Upload multiple images
5. Save and view property listing

### Step 3: Rewards & Points
1. Go to http://localhost:5173/rewards
2. View current points balance
3. Try converting points to different options
4. Check conversion history
5. Test referral system

### Step 4: Admin Dashboard
1. Login as admin (admin@propertyyards.com / admin123)
2. Access http://localhost:5173/admin
3. View system statistics
4. Monitor user activity
5. Test security features

## 🔧 Demo Configuration

### Environment Variables
```bash
# Database
MONGODB_URL=mongodb://localhost:27017/propertyyards_demo
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=demo_secret_key_change_in_production
API_SECRET_KEY=demo_api_secret_change_in_production

# Features
ENABLE_IMAGE_UPLOAD=true
ENABLE_REWARDS=true
ENABLE_CACHE_MONITORING=true
```

### Demo Data
The demo includes pre-populated data:
- **Sample Properties**: 50+ properties across different cities
- **Demo Users**: Various user roles and tiers
- **Sample Images**: Property photos and avatars
- **Transaction History**: Sample transactions for testing

## 📊 Performance Demo

### Load Testing
```bash
# Install Locust
pip install locust

# Run load test
locust -f demo/load_test.py --host=http://localhost:8000

# Access Locust Web UI
http://localhost:8089
```

### Cache Performance
```bash
# Test cache performance
curl "http://localhost:8000/api/cache/performance" \
  -H "Authorization: Bearer ADMIN_TOKEN"

# View cache metrics
curl "http://localhost:8000/api/cache/metrics" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## 🎨 Frontend Demo Features

### React Components
- **ImageUploader**: Drag-and-drop image upload with preview
- **PropertyCard**: Responsive property listing cards
- **RewardsDashboard**: Interactive rewards interface
- **SecurityMonitor**: Real-time security alerts
- **PerformanceCharts**: Live performance metrics

### Key Interactions
1. **Drag & Drop Upload**: Intuitive image upload interface
2. **Real-time Updates**: Live notifications and updates
3. **Responsive Design**: Works on desktop, tablet, and mobile
4. **Progressive Enhancement**: Graceful degradation for older browsers

## 🔍 API Demo Endpoints

### Image Upload
- `POST /api/images/upload` - Upload single image
- `POST /api/images/upload-multiple` - Upload multiple images
- `GET /api/images/list` - List uploaded images
- `GET /api/images/{id}` - Get image details
- `DELETE /api/images/{id}` - Delete image

### Rewards System
- `GET /api/rewards/wallet` - Get rewards wallet
- `POST /api/rewards/convert-points` - Convert points
- `GET /api/rewards/conversion/history` - Conversion history
- `GET /api/rewards/referral/code` - Get referral code

### Security & Monitoring
- `GET /api/security/threats` - View threat detection
- `GET /api/cache/metrics` - Cache performance
- `GET /api/admin/stats` - System statistics
- `POST /api/admin/block-ip` - Block suspicious IP

## 🚨 Demo Alerts & Monitoring

### Security Alerts
- **Failed Login Attempts**: Multiple failed logins trigger alerts
- **Suspicious Activity**: Unusual API usage patterns
- **IP Blocking**: Automatic IP blocking for threats
- **Admin Access**: Admin endpoint access monitoring

### Performance Alerts
- **High Response Time**: API response time > 1 second
- **Low Cache Hit Rate**: Cache hit rate < 70%
- **Memory Usage**: High memory consumption alerts
- **Error Rate**: Error rate > 5%

## 📱 Mobile Demo

The demo is fully responsive and works on mobile devices:
- **Touch Gestures**: Swipe, tap, and pinch interactions
- **Mobile Upload**: Camera integration for image uploads
- **Push Notifications**: Real-time alerts on mobile
- **Offline Support**: Basic functionality without internet

## 🎯 Demo Success Metrics

### Performance Targets
- **API Response Time**: < 200ms (95th percentile)
- **Image Upload**: < 5 seconds for 10MB file
- **Cache Hit Rate**: > 80%
- **Security Response**: < 100ms for threat detection

### User Experience
- **Page Load Time**: < 3 seconds
- **Image Load Time**: < 2 seconds
- **Form Submission**: < 1 second response
- **Mobile Performance**: 90+ Lighthouse score

## 🔧 Troubleshooting Demo

### Common Issues
1. **Image Upload Fails**: Check file size and format
2. **Rewards Not Working**: Verify JWT token
3. **Cache Issues**: Restart Redis service
4. **Security Alerts**: Check IP whitelist settings

### Demo Reset
```bash
# Reset demo data
docker-compose exec backend python reset_demo.py

# Clear cache
docker-compose exec redis redis-cli FLUSHALL

# Reset images
rm -rf uploads/*
```

## 📞 Demo Support

### Getting Help
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **System Status**: http://localhost:8000/api/admin/stats
- **Error Logs**: `docker-compose logs backend`

### Demo Feedback
- **Report Issues**: GitHub Issues
- **Feature Requests**: GitHub Discussions
- **Security Concerns**: Private security contact
- **Performance Issues**: Performance monitoring dashboard

## 🎉 Demo Completion

After exploring all features:
1. Review the implemented functionality
2. Test security features
3. Evaluate performance
4. Check mobile responsiveness
5. Provide feedback for improvements

This demo showcases a production-ready real estate platform with enterprise-grade features, security, and performance optimization.
