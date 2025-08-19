import {
  useQuery,
  useMutation,
  useQueryClient,
  useInfiniteQuery
} from '@tanstack/react-query';
import { chatApi } from '../services/api';
import type { ChatMessage, ChatSession, ChatResponse } from '../types/chat.types';

export const chatKeys = {
  all: ['chat'] as const,
  sessionsList: (limit: number) => [...chatKeys.all, 'sessions', limit] as const,
  sessionMessages: (sessionId: string, limit: number) =>
    [...chatKeys.all, 'session', sessionId, 'messages', limit] as const,
  models: () => [...chatKeys.all, 'models'] as const,
  stats: () => [...chatKeys.all, 'stats'] as const,
  health: () => [...chatKeys.all, 'health'] as const,
} as const;

export const useSessions = (limit = 20) =>
  useQuery({
    queryKey: chatKeys.sessionsList(limit),
    queryFn: () => chatApi.getSessions(limit),
    staleTime: 5 * 60_000,
    gcTime: 10 * 60_000,
  });

export const useSessionMessages = (sessionId: string, limit = 50) =>
  useQuery({
    queryKey: chatKeys.sessionMessages(sessionId, limit),
    queryFn: () => chatApi.getSessionMessages(sessionId, limit),
    enabled: !!sessionId,
    staleTime: 2 * 60_000,
  });

export const useSendMessage = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ message, sessionId }: { message: string; sessionId?: string }) =>
      chatApi.sendMessage(message, sessionId),
    onMutate: async ({ message, sessionId }) => {
        if (sessionId) {
          await queryClient.cancelQueries(chatKeys.sessionMessages(sessionId, 50));
          const prev = queryClient.getQueryData<ChatMessage[]>(chatKeys.sessionMessages(sessionId, 50));
          queryClient.setQueryData(chatKeys.sessionMessages(sessionId, 50), old =>
            old ? [...old, { role: 'user', content: message, created_at: new Date().toISOString() }] : []
          );
          return { prev };
        }
      },
      onError: (err, vars, context) => {
        if (vars.sessionId && context?.prev) {
          queryClient.setQueryData(chatKeys.sessionMessages(vars.sessionId, 50), context.prev);
        }
      },
      onSuccess: (data) => {
        if (data.session_id) {
          queryClient.invalidateQueries(chatKeys.sessionsList(20));
          queryClient.invalidateQueries(chatKeys.sessionMessages(data.session_id, 50));
        }
      },
    }
  );
};

export const useUpdateSessionTitle = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ sessionId, title }: { sessionId: string; title: string }) =>
      chatApi.updateSessionTitle(sessionId, title),
    onSuccess: () => {
      queryClient.invalidateQueries(chatKeys.sessionsList(20));
    },
  });
};

export const useDeleteSession = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) =>
      chatApi.deleteSession(sessionId),
    onMutate: async (sessionId: string) => {
      await queryClient.cancelQueries(chatKeys.sessionsList(20));
      const previous = queryClient.getQueryData<ChatSession[]>(chatKeys.sessionsList(20));
      queryClient.setQueryData(
        chatKeys.sessionsList(20),
        old => old?.filter(s => s.id !== sessionId) ?? []
      );
      return { previous };
    },
    onError: (_err, sessionId, context) => {
      if (context?.previous) {
        queryClient.setQueryData(chatKeys.sessionsList(20), context.previous);
      }
    },
    onSuccess: (_data, sessionId) => {
      queryClient.removeQueries(chatKeys.sessionMessages(sessionId, 50));
      queryClient.invalidateQueries(chatKeys.sessionsList(20));
    },
  });
};

// Дополнительно: useAvailableModels(), useSystemStats(), useHealthCheck() по аналогии
