"use client"

import React, { useState, useEffect } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
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
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";

export default function CanvasTestPage() {
  // State for Canvas authentication
  const [canvasToken, setCanvasToken] = useState('');
  const [isVerifyingToken, setIsVerifyingToken] = useState(false);
  const [tokenVerified, setTokenVerified] = useState(false);
  const [userId, setUserId] = useState('');
  
  // State for courses
  const [courses, setCourses] = useState({});
  const [selectedCourse, setSelectedCourse] = useState('');
  const [isFetchingCourses, setIsFetchingCourses] = useState(false);
  const [downloadedCourses, setDownloadedCourses] = useState([]);
  
  // State for content
  const [contentType, setContentType] = useState('file_list');
  const [courseContent, setCourseContent] = useState(null);
  const [isLoadingContent, setIsLoadingContent] = useState(false);
  const [selectedItems, setSelectedItems] = useState({});
  
  // State for test operations
  const [processingFiles, setProcessingFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedTab, setSelectedTab] = useState('files');
  
  // Status messages
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  
  // Load token and userId from localStorage if available
  useEffect(() => {
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
  
  // Fetch canvas content when tab or course changes
  useEffect(() => {
    if (selectedCourse && downloadedCourses.includes(selectedCourse)) {
      fetchCourseContent(selectedCourse, selectedTab === 'files' ? 'file_list' : 'course_info');
    }
  }, [selectedCourse, selectedTab]);
  
  // Verify Canvas token
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
  
  // Fetch courses
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
  
  // Download course
  const downloadCourse = async () => {
    if (!selectedCourse) {
      setError('Please select a course to download');
      return;
    }
    
    setIsProcessing(true);
    setError('');
    setSuccessMessage('');
    
    // Add to processing list
    setProcessingFiles([
      { 
        name: `Course: ${courses[selectedCourse]}`,
        progress: 0,
        status: 'downloading'
      }
    ]);
    
    try {
      // Start progress simulation
      const progressInterval = setInterval(() => {
        setProcessingFiles(prev => {
          const newFiles = [...prev];
          if (newFiles[0]) {
            const currentProgress = newFiles[0].progress;
            if (currentProgress < 95) {
              newFiles[0].progress = currentProgress + Math.random() * 5;
            }
          }
          return newFiles;
        });
      }, 300);
      
      const response = await fetch('http://localhost:8012/download_course', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          course_id: parseInt(selectedCourse),
          token: canvasToken,
          user_id: String(userId)
        }),
      });
      
      clearInterval(progressInterval);
      
      if (!response.ok) {
        throw new Error('Failed to download course');
      }
      
      const data = await response.json();
      
      // Update progress to 100%
      setProcessingFiles(prev => {
        const newFiles = [...prev];
        if (newFiles[0]) {
          newFiles[0].progress = 100;
          newFiles[0].status = 'complete';
        }
        return newFiles;
      });
      
      setSuccessMessage(`Course downloaded successfully! (User ID: ${data.user_id})`);
      
      // Add the course to downloadedCourses
      if (!downloadedCourses.includes(selectedCourse)) {
        setDownloadedCourses([...downloadedCourses, selectedCourse]);
      }
      
      // Fetch content for the newly downloaded course
      fetchCourseContent(selectedCourse, selectedTab === 'files' ? 'file_list' : 'course_info');
      
      // Clear the processing files after a delay
      setTimeout(() => {
        setProcessingFiles([]);
      }, 3000);
    } catch (error) {
      console.error('Error downloading course:', error);
      setError(error.message || 'Failed to download course');
      
      // Update processing status to error
      setProcessingFiles(prev => {
        const newFiles = [...prev];
        if (newFiles[0]) {
          newFiles[0].status = 'error';
        }
        return newFiles;
      });
    } finally {
      setIsProcessing(false);
    }
  };
  
  // Fetch course content
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
      
      // Initialize selected items
      const newSelectedItems = {};
      if (type === 'file_list' && Array.isArray(data)) {
        data.forEach((item, index) => {
          newSelectedItems[`file_${index}`] = false;
        });
      } else if (type === 'course_info') {
        // For modules and pages
        if (data.modules) {
          data.modules.forEach((module, moduleIndex) => {
            if (module.items) {
              module.items.forEach((item, itemIndex) => {
                newSelectedItems[`module_${moduleIndex}_item_${itemIndex}`] = false;
              });
            }
          });
        }
        if (data.pages) {
          data.pages.forEach((page, pageIndex) => {
            newSelectedItems[`page_${pageIndex}`] = false;
          });
        }
      }
      setSelectedItems(newSelectedItems);
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

  // Complete downloadSelectedItems function with all fixes

