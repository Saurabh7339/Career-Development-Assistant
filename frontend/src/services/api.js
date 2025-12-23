import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Profile APIs
export const profileAPI = {
  // Create profile with structured data
  create: async (profileData) => {
    const response = await api.post('/api/profiles/create', profileData);
    return response.data;
  },

  // Upload profile via text description
  upload: async (profileText) => {
    const response = await api.post('/api/profiles/upload', {
      profile_text: profileText,
    });
    return response.data;
  },

  // Get profile by ID
  get: async (profileId) => {
    const response = await api.get(`/api/profiles/${profileId}`);
    return response.data;
  },

  // List all profiles
  list: async () => {
    const response = await api.get('/api/profiles');
    return response.data;
  },

  // Update profile
  update: async (profileId, profileData) => {
    const response = await api.put(`/api/profiles/${profileId}`, profileData);
    return response.data;
  },

  // Delete profile
  delete: async (profileId) => {
    const response = await api.delete(`/api/profiles/${profileId}`);
    return response.data;
  },

  // Get reports for a profile
  getReports: async (profileId) => {
    const response = await api.get(`/api/profiles/${profileId}/reports`);
    return response.data;
  },
};

// Analysis API
export const analysisAPI = {
  // Analyze skill gap
  analyze: async (requestData) => {
    const response = await api.post('/api/analyze', requestData);
    return response.data;
  },
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;

