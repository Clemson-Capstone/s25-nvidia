import React, { useState, useRef } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";

// Server URLs
const RAG_SERVER_URL = "http://localhost:8081";  // For retrieval operations
const INGESTION_SERVER_URL = "http://localhost:8082";  // For ingestion operations

const KnowledgeBase = ({
  documents,
  fetchDocuments,
  fetchCollections,
  setError,
  setSuccessMessage,
  formatFileSize
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [isDeletingFile, setIsDeletingFile] = useState(null);
  const [isClearing, setIsClearing] = useState(false);
  const [processingFiles, setProcessingFiles] = useState([]);
  const fileInputRef = useRef(null);

  // Handle file upload from computer
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    setIsUploading(true);
    setError('');
    setSuccessMessage('');
    
    // Add file to processing list
    setProcessingFiles([{ name: file.name, progress: 0, status: 'uploading' }]);
    
    // Create FormData object to send the file
    const formData = new FormData();
    formData.append('documents', file);
    
    // Add extraction and split options
    const data = {
      "collection_name": "default",
      "extraction_options": {
        "extract_text": true,
        "extract_tables": true,
        "extract_charts": true,
        "extract_images": false,
        "extract_method": "pdfium",
        "text_depth": "page",
      },
      "split_options": {
        "chunk_size": 1024,
        "chunk_overlap": 150
      }
    };
    formData.append('data', JSON.stringify(data));
    
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
      
      // Use the INGESTION server for document upload
      const response = await fetch(`${INGESTION_SERVER_URL}/v1/documents`, {
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
      setSuccessMessage(`File "${file.name}" uploaded successfully!`);
      
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
    }
  };
  
  // Clear all files from default collection
  const handleClearAllFiles = async () => {
    if (!confirm("Are you sure you want to delete all files from the default collection?")) {
      return;
    }
    
    setIsClearing(true);
    setError('');
    setSuccessMessage('');
    
    try {
      // Get all document names
      const docNames = documents.map(doc => 
        typeof doc === 'string' ? doc : (doc.document_name || '')
      ).filter(name => name);
      
      if (docNames.length === 0) {
        setSuccessMessage('No files to clear.');
        return;
      }
      
      // Delete all documents
      const response = await fetch(`${INGESTION_SERVER_URL}/v1/documents?collection_name=default`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(docNames),
      });
      
      if (!response.ok) {
        throw new Error('Failed to clear files');
      }
      
      await fetchDocuments();
      setSuccessMessage('All files cleared successfully!');
    } catch (error) {
      console.error('Error clearing files:', error);
      setError('Failed to clear files: ' + error.message);
    } finally {
      setIsClearing(false);
    }
  };
  
  // Handle file deletion
  const handleDeleteFile = async (filename) => {
    setIsDeletingFile(filename);
    setError('');
    setSuccessMessage('');
    
    try {
      // Use the ingestion server's v1 API with collection_name parameter
      const response = await fetch(`${INGESTION_SERVER_URL}/v1/documents?collection_name=default`, {
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
      setSuccessMessage(`File "${filename}" deleted successfully!`);
    } catch (error) {
      console.error('Error deleting file:', error);
      setError(`Failed to delete file "${filename}": ${error.message}`);
    } finally {
      setIsDeletingFile(null);
    }
  };
  
  // Render processing files
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
    <Card className="bg-card/80 backdrop-blur-sm border border-border max-w-4xl mx-auto">
      <CardContent className="p-6">
        <h2 className="text-xl font-semibold mb-4">Knowledge Base</h2>
        
        <div className="space-y-6">
          {/* Upload Files Section */}
          <div>
            <h3 className="text-lg font-medium mb-2">Upload Files</h3>
            <p className="text-muted-foreground mb-4">
              Upload files to enhance the knowledge base. Supported file types include: PDF, DOCX, TXT, CSV, PPTX, and MD.
            </p>
            
            <div className="flex flex-col gap-4 mb-4">
              <div className="flex gap-2">
                <Input 
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  disabled={isUploading}
                  accept=".pdf,.docx,.txt,.csv,.pptx,.md"
                  className="flex-1"
                />
                
                <Button
                  variant="default"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className="whitespace-nowrap"
                >
                  {isUploading ? 'Uploading...' : 'Upload File'}
                </Button>
              </div>
            </div>
          </div>
          
          {/* Files List */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">Files in Knowledge Base</h3>
              <div className="space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fetchDocuments()}
                  className="text-primary"
                >
                  Refresh
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleClearAllFiles}
                  disabled={isClearing || documents.length === 0}
                >
                  {isClearing ? 'Clearing...' : 'Clear All Files'}
                </Button>
              </div>
            </div>
            
            {documents.length === 0 ? (
              <div className="text-center p-8 bg-card rounded-lg border border-border">
                <p className="text-lg text-muted-foreground">No files in the knowledge base yet.</p>
                <p className="text-sm text-muted-foreground mt-2">Upload files to enhance the knowledge base.</p>
              </div>
            ) : (
              <ScrollArea className="h-[400px] pr-4">
                <div className="space-y-2">
                  {documents.map((document, index) => {
                    // Check if document is an object or string
                    const filename = typeof document === 'string' 
                      ? document 
                      : (document.document_name || 'Unknown file');
                    
                    return (
                      <div 
                        key={index} 
                        className="p-3 border rounded-md bg-card hover:bg-muted flex justify-between items-center"
                      >
                        <div>
                          <p className="font-medium">{filename}</p>
                          <p className="text-sm text-muted-foreground">
                            {typeof filename === 'string' && filename.includes('.') ? 
                              filename.split('.').pop().toUpperCase() : 'Unknown'} File
                          </p>
                        </div>
                        
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteFile(filename)}
                          disabled={isDeletingFile === filename}
                          className="text-destructive hover:bg-destructive/10"
                        >
                          {isDeletingFile === filename ? 'Deleting...' : 'Delete'}
                        </Button>
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            )}
          </div>
        </div>
        
        {/* Processing Files Section */}
        {renderProcessingFiles()}
      </CardContent>
    </Card>
  );
};

export default KnowledgeBase;