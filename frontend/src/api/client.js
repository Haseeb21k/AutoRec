import axios from 'axios';

// We use VITE_API_URL if set (for production), otherwise fallback to empty string (which uses the current domain/proxy)
const API_URL = import.meta.env.VITE_API_URL || '';

const apiClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    // Default headers if any
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