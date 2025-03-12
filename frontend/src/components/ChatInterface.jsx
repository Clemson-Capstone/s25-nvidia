import React, { useRef, useEffect } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

const ChatInterface = ({
  messages,
  streamingMessage,
  inputMessage,
  setInputMessage,
  handleSubmit,
  isLoading
}) => {
  const messagesEndRef = useRef(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <Card className="bg-white/80 backdrop-blur-sm border border-orange-100">
      <CardContent className="p-6">
        <ScrollArea className="h-[600px] mb-4 pr-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`mb-4 ${
                message.role === 'user' ? 'text-right' : 'text-left'
              }`}
            >
              <div
                className={`inline-block max-w-[80%] p-4 rounded-lg shadow-sm ${
                  message.role === 'user'
                    ? 'bg-gradient-to-r from-orange-500 to-orange-600 text-white'
                    : 'bg-white text-gray-800 border border-orange-100'
                }`}
              >
                {message.content}
              </div>
            </div>
          ))}
          {streamingMessage && (
            <div className="mb-4 text-left">
              <div className="inline-block max-w-[80%] p-4 rounded-lg bg-white text-gray-800 border border-orange-100 shadow-sm">
                {streamingMessage}
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </ScrollArea>

        <form onSubmit={handleSubmit} className="flex gap-3">
          <Input
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Type your message..."
            className="flex-grow bg-white/50"
            disabled={isLoading}
          />
          <Button 
            type="submit" 
            className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white shadow-sm"
            disabled={isLoading}
          >
            {isLoading ? 'Sending...' : 'Send'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export default ChatInterface;