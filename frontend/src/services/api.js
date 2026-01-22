import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

export const parseInput = async (input) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/parse`, { input });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Network error' };
  }
};

export const getItems = async (type = null) => {
  try {
    const url = type ? `${API_BASE_URL}/items?type=${type}` : `${API_BASE_URL}/items`;
    const response = await axios.get(url);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Network error' };
  }
};

export const deleteItem = async (id) => {
  try {
    const response = await axios.delete(`${API_BASE_URL}/items/${id}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Network error' };
  }
};

export const updateItem = async (id, updates) => {
  try {
    const response = await axios.put(`${API_BASE_URL}/items/${id}`, updates);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Network error' };
  }
};

export const searchItems = async (query) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/search`, { query });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Network error' };
  }
};

export const healthCheck = async () => {
  try {
    const response = await axios.get('http://localhost:5000/health');
    return response.data;
  } catch (error) {
    throw error;
  }
};