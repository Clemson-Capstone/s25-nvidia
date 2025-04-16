import React, { useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
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

const ChatSettings = ({
  useKnowledgeBase,
  setUseKnowledgeBase,
  ttsEnabled,
  setTTSEnabled,
  isDarkMode,
  setIsDarkMode,
  persona,
  setPersona,
  enableGuardrails,
  setEnableGuardrails,
  temperature,
  setTemperature,
  topP,
  setTopP,
  rerankerTopK,
  setRerankerTopK,
  vdbTopK,
  setVdbTopK
}) => {
  const [activeTab, setActiveTab] = useState('general');
  const [validationErrors, setValidationErrors] = useState({});
  
  // Input validation
  const validateTemperature = (value) => {
    const num = parseFloat(value);
    if (isNaN(num) || num < 0 || num > 1) {
      return "Temperature must be between 0 and 1";
    }
    return null;
  };
  
  const validateTopP = (value) => {
    const num = parseFloat(value);
    if (isNaN(num) || num < 0 || num > 1) {
      return "Top P must be between 0 and 1";
    }
    return null;
  };
  
  const validateTopK = (value) => {
    const num = parseInt(value);
    if (isNaN(num) || num < 1 || num > 100) {
      return "Top K must be between 1 and 100";
    }
    return null;
  };
  
  // Handle validated input changes
  const handleTemperatureChange = (e) => {
    const value = e.target.value;
    const error = validateTemperature(value);
    
    setValidationErrors(prev => ({
      ...prev,
      temperature: error
    }));
    
    if (!error) {
      setTemperature(parseFloat(value));
    }
  };
  
  const handleTopPChange = (e) => {
    const value = e.target.value;
    const error = validateTopP(value);
    
    setValidationErrors(prev => ({
      ...prev,
      topP: error
    }));
    
    if (!error) {
      setTopP(parseFloat(value));
    }
  };
  
  const handleRerankerTopKChange = (e) => {
    const value = e.target.value;
    const error = validateTopK(value);
    
    setValidationErrors(prev => ({
      ...prev,
      rerankerTopK: error
    }));
    
    if (!error) {
      setRerankerTopK(parseInt(value));
    }
  };
  
  const handleVdbTopKChange = (e) => {
    const value = e.target.value;
    const error = validateTopK(value);
    
    setValidationErrors(prev => ({
      ...prev,
      vdbTopK: error
    }));
    
    if (!error) {
      setVdbTopK(parseInt(value));
    }
  };
  
  return (
    <div className="max-w-4xl mx-auto mb-6">
      <Card className="bg-card/80 backdrop-blur-sm border border-border">
        <CardContent className="p-6">
          <h2 className="text-xl font-semibold mb-4">Chat Settings</h2>
          
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="mb-4">
              <TabsTrigger value="general">General</TabsTrigger>
              <TabsTrigger value="advanced">Advanced</TabsTrigger>
            </TabsList>
            
            {/* General Settings Tab */}
            <TabsContent value="general">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="kb-mode">Use Knowledge Base</Label>
                    <Switch
                      id="kb-mode"
                      checked={useKnowledgeBase}
                      onCheckedChange={setUseKnowledgeBase}
                    />
                  </div>
                  
                  {/* Query rewriting toggle removed as it may cause issues with CPU-based inference */}
                  
                  <div className="flex items-center justify-between">
                    <Label htmlFor="guardrails">Enable Guardrails</Label>
                    <Switch 
                      id="guardrails" 
                      checked={enableGuardrails} 
                      onCheckedChange={setEnableGuardrails} 
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <Label htmlFor="tts-mode">Enable Text-to-Speech</Label>
                    <Switch 
                      id="tts-mode" 
                      checked={ttsEnabled} 
                      onCheckedChange={setTTSEnabled} 
                    />
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="persona-select" className="mb-2 block">Select Persona:</Label>
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
                  
                  <Button
                    variant="outline"
                    onClick={() => setIsDarkMode(prev => !prev)}
                    className="w-full"
                  >
                    {isDarkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
                  </Button>
                </div>
              </div>
            </TabsContent>
            
            {/* Advanced Settings Tab */}
            <TabsContent value="advanced">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="temperature" className="mb-2 block">
                      Temperature: <span className="text-muted-foreground text-sm">(0-1)</span>
                    </Label>
                    <Input
                      id="temperature"
                      type="number"
                      step="0.1"
                      min="0"
                      max="1"
                      value={temperature}
                      onChange={handleTemperatureChange}
                    />
                    {validationErrors.temperature && (
                      <p className="text-red-500 text-xs mt-1">{validationErrors.temperature}</p>
                    )}
                  </div>
                  
                  <div>
                    <Label htmlFor="top-p" className="mb-2 block">
                      Top P: <span className="text-muted-foreground text-sm">(0-1)</span>
                    </Label>
                    <Input
                      id="top-p"
                      type="number"
                      step="0.1"
                      min="0"
                      max="1"
                      value={topP}
                      onChange={handleTopPChange}
                    />
                    {validationErrors.topP && (
                      <p className="text-red-500 text-xs mt-1">{validationErrors.topP}</p>
                    )}
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="reranker-top-k" className="mb-2 block">
                      Reranker Top K: <span className="text-muted-foreground text-sm">(1-100)</span>
                    </Label>
                    <Input
                      id="reranker-top-k"
                      type="number"
                      min="1"
                      max="100"
                      value={rerankerTopK}
                      onChange={handleRerankerTopKChange}
                    />
                    {validationErrors.rerankerTopK && (
                      <p className="text-red-500 text-xs mt-1">{validationErrors.rerankerTopK}</p>
                    )}
                  </div>
                  
                  <div>
                    <Label htmlFor="vdb-top-k" className="mb-2 block">
                      Vector DB Top K: <span className="text-muted-foreground text-sm">(1-100)</span>
                    </Label>
                    <Input
                      id="vdb-top-k"
                      type="number"
                      min="1"
                      max="100"
                      value={vdbTopK}
                      onChange={handleVdbTopKChange}
                    />
                    {validationErrors.vdbTopK && (
                      <p className="text-red-500 text-xs mt-1">{validationErrors.vdbTopK}</p>
                    )}
                  </div>
                  
                  <Alert className="bg-blue-50 border-blue-200">
                    <AlertDescription className="text-blue-700 text-sm">
                      Lower temperature (0.1-0.4) = more factual responses. Higher values (0.7-1.0) = more creative outputs.
                    </AlertDescription>
                  </Alert>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default ChatSettings;      