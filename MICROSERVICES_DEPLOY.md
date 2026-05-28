# 🚀 Microservices Deployment Guide

## 📦 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Vercel                               │
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │  Frontend       │  │  API Gateway (api-gateway/server.js) │  │
│  │  (React)        │  │  - Routing                         │  │
│  │  Static Hosting │  │  - Load Balancing                  │  │
│  └─────────────────┘  │  - Rate Limiting                   │  │
│                       └─────────────────┬────────────────────┘  │
│                                         │                      │
│    ┌────────────────────────────────────┼──────────────────┐   │
│    │                                    │                  │   │
│ ┌──▼────┐  ┌────────────┐  ┌───────────▼────┐  ┌────────▼─┐   │
│ │ Auth  │  │ Property   │  │  User          │  │ Report   │   │
│ │:8001   │  │ :8002      │  │  :8003         │  │ :8004    │   │
│ └───────┘  └────────────┘  └────────────────┘  └──────────┘   │
│ ┌────────────┐  ┌────────┐  ┌────────────────┐  ┌───────────┐   │
│ │ Insurance  │  │  AI    │  │ Notification   │  │ Analytics │   │
│ │ :8005      │  │ :8006  │  │ :8007          │  │ :8008     │   │
│ └────────────┘  └────────┘  └────────────────┘  └───────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Deployment Steps

### 1. 🔧 Prerequisites

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Install Railway CLI (for backend services)
npm i -g @railway/cli
```

### 2. 🏗️ Create Vercel Projects

Create a new Vercel project for each service:

```bash
# 1. API Gateway
cd microservices/api-gateway
vercel --name api-gateway-propertyyards

# 2. Auth Service
cd ../auth-service
vercel --name auth-service-propertyyards

# 3. Property Service
cd ../property-service
vercel --name property-service-propertyyards

# 4. User Service
cd ../user-service
vercel --name user-service-propertyyards

# 5. Report Service
cd ../report-service
vercel --name report-service-propertyyards

# 6. Insurance Service
cd ../insurance-service
vercel --name insurance-service-propertyyards

# 7. AI Service
cd ../ai-service
vercel --name ai-service-propertyyards

# 8. Notification Service
cd ../notification-service
vercel --name notification-service-propertyyards

# 9. Analytics Service
cd ../analytics-service
vercel --name analytics-service-propertyyards

# 10. Frontend
cd ../../frontend
vercel --name propertyyards-frontend
```

### 3. 🔐 Configure Environment Variables

Set secrets in Vercel dashboard for each project:

```bash
# Shared across all services
MONGODB_URL=mongodb+srv://...
REDIS_URL=redis://...
JWT_SECRET_KEY=your-secret-key
RABBITMQ_URL=amqp://...

# Service-specific
AUTH_SERVICE_URL=https://auth-service-propertyyards.vercel.app
PROPERTY_SERVICE_URL=https://property-service-propertyyards.vercel.app
USER_SERVICE_URL=https://user-service-propertyyards.vercel.app
REPORT_SERVICE_URL=https://report-service-propertyyards.vercel.app
INSURANCE_SERVICE_URL=https://insurance-service-propertyyards.vercel.app
AI_SERVICE_URL=https://ai-service-propertyyards.vercel.app
NOTIFICATION_SERVICE_URL=https://notification-service-propertyyards.vercel.app
ANALYTICS_SERVICE_URL=https://analytics-service-propertyyards.vercel.app

# AI Service specific
GEMINI_API_KEY=...
IMAGEN_API_KEY=...
OPENAI_API_KEY=...

# Notification Service specific
SMTP_HOST=...
SMTP_PORT=...
SMTP_USER=...
SMTP_PASS=...
TWILIO_SID=...
TWILIO_TOKEN=...
```

### 4. 🚀 Deploy via GitHub Actions

Push to trigger automatic deployment:

```bash
# Create a new branch
git checkout -b feature/microservices-deployment

# Add all new files
git add microservices/
git add .github/workflows/ci-cd.yml
git add vercel.json
git add MICROSERVICES_DEPLOY.md

# Commit
git commit -m "🏗️ Transform to microservices architecture

- Split monolithic backend into 8 services
- Add API Gateway for routing
- Configure Vercel deployment
- Setup GitHub Actions CI/CD
- Add health checks and monitoring
- Configure environment variables"

# Push and create PR
git push origin feature/microservices-deployment
```

### 5. 🔗 Link GitHub to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Import your GitHub repository
3. Connect each service to its directory:
   - Frontend: `frontend/`
   - API Gateway: `microservices/api-gateway/`
   - Auth Service: `microservices/auth-service/`
   - etc.

### 6. 🧪 Test Deployment

```bash
# Test API Gateway
curl https://api-gateway-propertyyards.vercel.app/api/health

# Test Auth Service
curl https://auth-service-propertyyards.vercel.app/api/auth/login

# Test Property Service
curl https://property-service-propertyyards.vercel.app/api/properties

# Test Insurance Service
curl https://insurance-service-propertyyards.vercel.app/api/insurance/plans
```

## 📊 Monitoring

### Health Checks

Each service exposes:
- `GET /health` - Service health status
- `GET /api/health` (gateway) - All services health

### Logs

View logs via Vercel CLI:
```bash
vercel logs api-gateway-propertyyards --json
vercel logs auth-service-propertyyards --json
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The `.github/workflows/ci-cd.yml` handles:

1. **Test Phase**:
   - Run pytest for each service
   - Code coverage reporting
   - Security scanning (Bandit)

2. **Build Phase**:
   - Build Docker images
   - Run linting (flake8, black, isort)

3. **Deploy Phase**:
   - Deploy Frontend to Vercel (Preview for PRs, Production for main)
   - Deploy Services to Railway/Vercel
   - Run smoke tests

### PR Process

1. Create feature branch
2. Make changes
3. Push and open PR
4. GitHub Actions runs tests
5. Vercel deploys preview
6. Code review
7. Merge to main
8. Auto-deploy to production

## 🚨 Troubleshooting

### Service Unreachable

Check service URL in gateway config:
```bash
# Update environment variable
vercel env add AUTH_SERVICE_URL
```

### CORS Issues

Ensure CORS headers are set in vercel.json:
```json
"headers": [
  {
    "source": "/api/(.*)",
    "headers": [
      { "key": "Access-Control-Allow-Origin", "value": "*" }
    ]
  }
]
```

### Database Connection

Verify MongoDB Atlas IP whitelist:
- Add `0.0.0.0/0` for all IPs (development only)
- Or use Vercel's IP ranges

### Cold Start Issues

Vercel has cold starts for serverless functions:
- Use Redis caching to reduce DB calls
- Implement connection pooling
- Use Vercel Pro for better performance

## 💰 Cost Optimization

### Free Tier Limits

| Service | Vercel Hobby | Railway Starter |
|---------|--------------|-----------------|
| Requests | 100K/day | 500 hrs/month |
| Bandwidth | 100GB | 5GB |
| Build Time | 6000 min | 500 hrs |

### Recommendations

1. Use Redis caching to reduce compute
2. Implement request batching
3. Use static generation where possible
4. Monitor usage with Vercel Analytics

## 📞 Support

- Vercel Docs: https://vercel.com/docs
- Railway Docs: https://docs.railway.app
- GitHub Actions: https://docs.github.com/actions
- FastAPI: https://fastapi.tiangolo.com

---

**Ready to deploy! 🚀**
