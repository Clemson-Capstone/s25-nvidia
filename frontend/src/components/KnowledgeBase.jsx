import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";

const KnowledgeBase = ({
  documents,
  fetchDocuments,
  fetchCollections,
  collections,
  selectedCollection: propSelectedCollection,
  setSelectedCollection: propSetSelectedCollection,
  setError,
  setSuccessMessage,
  canvasToken,
  userId,
  courses,
  selectedCourse,
  setSelectedCourse,
  downloadedCourses,
  formatFileSize
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [isDeletingFile, setIsDeletingFile] = useState(null);
  const [selectedCanvasTab, setSelectedCanvasTab] = useState('files');
  const [canvasContent, setCanvasContent] = useState(null);
  const [isLoadingCanvasContent, setIsLoadingCanvasContent] = useState(false);
  const [selectedItems, setSelectedItems] = useState({});
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingFiles, setProcessingFiles] = useState([]);
  const [uploadingToRag, setUploadingToRag] = useState(false);
  const fileInputRef = useRef(null);
  
  // Local collection state
  const [localSelectedCollection, setLocalSelectedCollection] = useState(propSelectedCollection || 'default');
  const [newCollectionName, setNewCollectionName] = useState('');
  const [isCreatingCollection, setIsCreatingCollection] = useState(false);
  const [showCollectionInput, setShowCollectionInput] = useState(false);
  
  // Sync with parent component when prop changes
  useEffect(() => {
    if (propSelectedCollection) {
      setLocalSelectedCollection(propSelectedCollection);
    }
  }, [propSelectedCollection]);
  
  // Update parent component when local state changes
  useEffect(() => {
    if (propSetSelectedCollection && localSelectedCollection !== propSelectedCollection) {
      propSetSelectedCollection(localSelectedCollection);
    }
  }, [localSelectedCollection, propSelectedCollection, propSetSelectedCollection]);
  
  // Fetch canvas content when tab or course changes
  useEffect(() => {
    if (selectedCourse && downloadedCourses.includes(selectedCourse)) {
      fetchCanvasContent(selectedCourse, selectedCanvasTab === 'files' ? 'file_list' : 'course_info');
    }
  }, [selectedCourse, selectedCanvasTab]);

  // Fetch canvas content
  const fetchCanvasContent = async (courseId, contentType) => {
    if (!courseId || !canvasToken || !userId) {
      return;
    }
    
    setIsLoadingCanvasContent(true);
    setCanvasContent(null);
    
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
          content_type: contentType
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch ${contentType} content`);
      }
      
      const data = await response.json();
      setCanvasContent(data);
      
      // Initialize selected items
      const newSelectedItems = {};
      if (contentType === 'file_list' && Array.isArray(data)) {
        data.forEach((item, index) => {
          newSelectedItems[`file_${index}`] = false;
        });
      } else if (contentType === 'course_info') {
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
      console.error('Error fetching canvas content:', error);
      setError(error.message || 'Failed to fetch canvas content');
    } finally {
      setIsLoadingCanvasContent(false);
    }
  };
  
  // Toggle selection of an item
  const toggleItemSelection = (itemKey) => {
    setSelectedItems(prev => ({
      ...prev,
      [itemKey]: !prev[itemKey]
    }));
  };
  
  // Calculate total selected items
  const getTotalSelectedItems = () => {
    return Object.values(selectedItems).filter(Boolean).length;
  };
  
  // Use the collections passed as props
  // These state declarations were redundant and causing conflicts

  // Removed redundant useEffect that would call the now-removed fetchCollections function

  // This function is now expected to be passed as a prop and shouldn't be redefined here

  // Create a new collection
  const handleCreateCollection = async () => {
    if (!newCollectionName.trim()) {
      setError('Please enter a collection name');
      return;
    }
    
    setIsCreatingCollection(true);
    setError('');
    
    try {
      const response = await fetch('http://localhost:8081/v1/collections', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ collection_name: newCollectionName }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to create collection');
      }
      
      await fetchCollections();
      setSuccessMessage(`Collection "${newCollectionName}" created successfully!`);
      setLocalSelectedCollection(newCollectionName);
      setNewCollectionName('');
      setShowCollectionInput(false);
    } catch (error) {
      console.error('Error creating collection:', error);
      setError('Failed to create collection: ' + error.message);
    } finally {
      setIsCreatingCollection(false);
    }
  };

  // Handle file upload from computer
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!localSelectedCollection) {
      setError('Please select a collection or create a new one first');
      return;
    }
    
    setIsUploading(true);
    setUploadProgress(0);
    setError('');
    setSuccessMessage('');
    
    // Add file to processing list
    setProcessingFiles([{ name: file.name, progress: 0, status: 'uploading' }]);
    
    // Create FormData object to send the file
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      // Create a mock progress simulation
      const progressInterval = setInterval(() => {
        setProcessingFiles(prev => {
          const newFiles = [...prev];
          if (newFiles[0]) {
            const currentProgress = newFiles[0].progress;
            // Simulate progress up to 90% (the last 10% will be when we get the response)
            if (currentProgress < 90) {
              newFiles[0].progress = currentProgress + Math.random() * 10;
              if (newFiles[0].progress > 90) newFiles[0].progress = 90;
            }
          }
          return newFiles;
        });
      }, 500);
      
      // Use the v1 API with collection_name parameter
      const response = await fetch(`http://localhost:8081/v1/documents?collection_name=${encodeURIComponent(localSelectedCollection)}`, {
        method: 'POST',
        body: formData,
      });
      
      clearInterval(progressInterval);
      
      if (!response.ok) {
        throw new Error('Failed to upload file');
      }
      
      // Update to 100% complete
      setProcessingFiles(prev => {
        const newFiles = [...prev];
        if (newFiles[0]) {
          newFiles[0].progress = 100;
          newFiles[0].status = 'complete';
        }
        return newFiles;
      });
      
      await fetchDocuments();
      setSuccessMessage(`File "${file.name}" uploaded successfully to collection "${localSelectedCollection}"!`);
      
      // Clear the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      // Clear the processing files after a delay
      setTimeout(() => {
        setProcessingFiles([]);
      }, 3000);
    } catch (error) {
      console.error('Error uploading file:', error);
      setError('Failed to upload file: ' + error.message);
      
      // Update status to error
      setProcessingFiles(prev => {
        const newFiles = [...prev];
        if (newFiles[0]) {
          newFiles[0].status = 'error';
        }
        return newFiles;
      });
    } finally {
      setIsUploading(false);
      setUploadProgress(100);
    }
  };
  
  // Upload selected canvas items to RAG
  const uploadSelectedCanvasItems = async () => {
    const selectedCount = getTotalSelectedItems();
    if (selectedCount === 0) {
      setError('Please select at least one item to upload');
      return;
    }
    
    if (!localSelectedCollection) {
      setError('Please select a collection or create a new one first');
      return;
    }
    
    setUploadingToRag(true);
    setError('');
    setSuccessMessage('');
    
    // Create an array of files to process
    const filesToProcess = [];
    
    // Collect the selected files
    if (selectedCanvasTab === 'files' && Array.isArray(canvasContent)) {
      canvasContent.forEach((file, index) => {
        const key = `file_${index}`;
        if (selectedItems[key]) {
          filesToProcess.push({
            name: file.name,
            url: file.url,
            key: key,
            type: 'file',
            progress: 0,
            status: 'queued'
          });
        }
      });
    } else if (selectedCanvasTab === 'structure' && canvasContent) {
      // Handle modules
      if (canvasContent.modules) {
        canvasContent.modules.forEach((module, moduleIndex) => {
          if (module.items) {
            module.items.forEach((item, itemIndex) => {
              const key = `module_${moduleIndex}_item_${itemIndex}`;
              if (selectedItems[key]) {
                filesToProcess.push({
                  name: item.title,
                  url: item.html_url,
                  key: key,
                  type: item.type,
                  progress: 0,
                  status: 'queued'
                });
              }
            });
          }
        });
      }
      
      // Handle pages
      if (canvasContent.pages) {
        canvasContent.pages.forEach((page, pageIndex) => {
          const key = `page_${pageIndex}`;
          if (selectedItems[key]) {
            filesToProcess.push({
              name: page.title,
              url: page.html_url,
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
    
    // Create course collection if using a specific one for the course
    let courseCollection = localSelectedCollection;
    if (localSelectedCollection === 'course_auto') {
      // Create a collection specifically for this course
      courseCollection = `course_${selectedCourse}`;
      
      try {
        // Check if the collection already exists
        const existingCollection = collections.find(c => 
          c.collection_name === courseCollection
        );
        
        if (!existingCollection) {
          // Create collection for this course
          const createResponse = await fetch('http://localhost:8081/v1/collections', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ collection_name: courseCollection }),
          });
          
          if (!createResponse.ok) {
            throw new Error(`Failed to create collection "${courseCollection}"`);
          }
          
          // Update collections list
          await fetchCollections();
        }
      } catch (error) {
        console.error('Error creating course collection:', error);
        setError(`Failed to create course collection: ${error.message}`);
        setUploadingToRag(false);
        return;
      }
    }
    
    // Process each file sequentially
    for (let i = 0; i < filesToProcess.length; i++) {
      const file = filesToProcess[i];
      
      // Update current file status to uploading
      setProcessingFiles(prev => {
        const newFiles = [...prev];
        const fileIndex = newFiles.findIndex(f => f.key === file.key);
        if (fileIndex !== -1) {
          newFiles[fileIndex].status = 'uploading';
        }
        return newFiles;
      });
      
      try {
        // Create a mock progress simulation for this file
        const progressInterval = setInterval(() => {
          setProcessingFiles(prev => {
            const newFiles = [...prev];
            const fileIndex = newFiles.findIndex(f => f.key === file.key);
            if (fileIndex !== -1 && newFiles[fileIndex].status === 'uploading') {
              const currentProgress = newFiles[fileIndex].progress;
              // Simulate progress up to 90%
              if (currentProgress < 90) {
                newFiles[fileIndex].progress = currentProgress + Math.random() * 10;
                if (newFiles[fileIndex].progress > 90) newFiles[fileIndex].progress = 90;
              }
            }
            return newFiles;
          });
        }, 500);
        
        // Make a request to download and upload this file to RAG
        // Include the collection name in the request
        const response = await fetch('http://localhost:8012/download_and_upload_to_rag', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            url: file.url,
            name: file.name,
            type: file.type,
            course_id: parseInt(selectedCourse),
            token: canvasToken,
            user_id: String(userId),
            collection_name: courseCollection
          }),
        });
        
        clearInterval(progressInterval);
        
        if (!response.ok) {
          throw new Error(`Failed to process ${file.name}`);
        }
        
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
      } catch (error) {
        console.error(`Error processing ${file.name}:`, error);
        
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
    
    // Refresh the document list
    await fetchDocuments();
    setSuccessMessage(`Uploaded ${filesToProcess.length} items to the collection "${courseCollection}"!`);
    setUploadingToRag(false);
    
    // Clear the processing files after a delay
    setTimeout(() => {
      setProcessingFiles([]);
    }, 5000);
  };
  
  // Handle file deletion
  const handleDeleteFile = async (filename) => {
    if (!localSelectedCollection) {
      setError('No collection selected');
      return;
    }
    
    setIsDeletingFile(filename);
    setError('');
    setSuccessMessage('');
    
    try {
      // Use the v1 API with collection_name parameter
      const response = await fetch(`http://localhost:8081/v1/documents?collection_name=${encodeURIComponent(localSelectedCollection)}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify([filename]),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete file "${filename}"`);
      }
      
      await fetchDocuments();
      setSuccessMessage(`File "${filename}" deleted successfully from collection "${localSelectedCollection}"!`);
    } catch (error) {
      console.error('Error deleting file:', error);
      setError(`Failed to delete file "${filename}": ${error.message}`);
    } finally {
      setIsDeletingFile(null);
    }
  };
  
  // Handle collection deletion
  const handleDeleteCollection = async (collectionName) => {
    if (collectionName === 'default') {
      setError('Cannot delete the default collection');
      return;
    }
    
    if (!confirm(`Are you sure you want to delete the collection "${collectionName}" and all its documents?`)) {
      return;
    }
    
    setError('');
    setSuccessMessage('');
    
    try {
      const response = await fetch(`http://localhost:8081/v1/collections`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ collection_names: [collectionName] }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete collection "${collectionName}"`);
      }
      
      // Reset to default collection
      setLocalSelectedCollection('default');
      await fetchCollections();
      await fetchDocuments();
      setSuccessMessage(`Collection "${collectionName}" deleted successfully!`);
    } catch (error) {
      console.error('Error deleting collection:', error);
      setError(`Failed to delete collection: ${error.message}`);
    }
  };
  
  // Render Canvas files tab
  const renderCanvasFiles = () => {
    if (!canvasContent || !Array.isArray(canvasContent)) {
      return (
        <div className="text-center p-8 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-lg text-gray-600">No files available</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-2">
        {canvasContent.map((file, index) => (
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
  
  // Render Canvas course structure tab
  const renderCanvasStructure = () => {
    if (!canvasContent || !canvasContent.modules || !canvasContent.pages) {
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
          {canvasContent.modules.length === 0 ? (
            <div className="p-4 border rounded-md bg-gray-50 text-center">No modules available</div>
          ) : (
            <div className="space-y-2">
              {canvasContent.modules.map((module, moduleIndex) => (
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
          {canvasContent.pages.length === 0 ? (
            <div className="p-4 border rounded-md bg-gray-50 text-center">No pages available</div>
          ) : (
            <div className="space-y-2">
              {canvasContent.pages.map((page, pageIndex) => (
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
                    file.status === 'uploading' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
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
  
  return (
    <Card className="bg-white/80 backdrop-blur-sm border border-orange-100">
      <CardContent className="p-6">
        <h2 className="text-xl font-semibold mb-4">Knowledge Base</h2>
        
        <Tabs defaultValue="upload" className="w-full mb-6">
          <TabsList className="mb-4">
            <TabsTrigger value="upload">Upload Content</TabsTrigger>
            <TabsTrigger value="browse">Browse Knowledge Base</TabsTrigger>
          </TabsList>
          
          {/* Upload Content Tab */}
          <TabsContent value="upload" className="space-y-6">
            {/* Upload from Computer Section */}
            <div>
              <h3 className="text-lg font-medium mb-2">Upload from Computer</h3>
              <p className="text-gray-600 mb-4">
                Upload files to enhance the knowledge base. Supported file types include: PDF, DOCX, TXT, CSV, PPTX, and MD.
              </p>
              
              <div className="flex flex-col gap-4 mb-4">
                <div className="flex flex-col md:flex-row gap-2 items-start">
                  <div className="w-full md:w-1/3">
                    <label className="text-sm font-medium mb-1 block">Select Collection</label>
                    <Select 
                      value={localSelectedCollection} 
                      onValueChange={setLocalSelectedCollection}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select a collection" />
                      </SelectTrigger>
                      <SelectContent>
                        {collections.length === 0 ? (
                          <SelectItem value="default">Default</SelectItem>
                        ) : (
                          collections.map(collection => (
                            <SelectItem 
                              key={collection.collection_name} 
                              value={collection.collection_name}
                            >
                              {collection.collection_name}
                            </SelectItem>
                          ))
                        )}
                        <SelectItem value="course_auto">Course-Specific (Auto)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="w-full md:w-2/3 md:pl-2">
                    <label className="text-sm font-medium mb-1 block">Choose File</label>
                    <div className="flex gap-2">
                      <Input 
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileUpload}
                        disabled={isUploading || !localSelectedCollection}
                        accept=".pdf,.docx,.txt,.csv,.pptx,.md"
                        className="flex-1"
                      />
                      
                      <Button
                        variant="outline"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading || !localSelectedCollection}
                        className="whitespace-nowrap bg-orange-500 hover:bg-orange-600 text-white"
                      >
                        {isUploading ? 'Uploading...' : 'Upload File'}
                      </Button>
                    </div>
                  </div>
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCollectionInput(true)}
                  className="text-green-600 border-green-600 hover:bg-green-50 w-auto"
                >
                  Create New Collection
                </Button>
              </div>
              
              {/* New Collection Form */}
              {showCollectionInput && (
                <div className="flex items-center gap-2 mb-4 p-3 bg-gray-50 rounded-md border border-gray-200">
                  <Input
                    value={newCollectionName}
                    onChange={(e) => setNewCollectionName(e.target.value)}
                    placeholder="Enter collection name"
                    className="flex-grow"
                    disabled={isCreatingCollection}
                  />
                  <Button
                    onClick={handleCreateCollection}
                    disabled={!newCollectionName.trim() || isCreatingCollection}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    {isCreatingCollection ? 'Creating...' : 'Create'}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowCollectionInput(false);
                      setNewCollectionName('');
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              )}
            </div>
            
            {/* Upload from Canvas */}
            {canvasToken && (
              <div>
                <h3 className="text-lg font-medium mb-2">Upload from Canvas</h3>
                
                {/* Course Selection */}
                <div className="mb-4">
                  <Select 
                    value={selectedCourse} 
                    onValueChange={setSelectedCourse}
                    disabled={!Object.keys(courses).length}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a course" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.keys(courses).length === 0 ? (
                        <SelectItem value="none" disabled>
                          No courses available
                        </SelectItem>
                      ) : (
                        Object.entries(courses).map(([id, name]) => (
                          <SelectItem key={id} value={id} disabled={!downloadedCourses.includes(id)}>
                            {name} {!downloadedCourses.includes(id) ? '(Not Downloaded)' : ''}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>
                
                {selectedCourse && downloadedCourses.includes(selectedCourse) ? (
                  <>
                    <div className="mb-4">
                      <Tabs value={selectedCanvasTab} onValueChange={setSelectedCanvasTab}>
                        <TabsList>
                          <TabsTrigger value="files">Files</TabsTrigger>
                          <TabsTrigger value="structure">Course Structure</TabsTrigger>
                        </TabsList>
                      </Tabs>
                    </div>
                    
                    <ScrollArea className="h-[300px] pr-4 mb-4">
                      {isLoadingCanvasContent ? (
                        <div className="flex justify-center items-center h-64">
                          <p className="text-gray-500">Loading content...</p>
                        </div>
                      ) : (
                        selectedCanvasTab === 'files' ? renderCanvasFiles() : renderCanvasStructure()
                      )}
                    </ScrollArea>
                    
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="font-medium">{getTotalSelectedItems()}</span> items selected
                      </div>
                      <Button
                        disabled={getTotalSelectedItems() === 0 || uploadingToRag}
                        onClick={uploadSelectedCanvasItems}
                        className="bg-orange-500 hover:bg-orange-600 text-white"
                      >
                        {uploadingToRag ? 'Uploading...' : 'Upload Selected to Knowledge Base'}
                      </Button>
                    </div>
                  </>
                ) : (
                  <div className="text-center p-8 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-gray-600">Please select a downloaded course to view its content.</p>
                  </div>
                )}
              </div>
            )}
            
            {/* Processing Files Section */}
            {renderProcessingFiles()}
          </TabsContent>
          
          {/* Browse Knowledge Base Tab */}
          <TabsContent value="browse">
            <h3 className="text-lg font-medium mb-4">Files in Knowledge Base</h3>
            
            {documents.length === 0 ? (
              <div className="text-center p-8 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-lg text-gray-600">
                  {collections.length === 0 
                    ? "No collections or files in the knowledge base yet." 
                    : `No files in the "${localSelectedCollection}" collection.`}
                </p>
                <p className="text-sm text-gray-500 mt-2">Upload files to enhance the knowledge base.</p>
              </div>
            ) : (
              <ScrollArea className="h-[400px] pr-4">
                <div className="space-y-2">
                  {documents.map((filename, index) => (
                    <div 
                      key={index} 
                      className="p-3 border rounded-md bg-white hover:bg-gray-50 flex justify-between items-center"
                    >
                      <div>
                        <p className="font-medium">{filename}</p>
                        <p className="text-sm text-gray-500">
                          {filename.split('.').pop().toUpperCase()} File
                          <span className="ml-2 text-xs text-gray-400">
                            Collection: {localSelectedCollection}
                          </span>
                        </p>
                      </div>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteFile(filename)}
                        disabled={isDeletingFile === filename}
                        className="text-red-500 hover:text-red-700 hover:bg-red-50"
                      >
                        {isDeletingFile === filename ? 'Deleting...' : 'Delete'}
                      </Button>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default KnowledgeBase;