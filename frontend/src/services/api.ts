import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  ChatMessage, 
  ChatSession, 
  ChatResponse, 
  SystemStats, 
  ApiError 
} from '../types/chat.types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Добавляем токен авторизации (временное решение)
    this.api.interceptors.request.use((config) => {
      config.headers.Authorization = 'Bearer test-token';
      return config;
    });

    // Обработка ошибок
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error);
        return Promise.reject(error);
      }
    );
  }

  // Чат API
  async sendMessage(message: string, sessionId?: string, preferredModel?: string): Promise<ChatResponse> {
    const response: AxiosResponse<ChatResponse> = await this.api.post('/api/chat/message', {
      message,
      session_id: sessionId,
      preferred_model: preferredModel,
    });
    return response.data;
  }

  async getSessions(limit: number = 20): Promise<ChatSession[]> {
    const response: AxiosResponse<ChatSession[]> = await this.api.get(`/api/chat/sessions?limit=${limit}`);
    return response.data;
  }

  async getSessionMessages(sessionId: string, limit: number = 50): Promise<ChatMessage[]> {
    const response: AxiosResponse<ChatMessage[]> = await this.api.get(
      `/api/chat/sessions/${sessionId}/messages?limit=${limit}`
    );
    return response.data;
  }

  async updateSessionTitle(sessionId: string, title: string): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await this.api.put(
      `/api/chat/sessions/${sessionId}/title`,
      { title }
    );
    return response.data;
  }

  async deleteSession(sessionId: string): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await this.api.delete(
      `/api/chat/sessions/${sessionId}`
    );
    return response.data;
  }

  async getAvailableModels(): Promise<{
    available_models: string[];
    default_model: string;
    fallback_models: string[];
  }> {
    const response: AxiosResponse = await this.api.get('/api/chat/models');
    return response.data;
  }

  async getSystemStats(): Promise<SystemStats> {
    const response: AxiosResponse<SystemStats> = await this.api.get('/api/status');
    return response.data;
  }

  async testChat(): Promise<any> {
    const response: AxiosResponse = await this.api.post('/api/chat/test');
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: number; version: string }> {
    const response: AxiosResponse = await this.api.get('/health');
    return response.data;
  }
}

export const apiService = new ApiService();
