import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRoute, useLocation } from "wouter";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Workflow, Clock, Globe, Plus, Zap } from "lucide-react";
import { Link } from "wouter";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { InsertWorkflow } from "@shared/schema";

export default function CreateFlowPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [, setLocation] = useLocation();
  const [match, params] = useRoute("/flows/create");
  
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);

  // Get template from URL params
  const urlParams = new URLSearchParams(window.location.search);
  const templateFromUrl = urlParams.get('template');

  const templates = [
    {
      id: 'webhook',
      name: 'Webhook Trigger',
      description: 'Start with an HTTP webhook that can receive data from external sources',
      icon: Globe,
      color: 'bg-coral',
      gradient: 'from-coral-50 to-white',
      border: 'border-coral-200',
      hover: 'hover:border-coral hover:shadow-lg hover:scale-[1.02]',
      nodes: [
        {
          id: 'webhook-start',
          type: 'webhook',
          position: { x: 200, y: 150 },
          data: {
            label: 'Webhook Trigger',
            description: 'Receives HTTP requests',
            category: 'trigger' as const,
            config: {
              method: 'POST',
              path: '/webhook/new'
            }
          }
        }
      ],
      edges: []
    },
    {
      id: 'schedule',
      name: 'Scheduled Flow',
      description: 'Create a workflow that runs automatically on a schedule',
      icon: Clock,
      color: 'bg-blue-500',
      gradient: 'from-blue-50 to-white',
      border: 'border-blue-200',
      hover: 'hover:border-blue-500 hover:shadow-lg hover:scale-[1.02]',
      nodes: [
        {
          id: 'schedule-start',
          type: 'schedule',
          position: { x: 200, y: 150 },
          data: {
            label: 'Schedule Trigger',
            description: 'Runs on a schedule',
            category: 'trigger' as const,
            config: {
              cron: '0 9 * * *'
            }
          }
        }
      ],
      edges: []
    },
    {
      id: 'blank',
      name: 'Blank Flow',
      description: 'Start with an empty canvas and build your workflow from scratch',
      icon: Plus,
      color: 'bg-gray-500',
      gradient: 'from-gray-50 to-white',
      border: 'border-gray-200',
      hover: 'hover:border-gray-400 hover:shadow-lg hover:scale-[1.02]',
      nodes: [],
      edges: []
    }
  ];

  const createWorkflowMutation = useMutation({
    mutationFn: async (workflowData: InsertWorkflow) => {
      const response = await apiRequest('POST', '/api/workflows', workflowData);
      return response.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['/api/workflows'] });
      toast({
        title: "Flow Created",
        description: "Your new workflow has been created successfully.",
      });
      setLocation(`/flows/${data.id}/edit`);
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to create workflow.",
        variant: "destructive",
      });
    }
  });

  const handleCreateFlow = () => {
    if (!name.trim()) {
      toast({
        title: "Name Required",
        description: "Please enter a name for your workflow.",
        variant: "destructive",
      });
      return;
    }

    const template = templates.find(t => t.id === (selectedTemplate || templateFromUrl));
    
    const workflowData: InsertWorkflow = {
      name: name.trim(),
      description: description.trim() || null,
      nodes: template?.nodes || [],
      edges: template?.edges || [],
      isActive: false
    };

    createWorkflowMutation.mutate(workflowData);
  };

  return (
    <div className="p-6 bg-light-grey min-h-full overflow-visible" data-testid="create-flow-page">
      {/* Enhanced Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link href="/flows">
              <Button 
                variant="outline" 
                size="sm" 
                className="border-2 border-gray-200 hover:border-coral hover:bg-coral hover:text-white transition-all duration-200"
                data-testid="button-back-to-flows"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Flows
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-text-dark mb-2 flex items-center">
                <Workflow className="w-8 h-8 text-coral mr-3" />
                Create New Flow
              </h1>
              <p className="text-gray-600">Choose a template or start from scratch</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Link href="/flows">
              <Button 
                variant="outline" 
                className="border-2 border-gray-200 hover:border-gray-400 hover:bg-gray-50 transition-all duration-200"
                data-testid="button-cancel-header"
              >
                Cancel
              </Button>
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto space-y-6">
        {/* Enhanced Flow Details */}
        <Card className="border-2 border-gray-200 hover:border-gray-300 hover:shadow-lg transition-all duration-200">
          <CardHeader className="bg-gradient-to-r from-gray-50 to-white border-b border-gray-100 rounded-t-lg">
            <CardTitle className="text-lg text-gray-800 flex items-center">
              <Zap className="w-5 h-5 text-coral mr-2" />
              Flow Details
            </CardTitle>
            <CardDescription className="text-gray-600">Give your workflow a name and description</CardDescription>
          </CardHeader>
          <CardContent className="rounded-b-lg space-y-4 pt-6">
            <div className="space-y-2">
              <Label htmlFor="flow-name" className="text-gray-900 mb-2 block">Flow Name *</Label>
              <Input
                id="flow-name"
                placeholder="Enter flow name..."
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="border border-gray-200 hover:border-gray-300 focus:border-coral-400 focus:ring-2 focus:ring-coral-100 focus:outline-none"
                data-testid="input-flow-name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="flow-description" className="text-gray-900 mb-2 block">Description (Optional)</Label>
              <Textarea
                id="flow-description"
                placeholder="Describe what this workflow does..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="border border-gray-200 hover:border-gray-300 focus:border-coral-400 focus:ring-2 focus:ring-coral-100 focus:outline-none resize-none"
                data-testid="textarea-flow-description"
              />
            </div>
          </CardContent>
        </Card>

        {/* Enhanced Template Selection */}
        <Card className="border-2 border-gray-200 hover:border-gray-300 hover:shadow-lg transition-all duration-200">
          <CardHeader className="bg-gradient-to-r from-gray-50 to-white border-b border-gray-100 rounded-t-lg">
            <CardTitle className="text-lg text-gray-800 flex items-center">
              <Workflow className="w-5 h-5 text-purple-600 mr-2" />
              Choose a Template
            </CardTitle>
            <CardDescription className="text-gray-600">Select a starting point for your workflow</CardDescription>
          </CardHeader>
          <CardContent className="rounded-b-lg pt-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {templates.map((template) => {
                const isSelected = selectedTemplate === template.id || 
                                 (!selectedTemplate && templateFromUrl === template.id);
                
                return (
                  <Card 
                    key={template.id}
                    className={`cursor-pointer bg-gradient-to-br ${template.gradient} border-2 ${template.border} ${template.hover} transition-all duration-200 ${
                      isSelected 
                        ? 'ring-2 ring-coral border-coral shadow-xl scale-[1.02]' 
                        : 'hover:shadow-lg'
                    }`}
                    onClick={() => setSelectedTemplate(template.id)}
                    data-testid={`template-${template.id}`}
                  >
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <div className={`w-14 h-14 ${template.color} rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg transition-transform duration-200 ${isSelected ? 'scale-110' : ''}`}>
                          <template.icon className="w-7 h-7 text-white" />
                        </div>
                        <h3 className={`font-semibold mb-2 transition-colors duration-200 ${isSelected ? 'text-coral' : 'text-text-dark'}`}>{template.name}</h3>
                        <p className="text-sm text-gray-600">{template.description}</p>
                        <div className="mt-4">
                          <span className="text-xs text-gray-500">
                            {isSelected ? "✓ Selected" : "Click to select"}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Enhanced Action Buttons */}
        <div className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-white border-2 border-gray-200 rounded-lg">
          <div className="text-sm text-gray-600">
            {selectedTemplate || templateFromUrl ? (
              <span className="flex items-center">
                <span className="w-2 h-2 bg-coral rounded-full mr-2"></span>
                Selected: <span className="font-medium text-text-dark ml-1">
                  {templates.find(t => t.id === (selectedTemplate || templateFromUrl))?.name}
                </span>
              </span>
            ) : (
              "Select a template above to get started"
            )}
          </div>
          <div className="flex space-x-3">
            <Link href="/flows">
              <Button 
                variant="outline" 
                className="border-2 border-gray-200 hover:border-gray-400 hover:bg-gray-50 transition-all duration-200"
                data-testid="button-cancel"
              >
                Cancel
              </Button>
            </Link>
            <Button 
              className="bg-coral hover:bg-red-600 text-white border-2 border-coral hover:border-red-500 transition-all duration-200 shadow-md hover:shadow-lg hover:scale-105"
              onClick={handleCreateFlow}
              disabled={!name.trim() || createWorkflowMutation.isPending}
              data-testid="button-create-flow"
            >
              {createWorkflowMutation.isPending ? "Creating..." : "Create Flow"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}