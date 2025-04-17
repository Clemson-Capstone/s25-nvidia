import React, { useRef, useEffect, useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import ReactMarkdown from 'react-markdown';

const ChatInterface = ({
  messages,
  streamingMessage,
  inputMessage,
  setInputMessage,
  handleSubmit,
  isLoading,
  ttsEnabled
}) => {
  const messagesEndRef = useRef(null);
  const [activeCitations, setActiveCitations] = useState(null);
  const [isListening, setIsListening] = useState(false);
  
  // Add useEffect for browser detection after component mounts to avoid hydration mismatch
  useEffect(() => {
    // This code only runs on the client after hydration, avoiding mismatch
    const browserMessageEl = document.getElementById('browser-specific-message');
    if (browserMessageEl && navigator && navigator.userAgent) {
      const isFirefox = navigator.userAgent.indexOf("Firefox") > -1;
      if (isFirefox) {
        browserMessageEl.textContent = " Firefox users: If speech doesn't work, try Chrome or Edge.";
      }
    }
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  // Toggle citations panel
  const toggleCitations = (citations) => {
    if (activeCitations === citations) {
      setActiveCitations(null);
    } else {
      setActiveCitations(citations);
    }
    
    // Log citation information for debugging
    console.log("Citations toggled:", citations);
  };
  
  // Render citations panel
  const renderCitationsPanel = () => {
    if (!activeCitations || activeCitations.length === 0) return null;
    
    return (
      <div className="mt-2 p-3 bg-black/30 border border-border rounded-lg">
        <h3 className="font-medium text-sm mb-2">Citations</h3>
        <div className="space-y-2">
          {activeCitations.map((citation, index) => (
            <div key={index} className="p-2 bg-card/50 rounded border-l-2 border-primary text-sm">
              <div className="flex justify-between items-start mb-1">
                <Badge variant="outline" className="text-xs">Source {index + 1}</Badge>
                <span className="text-xs opacity-70">{citation.source}</span>
              </div>
              <p className="text-xs opacity-90">{citation.text}</p>
            </div>
          ))}
        </div>
      </div>
    );
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
                <div>
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
                  
                  {message.role === 'assistant' && message.citations && message.citations.length > 0 && (
                    <div className="mt-2 text-xs">
                      <Button 
                        variant="link" 
                        className="p-0 h-auto text-primary hover:text-primary/80"
                        onClick={() => toggleCitations(message.citations)}
                      >
                        {message.citations.length} Citation{message.citations.length > 1 ? 's' : ''}
                      </Button>
                    </div>
                  )}
                  
                  {message.role === 'assistant' && activeCitations === message.citations && renderCitationsPanel()}
                </div>
              </div>
            </div>
          ))}
          {streamingMessage && (
            <div className="mb-4 text-left">
              <div className="inline-block max-w-[80%] p-4 rounded-lg bg-card text-card-foreground border border-border shadow-sm">
                <div className="flex items-center mb-2">
                  <div className="h-2 w-2 bg-primary rounded-full mr-2 animate-pulse"></div>
                  <span className="text-xs text-muted-foreground">AI is responding...</span>
                </div>
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
          {isLoading ? (
            <Button 
              type="button" 
              onClick={() => window.stopStream && window.stopStream()}
              className="bg-red-600 hover:bg-red-700 text-white shadow-sm"
            >
              Cancel
            </Button>
          ) : (
            <Button 
              type="submit" 
              className="bg-gradient-to-r from-primary to-primary/90 text-primary-foreground hover:brightness-110 shadow-sm"
              disabled={!inputMessage.trim()}
            >
              Send
            </Button>
          )}
        </form>
        <div className="mt-2 flex flex-col">
          <div className="flex gap-2">
            <Button 
              onClick={() => {
              // Directly implement speech recognition here instead of relying on window functions
              console.log("Speech recognition button clicked");
              
              // Set UI state first
              setIsListening(true);
              setInputMessage("Listening...");
              
              // Directly implement speech recognition
              const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
              
              if (!SpeechRecognition) {
                console.error("Speech recognition not supported in this browser. Please try Chrome.");
                setIsListening(false);
                setInputMessage("");
                alert("Speech recognition is not supported in this browser. Please try Chrome or Edge.");
                return;
              }
              
              // Check browser type without causing hydration mismatch
              let isFirefox = false;
              // Only run this on the client side
              if (typeof navigator !== 'undefined' && navigator.userAgent) {
                isFirefox = navigator.userAgent.indexOf("Firefox") > -1;
                if (isFirefox) {
                  console.warn("Using Firefox for speech recognition. For better results, try Chrome or Edge.");
                }
              }
              
              try {
                const recognition = new SpeechRecognition();
                
                // Configure recognition
                recognition.lang = "en-US";
                recognition.interimResults = false;
                recognition.continuous = false;
                recognition.maxAlternatives = 1;
                
                // Firefox needs special handling - only run this code if isFirefox is true
                // and we're in the browser (not during server rendering)
                if (isFirefox) {
                  // Firefox sometimes needs these settings to be more explicit
                  recognition.interimResults = false;
                  recognition.continuous = false;
                }
                
                // Set a timeout for all browsers to prevent hanging
                const timeoutId = setTimeout(() => {
                  if (isListening) {
                    try {
                      recognition.stop();
                    } catch (e) {
                      console.log("Error stopping recognition:", e);
                    }
                    setIsListening(false);
                    setInputMessage(prev => prev === "Listening..." ? "" : prev);
                    console.log("Stopped listening due to timeout");
                  }
                }, 10000);
                
                // Clear timeout if recognition ends normally
                recognition.onend = () => {
                  clearTimeout(timeoutId);
                  console.log("Speech recognition ended");
                  setIsListening(false);
                };
                
                // Firefox needs these handlers set BEFORE calling start()
                recognition.onstart = () => {
                  console.log("Speech recognition started successfully");
                  setIsListening(true);
                  setInputMessage("Listening...");
                };
                
                recognition.onresult = (event) => {
                  console.log("Speech recognition result received", event);
                  if (event.results && event.results[0] && event.results[0][0]) {
                    const speechResult = event.results[0][0].transcript;
                    console.log("Speech recognized:", speechResult);
                    setInputMessage(speechResult);
                  } else {
                    console.warn("Received speech event but no transcript found");
                  }
                  setIsListening(false);
                };
                
                recognition.onerror = (event) => {
                  console.error("Speech recognition error:", event.error);
                  setInputMessage("");
                  setIsListening(false);
                  
                  // Show alert for common errors
                  if (event.error === 'not-allowed') {
                    alert("Microphone access was denied. Please allow microphone access to use speech recognition.");
                  } else if (event.error === 'no-speech') {
                    alert("No speech was detected. Please try again.");
                  }
                };
                
                recognition.onend = () => {
                  console.log("Speech recognition ended");
                  setIsListening(false);
                };
                
                // Start recognition
                recognition.start();
                console.log("Called recognition.start()");
                
              } catch (error) {
                console.error("Error starting speech recognition:", error);
                setIsListening(false);
                setInputMessage("");
                alert("Error starting speech recognition: " + error.message);
              }
            }}
            disabled={isListening}
            className={`
              ${isListening 
                ? 'bg-red-500 animate-pulse' 
                : 'bg-gradient-to-r from-primary to-primary/90'} 
              text-primary-foreground hover:brightness-110 shadow-sm
            `}
          >
            {isListening ? "Listening..." : "🎤 Start Speaking"}
          </Button>
          
          {activeCitations && (
            <Button 
              variant="outline" 
              onClick={() => setActiveCitations(null)}
              className="border-primary/50 text-primary hover:bg-primary/10"
            >
              Hide Citations
            </Button>
          )}
          
          {messages.length > 0 && (
            <Button 
              variant="outline" 
              onClick={() => {
                if (window.confirm("Are you sure you want to reset the conversation?")) {
                  // Find the global reset function if available
                  if (typeof window.resetConversation === 'function') {
                    window.resetConversation();
                  }
                }
              }}
              className="border-red-500/50 text-red-500 hover:bg-red-500/10"
            >
              Reset Conversation
            </Button>
          )}
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            Note: You may need to allow microphone access when prompted.
            {/* Move browser detection logic to a useEffect to avoid hydration mismatch */}
            <span id="browser-specific-message"></span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ChatInterface;
