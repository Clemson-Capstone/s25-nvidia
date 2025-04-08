import React, { useRef, useEffect, useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import ReactMarkdown from 'react-markdown';

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

  // Custom styles for markdown elements
  const markdownStyles = {
    // Add custom styling for markdown elements
    p: "my-1",
    h1: "text-xl font-bold my-2",
    h2: "text-lg font-bold my-2",
    h3: "text-md font-bold my-1",
    ul: "list-disc ml-4 my-2",
    ol: "list-decimal ml-4 my-2",
    li: "ml-2",
    blockquote: "border-l-4 border-border pl-4 italic my-2",
  code: "bg-muted text-muted-foreground rounded px-1 py-0.5 font-mono text-sm",
  pre: "bg-muted text-muted-foreground rounded p-2 my-2 font-mono text-sm overflow-x-auto",
  };

  return (
    <Card className="bg-card/80 backdrop-blur-sm border border-border">
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
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-card text-card-foreground border border-border'
                }`}
              >
                <ReactMarkdown
                  components={{
                    p: ({ node, ...props }) => <p className={markdownStyles.p} {...props} />,
                    h1: ({ node, ...props }) => <h1 className={markdownStyles.h1} {...props} />,
                    h2: ({ node, ...props }) => <h2 className={markdownStyles.h2} {...props} />,
                    h3: ({ node, ...props }) => <h3 className={markdownStyles.h3} {...props} />,
                    ul: ({ node, ...props }) => <ul className={markdownStyles.ul} {...props} />,
                    ol: ({ node, ...props }) => <ol className={markdownStyles.ol} {...props} />,
                    li: ({ node, ...props }) => <li className={markdownStyles.li} {...props} />,
                    blockquote: ({ node, ...props }) => <blockquote className={markdownStyles.blockquote} {...props} />,
                    code: ({ node, inline, ...props }) => 
                      inline ? (
                        <code className={`${markdownStyles.code} ${message.role === 'user' ? 'bg-orange-200/30 text-white' : ''}`} {...props} />
                      ) : (
                        <pre className={`${markdownStyles.pre} ${message.role === 'user' ? 'bg-orange-700/50' : ''}`}><code {...props} /></pre>
                      ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            </div>
          ))}
          {streamingMessage && (
            <div className="mb-4 text-left">
              <div className="inline-block max-w-[80%] p-4 rounded-lg bg-card text-card-foreground border border-border shadow-sm">
                <ReactMarkdown
                  components={{
                    p: ({ node, ...props }) => <p className={markdownStyles.p} {...props} />,
                    h1: ({ node, ...props }) => <h1 className={markdownStyles.h1} {...props} />,
                    h2: ({ node, ...props }) => <h2 className={markdownStyles.h2} {...props} />,
                    h3: ({ node, ...props }) => <h3 className={markdownStyles.h3} {...props} />,
                    ul: ({ node, ...props }) => <ul className={markdownStyles.ul} {...props} />,
                    ol: ({ node, ...props }) => <ol className={markdownStyles.ol} {...props} />,
                    li: ({ node, ...props }) => <li className={markdownStyles.li} {...props} />,
                    blockquote: ({ node, ...props }) => <blockquote className={markdownStyles.blockquote} {...props} />,
                    code: ({ node, inline, ...props }) => 
                      inline ? (
                        <code className={markdownStyles.code} {...props} />
                      ) : (
                        <pre className={markdownStyles.pre}><code {...props} /></pre>
                      ),
                  }}
                >
                  {streamingMessage}
                </ReactMarkdown>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </ScrollArea>

        <form onSubmit={handleSubmit} className="flex gap-3">
          <Textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (inputMessage.trim() && !isLoading) {
                  handleSubmit(e);
                }
              }
            }}
            placeholder="Type your message... (Shift+Enter for new line)"
            className="flex-grow bg-card/50 text-card-foreground"
            disabled={isLoading}
          />
          <Button 
            type="submit" 
            className="bg-gradient-to-r from-primary to-primary/90 text-primary-foreground hover:brightness-110 shadow-sm"
            disabled={isLoading || !inputMessage.trim()}
          >
            {isLoading ? 'Sending...' : 'Send'}
          </Button>
        </form>
        <div className="mt-2">
          <Button onClick={() => startSpeechRecognition(setInputMessage)} className="bg-gradient-to-r from-primary to-primary/90 text-primary-foreground hover:brightness-110 shadow-sm" >
            Start Speaking
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default ChatInterface;
