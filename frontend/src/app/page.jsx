"use client"

import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";

import CanvasIntegration from '@/components/CanvasIntegration';
import ChatSettings from '@/components/ChatSettings';
import ChatInterface from '@/components/ChatInterface';
import CourseContent from '@/components/CourseContent';
import KnowledgeBase from '@/components/KnowledgeBase';

export default function ChatPage() {
  // State variables
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [useKnowledgeBase, setUseKnowledgeBase] = useState(false);
  const [selectedEdgeCase, setSelectedEdgeCase] = useState(null);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Canvas-related state variables
  const [canvasToken, setCanvasToken] = useState('');
  const [userId, setUserId] = useState('');
  const [courses, setCourses] = useState({});
  const [selectedCourse, setSelectedCourse] = useState('');
  const [isVerifyingToken, setIsVerifyingToken] = useState(false);
  const [isFetchingCourses, setIsFetchingCourses] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [tokenVerified, setTokenVerified] = useState(false);
  const [downloadedCourses, setDownloadedCourses] = useState([]);
  
  // Course content state variables
  const [courseContent, setCourseContent] = useState(null);
  const [contentType, setContentType] = useState('file_list');
  const [isLoadingContent, setIsLoadingContent] = useState(false);
  
  // UI state variables
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [activeTab, setActiveTab] = useState('chat');

  useEffect(() => {
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
  }, []);
  
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
      setActiveTab('knowledge');
      
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
        canvas_token: useKnowledgeBase ? canvasToken : undefined
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
    const edgeCases = require('@/app/data/edgecase_dataset.json');
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

      {/* Canvas Integration */}
      <CanvasIntegration 
        canvasToken={canvasToken}
        setCanvasToken={setCanvasToken}
        isVerifyingToken={isVerifyingToken}
        tokenVerified={tokenVerified}
        userId={userId}
        courses={courses}
        selectedCourse={selectedCourse}
        setSelectedCourse={setSelectedCourse}
        isFetchingCourses={isFetchingCourses}
        isDownloading={isDownloading}
        downloadedCourses={downloadedCourses}
        verifyToken={verifyToken}
        handleLogout={handleLogout}
        downloadCourse={downloadCourse}
      />

      {/* Chat Settings */}
      <ChatSettings 
        useKnowledgeBase={useKnowledgeBase}
        setUseKnowledgeBase={setUseKnowledgeBase}
        selectedEdgeCase={selectedEdgeCase}
        handleEdgeCaseSelect={handleEdgeCaseSelect}
        handleSubmit={handleSubmit}
        isLoading={isLoading}
      />

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
            {/* <TabsTrigger 
              value="content" 
              disabled={!tokenVerified || downloadedCourses.length === 0}
            >
              Course Content
            </TabsTrigger> */}
            <TabsTrigger value="knowledge">
              Knowledge Base
            </TabsTrigger>
          </TabsList>
          
          {/* Chat Tab */}
          <TabsContent value="chat">
            <ChatInterface 
              messages={messages}
              streamingMessage={streamingMessage}
              inputMessage={inputMessage}
              setInputMessage={setInputMessage}
              handleSubmit={handleSubmit}
              isLoading={isLoading}
            />
          </TabsContent>
          
          {/* Course Content Tab */}
          {/* <TabsContent value="content">
            <CourseContent 
              selectedCourse={selectedCourse}
              setSelectedCourse={setSelectedCourse}
              downloadedCourses={downloadedCourses}
              courses={courses}
              isLoadingContent={isLoadingContent}
              contentType={contentType}
              fetchCourseContent={fetchCourseContent}
              courseContent={courseContent}
              formatFileSize={formatFileSize}
            />
          </TabsContent> */}
          
          {/* Knowledge Base Tab */}
          <TabsContent value="knowledge">
            <KnowledgeBase 
              documents={documents}
              fetchDocuments={fetchDocuments}
              setError={setError}
              setSuccessMessage={setSuccessMessage}
              canvasToken={canvasToken}
              userId={userId}
              courses={courses}
              selectedCourse={selectedCourse}
              setSelectedCourse={setSelectedCourse}
              downloadedCourses={downloadedCourses}
              formatFileSize={formatFileSize}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}