export interface ChatMessage {
  id?: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  model_used?: string;
  tokens_used?: number;
  response_time?: number;
  created_at?: string;
  context_sources?: string;
  similarity_scores?: string;
}

export interface ChatSession {
  session_id: string;
  title: string;
  model_used: string;
  created_at: string;
  updated_at: string;
  last_message: string;
  message_count: number;
}

export interface ChatResponse {
  session_id: string;
  response: string;
  model_used: string;
  context_sources: ContextSource[];
  similarity_scores: number[];
  response_time: number;
  success: boolean;
}

export interface ContextSource {
  id: string;
  title: string;
  url?: string;
  similarity: number;
}

export interface WebSocketMessage {
  type: 'chat' | 'typing' | 'session' | 'connection' | 'chat_response' | 'error';
  message?: string;
  session_id?: string;
  preferred_model?: string;
  status?: 'start' | 'stop';
  action?: string;
  response?: string;
  model_used?: string;
  context_sources?: ContextSource[];
  similarity_scores?: number[];
  response_time?: number;
  success?: boolean;
  sessions?: ChatSession[];
  messages?: ChatMessage[];
  timestamp?: number;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface SystemStats {
  status: string;
  available_models: string[];
  vector_store_stats: {
    total_documents: number;
    collection_name: string;
    persist_directory: string;
  };
  websocket_connections: number;
}
