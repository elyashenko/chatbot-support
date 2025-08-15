import React from 'react';
import { ChatMessage as ChatMessageType } from '../../types/chat.types';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { User, Bot, Clock, Zap } from 'lucide-react';

interface ChatMessageProps {
  message: ChatMessageType;
  showMetadata?: boolean;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ 
  message, 
  showMetadata = false 
}) => {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  const formatTime = (timestamp: string) => {
    try {
      return format(new Date(timestamp), 'HH:mm', { locale: ru });
    } catch {
      return '--:--';
    }
  };

  return (
    <div className={`flex gap-3 p-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {isAssistant && (
        <div className="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
          <Bot className="w-5 h-5 text-white" />
        </div>
      )}
      
      <div className={`flex flex-col max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`rounded-lg px-4 py-3 ${
          isUser 
            ? 'bg-blue-500 text-white' 
            : 'bg-gray-100 text-gray-900'
        }`}>
          <ReactMarkdown
            className="prose prose-sm max-w-none"
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={tomorrow}
                    language={match[1]}
                    PreTag="div"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
        
        {showMetadata && (
          <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
            <Clock className="w-3 h-3" />
            <span>{formatTime(message.created_at || '')}</span>
            
            {message.model_used && (
              <>
                <Zap className="w-3 h-3" />
                <span>{message.model_used}</span>
              </>
            )}
            
            {message.response_time && (
              <span>({message.response_time.toFixed(2)}с)</span>
            )}
          </div>
        )}
      </div>
      
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-gray-500 rounded-full flex items-center justify-center">
          <User className="w-5 h-5 text-white" />
        </div>
      )}
    </div>
  );
};
