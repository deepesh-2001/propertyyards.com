# PropertyYards Backend

FastAPI-based backend service for PropertyYards real estate platform with comprehensive features including property management, user authentication, rewards system, and advanced caching.

## Features

### Core Functionality
- **Property Management**: CRUD operations for properties with advanced search and filtering
- **User Authentication**: JWT-based authentication with role-based access control
- **Payment Processing**: Secure payment integration with multiple providers
- **Rewards System**: Comprehensive points and commission system with conversion options
- **Analytics**: Real-time analytics and reporting capabilities
- **AI Integration**: AI-powered property recommendations and SEO optimization

### Advanced Features
- **Security**: Advanced threat detection, rate limiting, and input sanitization
- **Caching**: Redis-based multi-layer caching with intelligent invalidation
- **Monitoring**: Performance monitoring and health checks
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: MongoDB with Motor (async driver)
- **Cache**: Redis with aioredis
- **Authentication**: JWT with python-jose
- **Security**: bcrypt, slowapi for rate limiting
- **Testing**: pytest with async support
- **Documentation**: OpenAPI/Swagger

## Quick Start

### Prerequisites
- Python 3.8+
- MongoDB
- Redis
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/propertyyards-backend.git
   cd propertyyards-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start the services**
   ```bash
   # Start MongoDB and Redis (using Docker)
   docker-compose up -d mongodb redis

   # Run the application
   python run.py
   ```

### Docker Setup

```bash
# Build and run with Docker
docker-compose up -d

# View logs
docker-compose logs -f backend
```

## Configuration

### Environment Variables

```bash
# Database
MONGODB_URL=mongodb://localhost:27017/housing_db
MONGO_ROOT_PASSWORD=your_password

# Redis
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# JWT
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
DEBUG=False
SECRET_KEY=your_app_secret
API_V1_STR=/api/v1
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Project Structure

```
backend/
├── app/                    # Application code
│   ├── api/               # API routes
│   ├── auth.py            # Authentication logic
│   ├── cache.py           # Caching layer
│   ├── config.py          # Configuration
│   ├── database.py        # Database connection
│   ├── models.py          # Data models
│   ├── security.py        # Security middleware
│   └── services/          # Business logic
├── tests/                 # Test suite
├── scripts/               # Utility scripts
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project configuration
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Development services
└── README.md              # This file
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

### Database Migrations

```bash
# Initialize database
python -m app.init_db

# Create indexes
python -m app.create_indexes
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/logout` - User logout

### Properties
- `GET /api/properties` - List properties
- `POST /api/properties` - Create property
- `GET /api/properties/{id}` - Get property
- `PUT /api/properties/{id}` - Update property
- `DELETE /api/properties/{id}` - Delete property

### Rewards
- `GET /api/rewards/wallet` - Get rewards wallet
- `POST /api/rewards/convert-points` - Convert points to cash
- `GET /api/rewards/conversion/history` - Conversion history
- `GET /api/rewards/referral/code` - Get referral code

### Admin
- `GET /api/admin/stats` - System statistics
- `POST /api/admin/process-commission` - Process commission
- `GET /api/admin/users` - User management

## Security Features

### Threat Detection
- SQL injection protection
- XSS attack detection
- Path traversal prevention
- Rate limiting per endpoint
- IP blocking for suspicious activity

### Authentication & Authorization
- JWT token-based authentication
- Role-based access control (RBAC)
- Session management
- Multi-factor authentication support

### Data Protection
- Input sanitization and validation
- Password hashing with bcrypt
- CORS configuration
- Security headers middleware

## Caching Strategy

### Multi-Layer Caching
- **L1**: Application-level caching
- **L2**: Redis distributed caching
- **L3**: Database query caching

### Cache Features
- Intelligent invalidation
- Cache warming for frequently accessed data
- Performance monitoring and metrics
- Fallback mechanisms for cache failures

## Monitoring & Logging

### Health Checks
- `/health` - Basic health check
- `/health/detailed` - Detailed system health
- `/metrics` - Application metrics

### Logging
- Structured JSON logging
- Request/response logging
- Error tracking and alerting
- Performance monitoring

## Deployment

### Production Deployment

```bash
# Build production image
docker build -t propertyyards-backend .

# Run with production configuration
docker run -d --name backend \
  -e MONGODB_URL=mongodb://mongo:27017/housing_db \
  -e REDIS_URL=redis://redis:6379/0 \
  -p 8000:8000 \
  propertyyards-backend
```

### Environment-Specific Configs

- **Development**: Debug mode, local databases
- **Staging**: Production-like setup with test data
- **Production**: Optimized configuration, monitoring enabled

## Performance Optimization

### Database Optimization
- MongoDB indexing strategy
- Connection pooling
- Query optimization
- Data archiving policies

### API Optimization
- Response compression
- Pagination for large datasets
- Caching strategies
- Async/await patterns

### Memory Management
- Connection reuse
- Memory profiling
- Garbage collection optimization
- Resource cleanup

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [API Documentation](http://localhost:8000/docs)
- **Issues**: [GitHub Issues](https://github.com/your-org/propertyyards-backend/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/propertyyards-backend/discussions)

## Related Repositories

- [Frontend Repository](https://github.com/your-org/propertyyards-frontend)
- [Infrastructure Repository](https://github.com/your-org/propertyyards-infrastructure)
- [Documentation Repository](https://github.com/your-org/propertyyards-docs)
