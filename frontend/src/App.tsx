import { ChatContainer } from './components/Chat/ChatContainer';
import { useChat } from './hooks/useChat';

function App() {
  const {
    messages,
    isLoading,
    isTyping,
    isConnected,
    error,
    sendMessage,
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
