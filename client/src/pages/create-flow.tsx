import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRoute, useLocation } from "wouter";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Workflow, Clock, Globe, Plus } from "lucide-react";
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
      color: 'bg-slate-blue',
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
      color: 'bg-gray-400',
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
    <div className="h-screen bg-light-grey overflow-auto" data-testid="create-flow-page">
      {/* Header */}
      <div className="flex items-center justify-between p-6 bg-white border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <Link href="/flows">
            <Button variant="ghost" size="sm" data-testid="button-back-to-flows">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Flows
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-text-dark">Create New Flow</h1>
            <p className="text-gray-600">Choose a template or start from scratch</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" data-testid="button-share">
            Share
          </Button>
          <Link href="/flows">
            <Button variant="outline" data-testid="button-cancel-header">
              Cancel
            </Button>
          </Link>
        </div>
      </div>

      <div className="p-6">

      <div className="max-w-4xl space-y-6">
        {/* Flow Details */}
        <Card>
          <CardHeader>
            <CardTitle>Flow Details</CardTitle>
            <CardDescription>Give your workflow a name and description</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="flow-name">Flow Name *</Label>
              <Input
                id="flow-name"
                placeholder="Enter flow name..."
                value={name}
                onChange={(e) => setName(e.target.value)}
                data-testid="input-flow-name"
              />
            </div>
            <div>
              <Label htmlFor="flow-description">Description (Optional)</Label>
              <Textarea
                id="flow-description"
                placeholder="Describe what this workflow does..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                data-testid="textarea-flow-description"
              />
            </div>
          </CardContent>
        </Card>

        {/* Template Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Choose a Template</CardTitle>
            <CardDescription>Select a starting point for your workflow</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {templates.map((template) => {
                const isSelected = selectedTemplate === template.id || 
                                 (!selectedTemplate && templateFromUrl === template.id);
                
                return (
                  <Card 
                    key={template.id}
                    className={`cursor-pointer transition-all ${
                      isSelected 
                        ? 'ring-2 ring-coral border-coral shadow-md' 
                        : 'hover:shadow-md border-dashed border-2 border-gray-300'
                    }`}
                    onClick={() => setSelectedTemplate(template.id)}
                    data-testid={`template-${template.id}`}
                  >
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <div className={`w-12 h-12 ${template.color} rounded-lg flex items-center justify-center mx-auto mb-3`}>
                          <template.icon className="w-6 h-6 text-white" />
                        </div>
                        <h3 className="font-semibold text-text-dark mb-1">{template.name}</h3>
                        <p className="text-sm text-gray-500">{template.description}</p>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            {selectedTemplate || templateFromUrl ? (
              `Selected: ${templates.find(t => t.id === (selectedTemplate || templateFromUrl))?.name}`
            ) : (
              "Select a template above to get started"
            )}
          </div>
          <div className="flex space-x-3">
            <Link href="/flows">
              <Button variant="outline" data-testid="button-cancel">
                Cancel
              </Button>
            </Link>
            <Button 
              className="bg-coral hover:bg-red-600 text-white"
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
    </div>
  );
}