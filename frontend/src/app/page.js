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
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";

import edgeCases from '@/app/data/edgecase_dataset.json';

// function for text-to-speech
function speakText(text) {
  if ('speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(text);
    
    const voices = window.speechSynthesis.getVoices();
    // Try to find a female voice. Note that not all browsers provide gender info.
    // You might need to filter by voice name or language. For example:
    const femaleVoice = voices.find(voice =>
      voice.name.toLowerCase().includes('samantha') ||
      voice.name.toLowerCase().includes('zira') ||
      (voice.lang === 'en-US' && voice.name.toLowerCase().includes('female'))
    );
    if (femaleVoice) {
      utterance.voice = femaleVoice;
    } else {
      console.warn('No female voice found; using default voice.');
    }

    // Adjust additional parameters as needed ( 1 being default ):
    utterance.pitch = 1;
    utterance.rate = 1.4;
    utterance.volume = 1;
    window.speechSynthesis.speak(utterance);
  } else {
    console.error('Speech synthesis not supported in this browser.');
  }
}

// function for speech-to-text
function startSpeechRecognition(setInputMessage) {
  // Set the input to "Listening..." immediately
  setInputMessage("Listening...");
  
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.error("Speech recognition is not supported in this browser.");
    return;
  }
  const recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = (event) => {
    const speechResult = event.results[0][0].transcript;
    setInputMessage(speechResult);
  };
  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
  };
  recognition.start();
}

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
  
  // New state variables
  const [userId, setUserId] = useState('');
  const [courses, setCourses] = useState({});
  const [selectedCourse, setSelectedCourse] = useState('');
  const [isVerifyingToken, setIsVerifyingToken] = useState(false);
  const [isFetchingCourses, setIsFetchingCourses] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [tokenVerified, setTokenVerified] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [activeTab, setActiveTab] = useState('chat');
  const [courseContent, setCourseContent] = useState(null);
  const [contentType, setContentType] = useState('file_list');
  const [isLoadingContent, setIsLoadingContent] = useState(false);
  const [downloadedCourses, setDownloadedCourses] = useState([]);
  const [persona, setPersona] = useState("formal");

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
    fetchDocuments();
    
    // Load token and userId from localStorage if available
    const savedToken = localStorage.getItem('canvasToken');
    const savedUserId = localStorage.getItem('userId');
    
    if (savedToken) {
      setCanvasToken(savedToken);
      setTokenVerified(true);
    }
    
    if (savedUserId) {
      setUserId(savedUserId);
    }
    
    // If we have both, fetch courses
    if (savedToken && savedUserId) {
      fetchCourses(savedToken);
    }
  }, [messages, streamingMessage]);


  
  // Check for downloaded courses whenever userId changes
  useEffect(() => {
    if (userId && tokenVerified) {
      checkDownloadedCourses();
    }
  }, [userId, tokenVerified]);

  const fetchDocuments = async () => {
    try {
      const response = await fetch('http://localhost:8081/documents');
      if (!response.ok) throw new Error('Failed to fetch documents');
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  // Verify Canvas token and get user ID
  const verifyToken = async () => {
    if (!canvasToken.trim()) {
      setError('Canvas access token is required');
      return false;
    }
    
    setIsVerifyingToken(true);
    setError('');
    setSuccessMessage('');
    
    try {
      const response = await fetch(`http://localhost:8012/user_info?token=${canvasToken}`);
      
      if (!response.ok) {
        throw new Error('Failed to verify Canvas token');
      }
      
      const data = await response.json();
      
      if (data.user_id) {
        // Convert user_id to string to ensure it's stored as a string
        const userIdStr = String(data.user_id);
        
        // Save token and userId to localStorage
        localStorage.setItem('canvasToken', canvasToken);
        localStorage.setItem('userId', userIdStr);
        
        setUserId(userIdStr);
        setTokenVerified(true);
        setSuccessMessage('Token verified successfully!');
        
        // Fetch courses using the verified token
        fetchCourses(canvasToken);
        return true;
      } else {
        throw new Error('User ID not found in response');
      }
    } catch (error) {
      console.error('Error verifying token:', error);
      setError(error.message || 'Failed to verify Canvas token');
      return false;
    } finally {
      setIsVerifyingToken(false);
    }
  };

  // Fetch courses using the Canvas token
  const fetchCourses = async (token) => {
    setIsFetchingCourses(true);
    setError('');
    
    try {
      const response = await fetch('http://localhost:8012/get_courses', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch courses');
      }
      
      const courseData = await response.json();
      setCourses(courseData);
      setSuccessMessage('Courses loaded successfully!');
      // If no course is selected yet and we have courses, select the first one
      if (!selectedCourse && Object.keys(courseData).length > 0) {
        setSelectedCourse(Object.keys(courseData)[0]);
      }
    } catch (error) {
      console.error('Error fetching courses:', error);
      setError(error.message || 'Failed to fetch courses');
    } finally {
      setIsFetchingCourses(false);
    }
  };

  // Download selected course
  // Check which courses have been downloaded
  const checkDownloadedCourses = async () => {
    if (!userId || !canvasToken) return;
    
    try {
      // For each course in courses, check if it exists in the backend
      const downloadedList = [];
      
      for (const courseId of Object.keys(courses)) {
        try {
          // Try to fetch file_list.json for this course
          const response = await fetch('http://localhost:8012/get_course_content', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              course_id: parseInt(courseId),
              token: canvasToken,
              user_id: String(userId),
              content_type: 'file_list'
            }),
          });
          
          // If we get a 200 response, the course has been downloaded
          if (response.ok) {
            downloadedList.push(courseId);
          }
        } catch (error) {
          // Continue checking other courses
          console.log(`Course ${courseId} not downloaded or error checking`);
        }
      }
      
      setDownloadedCourses(downloadedList);
    } catch (error) {
      console.error('Error checking downloaded courses:', error);
    }
  };

  const downloadCourse = async () => {
    if (!selectedCourse) {
      setError('Please select a course to download');
      return;
    }
    
    setIsDownloading(true);
    setError('');
    setSuccessMessage('');
    
    try {
      const response = await fetch('http://localhost:8012/download_course', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          course_id: parseInt(selectedCourse),
          token: canvasToken,
          user_id: String(userId) // Ensure userId is a string
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to download course');
      }
      
      const data = await response.json();
      setSuccessMessage(`Course downloaded successfully! (User ID: ${data.user_id})`);
      
      // Add the course to downloadedCourses
      if (!downloadedCourses.includes(selectedCourse)) {
        setDownloadedCourses([...downloadedCourses, selectedCourse]);
      }
      
      // Switch to the content tab
      setActiveTab('content');
      
      // Load content for the newly downloaded course
      fetchCourseContent(selectedCourse, 'file_list');
    } catch (error) {
      console.error('Error downloading course:', error);
      setError(error.message || 'Failed to download course');
    } finally {
      setIsDownloading(false);
    }
  };
  
  // Fetch course content from the backend
  const fetchCourseContent = async (courseId, type) => {
    if (!courseId || !canvasToken || !userId) {
      setError('Missing required information to fetch course content');
      return;
    }
    
    setIsLoadingContent(true);
    setError('');
    setCourseContent(null);
    
    try {
      const response = await fetch('http://localhost:8012/get_course_content', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          course_id: parseInt(courseId),
          token: canvasToken,
          user_id: String(userId),
          content_type: type
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch ${type} content`);
      }
      
      const data = await response.json();
      setCourseContent(data);
      setContentType(type);
    } catch (error) {
      console.error('Error fetching course content:', error);
      setError(error.message || 'Failed to fetch course content');
    } finally {
      setIsLoadingContent(false);
    }
  };

  const handleSubmit = async (e) => {
    if (e) {
      e.preventDefault();
    }

    if (!inputMessage.trim()) return;

    if (useKnowledgeBase && !canvasToken) {
      setError('Canvas access token is required when using knowledge base');
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

    try {
      const requestBody = {
        messages: [...messages, newMessage],
        use_knowledge_base: useKnowledgeBase,
        canvas_token: useKnowledgeBase ? canvasToken : undefined,
      	persona
      };
      
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
                  speakText(accumulatedMessage);
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
      setInputMessage(selectedCase.user_input);
      setSelectedEdgeCase(value);
    }
  };

  // Clear token and user data
  const handleLogout = () => {
    localStorage.removeItem('canvasToken');
    localStorage.removeItem('userId');
    setCanvasToken('');
    setUserId('');
    setTokenVerified(false);
    setCourses({});
    setSelectedCourse('');
    setSuccessMessage('Token and user data cleared');
  };

  // Format the content for display
  const renderContent = () => {
    if (!courseContent) {
      return <div className="text-center p-4 text-gray-500">No content to display</div>;
    }
    
    if (contentType === 'file_list') {
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Files in {courses[selectedCourse] || 'Selected Course'}</h3>
          <div className="grid gap-2">
            {courseContent.length === 0 ? (
              <div className="p-4 border rounded-md bg-gray-50 text-center">No files available</div>
            ) : (
              courseContent.map((file, index) => (
                <div key={index} className="p-3 border rounded-md bg-white hover:bg-gray-50 flex justify-between items-center">
                  <div>
                    <p className="font-medium">{file.name}</p>
                    <p className="text-sm text-gray-500">{file.type || 'Unknown type'} - {formatFileSize(file.size)}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      );
    }
    
    if (contentType === 'course_info') {
      return (
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium mb-2">Modules</h3>
            {courseContent.modules.length === 0 ? (
              <div className="p-4 border rounded-md bg-gray-50 text-center">No modules available</div>
            ) : (
              <div className="space-y-2">
                {courseContent.modules.map((module, index) => (
                  <div key={index} className="p-3 border rounded-md bg-white">
                    <p className="font-medium">{module.name}</p>
                    {module.items && module.items.length > 0 && (
                      <div className="ml-4 mt-2 space-y-1">
                        {module.items.map((item, itemIndex) => (
                          <div key={itemIndex} className="text-sm p-2 border-l-2 border-orange-200">
                            {item.title} <span className="text-gray-500">({item.type})</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div>
            <h3 className="text-lg font-medium mb-2">Pages</h3>
            {courseContent.pages.length === 0 ? (
              <div className="p-4 border rounded-md bg-gray-50 text-center">No pages available</div>
            ) : (
              <div className="grid gap-2">
                {courseContent.pages.map((page, index) => (
                  <div key={index} className="p-3 border rounded-md bg-white">
                    <p className="font-medium">{page.title}</p>
                    <p className="text-sm text-gray-500">Last updated: {new Date(page.updated_at).toLocaleString()}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      );
    }
    
    return (
      <pre className="p-4 bg-gray-50 rounded-md overflow-auto">
        {JSON.stringify(courseContent, null, 2)}
      </pre>
    );
  };
  
  // Helper function to format file size
  const formatFileSize = (bytes) => {
    if (!bytes || isNaN(bytes)) return 'Unknown size';
    
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-100 via-white to-orange-50 p-4">
      {/* Title */}
      <div className="max-w-4xl mx-auto mb-6 text-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-orange-600 to-orange-400 bg-clip-text text-transparent">
          Virtual Teaching Assistant
        </h1>
      </div>

      {/* Canvas Integration Card */}
      <div className="max-w-4xl mx-auto mb-6">
        <Card className="bg-white/80 backdrop-blur-sm border border-orange-100">
          <CardContent className="p-6">
            <h2 className="text-xl font-semibold mb-4">Canvas Integration</h2>
            
            {/* Canvas Token Input */}
            <div className="flex flex-col md:flex-row gap-3 mb-4">
              <Input
                type="password"
                placeholder="Canvas Access Token"
                value={canvasToken}
                onChange={(e) => setCanvasToken(e.target.value)}
                disabled={isVerifyingToken || tokenVerified}
                className="flex-1"
              />
              
              {tokenVerified ? (
                <Button 
                  variant="outline"
                  onClick={handleLogout}
                  className="whitespace-nowrap"
                >
                  Clear Token
                </Button>
              ) : (
                <Button 
                  onClick={verifyToken} 
                  disabled={isVerifyingToken || !canvasToken.trim()}
                  className="whitespace-nowrap bg-orange-500 hover:bg-orange-600 text-white"
                >
                  {isVerifyingToken ? 'Verifying...' : 'Confirm Token'}
                </Button>
              )}
            </div>
            
            {/* User ID Display */}
            {userId && (
              <div className="text-sm text-gray-600 mb-4">
                Connected as User ID: {userId}
              </div>
            )}
            
            {/* Course Selection - Always visible when token is verified */}
            {tokenVerified && (
              <div className="flex flex-col md:flex-row gap-3 items-center mb-4">
                <div className="flex-1">
                  <Select 
                    value={selectedCourse} 
                    onValueChange={setSelectedCourse}
                    disabled={isFetchingCourses || !Object.keys(courses).length}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={isFetchingCourses ? "Loading courses..." : "Select a course"} />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.keys(courses).length === 0 ? (
                        <SelectItem value="loading" disabled>
                          {isFetchingCourses ? "Loading courses..." : "No courses available"}
                        </SelectItem>
                      ) : (
                        Object.entries(courses).map(([id, name]) => (
                          <SelectItem key={id} value={id}>
                            {name} {downloadedCourses.includes(id) ? '(Downloaded)' : ''}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>
                
                <Button
                  onClick={downloadCourse}
                  disabled={isDownloading || !selectedCourse || isFetchingCourses}
                  className="whitespace-nowrap bg-orange-500 hover:bg-orange-600 text-white"
                >
                  {isDownloading ? 'Downloading...' : downloadedCourses.includes(selectedCourse) ? 'Re-Download' : 'Download Course'}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Settings Card */}
      <div className="max-w-4xl mx-auto mb-6">
        <Card className="bg-white/80 backdrop-blur-sm border border-orange-100">
          <CardContent className="p-6">
            <h2 className="text-xl font-semibold mb-4">Chat Settings</h2>
            
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
                <Select onValueChange={handleEdgeCaseSelect} value={selectedEdgeCase}>
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
              
              {selectedEdgeCase && (
                <Button 
                  onClick={() => handleSubmit()}
                  disabled={isLoading}
                  className="whitespace-nowrap"
                >
                  Run Test Case
                </Button>
              )}
            </div>
	    {/* Persona Selection */}
  	    <div className="flex items-center space-x-2">
    	      <Label htmlFor="persona-select">Select Persona:</Label>
  	    </div>
  	    <div className="flex-1">
    	      <Select value={persona} onValueChange={setPersona}>
      	        <SelectTrigger id="persona-select">
                  <SelectValue placeholder="Select a persona" />
      	        </SelectTrigger>
                <SelectContent>
                  <SelectItem value="formal">Formal</SelectItem>
                  <SelectItem value="casual">Casual</SelectItem>
                  <SelectItem value="drill_sergeant">Drill Sergeant</SelectItem>
                  <SelectItem value="enthusiastic">Enthusiastic</SelectItem>
                  <SelectItem value="supportive">Supportive</SelectItem>
                  <SelectItem value="meme_lord">Meme Lord</SelectItem>
                  <SelectItem value="humorous">Humorous</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Status Messages */}
      {successMessage && (
        <div className="max-w-4xl mx-auto mb-6">
          <Alert className="bg-green-50 border-green-200">
            <AlertDescription className="text-green-700">{successMessage}</AlertDescription>
          </Alert>
        </div>
      )}
      
      {/* Error Alert */}
      {error && (
        <div className="max-w-4xl mx-auto mb-6">
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      )}

      {/* Loading Indicators */}
      {(isFetchingCourses || isDownloading || isLoadingContent) && !error && !successMessage && (
        <div className="max-w-4xl mx-auto mb-6">
          <Alert>
            <AlertDescription>
              {isFetchingCourses ? 'Fetching courses...' : 
               isDownloading ? 'Downloading course...' : 
               'Loading course content...'}
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Main Content Area with Tabs */}
      <div className="max-w-4xl mx-auto">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid grid-cols-2 mb-4">
            <TabsTrigger value="chat">Chat</TabsTrigger>
            <TabsTrigger 
              value="content" 
              disabled={!tokenVerified || downloadedCourses.length === 0}
            >
              Course Content
            </TabsTrigger>
          </TabsList>
          
          {/* Chat Tab */}
          <TabsContent value="chat">
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
                <div className="mt-2">
                  <Button onClick={() => startSpeechRecognition(setInputMessage)} className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white shadow-sm">
                    Start Speaking
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* Course Content Tab */}
          <TabsContent value="content">
            <Card className="bg-white/80 backdrop-blur-sm border border-orange-100">
              <CardContent className="p-6">
                <div className="mb-6">
                  <div className="flex flex-col md:flex-row gap-4 mb-4">
                    <div className="flex-1">
                      <Select 
                        value={selectedCourse} 
                        onValueChange={(value) => {
                          setSelectedCourse(value);
                          if (downloadedCourses.includes(value)) {
                            fetchCourseContent(value, contentType);
                          }
                        }}
                        disabled={!downloadedCourses.length}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select a downloaded course" />
                        </SelectTrigger>
                        <SelectContent>
                          {downloadedCourses.length === 0 ? (
                            <SelectItem value="none" disabled>
                              No downloaded courses
                            </SelectItem>
                          ) : (
                            downloadedCourses.map((id) => (
                              <SelectItem key={id} value={id}>
                                {courses[id] || `Course ${id}`}
                              </SelectItem>
                            ))
                          )}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button
                        variant={contentType === 'file_list' ? 'default' : 'outline'}
                        onClick={() => fetchCourseContent(selectedCourse, 'file_list')}
                        disabled={isLoadingContent || !selectedCourse || !downloadedCourses.includes(selectedCourse)}
                        className={contentType === 'file_list' ? 'bg-orange-500 hover:bg-orange-600 text-white' : ''}
                      >
                        Files
                      </Button>
                      <Button
                        variant={contentType === 'course_info' ? 'default' : 'outline'}
                        onClick={() => fetchCourseContent(selectedCourse, 'course_info')}
                        disabled={isLoadingContent || !selectedCourse || !downloadedCourses.includes(selectedCourse)}
                        className={contentType === 'course_info' ? 'bg-orange-500 hover:bg-orange-600 text-white' : ''}
                      >
                        Course Structure
                      </Button>
                    </div>
                  </div>
                  
                  {downloadedCourses.length === 0 && (
                    <div className="text-center p-8 bg-gray-50 rounded-lg border border-gray-200">
                      <p className="text-lg text-gray-600">No courses have been downloaded yet.</p>
                      <p className="text-sm text-gray-500 mt-2">Download a course to view its content here.</p>
                    </div>
                  )}
                  
                  {selectedCourse && downloadedCourses.includes(selectedCourse) && (
                    <div className="mt-4">
                      <ScrollArea className="h-[500px] pr-4">
                        {isLoadingContent ? (
                          <div className="flex justify-center items-center h-64">
                            <p className="text-gray-500">Loading content...</p>
                          </div>
                        ) : (
                          renderContent()
                        )}
                      </ScrollArea>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
