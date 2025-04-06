import React from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const ChatSettings = ({
  useKnowledgeBase,
  setUseKnowledgeBase,
  selectedEdgeCase,
  handleEdgeCaseSelect,
  handleSubmit,
  isLoading
}) => {
  const edgeCases = require('@/app/data/edgecase_dataset.json');
  
  return (
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
        </CardContent>
      </Card>
    </div>
  );
};

export default ChatSettings;