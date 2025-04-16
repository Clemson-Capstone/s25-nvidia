// Fixed handleSubmit function with proper API parameters based on the NVIDIA RAG server requirements

const handleSubmit = async (e) => {
  if (e) {
    e.preventDefault();
  }

  if (!inputMessage.trim()) return;

  if (useKnowledgeBase && documents.length === 0) {
    setError('No documents in knowledge base. Please upload course content first.');
    return;
  }

  const newMessage = { role: 'user', content: inputMessage };
  setMessages(prev => [...prev, newMessage]);
  setInputMessage('');
  setIsLoading(true);
  setError('');
  setSuccessMessage('');
  setStreamingMessage('');

  let accumulatedMessage = '';
  let latestCitations = [];

  try {
    // Always use the default collection regardless of selected course
    let collectionName = "default";

    const requestBody = {
      messages: [...messages, newMessage],
      use_knowledge_base: useKnowledgeBase,
      persona,
      temperature: 0.7,
      top_p: 0.8,
      max_tokens: 1024,
      reranker_top_k: 2,  // Added from the notebook example
      vdb_top_k: 10,      // Added from the notebook example
      vdb_endpoint: "http://milvus:19530", // Added from the notebook example
      collection_name: collectionName,
      enable_query_rewriting: true,  // Added from the notebook example
      enable_reranker: true,         // Added from the notebook example
      enable_citations: true,        // Enable citations from the RAG server
      model: "",                     // Let server use default model
      stop: []                       // Added from the notebook example
    };
    
    console.log("Sending request to RAG server:", requestBody);
    
    // Use the v1 API endpoint for the generate request from the RAG server
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
                  content: accumulatedMessage,
                  citations: latestCitations.length > 0 ? latestCitations : undefined
                }]);
                
                if (ttsEnabled) {
                  // Extract text without citation markers for TTS
                  const textOnly = accumulatedMessage.replace(/<cite[^>]*>|<\/cite>/g, '');
                  speakText(textOnly);
                }
                setStreamingMessage('');
              }
              break;
            }

            // Process message content
            if (jsonData.choices?.[0]?.delta?.content || jsonData.choices?.[0]?.message?.content) {
              const content = jsonData.choices[0]?.delta?.content || jsonData.choices[0]?.message?.content;
              accumulatedMessage += content;
              setStreamingMessage(accumulatedMessage);
            }

            // Process citations if available
            if (jsonData.citations?.results?.length > 0) {
              latestCitations = jsonData.citations.results.map(source => ({
                text: source.content,
                source: source.document_name,
                document_type: source.document_type || "text",
              }));
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