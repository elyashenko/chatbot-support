import { WebSocketMessage } from '../types/chat.types';

type MessageHandler = (message: WebSocketMessage) => void;
type ConnectionHandler = (connected: boolean) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private userId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: MessageHandler[] = [];
  private connectionHandlers: ConnectionHandler[] = [];
  private isConnecting = false;

  constructor() {
    this.url = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
    this.userId = '1'; // Временное решение, в реальном приложении получать из аутентификации
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        reject(new Error('Connection already in progress'));
        return;
      }

      this.isConnecting = true;

      try {
        this.ws = new WebSocket(`${this.url}/ws/${this.userId}`);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.notifyConnectionHandlers(true);
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.isConnecting = false;
          this.notifyConnectionHandlers(false);
          
          // Попытка переподключения
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
              this.reconnectAttempts++;
              this.connect().catch(console.error);
            }, this.reconnectDelay * this.reconnectAttempts);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  sendMessage(message: WebSocketMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  // Отправка чат-сообщения
  sendChatMessage(message: string, sessionId?: string, preferredModel?: string): void {
    this.sendMessage({
      type: 'chat',
      message,
      session_id: sessionId,
      preferred_model: preferredModel,
    });
  }

  // Отправка индикатора печати
  sendTypingIndicator(status: 'start' | 'stop'): void {
    this.sendMessage({
      type: 'typing',
      status,
    });
  }

  // Запрос списка сессий
  requestSessions(): void {
    this.sendMessage({
      type: 'session',
      action: 'get_sessions',
    });
  }

  // Запрос сообщений сессии
  requestSessionMessages(sessionId: string): void {
    this.sendMessage({
      type: 'session',
      action: 'get_messages',
      session_id: sessionId,
    });
  }

  // Обновление заголовка сессии
  updateSessionTitle(sessionId: string, title: string): void {
    this.sendMessage({
      type: 'session',
      action: 'update_title',
      session_id: sessionId,
      title,
    });
  }

  // Удаление сессии
  deleteSession(sessionId: string): void {
    this.sendMessage({
      type: 'session',
      action: 'delete_session',
      session_id: sessionId,
    });
  }

  // Подписка на сообщения
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.push(handler);
    return () => {
      const index = this.messageHandlers.indexOf(handler);
      if (index > -1) {
        this.messageHandlers.splice(index, 1);
      }
    };
  }

  // Подписка на изменения состояния соединения
  onConnectionChange(handler: ConnectionHandler): () => void {
    this.connectionHandlers.push(handler);
    return () => {
      const index = this.connectionHandlers.indexOf(handler);
      if (index > -1) {
        this.connectionHandlers.splice(index, 1);
      }
    };
  }

  private handleMessage(message: WebSocketMessage): void {
    this.messageHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in message handler:', error);
      }
    });
  }

  private notifyConnectionHandlers(connected: boolean): void {
    this.connectionHandlers.forEach(handler => {
      try {
        handler(connected);
      } catch (error) {
        console.error('Error in connection handler:', error);
      }
    });
  }

  // Проверка состояния соединения
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  // Получение состояния соединения
  getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }
}

export const websocketService = new WebSocketService();
