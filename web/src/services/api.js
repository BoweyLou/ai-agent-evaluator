import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API methods
export const apiService = {
  // Health check
  async health() {
    const response = await api.get('/health');
    return response.data;
  },

  // Tasks
  async getTasks(params = {}) {
    const response = await api.get('/tasks', { params });
    return response.data;
  },

  async getTask(taskId) {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  },

  async createTask(formData) {
    const response = await api.post('/tasks', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async deleteTask(taskId) {
    const response = await api.delete(`/tasks/${taskId}`);
    return response.data;
  },

  // Agents
  async getAgents(taskCategory = null) {
    const params = taskCategory ? { task_category: taskCategory } : {};
    const response = await api.get('/agents', { params });
    return response.data;
  },

  async getAgent(agentId) {
    const response = await api.get(`/agents/${agentId}`);
    return response.data;
  },

  // Evaluations
  async getEvaluations(params = {}) {
    const response = await api.get('/evaluations', { params });
    return response.data;
  },

  async getEvaluation(evaluationId) {
    const response = await api.get(`/evaluations/${evaluationId}`);
    return response.data;
  },

  async createEvaluation(data) {
    const response = await api.post('/evaluations', data);
    return response.data;
  },

  async markAgentComplete(evaluationId, agentName) {
    const response = await api.post(`/evaluations/${evaluationId}/agents/${agentName}/complete`);
    return response.data;
  },

  async resetEvaluation(evaluationId) {
    const response = await api.post(`/evaluations/${evaluationId}/reset`);
    return response.data;
  },

  // Results
  async getResultsSummary() {
    const response = await api.get('/results/summary');
    return response.data;
  },

  async getEvaluationComparison(evaluationId) {
    const response = await api.get(`/results/comparison/${evaluationId}`);
    return response.data;
  },

  async getLeaderboard(params = {}) {
    const response = await api.get('/results/leaderboard', { params });
    return response.data;
  },

  async getPerformanceTrends(params = {}) {
    const response = await api.get('/results/trends', { params });
    return response.data;
  },
};

export default api;