"use client"

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import CanvasIntegration from '@/components/CanvasIntegration';
import ChatSettings from '@/components/ChatSettings';
import ChatInterface from '@/components/ChatInterface';
import KnowledgeBase from '@/components/KnowledgeBase';

// function for text-to-speech
function speakText(text) {
  if ('speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(text);
    
    const voices = window.speechSynthesis.getVoices();
    // Try to find a female voice. Note that not all browsers provide gender info.
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
  // State variables
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [useKnowledgeBase, setUseKnowledgeBase] = useState(true);
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
  const [persona, setPersona] = useState("formal");
  const [ttsEnabled, setTTSEnabled] = useState(true);
  const [isDarkMode, setIsDarkMode] = useState(false);
  
  // Course content state variables
  const [courseContent, setCourseContent] = useState(null);
  const [contentType, setContentType] = useState('file_list');
  const [isLoadingContent, setIsLoadingContent] = useState(false);
  const [selectedItems, setSelectedItems] = useState({});
  const [processingFiles, setProcessingFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedTab, setSelectedTab] = useState('files');
  
  // UI state variables
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [activeTab, setActiveTab] = useState('chat');
  
  // Server URLs
  const RAG_SERVER_URL = "http://localhost:8081";  // For retrieval operations
  const INGESTION_SERVER_URL = "http://localhost:8082";  // For ingestion operations
  
  // State for collections
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState('default');
  
  // Fetch documents from the knowledge base - Define this function BEFORE it's used in any hooks
  const fetchDocuments = async (collectionName) => {
    try {
      // Always require a collection name, defaulting to 'default' if none provided
      const collection = collectionName || 'default';
      
      // Use the v1 API with collection_name parameter from the INGESTION server
      const response = await fetch(`${INGESTION_SERVER_URL}/v1/documents?collection_name=${encodeURIComponent(collection)}`);
      if (!response.ok) throw new Error('Failed to fetch documents');
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  useEffect(() => {
    // Fetch collections first
    fetchCollections();
    
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
    
    // Fetch documents with default collection - do this after collections are loaded
    setTimeout(() => {
      fetchDocuments('default');
    }, 100);
  }, []);
  
  // Define the function that handles both setting the collection and fetching documents
  const fetchCollectionDocuments = useCallback((collectionName) => {
    if (collectionName) {
      setSelectedCollection(collectionName);
      // Use a setTimeout to ensure this runs after state is updated
      setTimeout(() => {
        fetchDocuments(collectionName);
      }, 0);
    }
  }, []); // Empty dependency array since fetchDocuments is now in scope
  
  // Check for downloaded courses whenever userId changes
  useEffect(() => {
    if (userId && tokenVerified) {
      checkDownloadedCourses();
    }
  }, [userId, tokenVerified]);

  // Apply the dark class to <html> when isDarkMode changes
  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDarkMode);
  }, [isDarkMode]);

  // Reset selected items when course content changes
  useEffect(() => {
    if (courseContent) {
      initializeSelectedItems();
    }
  }, [courseContent, contentType, selectedTab]);

  // These state declarations have been moved to the top of the component
  
  // Fetch available collections
  const fetchCollections = async () => {
    try {
      const response = await fetch(`${INGESTION_SERVER_URL}/v1/collections`);
      if (!response.ok) throw new Error('Failed to fetch collections');
      
      const data = await response.json();
      setCollections(data.collections || []);
      
      // If no collection is selected and collections exist, select the default or first one
      if ((!selectedCollection || selectedCollection === '') && data.collections && data.collections.length > 0) {
        const defaultColl = data.collections.find(c => c.collection_name === 'default');
        if (defaultColl) {
          // Use the new function instead of directly setting the state
          fetchCollectionDocuments('default');
        } else if (data.collections.length > 0) {
          // Use the new function instead of directly setting the state
          fetchCollectionDocuments(data.collections[0].collection_name);
        }
      }
    } catch (error) {
      console.error('Error fetching collections:', error);
    }
  };

  // Initialize selected items based on current content
  const initializeSelectedItems = () => {
    const newSelectedItems = {};
    
    if (selectedTab === 'files' && Array.isArray(courseContent)) {
      courseContent.forEach((item, index) => {
        newSelectedItems[`file_${index}`] = false;
      });
    } else if (selectedTab === 'structure' && courseContent) {
      // For modules and pages
      if (courseContent.modules) {
        courseContent.modules.forEach((module, moduleIndex) => {
          if (module.items) {
            module.items.forEach((item, itemIndex) => {
              newSelectedItems[`module_${moduleIndex}_item_${itemIndex}`] = false;
            });
          }
        });
      }
      if (courseContent.pages) {
        courseContent.pages.forEach((page, pageIndex) => {
          newSelectedItems[`page_${pageIndex}`] = false;
        });
      }
    }
    
    setSelectedItems(newSelectedItems);
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
      
      // Update the tab based on content type
      if (type === 'file_list') {
        setSelectedTab('files');
      } else if (type === 'course_info') {
        setSelectedTab('structure');
      }
    } catch (error) {
      console.error('Error fetching course content:', error);
      setError(error.message || 'Failed to fetch course content');
    } finally {
      setIsLoadingContent(false);
    }
  };

  // Toggle item selection
  const toggleItemSelection = (itemKey) => {
    setSelectedItems(prev => ({
      ...prev,
      [itemKey]: !prev[itemKey]
    }));
  };

  // Get total selected items
  const getTotalSelectedItems = () => {
    return Object.values(selectedItems).filter(Boolean).length;
  };

  // Upload selected items to RAG knowledge base
  const uploadSelectedToRAG = async () => {
    const selectedCount = getTotalSelectedItems();
    if (selectedCount === 0) {
      setError('Please select at least one item to upload to knowledge base');
      return;
    }
    
    setIsProcessing(true);
    setError('');
    setSuccessMessage('');
    
    // Collect the selected items
    const itemsToUpload = [];
    
    // Process files tab
    if (selectedTab === 'files' && Array.isArray(courseContent)) {
      courseContent.forEach((file, index) => {
        const key = `file_${index}`;
        if (selectedItems[key]) {
          // Extract file ID from the URL if available
          let fileId = null;
          if (file.url) {
            const matches = file.url.match(/\/files\/(\d+)/);
            if (matches && matches[1]) {
              fileId = matches[1];
            }
          } else if (file.id) {
            fileId = file.id;
          }
          
          itemsToUpload.push({
            name: file.name,
            type: 'file',
            id: fileId,
            courseId: selectedCourse
          });
        }
      });
    } 
    // Process structure tab
    else if (selectedTab === 'structure' && courseContent) {
      // Handle modules
      if (courseContent.modules) {
        courseContent.modules.forEach((module, moduleIndex) => {
          if (module.items) {
            module.items.forEach((item, itemIndex) => {
              const key = `module_${moduleIndex}_item_${itemIndex}`;
              if (selectedItems[key]) {
                itemsToUpload.push({
                  name: item.title,
                  type: item.type.toLowerCase(),
                  id: item.content_id,
                  courseId: selectedCourse
                });
              }
            });
          }
        });
      }
      
      // Handle pages
      if (courseContent.pages) {
        courseContent.pages.forEach((page, pageIndex) => {
          const key = `page_${pageIndex}`;
          if (selectedItems[key]) {
            itemsToUpload.push({
              name: page.title,
              type: 'page',
              id: page.url.split('/').pop(), // Extract page ID from URL
              courseId: selectedCourse
            });
          }
        });
      }
    }
    
    // Update UI to show upload progress
    setProcessingFiles(itemsToUpload.map(item => ({
      name: item.name,
      progress: 0,
      status: 'uploading'
    })));
    
    try {
      // Create a collection name based on the course ID
      const courseCollection = `course_${selectedCourse}`;
      
      // Call the backend to upload all selected items to the RAG collection
      const response = await fetch('http://localhost:8012/upload_selected_to_rag', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          course_id: selectedCourse,
          token: canvasToken,
          user_id: userId,
          selected_items: itemsToUpload,
          collection_name: courseCollection
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to upload items to knowledge base');
      }
      
      const data = await response.json();
      
      // Update UI with success
      setSuccessMessage(`Successfully uploaded ${data.message}`);
      
      if (data.failed_items && data.failed_items.length > 0) {
        setError(`Failed to upload ${data.failed_items.length} items. Please try again.`);
      }
      
      // Update the processing files status
      setProcessingFiles(prev => prev.map(file => ({
        ...file,
        progress: 100,
        status: 'complete'
      })));
      
      // Refresh the knowledge base document list
      fetchDocuments(selectedCollection);
      
      // Clear the processing files after a delay
      setTimeout(() => {
        setProcessingFiles([]);
      }, 3000);
      
    } catch (error) {
      console.error('Error uploading to knowledge base:', error);
      setError(error.message || 'Failed to upload to knowledge base');
      
      // Update processing status to error
      setProcessingFiles(prev => prev.map(file => ({
        ...file,
        status: 'error'
      })));
    } finally {
      setIsProcessing(false);
    }
  };

  // Render progress files
  const renderProcessingFiles = () => {
    if (processingFiles.length === 0) return null;
    
    return (
      <div className="mt-4 mb-4 space-y-4 p-4 border rounded-md bg-card text-card-foreground">
        <h3 className="text-md font-medium">Processing Files</h3>
        {processingFiles.map((file, index) => (
          <div key={index} className="space-y-1">
            <div className="flex justify-between">
              <div className="flex items-center">
                <span className="mr-2">{file.name}</span>
                <Badge 
                  className={
                    file.status === 'complete' ? 'bg-green-100 text-green-800' :
                    file.status === 'error' ? 'bg-red-100 text-red-800' :
                    file.status === 'uploading' ? 'bg-blue-100 text-blue-800' :
                    'bg-card text-card-foreground'
                  }
                >
                  {file.status === 'complete' ? 'Complete' :
                   file.status === 'error' ? 'Failed' :
                   file.status === 'uploading' ? 'Uploading' :
                   'Queued'}
                </Badge>
              </div>
              <span className="text-sm">{Math.round(file.progress)}%</span>
            </div>
            <Progress value={file.progress} max={100} className="h-2" />
          </div>
        ))}
      </div>
    );
  };

  // Render Canvas files
  const renderCanvasFiles = () => {
    if (!courseContent || !Array.isArray(courseContent)) {
      return (
        <div className="text-center p-8 bg-card text-card-foreground rounded-lg border border-border">
          <p className="text-lg text-muted-foreground">No files available</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-2">
        {courseContent.map((file, index) => (
          <div 
            key={index} 
            className="p-3 border rounded-md bg-card hover:bg-muted text-card-foreground flex items-center"
          >
            <div className="flex-shrink-0 mr-3">
              <Checkbox 
                id={`file-${index}`} 
                checked={selectedItems[`file_${index}`] || false}
                onCheckedChange={() => toggleItemSelection(`file_${index}`)}
              />
            </div>
            <div className="flex-grow">
              <Label htmlFor={`file-${index}`} className="font-medium cursor-pointer">
                {file.name}
              </Label>
              <p className="text-sm text-muted-foreground">{file.type || 'Unknown type'} - {formatFileSize(file.size)}</p>
            </div>
          </div>
        ))}
      </div>
    );
  };

  // Render Canvas course structure
  const renderCanvasStructure = () => {
    if (!courseContent || !courseContent.modules || !courseContent.pages) {
      return (
        <div className="text-center p-8 bg-card text-card-foreground rounded-lg border border-border">
          <p className="text-lg text-muted-foreground">No course structure available</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        {/* Modules */}
        <div>
          <h3 className="text-lg font-medium mb-2">Modules</h3>
          {courseContent.modules.length === 0 ? (
            <div className="p-4 border rounded-md bg-card text-card-foreground text-center">No modules available</div>
          ) : (
            <div className="space-y-2">
              {courseContent.modules.map((module, moduleIndex) => (
                <div key={moduleIndex} className="p-3 border rounded-md bg-card text-card-foreground">
                  <p className="font-medium">{module.name}</p>
                  {module.items && module.items.length > 0 && (
                    <div className="ml-4 mt-2 space-y-1">
                      {module.items.map((item, itemIndex) => (
                        <div key={itemIndex} className="flex items-center p-2 border-l-2 border-border text-foreground">
                          <div className="flex-shrink-0 mr-3">
                            <Checkbox 
                              id={`module-${moduleIndex}-item-${itemIndex}`} 
                              checked={selectedItems[`module_${moduleIndex}_item_${itemIndex}`] || false}
                              onCheckedChange={() => toggleItemSelection(`module_${moduleIndex}_item_${itemIndex}`)}
                            />
                          </div>
                          <Label 
                            htmlFor={`module-${moduleIndex}-item-${itemIndex}`} 
                            className="cursor-pointer"
                          >
                            {item.title} <span className="text-muted-foreground">({item.type})</span>
                          </Label>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Pages */}
        <div>
          <h3 className="text-lg font-medium mb-2">Pages</h3>
          {courseContent.pages.length === 0 ? (
            <div className="p-4 border rounded-md bg-card text-card-foreground text-center">No pages available</div>
          ) : (
            <div className="space-y-2">
              {courseContent.pages.map((page, pageIndex) => (
                <div key={pageIndex} className="p-3 border rounded-md bg-card text-card-foreground flex items-center">
                  <div className="flex-shrink-0 mr-3">
                    <Checkbox 
                      id={`page-${pageIndex}`} 
                      checked={selectedItems[`page_${pageIndex}`] || false}
                      onCheckedChange={() => toggleItemSelection(`page_${pageIndex}`)}
                    />
                  </div>
                  <div>
                    <Label htmlFor={`page-${pageIndex}`} className="font-medium cursor-pointer">
                      {page.title}
                    </Label>
                    <p className="text-sm text-muted-foreground">Last updated: {new Date(page.updated_at).toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

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
      // Determine which collection to use based on selected course
      let collectionName = "";
      if (useKnowledgeBase && selectedCourse) {
        collectionName = `course_${selectedCourse}`;
      }

      const requestBody = {
        messages: [...messages, newMessage],
        use_knowledge_base: useKnowledgeBase,
        persona,
        temperature: 0.7,
        top_p: 0.8,
        max_tokens: 1024,
        top_k: 4,
        collection_name: collectionName,
        model: "",
        enable_citations: true  // Enable citations from the RAG server
      };
      
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
    <div className="min-h-screen bg-background text-foreground p-4">
      {/* Title */}
      <div className="max-w-4xl mx-auto mb-6 text-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-primary/80 bg-clip-text text-transparent"> 
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
        ttsEnabled={ttsEnabled}
        setTTSEnabled={setTTSEnabled}
        isDarkMode={isDarkMode}
        setIsDarkMode={setIsDarkMode}
        selectedEdgeCase={selectedEdgeCase}
        handleEdgeCaseSelect={handleEdgeCaseSelect}
        handleSubmit={handleSubmit}
        isLoading={isLoading}
        persona={persona}
        setPersona={setPersona}
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
      {(isFetchingCourses || isDownloading || isLoadingContent || isProcessing) && !error && !successMessage && (
        <div className="max-w-4xl mx-auto mb-6">
          <Alert>
            <AlertDescription>
              {isFetchingCourses ? 'Fetching courses...' : 
               isDownloading ? 'Downloading course...' : 
               isProcessing ? 'Processing files...' :
               'Loading course content...'}
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Processing Files */}
      {renderProcessingFiles()}

      {/* Main Content Area with Tabs */}
      <div className="max-w-4xl mx-auto">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid grid-cols-3 mb-4">
            <TabsTrigger value="chat">Chat</TabsTrigger>
            <TabsTrigger 
              value="content" 
              disabled={!tokenVerified || downloadedCourses.length === 0}
            >
              Course Content
            </TabsTrigger>
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
          <TabsContent value="content">
            <Card className="bg-card/80 backdrop-blur-sm border border-border">
              <CardContent className="p-6">
                <div className="mb-6">
                  <div className="flex flex-col md:flex-row gap-4 mb-4">
                    <div className="flex-1">
                      <Select 
                        value={selectedCourse} 
                        onValueChange={(value) => {
                          setSelectedCourse(value);
                          if (downloadedCourses.includes(value)) {
                            fetchCourseContent(value, 'file_list');
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
                        variant={selectedTab === 'files' ? 'default' : 'outline'}
                        onClick={() => {
                          setSelectedTab('files');
                          fetchCourseContent(selectedCourse, 'file_list');
                        }}
                        disabled={isLoadingContent || !selectedCourse || !downloadedCourses.includes(selectedCourse)}
                        className={selectedTab === 'files' ? 'bg-primary hover:brightness-110 text-primary-foreground' : ''}
                      >
                        Files
                      </Button>
                      <Button
                        variant={selectedTab === 'structure' ? 'default' : 'outline'}
                        onClick={() => {
                          setSelectedTab('structure');
                          fetchCourseContent(selectedCourse, 'course_info');
                        }}
                        disabled={isLoadingContent || !selectedCourse || !downloadedCourses.includes(selectedCourse)}
                        className={selectedTab === 'structure' ? 'bg-primary hover:brightness-110 text-primary-foreground' : ''}
                      >
                        Course Structure
                      </Button>
                    </div>
                  </div>
                  
                  {downloadedCourses.length === 0 && (
                    <div className="text-center p-8 bg-card rounded-lg border border-border text-card-foreground">
                      <p className="text-lg">No courses have been downloaded yet.</p>
                      <p className="text-sm text-muted-foreground mt-2">Download a course to view its content here.</p>
                    </div>
                  )}
                  
                  {selectedCourse && downloadedCourses.includes(selectedCourse) && (
                    <div className="mt-4">
                      <ScrollArea className="h-[500px] pr-4 mb-4">
                        {isLoadingContent ? (
                          <div className="flex justify-center items-center h-64">
                            <p className="text-muted-foreground">Loading content...</p>
                          </div>
                        ) : (
                          selectedTab === 'files' ? renderCanvasFiles() : renderCanvasStructure()
                        )}
                      </ScrollArea>
                      
                      <div className="flex justify-between items-center mt-4">
                        <div>
                          <span className="font-medium">{getTotalSelectedItems()}</span> items selected
                        </div>
                        <Button
                          disabled={getTotalSelectedItems() === 0 || isProcessing}
                          onClick={uploadSelectedToRAG}
                          className='bg-primary hover:brightness-110 text-primary-foreground'
                        >
                          {isProcessing ? 'Uploading...' : 'Upload Selected to Knowledge Base'}
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* Knowledge Base Tab */}
          <TabsContent value="knowledge">
            <KnowledgeBase 
              documents={documents}
              fetchDocuments={fetchDocuments}
              fetchCollections={fetchCollections}
              collections={collections}
              selectedCollection={selectedCollection}
              setSelectedCollection={fetchCollectionDocuments}
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
