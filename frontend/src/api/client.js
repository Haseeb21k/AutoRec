import axios from 'axios';

// Create a dedicated Axios instance
const apiClient = axios.create({
  // We use /api because vite.config.js proxies this to http://127.0.0.1:8000
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a response interceptor to handle generic errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      sessionStorage.removeItem('token');
      // Force redirect to login
      window.location.href = '/login';
    }
    console.error("API Error:", error.response ? error.response.data : error.message);
    return Promise.reject(error);
  }
);

export default apiClient;