// API Configuration for different environments.
// NOTE: baseURL is the ORIGIN only (no trailing /api). All endpoint paths in
// services/api.js already include the leading "/api". In development an empty
// string is used so requests stay relative and go through the Vite dev proxy
// (see vite.config.js) which forwards /api -> http://localhost:8000.
const API_CONFIG = {
  development: {
    baseURL: '', // relative -> handled by Vite proxy
  },
  production: {
    // Replace with your actual backend origin (no trailing /api).
    // Can also be overridden at build time via VITE_API_BASE_URL.
    baseURL: import.meta.env.VITE_API_BASE_URL || 'https://your-backend-api.com',
  },
  staging: {
    baseURL: import.meta.env.VITE_API_BASE_URL || 'https://your-staging-api.com',
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
