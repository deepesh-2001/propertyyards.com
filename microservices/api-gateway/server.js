/**
 * PropertyYards API Gateway
 * Routes requests to appropriate microservices
 * Handles load balancing, rate limiting, and caching
 */

const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const cors = require('cors');
const morgan = require('morgan');

const app = express();
const PORT = process.env.PORT || 3000;

// Service URLs from environment variables
const SERVICES = {
  auth: process.env.AUTH_SERVICE_URL || 'http://localhost:8001',
  property: process.env.PROPERTY_SERVICE_URL || 'http://localhost:8002',
  user: process.env.USER_SERVICE_URL || 'http://localhost:8003',
  report: process.env.REPORT_SERVICE_URL || 'http://localhost:8004',
  insurance: process.env.INSURANCE_SERVICE_URL || 'http://localhost:8005',
  ai: process.env.AI_SERVICE_URL || 'http://localhost:8006',
  notification: process.env.NOTIFICATION_SERVICE_URL || 'http://localhost:8007',
  analytics: process.env.ANALYTICS_SERVICE_URL || 'http://localhost:8008',
};

// Security middleware
app.use(helmet());
app.use(cors({
  origin: ['https://propertyyards.com', 'https://*.propertyyards.vercel.app'],
  credentials: true
}));

// Logging
app.use(morgan('combined'));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 1000, // limit each IP to 1000 requests per windowMs
  message: {
    error: 'Too many requests, please try again later.'
  }
});
app.use('/api/', limiter);

// Health check endpoint
app.get('/api/health', async (req, res) => {
  const health = {
    gateway: 'healthy',
    timestamp: new Date().toISOString(),
    services: {}
  };

  // Check each service health
  for (const [name, url] of Object.entries(SERVICES)) {
    try {
      const response = await fetch(`${url}/health`, { 
        method: 'GET',
        timeout: 5000 
      });
      health.services[name] = response.ok ? 'healthy' : 'unhealthy';
    } catch (error) {
      health.services[name] = 'unreachable';
    }
  }

  const allHealthy = Object.values(health.services).every(s => s === 'healthy');
  res.status(allHealthy ? 200 : 503).json(health);
});

// Gateway status
app.get('/api/gateway/status', (req, res) => {
  res.json({
    status: 'running',
    version: '1.0.0',
    services: Object.keys(SERVICES),
    uptime: process.uptime()
  });
});

// Service routing
const createServiceProxy = (serviceUrl, pathRewrite = {}) => {
  return createProxyMiddleware({
    target: serviceUrl,
    changeOrigin: true,
    pathRewrite,
    onError: (err, req, res) => {
      console.error(`Proxy error: ${err.message}`);
      res.status(502).json({
        error: 'Service temporarily unavailable',
        message: 'The requested service is currently unreachable'
      });
    },
    onProxyReq: (proxyReq, req, res) => {
      console.log(`[${req.method}] ${req.path} → ${serviceUrl}`);
    }
  });
};

// Route to services
app.use('/api/auth', createServiceProxy(SERVICES.auth));
app.use('/api/properties', createServiceProxy(SERVICES.property));
app.use('/api/users', createServiceProxy(SERVICES.user));
app.use('/api/reports', createServiceProxy(SERVICES.report));
app.use('/api/insurance', createServiceProxy(SERVICES.insurance));
app.use('/api/ai', createServiceProxy(SERVICES.ai));
app.use('/api/notifications', createServiceProxy(SERVICES.notification));
app.use('/api/analytics', createServiceProxy(SERVICES.analytics));

// Cron health check endpoint for Vercel
app.get('/api/cron/health-check', async (req, res) => {
  // This endpoint is called by Vercel Cron every 6 hours
  console.log('[CRON] Health check triggered at', new Date().toISOString());
  
  // Perform health checks
  const results = {};
  for (const [name, url] of Object.entries(SERVICES)) {
    try {
      const response = await fetch(`${url}/health`, { timeout: 10000 });
      results[name] = {
        status: response.ok ? 'healthy' : 'unhealthy',
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      results[name] = {
        status: 'error',
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }
  
  res.json({
    cron: 'health-check',
    timestamp: new Date().toISOString(),
    services: results
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.path} not found`,
    availableRoutes: [
      '/api/auth',
      '/api/properties',
      '/api/users',
      '/api/reports',
      '/api/insurance',
      '/api/ai',
      '/api/notifications',
      '/api/analytics',
      '/api/health'
    ]
  });
});

// Error handler
app.use((err, req, res, next) => {
  console.error('Gateway error:', err);
  res.status(500).json({
    error: 'Internal Server Error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
  });
});

app.listen(PORT, () => {
  console.log(`🚀 API Gateway running on port ${PORT}`);
  console.log('📦 Services configured:');
  Object.entries(SERVICES).forEach(([name, url]) => {
    console.log(`  - ${name}: ${url}`);
  });
});

module.exports = app;
