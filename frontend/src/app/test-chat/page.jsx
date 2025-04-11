'use client'

import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import ReactMarkdown from 'react-markdown';

export default function TestChat() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [streamingOutput, setStreamingOutput] = useState('');
  const [response, setResponse] = useState('');
  const [citations, setCitations] = useState([]);
  const [isDebugMode, setIsDebugMode] = useState(true);
  const [useSystemPrompt, setUseSystemPrompt] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState("You are a helpful AI assistant named Envie. You will only reply based on the context provided.");
  
  const RAG_SERVER_URL = "http://localhost:8081";
  
  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim()) return;
    
    setIsLoading(true);
    setError('');
    setStreamingOutput('');
    setResponse('');
    setCitations([]);
    
    // Add message to history
    const newMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, newMessage]);
    setInput('');
    
    // Buffer for incomplete lines
    let buffer = '';
    
    try {
      // Prepare messages array including an optional system message
      let allMessages = [...messages, newMessage].map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      // Add system message if enabled
      if (useSystemPrompt) {
        allMessages.unshift({
          role: "system",
          content: systemPrompt
        });
      }
      
      const requestBody = {
        messages: allMessages,
        use_knowledge_base: true,
        temperature: 0.2,
        top_p: 0.7,
        max_tokens: 1024,
        reranker_top_k: 2,
        vdb_top_k: 10,
        vdb_endpoint: "http://milvus:19530", 
        collection_name: "default",
        enable_query_rewriting: true,
        enable_reranker: true,
        enable_citations: true,
        model: "meta/llama-3.1-70b-instruct",
        reranker_model: "nvidia/llama-3.2-nv-rerankqa-1b-v2",
        embedding_model: "nvidia/llama-3.2-nv-embedqa-1b-v2",
        stop: []
      };
      
      console.log("Sending request:", requestBody);
      
      const response = await fetch(`${RAG_SERVER_URL}/v1/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Handle streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';
      let latestCitations = [];
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        buffer += chunk;
        
        if (isDebugMode) {
          // Show raw chunks in debug mode
          setStreamingOutput(prev => prev + "\n\n--- NEW CHUNK ---\n" + chunk);
        }
        
        // Split on newlines, keeping potentially incomplete line in buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.trim() === '' || !line.startsWith('data: ')) continue;
          
          try {
            const data = JSON.parse(line.slice(5));
            console.log("Parsed data:", data);
            
            // Handle different response formats
            if (data.choices?.[0]?.delta?.content) {
              accumulatedContent += data.choices[0].delta.content;
              setResponse(accumulatedContent);
            } 
            else if (data.choices?.[0]?.message?.content) {
              if (!accumulatedContent.endsWith(data.choices[0].message.content)) {
                accumulatedContent += data.choices[0].message.content;
                setResponse(accumulatedContent);
              }
            }
            else if (data.content) {
              accumulatedContent = data.content;
              setResponse(data.content);
            }
            
            // Handle citations
            if (data.citations?.results?.length > 0) {
              latestCitations = data.citations.results;
              setCitations(latestCitations);
            } 
            else if (Array.isArray(data.citations)) {
              latestCitations = data.citations;
              setCitations(latestCitations);
            }
            else if (data.choices?.[0]?.message?.citations) {
              latestCitations = data.choices[0].message.citations;
              setCitations(latestCitations);
            }
            
            // Handle completion
            if (data.choices?.[0]?.finish_reason === 'stop' || 
                data.finish_reason === 'stop' || 
                data.done === true) {
              
              console.log("Stream complete");
              // Add assistant message to history
              setMessages(prev => [...prev, {
                role: 'assistant',
                content: accumulatedContent,
                citations: latestCitations.length > 0 ? latestCitations : undefined
              }]);
              break;
            }
          } catch (e) {
            console.error('Error parsing JSON from chunk:', e);
            continue;
          }
        }
      }
      
    } catch (error) {
      console.error('Error:', error);
      setError(error.message);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error: ' + error.message
      }]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const clearConversation = () => {
    setMessages([]);
    setStreamingOutput('');
    setResponse('');
    setCitations([]);
    setError('');
  };
  
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">RAG Chat Test Interface</h1>
      
      <div className="flex gap-4 mb-4">
        <Button onClick={clearConversation} variant="destructive">
          Clear Conversation
        </Button>
        <Button 
          onClick={() => setIsDebugMode(!isDebugMode)}
          variant={isDebugMode ? "default" : "outline"}
        >
          {isDebugMode ? "Debug Mode: ON" : "Debug Mode: OFF"}
        </Button>
        
        <Button 
          onClick={() => setUseSystemPrompt(!useSystemPrompt)}
          variant={useSystemPrompt ? "default" : "outline"}
        >
          {useSystemPrompt ? "System Prompt: ON" : "System Prompt: OFF"}
        </Button>
      </div>
      
      {useSystemPrompt && (
        <div className="mb-4">
          <h3 className="text-sm font-medium mb-2">System Prompt:</h3>
          <Textarea
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            placeholder="Enter system prompt here..."
            className="w-full h-24"
          />
        </div>
      )}
      
      {error && (
        <div className="p-4 mb-6 bg-red-100 text-red-800 rounded-md">
          <p className="font-medium">Error:</p>
          <p>{error}</p>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="col-span-1">
          <CardContent className="pt-6">
            <h2 className="text-xl font-semibold mb-4">Conversation</h2>
            <ScrollArea className="h-[400px] mb-4">
              {messages.map((msg, idx) => (
                <div key={idx} className={`mb-4 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                  <div className={`inline-block max-w-[90%] p-4 rounded-lg ${
                    msg.role === 'user' 
                      ? 'bg-primary text-primary-foreground' 
                      : 'bg-card text-card-foreground border border-border'
                  }`}>
                    <ReactMarkdown>
                      {msg.content}
                    </ReactMarkdown>
                    
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-2 text-xs">
                        <p>{msg.citations.length} Citations</p>
                        <div className="mt-1 p-2 bg-black/10 rounded text-left">
                          {msg.citations.map((citation, cidx) => (
                            <div key={cidx} className="mb-1">
                              <p>• {citation.document_name || citation.source}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
              {/* Streaming response */}
              {response && isLoading && (
                <div className="mb-4 text-left">
                  <div className="inline-block max-w-[90%] p-4 rounded-lg bg-card text-card-foreground border border-border">
                    <div className="flex items-center mb-2">
                      <div className="h-2 w-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                      <span className="text-xs text-muted-foreground">AI is responding...</span>
                    </div>
                    <ReactMarkdown>
                      {response}
                    </ReactMarkdown>
                  </div>
                </div>
              )}
            </ScrollArea>
            
            <form onSubmit={handleSubmit} className="flex gap-3">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (input.trim() && !isLoading) {
                      handleSubmit(e);
                    }
                  }
                }}
                placeholder="Type your message..."
                className="flex-grow"
                disabled={isLoading}
              />
              <Button 
                type="submit" 
                disabled={isLoading || !input.trim()}
              >
                {isLoading ? 'Sending...' : 'Send'}
              </Button>
            </form>
          </CardContent>
        </Card>
        
        {isDebugMode && (
          <Card className="col-span-1">
            <CardContent className="pt-6">
              <h2 className="text-xl font-semibold mb-4">Debug Output</h2>
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium mb-2">Raw Response Stream:</h3>
                  <ScrollArea className="h-[200px]">
                    <pre className="p-4 bg-zinc-800 text-zinc-100 rounded-md text-xs overflow-x-auto whitespace-pre-wrap">
                      {streamingOutput || "Waiting for response..."}
                    </pre>
                  </ScrollArea>
                </div>
                
                <div>
                  <h3 className="font-medium mb-2">Current Response:</h3>
                  <div className="p-4 bg-zinc-100 rounded-md text-sm">
                    {response || "No response yet"}
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium mb-2">Citations:</h3>
                  <pre className="p-4 bg-zinc-100 rounded-md text-xs overflow-x-auto">
                    {citations.length > 0 
                      ? JSON.stringify(citations, null, 2) 
                      : "No citations available"}
                  </pre>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
