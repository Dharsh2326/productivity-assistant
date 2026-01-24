import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

// Health check
export const healthCheck = async () => {
  try {
    const response = await axios.get('http://localhost:5000/health');
    return response.data;
  } catch (error) {
    throw error;
  }
};

// Parse natural language input
export const parseInput = async (input) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/parse`, { input });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Network error' };
  }
};

// Get all items with optional type filter
export const getItems = async (type = null) => {
  try {
    const url = type ? `${API_BASE_URL}/items?type=${type}` : `${API_BASE_URL}/items`;
    const response = await axios.get(url);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Network error' };
  }
};

// Get items grouped by time (today, tomorrow, upcoming)
export const getItemsGrouped = async (view = 'all') => {
  try {
    const response = await axios.get(`${API_BASE_URL}/items/grouped?view=${view}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Network error' };
  }
};

// Delete an item
export const deleteItem = async (id) => {
  try {
    const response = await axios.delete(`${API_BASE_URL}/items/${id}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Network error' };
  }
};

// Update an item
export const updateItem = async (id, updates) => {
  try {
    const response = await axios.put(`${API_BASE_URL}/items/${id}`, updates);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Network error' };
  }
};

// Semantic search
export const searchItems = async (query) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/search`, { query });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Network error' };
  }
};

// Sync external data (calendar, email)
export const syncExternalData = async () => {
  try {
    const response = await axios.post(`${API_BASE_URL}/sync`);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Network error' };
  }
};

// Generate visual day view
export const visualizeDay = async (date) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/visualize/day`, { date });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Network error' };
  }
};