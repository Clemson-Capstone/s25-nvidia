/**
 * THIS FILE IS DEPRECATED AND WILL BE REMOVED IN THE FUTURE. IT IS NOT IN USE BY THE FRONTEND.
 * IT IS KEPT HERE FOR REFERENCE PURPOSES ONLY.
 */

import React from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const CourseContent = ({
  selectedCourse,
  setSelectedCourse,
  downloadedCourses,
  courses,
  isLoadingContent,
  contentType,
  fetchCourseContent,
  courseContent,
  formatFileSize
}) => {
  // Render the content based on its type
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

  return (
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
  );
};

export default CourseContent;