// API Configuration for different environments
const API_CONFIG = {
  development: {
    baseURL: 'http://localhost:8000/api',
  },
  production: {
    baseURL: 'https://your-backend-api.com/api', // Replace with your actual backend URL
  },
  staging: {
    baseURL: 'https://your-staging-api.com/api', // Replace with staging backend if needed
  }
};

// Get current environment
const getEnvironment = () => {
  if (import.meta.env.DEV) return 'development';
  if (import.meta.env.PROD) return 'production';
  return 'development';
};

// Export API base URL for current environment
export const API_BASE_URL = API_CONFIG[getEnvironment()].baseURL;

// Export full config if needed
export default API_CONFIG;
