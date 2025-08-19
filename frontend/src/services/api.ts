import type {
  ChatMessage,
  ChatSession,
  ChatResponse,
  SystemStats
} from '../types/chat.types';

const apiRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const url = `${baseUrl}${endpoint}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000);

  const config: RequestInit = {
    ...options,
    signal: controller.signal,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer test-token',
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} ${response.statusText} – ${errorText}`);
    }

    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    }

    return response.text() as unknown as T;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error('Request timeout');
    }
    throw err;
  }
};

export const chatApi = {
  sendMessage: (message: string, sessionId?: string, preferredModel?: string) =>
    apiRequest<ChatResponse>('/api/chat/message', {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId, preferred_model: preferredModel }),
    }),

  getSessions: (limit = 20) =>
    apiRequest<ChatSession[]>(`/api/chat/sessions?limit=${limit}`),

  getSessionMessages: (sessionId: string, limit = 50) =>
    apiRequest<ChatMessage[]>(`/api/chat/sessions/${sessionId}/messages?limit=${limit}`),

  updateSessionTitle: (sessionId: string, title: string) =>
    apiRequest<{ message: string }>(`/api/chat/sessions/${sessionId}/title`, {
      method: 'PUT',
      body: JSON.stringify({ title }),
    }),

  deleteSession: (sessionId: string) =>
    apiRequest<{ message: string }>(`/api/chat/sessions/${sessionId}`, {
      method: 'DELETE',
    }),

  getAvailableModels: () =>
    apiRequest<{
      available_models: string[];
      default_model: string;
      fallback_models: string[];
    }>('/api/chat/models'),

  getSystemStats: () =>
    apiRequest<SystemStats>('/api/status'),

  testChat: () =>
    apiRequest<any>('/api/chat/test', { method: 'POST' }),

  healthCheck: () =>
    apiRequest<{ status: string; timestamp: number; version: string }>('/health'),
};
