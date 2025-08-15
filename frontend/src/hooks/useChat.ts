import { useState, useEffect, useCallback, useRef } from 'react';
import { ChatMessage, ChatSession, WebSocketMessage } from '../types/chat.types';
import { apiService } from '../services/api';
import { websocketService } from '../services/websocket';

interface UseChatReturn {
  messages: ChatMessage[];
  sessions: ChatSession[];
  currentSessionId: string | null;
  isLoading: boolean;
  isTyping: boolean;
  isConnected: boolean;
  error: string | null;
  sendMessage: (message: string) => void;
  loadSession: (sessionId: string) => void;
  createNewSession: () => void;
  updateSessionTitle: (sessionId: string, title: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  loadSessions: () => Promise<void>;
  clearError: () => void;
}

export const useChat = (): UseChatReturn => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const messageQueue = useRef<ChatMessage[]>([]);

  // Подключение к WebSocket
  useEffect(() => {
    const connectWebSocket = async () => {
      try {
        await websocketService.connect();
      } catch (err) {
        console.error('Failed to connect WebSocket:', err);
        setError('Ошибка подключения к серверу');
      }
    };

    connectWebSocket();

    // Подписка на сообщения WebSocket
    const unsubscribeMessage = websocketService.onMessage(handleWebSocketMessage);
    const unsubscribeConnection = websocketService.onConnectionChange(setIsConnected);

    return () => {
      unsubscribeMessage();
      unsubscribeConnection();
      websocketService.disconnect();
    };
  }, []);

  // Обработка WebSocket сообщений
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'connection':
        console.log('Connected to WebSocket');
        break;

      case 'typing':
        setIsTyping(message.status === 'start');
        break;

      case 'chat_response':
        if (message.success && message.response) {
          const newMessage: ChatMessage = {
            role: 'assistant',
            content: message.response,
            model_used: message.model_used,
            response_time: message.response_time,
            created_at: new Date().toISOString(),
          };
          
          setMessages(prev => [...prev, newMessage]);
          
          // Обновляем текущую сессию
          if (message.session_id) {
            setCurrentSessionId(message.session_id);
          }
        } else {
          setError('Ошибка получения ответа от сервера');
        }
        break;

      case 'sessions_list':
        if (message.sessions) {
          setSessions(message.sessions);
        }
        break;

      case 'messages_list':
        if (message.messages) {
          setMessages(message.messages);
        }
        break;

      case 'error':
        setError(message.message || 'Произошла ошибка');
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }, []);

  // Отправка сообщения
  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim()) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      // Отправляем через WebSocket
      websocketService.sendChatMessage(message, currentSessionId);
      
      // Также отправляем через REST API как fallback
      const response = await apiService.sendMessage(message, currentSessionId);
      
      if (response.success) {
        setCurrentSessionId(response.session_id);
      }
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Ошибка отправки сообщения');
    } finally {
      setIsLoading(false);
    }
  }, [currentSessionId]);

  // Загрузка сессии
  const loadSession = useCallback(async (sessionId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      // Загружаем через WebSocket
      websocketService.requestSessionMessages(sessionId);
      
      // Также загружаем через REST API как fallback
      const messages = await apiService.getSessionMessages(sessionId);
      setMessages(messages);
      setCurrentSessionId(sessionId);
    } catch (err) {
      console.error('Error loading session:', err);
      setError('Ошибка загрузки сессии');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Создание новой сессии
  const createNewSession = useCallback(() => {
    setMessages([]);
    setCurrentSessionId(null);
    setError(null);
  }, []);

  // Обновление заголовка сессии
  const updateSessionTitle = useCallback(async (sessionId: string, title: string) => {
    try {
      await apiService.updateSessionTitle(sessionId, title);
      await loadSessions(); // Перезагружаем список сессий
    } catch (err) {
      console.error('Error updating session title:', err);
      setError('Ошибка обновления заголовка сессии');
    }
  }, []);

  // Удаление сессии
  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      await apiService.deleteSession(sessionId);
      
      if (currentSessionId === sessionId) {
        createNewSession();
      }
      
      await loadSessions(); // Перезагружаем список сессий
    } catch (err) {
      console.error('Error deleting session:', err);
      setError('Ошибка удаления сессии');
    }
  }, [currentSessionId, createNewSession]);

  // Загрузка списка сессий
  const loadSessions = useCallback(async () => {
    try {
      // Загружаем через WebSocket
      websocketService.requestSessions();
      
      // Также загружаем через REST API как fallback
      const sessions = await apiService.getSessions();
      setSessions(sessions);
    } catch (err) {
      console.error('Error loading sessions:', err);
      setError('Ошибка загрузки списка сессий');
    }
  }, []);

  // Очистка ошибки
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Загружаем сессии при монтировании
  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  return {
    messages,
    sessions,
    currentSessionId,
    isLoading,
    isTyping,
    isConnected,
    error,
    sendMessage,
    loadSession,
    createNewSession,
    updateSessionTitle,
    deleteSession,
    loadSessions,
    clearError,
  };
};
