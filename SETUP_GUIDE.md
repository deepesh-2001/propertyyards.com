# Setup Guide - Housing Platform

## Prerequisites

### System Requirements
- Linux/Mac/Windows with WSL2
- 8GB RAM minimum
- 20GB disk space

### Required Software
- Git
- Docker & Docker Compose (for containerized setup)
- Python 3.9+ (for local development)
- Node.js 16+ (for frontend development)
- PostgreSQL 12+ (for local development)
- Redis 6+ (for local development)

## Quick Start (Docker Compose)

### 1. Clone the Repository
```bash
cd housing_platform
```

### 2. Configure Environment Variables
```bash
# Backend
cp backend/.env.example backend/.env

# Update backend/.env with your values:
# DATABASE_URL=postgresql://housing_user:housing_password@postgres:5432/housing_db
# REDIS_URL=redis://redis:6379
# JWT_SECRET_KEY=your-super-secret-key-change-in-production

# Frontend
cp frontend/.env.example frontend/.env
```

### 3. Build and Start Services
```bash
docker-compose up -d
```

This will start:
- PostgreSQL on localhost:5432
- Redis on localhost:6379
- Backend API on localhost:8000
- Frontend on localhost:5173
- Nginx reverse proxy on localhost:80

### 4. Initialize Database
```bash
docker-compose exec backend python app/init_db.py
```

### 5. Access the Application
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Local Development Setup

### Backend Setup

#### 1. Install Python Dependencies
```bash
cd backend
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

#### 2. Setup Database
```bash
# Create PostgreSQL database
createdb housing_db

# Or use Docker:
docker run --name housing_postgres \
  -e POSTGRES_USER=housing_user \
  -e POSTGRES_PASSWORD=housing_password \
  -e POSTGRES_DB=housing_db \
  -p 5432:5432 \
  -d postgres:15-alpine

# Or use Docker Compose for just DB:
docker-compose up -d postgres redis
```

#### 3. Setup Redis Cache
```bash
# Docker
docker run --name housing_redis -p 6379:6379 -d redis:7-alpine

# Or use Docker Compose:
docker-compose up -d redis
```

#### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your local settings
```

#### 5. Initialize Database
```bash
python app/init_db.py
```

Database will be populated with:
- Admin user: admin@housing.com / admin@housing123
- Test seller: seller@housing.com / seller@housing123
- Test buyer: buyer@housing.com / buyer@housing123

#### 6. Run Backend Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### Frontend Setup

#### 1. Install Node Dependencies
```bash
cd frontend
npm install
```

#### 2. Configure Environment
```bash
# Create .env file (already done in docker setup)
echo "VITE_API_URL=http://localhost:8000" > .env
```

#### 3. Run Development Server
```bash
npm run dev
```

Frontend will be available at: http://localhost:5173

#### 4. Build for Production
```bash
npm run build
npm run preview  # Preview production build
```

## API Documentation

### Swagger UI
Visit: http://localhost:8000/docs

### ReDoc
Visit: http://localhost:8000/redoc

## Load Testing

### Prerequisites
```bash
pip install locust
```

### Run Load Test (1000 users)
```bash
cd backend
locust -f tests/test_load.py \
  --host=http://localhost:8000 \
  --users 1000 \
  --spawn-rate 100 \
  --run-time 5m
```

This will:
- Spawn 1000 concurrent users
- Spawn 100 users per second
- Run the test for 5 minutes
- Simulate: property searches, bookmarks, inquiries, profile updates

### Access Load Test UI
Visit: http://localhost:8089

## Database Management

### Backup Database
```bash
docker-compose exec postgres pg_dump -U housing_user housing_db > backup.sql
```

### Restore Database
```bash
docker-compose exec -T postgres psql -U housing_user housing_db < backup.sql
```

### Access Database Shell
```bash
docker-compose exec postgres psql -U housing_user -d housing_db
```

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process using port
lsof -i :8000  # Find process
kill -9 <PID>

# Or change port in docker-compose.yml or .env
```

### Database Connection Issues
```bash
# Check if PostgreSQL is running:
docker-compose ps postgres

# View PostgreSQL logs:
docker-compose logs postgres

# Restart PostgreSQL:
docker-compose restart postgres
```

### Redis Connection Issues
```bash
# Test Redis connection:
redis-cli ping

# View Redis logs:
docker-compose logs redis
```

### Frontend Build Issues
```bash
# Clear npm cache:
npm cache clean --force

# Reinstall dependencies:
rm -rf node_modules package-lock.json
npm install
```

## Development Workflow

### Starting All Services
```bash
# Using Docker Compose (recommended):
docker-compose up

# Or start manually:
# Terminal 1: Backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: PostgreSQL (if using Docker)
docker-compose up postgres redis
```

### Making Code Changes

**Backend**:
- Server auto-reloads with `--reload` flag
- Check http://localhost:8000/docs for updated API docs

**Frontend**:
- Vite hot module replacement (HMR)
- Changes auto-reflect in browser

### Database Migrations

To add new models:
1. Create model in `backend/app/models.py`
2. Restart backend (auto-creates tables with `Base.metadata.create_all()`)

## Deployment

### AWS Deployment
```bash
# Use AWS ECS with Docker images
# Set up RDS PostgreSQL
# Set up ElastiCache Redis
# Configure environment variables
```

### Heroku Deployment
```bash
# Create Procfile
# Add buildpacks for Python and Node
# Deploy with: git push heroku main
```

### DigitalOcean App Platform
```bash
# Create app.yaml with services
# Connect GitHub repository
# Auto-deploy on push
```

## Performance Optimization

### Caching Strategy
- Properties: 5 minute cache
- User profiles: 30 minute cache
- Search results: 5 minute cache
- Admin analytics: 15 minute cache

### Database Optimization
- Indexes on: user_id, property_id, city, price, created_at
- Connection pooling: 20 connections, 40 max overflow
- Query pagination: max 100 items per page

### Frontend Optimization
- Code splitting with React Router
- Image lazy loading
- Gzip compression enabled
- CDN ready

## Monitoring & Logging

### Application Logs
```bash
# Backend logs:
docker-compose logs backend -f

# Frontend logs:
docker-compose logs frontend -f

# Nginx logs:
docker-compose logs nginx -f
```

### Performance Metrics
- Check API response times at: http://localhost:8000/docs
- Monitor Redis at: redis-cli MONITOR
- Check database with: SELECT * FROM pg_stat_statements;

## Security

### Best Practices
1. ✓ JWT authentication with expiration
2. ✓ Password hashing with bcrypt
3. ✓ SQL injection prevention (SQLAlchemy ORM)
4. ✓ CORS properly configured
5. ✓ Environment variables for secrets
6. ✓ Role-based access control

### Pre-deployment Checklist
- [ ] Change JWT_SECRET_KEY in .env
- [ ] Set DEBUG=false in production
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Configure monitoring alerts
- [ ] Review CORS origins
- [ ] Enable rate limiting

## Support & Contributing

### Reporting Issues
Create an issue with:
- System information
- Steps to reproduce
- Expected vs actual behavior
- Error logs

### Contributing
1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create pull request

## License

MIT License - See LICENSE file for details

## Contacts

- Technical Support: support@housing-platform.com
- Documentation: https://docs.housing-platform.com
- Issues: https://github.com/housing-platform/issues

