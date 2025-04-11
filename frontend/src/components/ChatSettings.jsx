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
  ttsEnabled,
  setTTSEnabled,
  isDarkMode,
  setIsDarkMode,
  selectedEdgeCase,
  handleEdgeCaseSelect,
  handleSubmit,
  isLoading,
  persona,
  setPersona,
  enableQueryRewriting,
  setEnableQueryRewriting
}) => {
  const edgeCases = require('@/app/data/edgecase_dataset.json');
  
  return (
    <div className="max-w-4xl mx-auto mb-6">
      <Card className="bg-card/80 backdrop-blur-sm border border-border">
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
              <div className="flex items-center space-x-2">
                <Switch id="tts-mode" checked={ttsEnabled} onCheckedChange={setTTSEnabled} />
                <Label htmlFor="tts-mode">Enable Text-to-Speech</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch id="query-rewriting" checked={enableQueryRewriting} onCheckedChange={setEnableQueryRewriting} />
                <Label htmlFor="query-rewriting">Enable Query Rewriting</Label>
              </div>
              <Button
                variant="outline"
                onClick={() => setIsDarkMode(prev => !prev)}
                className="whitespace-nowrap"
              >
                {isDarkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
              </Button>

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
  );
};

export default ChatSettings;      