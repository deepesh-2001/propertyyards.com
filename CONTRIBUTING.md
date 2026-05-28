# Contributing to PropertyYards Platform

Thank you for your interest in contributing to PropertyYards! This guide will help you get started with contributing to our real estate SaaS platform.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- Docker & Docker Compose
- Git
- MongoDB (local or MongoDB Atlas)
- Redis (local or Redis Cloud)

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/housing_platform.git
   cd housing_platform
   ```

2. **Set up Python environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up frontend environment**
   ```bash
   cd frontend
   npm install
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

5. **Start development services**
   ```bash
   # Start databases and services
   docker-compose -f docker-compose.local.yml up -d
   
   # Start backend API
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Start frontend (in another terminal)
   cd frontend
   npm run dev
   ```

## 📋 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes

- Follow the existing code style and patterns
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 3. Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### 4. Commit Your Changes

Follow our commit message convention:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(auth): add two-factor authentication
fix(api): resolve property listing pagination bug
docs(readme): update installation instructions
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Create a pull request with:
- Clear description of changes
- Related issues
- Testing instructions
- Screenshots if applicable

## 🏗️ Project Structure

```
housing_platform/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── routers/        # API route handlers
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom hooks
│   │   └── utils/          # Utility functions
│   ├── public/             # Static assets
│   └── package.json        # Node dependencies
├── microservices/          # Additional microservices
├── k8s/                    # Kubernetes manifests
├── .github/workflows/      # CI/CD workflows
└── docs/                   # Documentation
```

## 🧪 Testing Guidelines

### Backend Testing

- Use `pytest` for unit and integration tests
- Mock external dependencies
- Test both success and error cases
- Aim for >80% code coverage

```python
# Example test structure
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_property():
    response = client.post("/api/properties", json={
        "title": "Test Property",
        "price": 250000,
        "location": "Test City"
    })
    assert response.status_code == 201
    assert response.json()["title"] == "Test Property"
```

### Frontend Testing

- Use `Jest` and `React Testing Library`
- Test component behavior, not implementation
- Use meaningful test descriptions
- Test user interactions

```javascript
// Example component test
import { render, screen, fireEvent } from '@testing-library/react';
import PropertyCard from '../components/PropertyCard';

test('renders property card with correct information', () => {
  const property = {
    title: 'Test Property',
    price: 250000,
    location: 'Test City'
  };
  
  render(<PropertyCard property={property} />);
  
  expect(screen.getByText('Test Property')).toBeInTheDocument();
  expect(screen.getByText('$250,000')).toBeInTheDocument();
  expect(screen.getByText('Test City')).toBeInTheDocument();
});
```

## 📝 Code Style Guidelines

### Python (Backend)

- Follow PEP 8
- Use `black` for formatting
- Use `flake8` for linting
- Use type hints where possible
- Maximum line length: 88 characters

```bash
# Format code
black backend/

# Lint code
flake8 backend/
```

### JavaScript/TypeScript (Frontend)

- Use ESLint and Prettier
- Follow Airbnb style guide
- Use TypeScript for new components
- Maximum line length: 100 characters

```bash
# Format code
npm run format

# Lint code
npm run lint
```

## 🔧 Development Tools

### Recommended VS Code Extensions

- Python
- ES7+ React/Redux/React-Native snippets
- Prettier - Code formatter
- ESLint
- Docker
- GitLens
- Thunder Client (for API testing)

### Environment Variables

Never commit sensitive information! Use `.env.example` as a template:

```bash
# Required for development
DATABASE_URL=mongodb://localhost:27017/housing_db
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your-development-secret

# Optional for testing
STRIPE_SECRET_KEY=sk_test_...
GEMINI_API_KEY=your-test-key
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment**: OS, Python/Node version, browser
2. **Steps to reproduce**: Detailed reproduction steps
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Error messages**: Full error logs/stack traces
6. **Screenshots**: If applicable

## 💡 Feature Requests

For feature requests:

1. Check existing issues first
2. Provide clear use case and motivation
3. Consider implementation complexity
4. Suggest API design if applicable

## 📚 Documentation

- Update README.md for major changes
- Add inline comments for complex logic
- Update API documentation in docstrings
- Create/update user guides for new features

## 🤝 Code Review Process

1. **Self-review**: Review your own changes first
2. **Automated checks**: Ensure CI/CD passes
3. **Peer review**: At least one team member review
4. **Approval**: Required approval before merge
5. **Deployment**: Automated after merge to main

## 🚀 Release Process

1. Update version numbers
2. Update CHANGELOG.md
3. Create release tag
4. Automated deployment to staging
5. Manual testing on staging
6. Deploy to production

## 📞 Getting Help

- Create an issue for bugs or questions
- Join our Slack/Discord community
- Check existing documentation
- Review similar issues/PRs

## 🏆 Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- Annual contributor highlights

Thank you for contributing to PropertyYards! 🎉
