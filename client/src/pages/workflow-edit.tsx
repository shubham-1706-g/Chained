import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRoute } from "wouter";
import { WorkflowSidebar } from "@/components/workflow/sidebar";
import { WorkflowCanvas } from "@/components/workflow/canvas";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { Workflow, WorkflowNode, WorkflowEdge } from "@shared/schema";
import { ExecutionStatus } from "../types/workflow";

export default function WorkflowEditPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [match, params] = useRoute("/flows/:id/edit");
  const workflowId = params?.id;
  
  const [executionStatus, setExecutionStatus] = useState<ExecutionStatus>({
    status: 'idle'
  });
  const [workflowNodes, setWorkflowNodes] = useState<WorkflowNode[]>([]);
  const [workflowEdges, setWorkflowEdges] = useState<WorkflowEdge[]>([]);

  // Fetch workflow
  const { data: workflow, isLoading } = useQuery<Workflow>({
    queryKey: ['/api/workflows', workflowId],
    enabled: !!workflowId,
  });

  // Load workflow data
  useEffect(() => {
    if (workflow) {
      setWorkflowNodes(workflow.nodes);
      setWorkflowEdges(workflow.edges);
    }
  }, [workflow]);

  // Execute workflow mutation
  const executeMutation = useMutation({
    mutationFn: async (workflowId: string) => {
      const response = await apiRequest('POST', `/api/workflows/${workflowId}/execute`);
      return response.json();
    },
    onSuccess: (data) => {
      setExecutionStatus({
        status: 'running',
        lastExecution: new Date(),
        message: data.message
      });
      
      setTimeout(() => {
        setExecutionStatus(prev => ({
          ...prev,
          status: 'completed',
          message: 'Workflow execution completed successfully'
        }));
      }, 3000);
      
      toast({
        title: "Workflow Started",
        description: "Your workflow is now running.",
      });
    },
    onError: () => {
      setExecutionStatus(prev => ({
        ...prev,
        status: 'error',
        message: 'Failed to execute workflow'
      }));
      
      toast({
        title: "Error",
        description: "Failed to execute workflow.",
        variant: "destructive",
      });
    }
  });

  // Pause workflow mutation
  const pauseMutation = useMutation({
    mutationFn: async (workflowId: string) => {
      const response = await apiRequest('POST', `/api/workflows/${workflowId}/pause`);
      return response.json();
    },
    onSuccess: () => {
      setExecutionStatus(prev => ({ ...prev, status: 'paused' }));
      toast({
        title: "Workflow Paused",
        description: "Your workflow has been paused.",
      });
    }
  });

  // Stop workflow mutation
  const stopMutation = useMutation({
    mutationFn: async (workflowId: string) => {
      const response = await apiRequest('POST', `/api/workflows/${workflowId}/stop`);
      return response.json();
    },
    onSuccess: () => {
      setExecutionStatus(prev => ({ ...prev, status: 'stopped' }));
      toast({
        title: "Workflow Stopped",
        description: "Your workflow has been stopped.",
      });
    }
  });

  // Save workflow mutation
  const saveWorkflowMutation = useMutation({
    mutationFn: async () => {
      if (!workflowId) return;
      
      const response = await apiRequest('PUT', `/api/workflows/${workflowId}`, {
        nodes: workflowNodes,
        edges: workflowEdges
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/workflows'] });
      toast({
        title: "Workflow Saved",
        description: "Your workflow has been saved successfully.",
      });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to save workflow.",
        variant: "destructive",
      });
    }
  });

  const handleExecute = () => {
    if (workflowId) {
      executeMutation.mutate(workflowId);
    }
  };

  const handlePause = () => {
    if (workflowId) {
      pauseMutation.mutate(workflowId);
    }
  };

  const handleStop = () => {
    if (workflowId) {
      stopMutation.mutate(workflowId);
    }
  };

  const handleSave = () => {
    saveWorkflowMutation.mutate();
  };

  const handleLoad = () => {
    toast({
      title: "Load Workflow",
      description: "Load workflow functionality would be implemented here.",
    });
  };

  const handleNodesChange = (nodes: WorkflowNode[]) => {
    setWorkflowNodes(nodes);
  };

  const handleEdgesChange = (edges: WorkflowEdge[]) => {
    setWorkflowEdges(edges);
  };

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-lg">Loading workflow...</div>
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-lg">Workflow not found</div>
      </div>
    );
  }

  return (
    <div className="h-screen flex font-inter" data-testid="workflow-edit-page">
      <WorkflowSidebar
        workflowName={workflow.name}
        executionStatus={executionStatus}
        onExecute={handleExecute}
        onPause={handlePause}
        onStop={handleStop}
        onSave={handleSave}
        onLoad={handleLoad}
      />
      
      <WorkflowCanvas
        workflowName={workflow.name}
        initialNodes={workflowNodes}
        initialEdges={workflowEdges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
      />
    </div>
  );
}