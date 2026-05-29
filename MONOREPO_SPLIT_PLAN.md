# Monorepo Split Plan

## Overview
This document outlines the plan to split the current monorepo into separate frontend and backend repositories for better maintainability, independent deployments, and team collaboration.

## Current Structure Analysis
The current structure has partial separation:
- `backend/` - FastAPI Python application
- `frontend/` - React/Vite application  
- Root level contains shared configuration and deployment files

## Target Structure

### Backend Repository (`propertyyards-backend`)
```
propertyyards-backend/
├── app/                    # FastAPI application code
├── tests/                  # Backend tests
├── scripts/                # Backend scripts
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Python project config
├── Dockerfile              # Backend Dockerfile
├── .env.example           # Backend environment template
├── README.md              # Backend-specific README
├── .github/               # Backend CI/CD workflows
└── docker-compose.yml     # Backend services only
```

### Frontend Repository (`propertyyards-frontend`)
```
propertyyards-frontend/
├── src/                   # React application code
├── public/                # Static assets
├── package.json           # Node.js dependencies
├── vite.config.js         # Vite configuration
├── Dockerfile             # Frontend Dockerfile
├── .env.example          # Frontend environment template
├── README.md             # Frontend-specific README
├── .github/              # Frontend CI/CD workflows
├── netlify.toml          # Netlify deployment config
└── vercel.json           # Vercel deployment config
```

### Infrastructure Repository (`propertyyards-infrastructure`)
```
propertyyards-infrastructure/
├── docker-compose.yml     # Full stack services
├── docker-compose.local.yml
├── nginx.conf            # Reverse proxy config
├── k8s/                  # Kubernetes manifests
├── scripts/              # Deployment scripts
├── .github/              # Infrastructure CI/CD
└── README.md             # Infrastructure docs
```

## Migration Steps

### Phase 1: Backend Separation
1. Create new `propertyyards-backend` repository
2. Move backend-specific files:
   - `backend/app/` → `app/`
   - `backend/tests/` → `tests/`
   - `backend/scripts/` → `scripts/`
   - `backend/requirements.txt` → `requirements.txt`
   - `backend/pyproject.toml` → `pyproject.toml`
   - `backend/Dockerfile` → `Dockerfile`
   - `backend/.env.example` → `.env.example`
3. Create backend-specific README.md
4. Set up backend CI/CD workflows
5. Update backend Docker configuration

### Phase 2: Frontend Separation
1. Create new `propertyyards-frontend` repository
2. Move frontend-specific files:
   - `frontend/src/` → `src/`
   - `frontend/public/` → `public/`
   - `frontend/package.json` → `package.json`
   - `frontend/vite.config.js` → `vite.config.js`
   - `frontend/.env` → `.env.example`
   - `frontend/netlify.toml` → `netlify.toml`
   - `frontend/vercel.json` → `vercel.json`
3. Create frontend-specific README.md
4. Set up frontend CI/CD workflows
5. Create frontend Dockerfile
6. Update environment configuration

### Phase 3: Infrastructure Separation
1. Create new `propertyyards-infrastructure` repository
2. Move infrastructure files:
   - `docker-compose.yml`
   - `docker-compose.local.yml`
   - `nginx.conf`
   - `k8s/`
   - `deploy.sh`
   - `deploy.ps1`
3. Update service configurations to use external repositories
4. Create infrastructure-specific README.md
5. Set up infrastructure CI/CD workflows

### Phase 4: Documentation Migration
1. Create shared documentation repository or use GitHub Wiki
2. Migrate relevant documentation:
   - `API_SPECIFICATION.md` → Backend repo
   - `ARCHITECTURE.md` → Infrastructure repo
   - `LOCAL_SETUP.md` → Split between repos
   - `DEPLOYMENT_GUIDE.md` → Infrastructure repo
3. Update root README with repository links

## Configuration Updates

### Backend Updates
- Update Docker Compose service names
- Add CORS configuration for frontend domains
- Update environment variable references
- Add health checks and monitoring

### Frontend Updates
- Update API base URLs for different environments
- Add environment-specific configuration
- Update build and deployment scripts
- Add proxy configuration for development

### Infrastructure Updates
- Update Docker Compose to use external images
- Add service discovery configuration
- Update networking and volume configurations
- Add monitoring and logging setup

## Deployment Strategy

### Development Environment
- Local Docker Compose with mounted volumes
- Hot reloading for both frontend and backend
- Shared development database and cache

### Staging Environment
- Separate deployments for each service
- Integration testing between services
- Performance monitoring and logging

### Production Environment
- Independent scaling for each service
- Load balancing and failover
- Security hardening and monitoring

## Benefits of Split

### Development Benefits
- Independent development cycles
- Separate testing strategies
- Technology flexibility
- Reduced merge conflicts

### Deployment Benefits
- Independent deployments
- Faster rollback capabilities
- Better resource utilization
- Service-specific scaling

### Team Benefits
- Clear ownership boundaries
- Specialized team expertise
- Better code review processes
- Independent release schedules

## Timeline

- **Week 1**: Backend repository setup and migration
- **Week 2**: Frontend repository setup and migration  
- **Week 3**: Infrastructure repository setup and configuration
- **Week 4**: Testing, documentation, and final adjustments

## Rollback Plan

If issues arise during migration:
1. Maintain current monorepo as backup
2. Use feature branches for testing
3. Gradual migration with feature flags
4. Quick rollback using Git tags

## Success Metrics

- Zero downtime during migration
- Independent deployment success
- Team productivity maintained
- Documentation completeness
- CI/CD pipeline functionality
