# PropertyYards Frontend

Modern React-based frontend application for PropertyYards real estate platform with responsive design, real-time updates, and comprehensive user experience features.

## Features

### Core Functionality
- **Property Browse & Search**: Advanced filtering, sorting, and search capabilities
- **User Authentication**: Secure login, registration, and profile management
- **Property Management**: Create, edit, and manage property listings
- **Interactive Maps**: Location-based property discovery
- **Real-time Updates**: Live notifications and data synchronization

### Advanced Features
- **Responsive Design**: Mobile-first approach with progressive enhancement
- **Performance Optimization**: Code splitting, lazy loading, and caching
- **Accessibility**: WCAG 2.1 compliant with keyboard navigation
- **SEO Optimization**: Server-side rendering ready with meta tags
- **Analytics Integration**: User behavior tracking and insights

## Tech Stack

- **Framework**: React 18.3.1 with Hooks
- **Build Tool**: Vite 5.4.2
- **Routing**: React Router DOM 6.26.2
- **HTTP Client**: Axios 1.16.1
- **Styling**: CSS Modules with responsive design
- **Type Checking**: TypeScript support
- **Testing**: Jest and React Testing Library ready

## Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/propertyyards-frontend.git
   cd propertyyards-frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start development server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

5. **Open browser**
   Navigate to http://localhost:5173

### Docker Setup

```bash
# Build and run with Docker
docker build -t propertyyards-frontend .
docker run -p 5173:5173 propertyyards-frontend

# Or use Docker Compose
docker-compose up -d frontend
```

## Configuration

### Environment Variables

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api
VITE_API_TIMEOUT=10000

# Application
VITE_APP_NAME=PropertyYards
VITE_APP_VERSION=1.0.0
VITE_APP_DESCRIPTION=Real Estate Platform

# Features
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_PWA=true
VITE_ENABLE_OFFLINE=true

# Maps
VITE_MAP_API_KEY=your_map_api_key
VITE_MAP_DEFAULT_LAT=28.6139
VITE_MAP_DEFAULT_LNG=77.2090

# Third-party Services
VITE_GOOGLE_ANALYTICS_ID=GA_MEASUREMENT_ID
VITE_SENTRY_DSN=your_sentry_dsn
```

## Project Structure

```
frontend/
├── public/                 # Static assets
│   ├── favicon.ico        # Favicon
│   ├── manifest.json      # PWA manifest
│   └── robots.txt        # SEO robots
├── src/                   # Source code
│   ├── components/        # Reusable components
│   │   ├── common/        # Common UI components
│   │   ├── forms/         # Form components
│   │   └── layout/        # Layout components
│   ├── pages/             # Page components
│   │   ├── auth/          # Authentication pages
│   │   ├── properties/    # Property pages
│   │   └── profile/       # User profile pages
│   ├── hooks/             # Custom React hooks
│   ├── services/          # API services
│   ├── utils/             # Utility functions
│   ├── styles/            # Global styles
│   ├── types/             # TypeScript types
│   └── App.jsx            # Main App component
├── tests/                 # Test files
├── package.json           # Dependencies and scripts
├── vite.config.js         # Vite configuration
├── Dockerfile             # Docker configuration
└── README.md              # This file
```

## Development

### Available Scripts

```bash
# Development
npm run dev          # Start development server
npm run preview      # Preview production build

# Building
npm run build        # Build for production
npm run build:analyze # Build with bundle analysis

# Testing
npm run test         # Run tests
npm run test:watch   # Run tests in watch mode
npm run test:coverage # Run tests with coverage

# Code Quality
npm run lint         # Run ESLint
npm run lint:fix     # Fix linting issues
npm run format       # Format code with Prettier
npm run type-check   # TypeScript type checking
```

### Component Development

```jsx
// Example component structure
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { propertyService } from '../services/propertyService';
import styles from './PropertyList.module.css';

const PropertyList = ({ filters = {} }) => {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadProperties();
  }, [filters]);

  const loadProperties = async () => {
    try {
      setLoading(true);
      const data = await propertyService.getProperties(filters);
      setProperties(data);
    } catch (error) {
      console.error('Failed to load properties:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      {/* Component JSX */}
    </div>
  );
};

export default PropertyList;
```

### API Integration

```javascript
// Example service
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: import.meta.env.VITE_API_TIMEOUT,
});

// Request interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle authentication error
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const propertyService = {
  getProperties: (filters) => api.get('/properties', { params: filters }),
  getProperty: (id) => api.get(`/properties/${id}`),
  createProperty: (data) => api.post('/properties', data),
  updateProperty: (id, data) => api.put(`/properties/${id}`, data),
  deleteProperty: (id) => api.delete(`/properties/${id}`),
};
```

## Styling

### CSS Modules

```css
/* PropertyList.module.css */
.container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 2rem;
  padding: 2rem;
}

