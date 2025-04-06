import React from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const CanvasIntegration = ({
  canvasToken,
  setCanvasToken,
  isVerifyingToken,
  tokenVerified,
  userId,
  courses,
  selectedCourse,
  setSelectedCourse,
  isFetchingCourses,
  isDownloading,
  downloadedCourses,
  verifyToken,
  handleLogout,
  downloadCourse
}) => {
  return (
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
  );
};

export default CanvasIntegration;