const downloadSelectedItems = async () => {
  const selectedCount = getTotalSelectedItems();
  if (selectedCount === 0) {
    setError('Please select at least one item to download');
    return;
  }
  
  setIsProcessing(true);
  setError('');
  setSuccessMessage('');
  
  // Create an array of files to process
  const filesToProcess = [];
  
  // Collect the selected files
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
        
        filesToProcess.push({
          name: file.name,
          url: file.url,
          fileId: fileId,
          courseId: selectedCourse,
          key: key,
          type: 'file',
          progress: 0,
          status: 'queued'
        });
      }
    });
  } else if (selectedTab === 'structure' && courseContent) {
    // Handle modules
    if (courseContent.modules) {
      courseContent.modules.forEach((module, moduleIndex) => {
        if (module.items) {
          module.items.forEach((item, itemIndex) => {
            const key = `module_${moduleIndex}_item_${itemIndex}`;
            if (selectedItems[key]) {
              const itemData = {
                name: item.title,
                moduleId: module.id,
                itemId: item.id,
                contentId: item.content_id,
                courseId: selectedCourse,
                key: key,
                type: item.type.toLowerCase(),
                progress: 0,
                status: 'queued'
              };
              
              // Handle file items - store url and content_id which we need for file downloads
              if (item.type === 'File') {
                itemData.url = item.url;
                itemData.fileId = item.content_id;
              }
              
              filesToProcess.push(itemData);
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
          filesToProcess.push({
            name: page.title,
            contentId: page.url.split('/').pop(), // Extract page ID from URL
            courseId: selectedCourse,
            key: key,
            type: 'page',
            progress: 0,
            status: 'queued'
          });
        }
      });
    }
  }
  
  // Update the processing files list
  setProcessingFiles(filesToProcess);
  
  // Process each file sequentially
  for (let i = 0; i < filesToProcess.length; i++) {
    const file = filesToProcess[i];
    
    // Update current file status to downloading
    setProcessingFiles(prev => {
      const newFiles = [...prev];
      const fileIndex = newFiles.findIndex(f => f.key === file.key);
      if (fileIndex !== -1) {
        newFiles[fileIndex].status = 'downloading';
      }
      return newFiles;
    });
    
    try {
      // Create a mock progress simulation for this file
      const progressInterval = setInterval(() => {
        setProcessingFiles(prev => {
          const newFiles = [...prev];
          const fileIndex = newFiles.findIndex(f => f.key === file.key);
          if (fileIndex !== -1 && newFiles[fileIndex].status === 'downloading') {
            const currentProgress = newFiles[fileIndex].progress;
            // Simulate progress up to 90%
            if (currentProgress < 90) {
              newFiles[fileIndex].progress = currentProgress + Math.random() * 10;
              if (newFiles[fileIndex].progress > 90) newFiles[fileIndex].progress = 90;
            }
          }
          return newFiles;
        });
      }, 300);
      
      let downloadUrl;
      
      // Use the appropriate endpoint based on the content type
      if (file.type === 'file') {
        // For files from modules, use the content_id directly
        if (file.fileId) {
          downloadUrl = `http://localhost:8012/get_course_item?course_id=${file.courseId}&content_id=${file.fileId}&item_type=file&token=${canvasToken}`;
        } 
        // For files from the files tab, extract ID from URL
        else if (file.url) {
          const matches = file.url.match(/\/files\/(\d+)/);
          if (matches && matches[1]) {
            downloadUrl = `http://localhost:8012/get_course_item?course_id=${file.courseId}&content_id=${matches[1]}&item_type=file&token=${canvasToken}`;
          }
        }
        // As a fallback, use the download_module_item endpoint
        else if (file.moduleId && file.itemId) {
          downloadUrl = `http://localhost:8012/download_module_item?course_id=${file.courseId}&module_id=${file.moduleId}&item_id=${file.itemId}&token=${canvasToken}`;
        }
      } else if (file.moduleId && file.itemId) {
        // For module items, use the download_module_item endpoint
        downloadUrl = `http://localhost:8012/download_module_item?course_id=${file.courseId}&module_id=${file.moduleId}&item_id=${file.itemId}&token=${canvasToken}`;
      } else if (file.contentId) {
        // For other content types, use the get_course_item endpoint
        downloadUrl = `http://localhost:8012/get_course_item?course_id=${file.courseId}&content_id=${file.contentId}&item_type=${file.type}&token=${canvasToken}`;
      }
      
      // Create a temporary link to download the file
      if (downloadUrl) {
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = file.name || 'canvas_content';
        a.target = '_blank'; // Open in new tab to handle browser download behavior
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      } else {
        throw new Error(`Could not determine download URL for ${file.name}`);
      }
      
      clearInterval(progressInterval);
      
      // Update file status to complete
      setProcessingFiles(prev => {
        const newFiles = [...prev];
        const fileIndex = newFiles.findIndex(f => f.key === file.key);
        if (fileIndex !== -1) {
          newFiles[fileIndex].progress = 100;
          newFiles[fileIndex].status = 'complete';
        }
        return newFiles;
      });
      
      // Add a small delay between downloads to help browser handle multiple downloads
      await new Promise(resolve => setTimeout(resolve, 800));
    } catch (error) {
      console.error(`Error downloading ${file.name}:`, error);
      
      // Update file status to error
      setProcessingFiles(prev => {
        const newFiles = [...prev];
        const fileIndex = newFiles.findIndex(f => f.key === file.key);
        if (fileIndex !== -1) {
          newFiles[fileIndex].status = 'error';
        }
        return newFiles;
      });
    }
  }
  
  setSuccessMessage(`Downloaded ${filesToProcess.length} items!`);
  setIsProcessing(false);
  
  // Clear the processed files after a delay
  setTimeout(() => {
    if (filesToProcess.every(file => file.status === 'complete')) {
      setProcessingFiles([]);
    }
  }, 5000);
};

  // Format file size
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
  
  // Render Canvas files
  const renderCanvasFiles = () => {
    if (!courseContent || !Array.isArray(courseContent)) {
      return (
        <div className="text-center p-8 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-lg text-gray-600">No files available</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-2">
        {courseContent.map((file, index) => (
          <div 
            key={index} 
            className="p-3 border rounded-md bg-white hover:bg-gray-50 flex items-center"
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
              <p className="text-sm text-gray-500">{file.type || 'Unknown type'} - {formatFileSize(file.size)}</p>
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
        <div className="text-center p-8 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-lg text-gray-600">No course structure available</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        {/* Modules */}
        <div>
          <h3 className="text-lg font-medium mb-2">Modules</h3>
          {courseContent.modules.length === 0 ? (
            <div className="p-4 border rounded-md bg-gray-50 text-center">No modules available</div>
          ) : (
            <div className="space-y-2">
              {courseContent.modules.map((module, moduleIndex) => (
                <div key={moduleIndex} className="p-3 border rounded-md bg-white">
                  <p className="font-medium">{module.name}</p>
                  {module.items && module.items.length > 0 && (
                    <div className="ml-4 mt-2 space-y-1">
                      {module.items.map((item, itemIndex) => (
                        <div key={itemIndex} className="flex items-center p-2 border-l-2 border-orange-200">
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
                            {item.title} <span className="text-gray-500">({item.type})</span>
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
            <div className="p-4 border rounded-md bg-gray-50 text-center">No pages available</div>
          ) : (
            <div className="space-y-2">
              {courseContent.pages.map((page, pageIndex) => (
                <div key={pageIndex} className="p-3 border rounded-md bg-white flex items-center">
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
                    <p className="text-sm text-gray-500">Last updated: {new Date(page.updated_at).toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };
  
  // Render processing files
  const renderProcessingFiles = () => {
    if (processingFiles.length === 0) return null;
    
    return (
      <div className="mt-4 mb-4 space-y-4 p-4 border rounded-md bg-gray-50">
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
                    file.status === 'downloading' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }
                >
                  {file.status === 'complete' ? 'Complete' :
                   file.status === 'error' ? 'Failed' :
                   file.status === 'downloading' ? 'Downloading' :
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
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-100 via-white to-blue-50 p-4">
      {/* Title */}
      <div className="max-w-4xl mx-auto mb-6 text-center">
                  <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-blue-400 bg-clip-text text-transparent">
          Canvas Material Downloader (Test)
        </h1>
        <p className="text-gray-600 mt-2">
          Select and download Canvas course materials directly to your browser
        </p>
      </div>
      
      {/* Canvas Authentication */}
      <div className="max-w-4xl mx-auto mb-6">
        <Card className="bg-white/80 backdrop-blur-sm border border-blue-100">
          <CardContent className="p-6">
            <h2 className="text-xl font-semibold mb-4">Canvas Authentication</h2>
            
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
                  className="whitespace-nowrap bg-blue-500 hover:bg-blue-600 text-white"
                >
                  {isVerifyingToken ? 'Verifying...' : 'Verify Token'}
                </Button>
              )}
            </div>
            
            {userId && (
              <div className="text-sm text-gray-600 mb-2">
                Connected as User ID: {userId}
              </div>
            )}
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
      
      {error && (
        <div className="max-w-4xl mx-auto mb-6">
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      )}
      
      {/* Processing Files */}
      {renderProcessingFiles()}
      
      {/* Content Selection and Download */}
      {tokenVerified && (
        <div className="max-w-4xl mx-auto">
          <Card className="bg-white/80 backdrop-blur-sm border border-blue-100 mb-6">
            <CardContent className="p-6">
              <h2 className="text-xl font-semibold mb-4">Course Selection</h2>
              
              <div className="flex flex-col md:flex-row gap-3 mb-6">
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
                  disabled={isProcessing || !selectedCourse || isFetchingCourses}
                  className="whitespace-nowrap bg-blue-500 hover:bg-blue-600 text-white"
                >
                  {isProcessing ? 'Downloading...' : downloadedCourses.includes(selectedCourse) ? 'Re-Download' : 'Download Course'}
                </Button>
              </div>
              
              {selectedCourse && downloadedCourses.includes(selectedCourse) && (
                <>
                  <div className="mb-4">
                    <Tabs value={selectedTab} onValueChange={setSelectedTab}>
                      <TabsList>
                        <TabsTrigger value="files">Files</TabsTrigger>
                        <TabsTrigger value="structure">Course Structure</TabsTrigger>
                      </TabsList>
                    </Tabs>
                  </div>
                  
                  <ScrollArea className="h-[400px] pr-4 mb-4">
                    {isLoadingContent ? (
                      <div className="flex justify-center items-center h-64">
                        <p className="text-gray-500">Loading content...</p>
                      </div>
                    ) : (
                      selectedTab === 'files' ? renderCanvasFiles() : renderCanvasStructure()
                    )}
                  </ScrollArea>
                  
                  <div className="flex justify-between items-center">
                    <div>
                      <span className="font-medium">{getTotalSelectedItems()}</span> items selected
                    </div>
                    <Button
                      disabled={getTotalSelectedItems() === 0 || isProcessing}
                      onClick={downloadSelectedItems}
                      className="bg-blue-500 hover:bg-blue-600 text-white"
                    >
                      {isProcessing ? 'Downloading...' : 'Download Selected Files'}
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
          
          {/* API Testing Info */}
          <Card className="bg-white/80 backdrop-blur-sm border border-blue-100">
            <CardContent className="p-6">
              <h2 className="text-xl font-semibold mb-4">Test API Information</h2>
              
              <div className="space-y-4">
                <div>
                  <h3 className="text-md font-medium">Endpoints Being Tested:</h3>
                  <ul className="list-disc pl-6 mt-2 space-y-1">
                    <li className="text-gray-700"><code>/user_info</code> - Verifies Canvas token</li>
                    <li className="text-gray-700"><code>/get_courses</code> - Fetches course list</li>
                    <li className="text-gray-700"><code>/download_course</code> - Downloads all course data</li>
                    <li className="text-gray-700"><code>/get_course_content</code> - Retrieves specific course content</li>
                    <li className="text-gray-700"><code>Browser Downloads API</code> - Tests direct file downloads to browser</li>
                  </ul>
                </div>
                
                <div>
                  <h3 className="text-md font-medium">Connection Details:</h3>
                  <ul className="list-disc pl-6 mt-2 space-y-1">
                    <li className="text-gray-700">Canvas API Server: <code>http://localhost:8012</code></li>
                    <li className="text-gray-700">Canvas Download URLs accessed directly by browser</li>
                  </ul>
                </div>
                
                <div>
                  <h3 className="text-md font-medium">Testing Process:</h3>
                  <ol className="list-decimal pl-6 mt-2 space-y-1">
                    <li className="text-gray-700">Authenticate with Canvas token</li>
                    <li className="text-gray-700">Download a course to see its content</li>
                    <li className="text-gray-700">Select specific files or course materials</li>
                    <li className="text-gray-700">Test downloading files directly to your browser</li>
                    <li className="text-gray-700">Check progress indicators and response status</li>
                  </ol>
                </div>
                
                <div className="text-sm text-gray-600 p-3 bg-blue-50 rounded-md">
                  <p className="font-medium">Troubleshooting:</p>
                  <p>If you can't download files directly, make sure your Canvas token has sufficient permissions and that the files are accessible. Canvas API server should be running for course data access.</p>
                  <p>File downloads will appear in your browser's default download location.</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}