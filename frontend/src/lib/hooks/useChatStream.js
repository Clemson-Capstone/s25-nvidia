import { useState, useCallback } from 'react';

/**
 * Custom hook for handling streaming chat responses from the RAG server
 */
export const useChatStream = () => {
  const [streamState, setStreamState] = useState({
    content: "",
    citations: [],
    error: null,
    isStreaming: false,
  });

  const [abortController, setAbortController] = useState(new AbortController());

  // Reset the abort controller for a new request
  const resetAbortController = useCallback(() => {
    const controller = new AbortController();
    setAbortController(controller);
    return controller;
  }, []);

  // Stop the current stream
  const stopStream = useCallback(() => {
    abortController.abort();
    setStreamState((prev) => ({ ...prev, isStreaming: false }));
  }, [abortController]);

  // Process a streaming response
  const processStream = useCallback(async (
    response,
    setStreamingMessage,
    setFinalMessages
  ) => {
    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body");

    const decoder = new TextDecoder();
    let buffer = "";
    let content = "";
    let latestCitations = [];

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        buffer += chunk;

        // Split lines and keep the last potentially incomplete line in the buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim() === '' || !line.startsWith('data: ')) continue;

          try {
            const data = JSON.parse(line.slice(5));
            console.log("Parsed data chunk:", data);

            // Check for errors in the response
            if (data.choices?.[0]?.message?.content?.includes("Error from rag server")) {
              throw new Error("RAG server error");
            }

            // Handle delta content (check different possible formats)
            if (data.choices?.[0]?.delta?.content) {
              const deltaContent = data.choices[0].delta.content;
              content += deltaContent;
              setStreamingMessage(content);
              console.log("Streaming content update from delta:", content.slice(-50)); // Log last 50 chars
            } 
            // Alternative format - direct message content
            else if (data.choices?.[0]?.message?.content) {
              const messageContent = data.choices[0].message.content;
              // If this is new content (not just repeating), append it
              if (!content.endsWith(messageContent)) {
                content += messageContent;
                setStreamingMessage(content);
                console.log("Streaming content update from message:", messageContent); // Log content
              }
            }
            // For NVIDIA's format that might send the entire content each time
            else if (data.content) {
              // Only update if this is new content
              if (data.content !== content) {
                content = data.content; // Replace with full content
                setStreamingMessage(content);
                console.log("Streaming content update from direct content:", content.slice(-50));
              }
            }

            // Handle different citation formats
            // Format 1: NVIDIA's results array
            if (data.citations?.results?.length > 0) {
              latestCitations = data.citations.results.map(source => ({
                text: source.content,
                source: source.document_name,
                document_type: source.document_type || "text",
              }));
              console.log("Citations received (results format):", latestCitations);
            } 
            // Format 2: Direct citations array
            else if (Array.isArray(data.citations)) {
              latestCitations = data.citations.map(source => ({
                text: source.content || source.text || "",
                source: source.document_name || source.source || "Unknown source",
                document_type: source.document_type || "text",
              }));
              console.log("Citations received (direct array):", latestCitations);
            }
            // Format 3: Citations embedded in the message
            else if (data.choices?.[0]?.message?.citations) {
              latestCitations = data.choices[0].message.citations.map(source => ({
                text: source.content || source.text || "",
                source: source.document_name || source.source || "Unknown source",
                document_type: source.document_type || "text",
              }));
              console.log("Citations received (message citations):", latestCitations);
            }

            // Handle stream completion - check various possible formats
            if (data.choices?.[0]?.finish_reason === 'stop' || 
                data.finish_reason === 'stop' || 
                data.done === true) {
              
              console.log("Stream completion detected, final content length:", content.length);
              
              if (content) {
                setFinalMessages(prev => [...prev, {
                  role: 'assistant',
                  content: content,
                  citations: latestCitations.length > 0 ? latestCitations : undefined
                }]);
                
                setStreamingMessage('');
                setStreamState(prev => ({
                  ...prev,
                  content,
                  citations: latestCitations,
                  isStreaming: false,
                }));
              }
              break;
            }
          } catch (parseError) {
            if (!(parseError instanceof SyntaxError)) {
              throw parseError;
            }
          }
        }
      }
    } catch (error) {
      setStreamState(prev => ({
        ...prev,
        error: "Sorry, there was an error processing your request.",
        isStreaming: false,
      }));
      throw error;
    } finally {
      reader.releaseLock();
    }
  }, []);

  // Start a new stream
  const startStream = useCallback(() => {
    const controller = resetAbortController();
    setStreamState(prev => ({ ...prev, isStreaming: true, error: null }));
    return controller;
  }, [resetAbortController]);

  // Reset the stream state
  const resetStream = useCallback(() => {
    setStreamState({
      content: "",
      citations: [],
      error: null,
      isStreaming: false,
    });
  }, []);

  return {
    streamState,
    processStream,
    startStream,
    resetStream,
    stopStream,
    isStreaming: streamState.isStreaming,
  };
};

export default useChatStream;
