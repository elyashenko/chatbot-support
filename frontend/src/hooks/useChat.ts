import { useState, useEffect, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { websocketService } from '../services/websocket';
import type { ChatMessage, ChatSession, WebSocketMessage } from '../types/chat.types';

import {
  useSessions,
  useSessionMessages,
  useSendMessage,
  useUpdateSessionTitle,
  useDeleteSession,
  chatKeys
} from './useChatQueries';

export const useChat = () => {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const { data: sessions = [], refetch: refetchSessions } = useSessions(20);
  const { data: messages = [] } = useSessionMessages(currentSessionId || '', 50);

  const sendMessageMutation = useSendMessage();
  const updateTitleMutation = useUpdateSessionTitle();
  const deleteSessionMutation = useDeleteSession();

  // WebSocket остаётся без изменений
  useEffect(() => {
    websocketService.connect().catch(err => {
      console.error(err);
      setError('Ошибка подключения');
    });
    const unsubMsg = websocketService.onMessage(handleWS);
    const unsubConn = websocketService.onConnectionChange(setIsConnected);
    return () => {
      unsubMsg();
      unsubConn();
      websocketService.disconnect();
    };
  }, []);

  const handleWS = useCallback((msg: WebSocketMessage) => {
    switch (msg.type) {
      case 'typing':
        setIsTyping(msg.status === 'start');
        break;
      case 'chat_response':
        if (msg.success && msg.response && msg.session_id) {
          const newMsg: ChatMessage = {
            role: 'assistant',
            content: msg.response,
            model_used: msg.model_used,
            response_time: msg.response_time,
            created_at: new Date().toISOString(),
          };
          queryClient.setQueryData(
            chatKeys.sessionMessages(msg.session_id, 50),
            old => old ? [...old, newMsg] : [newMsg]
          );
          queryClient.invalidateQueries(chatKeys.sessionsList(20));
          setCurrentSessionId(msg.session_id);
        } else {
          setError('Ошибка ответа');
        }
        break;
      case 'sessions_list':
        if (msg.sessions) {
          queryClient.setQueryData(chatKeys.sessionsList(20), msg.sessions);
        }
        break;
      case 'messages_list':
        if (msg.messages && currentSessionId) {
          queryClient.setQueryData(
            chatKeys.sessionMessages(currentSessionId, 50),
            msg.messages
          );
        }
        break;
      case 'error':
        setError(msg.message || 'Ошибка');
        break;
    }
  }, [currentSessionId, queryClient]);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim()) return;
    setIsLoading(true);
    setError(null);
    websocketService.sendChatMessage(text, currentSessionId || undefined);
    try {
      await sendMessageMutation.mutateAsync({ message: text, sessionId: currentSessionId || undefined });
    } catch {
      setError('Ошибка отправки');
    } finally {
      setIsLoading(false);
    }
  }, [currentSessionId, sendMessageMutation]);

  const loadSession = useCallback((sid: string) => {
    setIsLoading(true);
    setError(null);
    websocketService.requestSessionMessages(sid);
    setCurrentSessionId(sid);
    setIsLoading(false);
  }, []);

  const createNewSession = () => {
    setCurrentSessionId(null);
    setError(null);
  };

  const updateSessionTitle = async (sid: string, title: string) => {
    try {
      await updateTitleMutation.mutateAsync({ sessionId: sid, title });
    } catch {
      setError('Ошибка обновления');
    }
  };

  const deleteSession = async (sid: string) => {
    try {
      await deleteSessionMutation.mutateAsync(sid);
      if (sid === currentSessionId) createNewSession();
    } catch {
      setError('Ошибка удаления');
    }
  };

  const loadSessions = async () => {
    websocketService.requestSessions();
    await refetchSessions();
  };

  const clearError = () => setError(null);

  useEffect(() => { loadSessions(); }, []);

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
