import { useState, useEffect, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRoute } from "wouter";
import { WorkflowHeader } from "@/components/workflow/header";
import { WorkflowCanvas } from "@/components/workflow/canvas";
import { NodeLibrary } from "@/components/workflow/node-library";
import { NodeLibraryToggle } from "@/components/workflow/node-library-toggle";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { Workflow } from "@shared/schema";
import { 
    Node, 
    Edge, 
    OnNodesChange, 
    OnEdgesChange, 
    applyNodeChanges, 
    applyEdgeChanges, 
    OnConnect,
    addEdge,
    Connection,
    ReactFlowProvider
} from "reactflow";


export default function WorkflowEditPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [match, params] = useRoute("/flows/:id/edit");
  const workflowId = params?.id;
  
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [isNodeLibraryOpen, setIsNodeLibraryOpen] = useState(true);

  const onNodesChange: OnNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    [setNodes]
  );

  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    [setEdges]
  );
  
  const onConnect: OnConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge({ ...connection, type: 'smoothstep' }, eds)),
    [setEdges],
  );

  // Fetch workflow
  const { data: workflow, isLoading } = useQuery<Workflow>({
    queryKey: ['/api/workflows', workflowId],
    enabled: !!workflowId,
  });

  // Load workflow data into React Flow state
  useEffect(() => {
    if (workflow) {
      const flowNodes = workflow.nodes.map(n => ({...n, position: {x: n.position.x || 0, y: n.position.y || 0}}));
      setNodes(flowNodes);
      setEdges(workflow.edges);
    }
  }, [workflow]);

  // Save workflow mutation
  const saveWorkflowMutation = useMutation({
    mutationFn: async () => {
      if (!workflowId) return;
      
      const payload: Partial<Workflow> = {
          nodes: nodes.map(({id, type, position, data}) => ({ 
              id, 
              type: type!, 
              position, 
              data
          })),
          edges: edges.map(edge => ({
              id: edge.id,
              source: edge.source,
              target: edge.target,
              sourceHandle: edge.sourceHandle || undefined,
              targetHandle: edge.targetHandle || undefined,
          })),
      }
      const response = await apiRequest('PUT', `/api/workflows/${workflowId}`, payload);
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/workflows', workflowId] });
      queryClient.invalidateQueries({ queryKey: ['/api/workflows']});
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
      toast({ title: "Execute Clicked", description: "Execute functionality would be implemented here."});
    }
  };

  const handlePause = () => {
    if (workflowId) {
      toast({ title: "Pause Clicked", description: "Pause functionality would be implemented here."});
    }
  };

  const handleStop = () => {
    if (workflowId) {
      toast({ title: "Stop Clicked", description: "Stop functionality would be implemented here."});
    }
  };

  const handleSave = () => {
    saveWorkflowMutation.mutate();
  };

  const handleToggleNodeLibrary = () => {
    setIsNodeLibraryOpen(!isNodeLibraryOpen);
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
    <div className="h-screen flex flex-col font-inter" data-testid="workflow-edit-page" style={{ overflow: 'visible' }}>
      {/* Header - Full Width */}
      <WorkflowHeader
        workflowName={workflow.name}
        onExecute={handleExecute}
        onPause={handlePause}
        onStop={handleStop}
        onSave={handleSave}
      />
      
      {/* Main Content Area */}
      <div className="flex-1 flex relative" style={{ overflow: 'visible' }}>
        {/* Node Library Sidebar */}
        <div className={`transition-all duration-300 ease-in-out ${isNodeLibraryOpen ? 'w-96' : 'w-0'}`}>
          <NodeLibrary 
            nodes={nodes} 
            isOpen={isNodeLibraryOpen}
            onClose={() => setIsNodeLibraryOpen(false)}
          />
        </div>
        
        {/* Canvas Area */}
        <div className="flex-1 relative" style={{ overflow: 'visible' }}>
          {/* Node Library Toggle Button */}
          {!isNodeLibraryOpen && (
            <NodeLibraryToggle onOpen={() => setIsNodeLibraryOpen(true)} />
          )}
          
          <ReactFlowProvider>
            <WorkflowCanvas
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              setNodes={setNodes}
              setEdges={setEdges}
            />
          </ReactFlowProvider>
        </div>
      </div>
    </div>
  );
}