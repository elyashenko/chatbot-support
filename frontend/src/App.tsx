import React from 'react';
import { ChatContainer } from './components/Chat/ChatContainer';
import { useChat } from './hooks/useChat';
import './App.css';

function App() {
  const {
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
  } = useChat();

  return (
    <div className="App h-screen bg-gray-50">
      <ChatContainer
        messages={messages}
        onSendMessage={sendMessage}
        isLoading={isLoading}
        isTyping={isTyping}
        isConnected={isConnected}
        error={error}
        onClearError={clearError}
      />
    </div>
  );
}

export default App;
