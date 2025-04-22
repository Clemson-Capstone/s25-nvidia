"use client"

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useChatStream } from '@/lib/hooks/useChatStream';
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
import Image from 'next/image'

import CanvasIntegration from '@/components/CanvasIntegration';
import ChatSettings from '@/components/ChatSettings';
import ChatInterface from '@/components/ChatInterface';
import KnowledgeBase from '@/components/KnowledgeBase';
import Footer from '@/components/Footer';

// TTS functionality removed as it's not working reliably across browsers

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
    console.log("Speech recognized:", speechResult);
  };
  
  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
    // Clear the "Listening..." text if there's an error
    setInputMessage("");
  };
  
  recognition.onend = () => {
    console.log("Speech recognition ended");
  };
  
  recognition.start();
  console.log("Speech recognition started");
}

// Expose startSpeechRecognition globally
if (typeof window !== 'undefined') {
  window.startSpeechRecognition = startSpeechRecognition;
}

export default function ChatPage() {
  // State variables
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [useKnowledgeBase, setUseKnowledgeBase] = useState(true);
  // Query rewriting disabled by default as it may cause issues with CPU-based inference
  const [enableQueryRewriting, setEnableQueryRewriting] = useState(false);
  const [enableGuardrails, setEnableGuardrails] = useState(true);
  const [selectedEdgeCase, setSelectedEdgeCase] = useState(null);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [ttsEnabled, setTTSEnabled] = useState(true); // Ensure TTS is enabled by default
  
  // Model parameters
  const [temperature, setTemperature] = useState(0.2);
  const [topP, setTopP] = useState(0.7);
  const [rerankerTopK, setRerankerTopK] = useState(2);
  const [vdbTopK, setVdbTopK] = useState(10);
  
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
  const [isDarkMode, setIsDarkMode] = useState(false);
  // ttsEnabled is already defined in the state variables section above
  
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
    
    // Ensure we're always fetching from the default collection first
    setSelectedCollection('default');
    
    // Fetch documents with default collection
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
  
  // TTS initialization removed as the feature is not being used

  // Reset selected items when course content changes
  useEffect(() => {
    if (courseContent) {
      initializeSelectedItems();
    }
  }, [courseContent, contentType, selectedTab]);

  // These state declarations have been moved to the top of the component
  
  // Fetch available collections and ensure default exists
  const fetchCollections = async () => {
    try {
      const response = await fetch(`${INGESTION_SERVER_URL}/v1/collections`);
      if (!response.ok) throw new Error('Failed to fetch collections');
      
      const data = await response.json();
      const collections = data.collections || [];
      
      // Check if default collection exists
      const defaultExists = collections.some(c => c.collection_name === 'default');
      
      // If default collection doesn't exist, create it
      if (!defaultExists) {
        try {
          // Use URLSearchParams to properly encode the query parameters for fetch
          const params = new URLSearchParams({
            collection_type: "text",
            embedding_dimension: 2048
          });
          
          const createResponse = await fetch(`${INGESTION_SERVER_URL}/v1/collections?${params.toString()}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(['default']),
          });
          
          if (!createResponse.ok) {
            throw new Error('Failed to create default collection');
          }
          
          // Fetch collections again after creating default
          const refreshResponse = await fetch(`${INGESTION_SERVER_URL}/v1/collections`);
          if (refreshResponse.ok) {
            const refreshedData = await refreshResponse.json();
            setCollections(refreshedData.collections || []);
          }
        } catch (createError) {
          console.error('Error creating default collection:', createError);
        }
      } else {
        // Set collections if default already exists
        setCollections(collections);
      }
      
      // Always select the default collection
      fetchCollectionDocuments('default');
      
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
          collection_name: "default"
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
      
      // Refresh the knowledge base document list - always get from 'default' collection
      fetchDocuments('default');
      
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
      <div className="mt-4 mb-4 space-y-4 p-4 border rounded-md bg-card text-card-foreground max-w-4xl mx-auto">
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

    if (courseContent.length === 0) {
      return (
        <div className="text-center p-8 bg-card text-card-foreground rounded-lg border border-border">
          <p className="text-lg text-muted-foreground">There seem to be no files in this course. Please click "course structure" and use that for uploads</p>
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

  // Add the useChatStream hook to handle streaming responses
  const { streamState, processStream, startStream, resetStream, stopStream, isStreaming } = useChatStream();
  
  // Sync isStreaming state with isLoading
  useEffect(() => {
    setIsLoading(streamState.isStreaming);
  }, [streamState.isStreaming]);
  
  // Expose utility functions to the global window object
  useEffect(() => {
    window.stopStream = stopStream;
    window.resetConversation = () => {
      setMessages([]);
      setStreamingMessage('');
      setError('');
      resetStream();
      console.log("Conversation reset");
    };
    
    return () => {
      window.stopStream = undefined;
      window.resetConversation = undefined;
    };
  }, [stopStream, resetStream]);
  
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

    // Reset stream and get a fresh abort controller
    resetStream();
    const controller = startStream();

    try {
      // Always use the default collection regardless of selected course
      let collectionName = "default";

      // Format the messages to match exactly what the RAG server expects
      const messagesFormatted = [...messages, newMessage].map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      // Construct the request body according to the notebook example
      // Check if we have more than one message (multiturn)
      const isMultiturn = messagesFormatted.length > 1;
      
      // Send the request with appropriate settings for multiturn conversations
      const requestBody = {
        messages: messagesFormatted,
        use_knowledge_base: useKnowledgeBase,
        temperature: temperature,
        top_p: topP,
        max_tokens: 1024, // Fixed value
        reranker_top_k: rerankerTopK,
        vdb_top_k: vdbTopK,
        vdb_endpoint: "http://milvus:19530",
        collection_name: collectionName,
        enable_query_rewriting: false, // Always disable query rewriting to prevent CPU inference issues
        enable_reranker: true,
        enable_citations: true,
        // Never override user settings for guardrails
        enable_guardrails: enableGuardrails,
        model: "meta/llama-3.1-70b-instruct", // Fixed model
        reranker_model: "nvidia/llama-3.2-nv-rerankqa-1b-v2", // Fixed reranker model
        embedding_model: "nvidia/llama-3.2-nv-embedqa-1b-v2", // Fixed embedding model
        stop: [],
        persona: persona,
      };
      
      console.log("Sending request to RAG server with parameters:", {
        temperature,
        topP,
        rerankerTopK,
        vdbTopK,
        enable_query_rewriting: false, // Always disabled
        enable_guardrails: enableGuardrails, // Use exactly what the user has set
        isMultiturn
      });
      
      console.log("Sending request to RAG server:", requestBody);
      
      const response = await fetch(`${RAG_SERVER_URL}/v1/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Process the streaming response using our hook
      await processStream(
        response, 
        setStreamingMessage,
        (updatedMessages) => {
          setMessages(updatedMessages);
          const lastMessage = updatedMessages[updatedMessages.length - 1];
          
          // TTS functionality disabled since it's not working reliably
          // Just update the messages without speaking
        }
      );

    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Stream was aborted');
        return;
      }
      
      console.error('Error:', error);
      
      // Check if this is a server error
      if (error.message.includes('Error') || 
          error.message.includes('CUDA') || 
          error.message.includes('memory') ||
          error.message.includes('uncorrectable')) {
        
        setError("A server error occurred. The RAG server may need to be restarted.");
        
        // Provide a generic message about the issue
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: 'I encountered a technical issue with the server. You can try resetting the conversation, or the server may need to be restarted.'
        }]);
      } 
      // Check if it's a model inference issue
      else if (error.message.includes('inference') || 
               error.message.includes('500') || 
               error.message.includes('Internal Server Error')) {
        
        setError("A model inference error occurred.");
        
        // Provide a troubleshooting message
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: 'There was an error with model inference. Some troubleshooting steps you can try:\n\n1. Reset the conversation\n2. Try a simpler or more direct question\n3. Ask your question as a new conversation'
        }]);
      } 
      else {
        // Generic error handling
        setError(error.message);
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: 'Sorry, I encountered an error processing your request. Please try again.'
        }]);
      }
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
      <div className="flex max-w-4xl mx-auto mb-6 items-center justify-center gap-4">
        <Image src="/logo.png" width={100} height={100} alt="Logo" />
        <p className="text-8xl font-ubuntu bg-gradient-to-r from-primary to-primary/80 bg-clip-text text-transparent"> 
          DORI
        </p>
      </div>

      {/* Tagline */}
      <div className="flex max-w-4xl mx-auto mb-6 items-center justify-center gap-4">
        <p className="text-2xl font-ubuntu text-muted-foreground">
          A virtual assistant to help you learn content
        </p>
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
        isDarkMode={isDarkMode}
        setIsDarkMode={setIsDarkMode}
        persona={persona}
        setPersona={setPersona}

        enableGuardrails={enableGuardrails}
        setEnableGuardrails={setEnableGuardrails}
        temperature={temperature}
        setTemperature={setTemperature}
        topP={topP}
        setTopP={setTopP}
        rerankerTopK={rerankerTopK}
        setRerankerTopK={setRerankerTopK}
        vdbTopK={vdbTopK}
        setVdbTopK={setVdbTopK}
      />

      {/* Status Messages */}
      {successMessage && (
        <div className="max-w-4xl mx-auto mb-6">
          <Alert className="bg-card text-card-foreground border-green-700 dark:border-green-200 max-w-4xl mx-auto">
            <AlertDescription className="text-green-700 dark:text-green-200">{successMessage}</AlertDescription>
          </Alert>
        </div>
      )}
      
      {/* Error Alert */}
      {error && (
        <div className="max-w-4xl mx-auto mb-6">
          <Alert variant="destructive" className="max-w-4xl mx-auto">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      )}

      {/* Loading Indicators */}
      {(isFetchingCourses || isDownloading || isLoadingContent || isProcessing) && !error && !successMessage && (
        <div className="max-w-4xl mx-auto mb-6">
          <Alert className="max-w-4xl mx-auto">
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
              setError={setError}
              setSuccessMessage={setSuccessMessage}
              formatFileSize={formatFileSize}
            />
          </TabsContent>
        </Tabs>
      </div>
      <Footer/>
    </div>
  );
}
