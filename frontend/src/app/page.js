"use client"

import React, { useState, useRef, useEffect } from 'react';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import edgeCases from '@/app/data/edgecase_dataset.json';

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [streamingMessage, setStreamingMessage] = useState('');
  const [useKnowledgeBase, setUseKnowledgeBase] = useState(false);
  const [canvasToken, setCanvasToken] = useState('');
  const [selectedEdgeCase, setSelectedEdgeCase] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
    fetchDocuments();
  }, [messages, streamingMessage]);

  const fetchDocuments = async () => {
    try {
      const response = await fetch('http://localhost:8081/documents');
      if (!response.ok) throw new Error('Failed to fetch documents');
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
      setError('Failed to fetch documents');
    }
  };

  const handleSubmit = async (e) => {
    if (e) {
      e.preventDefault();
    }
    handleMessageSubmit(inputMessage);

    if (useKnowledgeBase && !canvasToken) {
      setError('Canvas access token is required when using knowledge base');
      return;
    }

    const newMessage = { role: 'user', content: inputMessage };
    setMessages(prev => [...prev, newMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError('');
    setStreamingMessage('');

    let accumulatedMessage = '';

    try {
      const requestBody = {
        messages: [...messages, newMessage],
        use_knowledge_base: useKnowledgeBase,
        canvas_token: useKnowledgeBase ? canvasToken : undefined
      };
      
      console.log('Request body:', requestBody);

      const response = await fetch('http://localhost:8081/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonData = JSON.parse(line.slice(5));
              
              if (jsonData.choices?.[0]?.finish_reason === 'stop') {
                if (accumulatedMessage) {
                  setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: accumulatedMessage
                  }]);
                  setStreamingMessage('');
                }
                break;
              }

              if (jsonData.choices?.[0]?.message?.content) {
                const content = jsonData.choices[0].message.content;
                accumulatedMessage += content;
                setStreamingMessage(accumulatedMessage);
              }
            } catch (e) {
              console.error('Error parsing JSON from chunk:', e);
              continue;
            }
          }
        }
      }

    } catch (error) {
      console.error('Error:', error);
      setError(error.message);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error processing your request. Please try again.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdgeCaseSelect = (value) => {
    const selectedCase = edgeCases.find(c => c.id.toString() === value);
    if (selectedCase) {
      const message = selectedCase.user_input;
      setInputMessage(message);
      handleMessageSubmit(message);
    }
  };

  const handleMessageSubmit = (message) => {
    if (!message.trim()) return;

    if (useKnowledgeBase && !canvasToken) {
      setError('Canvas access token is required when using knowledge base');
      return;
    }

    const newMessage = { role: 'user', content: message };
    setMessages(prev => [...prev, newMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError('');
    setStreamingMessage('');

    let accumulatedMessage = '';

    fetch('http://localhost:8081/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: [...messages, newMessage],
        use_knowledge_base: useKnowledgeBase,
        canvas_token: useKnowledgeBase ? canvasToken : undefined
      }),
    })
    .then(response => {
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      return response.body.getReader();
    })
    .then(reader => {
      const decoder = new TextDecoder();

      function readChunk() {
        return reader.read().then(({ value, done }) => {
          if (done) {
            if (accumulatedMessage) {
              setMessages(prev => [...prev, {
                role: 'assistant',
                content: accumulatedMessage
              }]);
              setStreamingMessage('');
            }
            return;
          }

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const jsonData = JSON.parse(line.slice(5));
                
                if (jsonData.choices?.[0]?.finish_reason === 'stop') {
                  if (accumulatedMessage) {
                    setMessages(prev => [...prev, {
                      role: 'assistant',
                      content: accumulatedMessage
                    }]);
                    setStreamingMessage('');
                  }
                  return;
                }

                if (jsonData.choices?.[0]?.message?.content) {
                  const content = jsonData.choices[0].message.content;
                  accumulatedMessage += content;
                  setStreamingMessage(accumulatedMessage);
                }
              } catch (e) {
                console.error('Error parsing JSON from chunk:', e);
                continue;
              }
            }
          }

          return readChunk();
        });
      }

      return readChunk();
    })
    .catch(error => {
      console.error('Error:', error);
      setError(error.message);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error processing your request. Please try again.' 
      }]);
    })
    .finally(() => {
      setIsLoading(false);
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-100 via-white to-orange-50 p-4">
      {/* Title */}
      <div className="max-w-4xl mx-auto mb-6 text-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-orange-600 to-orange-400 bg-clip-text text-transparent">
          Virtual Teaching Assistant
        </h1>
      </div>

      {/* Settings Card */}
      <div className="max-w-4xl mx-auto mb-6">
        <Card className="bg-white/80 backdrop-blur-sm border border-orange-100">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row md:items-center gap-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="kb-mode"
                  checked={useKnowledgeBase}
                  onCheckedChange={setUseKnowledgeBase}
                />
                <Label htmlFor="kb-mode">Use Knowledge Base</Label>
              </div>
              <div className="flex-1">
                <Input
                  type="password"
                  placeholder="Canvas Access Token"
                  value={canvasToken}
                  onChange={(e) => setCanvasToken(e.target.value)}
                  disabled={!useKnowledgeBase}
                  className="w-full"
                />
              </div>
              <div className="w-full md:w-64">
                <Select onValueChange={handleEdgeCaseSelect}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select test case" />
                  </SelectTrigger>
                  <SelectContent>
                    {edgeCases.map((testCase) => (
                      <SelectItem key={testCase.id} value={testCase.id.toString()}>
                        {testCase.category}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="max-w-4xl mx-auto mb-6">
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      )}

      {/* Chat Interface */}
      <div className="max-w-4xl mx-auto">
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
      </div>
    </div>
  );
}