import { useCallback, useState, useMemo } from 'react';
import ReactFlow, {
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  Connection,
  Edge,
  Node,
  BackgroundVariant,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { CustomWorkflowNode } from './custom-nodes';
import { PropertyPanel } from './property-panel';
import { WorkflowNode, WorkflowEdge } from '@shared/schema';
import { nodeTypes } from '../../types/workflow';
import { Settings, Share2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface WorkflowCanvasProps {
  workflowName: string;
  initialNodes: WorkflowNode[];
  initialEdges: WorkflowEdge[];
  onNodesChange: (nodes: WorkflowNode[]) => void;
  onEdgesChange: (edges: WorkflowEdge[]) => void;
}

export function WorkflowCanvas({ 
  workflowName, 
  initialNodes, 
  initialEdges,
  onNodesChange,
  onEdgesChange 
}: WorkflowCanvasProps) {
  const [nodes, setNodes, onNodesChangeInternal] = useNodesState(
    initialNodes.map(node => ({
      id: node.id,
      type: node.type,
      position: node.position,
      data: node.data
    }))
  );
  
  const [edges, setEdges, onEdgesChangeInternal] = useEdgesState(
    initialEdges.map(edge => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      sourceHandle: edge.sourceHandle,
      targetHandle: edge.targetHandle,
      type: 'smoothstep'
    }))
  );

  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [showPropertyPanel, setShowPropertyPanel] = useState(false);

  // Custom node types for React Flow
  const customNodeTypes = useMemo(() => {
    const types: Record<string, React.ComponentType<any>> = {};
    nodeTypes.forEach(nodeType => {
      types[nodeType.id] = CustomWorkflowNode;
    });
    return types;
  }, []);

  const onConnect = useCallback((params: Connection) => {
    const newEdge: Edge = {
      id: `${params.source}-${params.target}`,
      source: params.source!,
      target: params.target!,
      type: 'smoothstep'
    };
    
    setEdges((eds) => addEdge(newEdge, eds));
    
    // Update parent component
    const updatedEdges: WorkflowEdge[] = [...initialEdges, {
      id: newEdge.id,
      source: newEdge.source,
      target: newEdge.target,
      sourceHandle: newEdge.sourceHandle || undefined,
      targetHandle: newEdge.targetHandle || undefined
    }];
    onEdgesChange(updatedEdges);
  }, [initialEdges, onEdgesChange, setEdges]);

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    const workflowNode = initialNodes.find(n => n.id === node.id);
    if (workflowNode) {
      setSelectedNode(workflowNode);
      setShowPropertyPanel(true);
    }
  }, [initialNodes]);

  const onDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();

    const reactFlowBounds = (event.target as Element).getBoundingClientRect();
    const type = event.dataTransfer.getData('application/reactflow');

    if (typeof type === 'undefined' || !type) {
      return;
    }

    const position = {
      x: event.clientX - reactFlowBounds.left,
      y: event.clientY - reactFlowBounds.top,
    };

    const nodeType = nodeTypes.find(n => n.id === type);
    if (!nodeType) return;

    const newNode: WorkflowNode = {
      id: `${type}-${Date.now()}`,
      type,
      position,
      data: {
        label: nodeType.name,
        description: nodeType.description,
        category: nodeType.category,
        config: { ...nodeType.config }
      }
    };

    const reactFlowNode: Node = {
      id: newNode.id,
      type: newNode.type,
      position: newNode.position,
      data: newNode.data
    };

    setNodes((nds) => nds.concat(reactFlowNode));
    onNodesChange([...initialNodes, newNode]);
  }, [initialNodes, onNodesChange, setNodes]);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onPropertySave = useCallback((nodeId: string, data: any) => {
    const updatedNodes = initialNodes.map(node => 
      node.id === nodeId 
        ? { ...node, data: { ...node.data, ...data } }
        : node
    );
    
    setNodes((nds) => nds.map(node =>
      node.id === nodeId
        ? { ...node, data: { ...node.data, ...data } }
        : node
    ));
    
    onNodesChange(updatedNodes);
  }, [initialNodes, onNodesChange, setNodes]);

  return (
    <div className="flex-1 flex flex-col bg-light-grey" data-testid="workflow-canvas">
      {/* Top Bar */}
      <div className="bg-white border-b border-border-light p-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-4">
          <h2 className="text-lg font-semibold text-text-dark" data-testid="text-workflow-name">
            {workflowName}
          </h2>
          <span className="px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full">
            Active
          </span>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="text-sm text-gray-500">
            Auto-save: <span className="text-green-600">On</span>
          </div>
          <Button variant="ghost" size="sm" data-testid="button-settings">
            <Settings className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="sm" data-testid="button-share">
            <Share2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 relative" style={{ overflow: 'hidden' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChangeInternal}
          onEdgesChange={onEdgesChangeInternal}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={customNodeTypes}
          fitView
          attributionPosition="bottom-left"
          preventScrolling={false}
          panOnScroll={true}
          selectNodesOnDrag={false}
          snapToGrid={false}
          nodesDraggable={true}
          nodesConnectable={true}
          elementsSelectable={true}
          nodeDragThreshold={10}
          multiSelectionKeyCode={null}
          deleteKeyCode={null}
        >
          <Background 
            variant={BackgroundVariant.Dots} 
            gap={20} 
            size={1}
            color="#E5E7EB"
          />
          <Controls 
            className="bg-white border border-border-light shadow-lg"
            data-testid="canvas-controls"
          />
          <Panel position="top-right" className="flex flex-col space-y-2">
            <div className="bg-white rounded-lg shadow-lg border border-border-light p-3">
              <div className="text-xs text-gray-500 text-center">100%</div>
            </div>
          </Panel>
        </ReactFlow>

        <PropertyPanel
          node={selectedNode}
          isOpen={showPropertyPanel}
          onClose={() => setShowPropertyPanel(false)}
          onSave={onPropertySave}
        />
      </div>
    </div>
  );
}