.propertyCard {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
}

.propertyCard:hover {
  transform: translateY(-4px);
}

@media (max-width: 768px) {
  .container {
    grid-template-columns: 1fr;
    padding: 1rem;
  }
}
```

### Responsive Design

The application uses a mobile-first approach with breakpoints:
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px  
- **Desktop**: > 1024px

## Performance Optimization

### Code Splitting

```javascript
// Lazy loading components
const PropertyDetail = React.lazy(() => import('./pages/PropertyDetail'));
const UserProfile = React.lazy(() => import('./pages/UserProfile'));

// Route with lazy loading
<Route path="/properties/:id" element={
  <Suspense fallback={<div>Loading...</div>}>
    <PropertyDetail />
  </Suspense>
} />
```

### Image Optimization

```jsx
// Optimized image component
const OptimizedImage = ({ src, alt, ...props }) => {
  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      decoding="async"
      {...props}
    />
  );
};
```

## Testing

### Component Testing

```jsx
// PropertyList.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import PropertyList from './PropertyList';

const mockProperties = [
  { id: 1, title: 'Test Property', price: 100000 },
];

jest.mock('../services/propertyService');

test('renders property list', async () => {
  propertyService.getProperties.mockResolvedValue(mockProperties);
  
  render(
    <BrowserRouter>
      <PropertyList />
    </BrowserRouter>
  );
  
  await waitFor(() => {
    expect(screen.getByText('Test Property')).toBeInTheDocument();
  });
});
```

## Deployment

### Build for Production

```bash
# Build optimized bundle
npm run build

# Preview build locally
npm run preview
```

### Environment-Specific Builds

```bash
# Development build
npm run build:dev

# Staging build
npm run build:staging

# Production build
npm run build:prod
```

### Deployment Platforms

#### Netlify
```bash
# Deploy to Netlify
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

#### Vercel
```bash
# Deploy to Vercel
npm install -g vercel
vercel --prod
```

#### Docker
```bash
# Build and deploy Docker image
docker build -t propertyyards-frontend .
docker push your-registry/propertyyards-frontend:latest
```

## Accessibility

### WCAG 2.1 Compliance

- Semantic HTML5 elements
- ARIA labels and roles
- Keyboard navigation support
- Screen reader compatibility
- Focus management
- Color contrast compliance

### Example Accessible Component

```jsx
const AccessibleButton = ({ children, onClick, ...props }) => {
  return (
    <button
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onClick(e);
        }
      }}
      aria-label={props['aria-label']}
      role="button"
      tabIndex={0}
      {...props}
    >
      {children}
    </button>
  );
};
```

## SEO Optimization

### Meta Tags

```jsx
// SEO component
const SEO = ({ title, description, keywords, image }) => {
  return (
    <Helmet>
      <title>{title} | PropertyYards</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={image} />
      <meta name="twitter:card" content="summary_large_image" />
    </Helmet>
  );
};
```

### Structured Data

```jsx
// JSON-LD structured data
const PropertyStructuredData = ({ property }) => {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "RealEstateListing",
    "name": property.title,
    "description": property.description,
    "image": property.images[0],
    "offers": {
      "@type": "Offer",
      "price": property.price,
      "priceCurrency": "INR"
    }
  };

  return (
    <script type="application/ld+json">
      {JSON.stringify(structuredData)}
    </script>
  );
};
```

## Monitoring & Analytics

### Error Tracking

```javascript
// Sentry integration
import * as Sentry from '@sentry/react';

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE,
});
```

### Analytics

```javascript
// Google Analytics
import ReactGA from 'react-ga4';

ReactGA.initialize(import.meta.env.VITE_GOOGLE_ANALYTICS_ID);

// Track page views
const trackPageView = (path) => {
  ReactGA.send({ hitType: 'pageview', page: path });
};

// Track events
const trackEvent = (category, action, label) => {
  ReactGA.event({ category, action, label });
};
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style Guidelines

- Use ESLint and Prettier configurations
- Follow React best practices
- Write meaningful commit messages
- Include tests for new features
- Update documentation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [Component Documentation](./docs/components.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/propertyyards-frontend/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/propertyyards-frontend/discussions)

## Related Repositories

- [Backend Repository](https://github.com/your-org/propertyyards-backend)
- [Infrastructure Repository](https://github.com/your-org/propertyyards-infrastructure)
- [Documentation Repository](https://github.com/your-org/propertyyards-docs)
