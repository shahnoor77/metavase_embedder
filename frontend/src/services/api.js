import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userEmail')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const workspaceAPI = {
  // Get all workspaces
  getAll: () => api.get('/api/workspaces'),
  
  // Get workspace by ID
  getById: (id) => api.get(`/api/workspaces/${id}`),
  
  // Create workspace
  create: (data) => api.post('/api/workspaces', data),
  
  // Add user to workspace
  addUser: (workspaceId, userId) => 
    api.post(`/api/workspaces/${workspaceId}/users/${userId}`),
}

export const dashboardAPI = {
  // Get all dashboards for workspace
  getAll: (workspaceId) => 
    api.get('/api/dashboards', { params: { workspace_id: workspaceId } }),
  
  // Get dashboard by ID
  getById: (id) => api.get(`/api/dashboards/${id}`),
  
  // Create dashboard
  create: (data) => api.post('/api/dashboards', data),
}

export const userAPI = {
  // Get current user
  getMe: () => api.get('/api/auth/me'),
}

export default api