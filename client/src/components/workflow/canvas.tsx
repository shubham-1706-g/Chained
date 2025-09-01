import { useCallback, useState, useMemo, useRef } from "react";
import ReactFlow, {
  Controls,
  Background,
  BackgroundVariant,
  Panel,
  ReactFlowInstance,
  Node,
  Edge,
  OnNodesChange,
  OnEdgesChange,
  OnConnect,
  applyEdgeChanges,
  applyNodeChanges,
  ConnectionLineType,
  Connection,
  addEdge
} from "reactflow";
import "reactflow/dist/style.css";

import { CustomWorkflowNode } from "./custom-nodes";
import { PropertyPanel } from "./property-panel";
import { nodeTypes } from "../../types/workflow";
import { WorkflowNode } from "@shared/schema";

interface WorkflowCanvasProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  setNodes: React.Dispatch<React.SetStateAction<Node[]>>;
  setEdges: React.Dispatch<React.SetStateAction<Edge[]>>;
}

export function WorkflowCanvas({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onConnect,
  setNodes,
  setEdges,
}: WorkflowCanvasProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [showPropertyPanel, setShowPropertyPanel] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const customNodeTypes = useMemo(() => {
    const types: Record<string, React.ComponentType<any>> = {};
    nodeTypes.forEach((nodeType) => {
      types[nodeType.id] = (props: any) => (
        <CustomWorkflowNode {...props} dragging={isDragging} />
      );
    });
    return types;
  }, [isDragging]);

  const onNodeClick = useCallback(
    (event: React.MouseEvent, node: Node) => {
      setSelectedNode(node as WorkflowNode);
      setShowPropertyPanel(true);
    },
    [],
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      setIsDragging(false);

      if (!reactFlowInstance || !reactFlowWrapper.current) {
        return;
      }

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const type = event.dataTransfer.getData('application/reactflow');

      if (typeof type === 'undefined' || !type) {
        return;
      }

      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const nodeTypeData = nodeTypes.find((n) => n.id === type);
      if (!nodeTypeData) return;

      const newNode: Node = {
        id: `${type}-${Date.now()}`,
        type,
        position,
        data: {
          label: nodeTypeData.name,
          description: nodeTypeData.description,
          category: nodeTypeData.category,
          config: { ...nodeTypeData.config },
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, setNodes]
  );

  const onPropertySave = useCallback(
    (nodeId: string, data: any) => {
        setNodes((nds) =>
            nds.map((node) =>
                node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node
            )
        );
    }, [setNodes]
  );

  const handleConnect = useCallback(
    (params: Connection) => {
      const newEdge = addEdge({ ...params, type: 'smoothstep' }, edges);
      setEdges(newEdge);
    },
    [edges, setEdges]
  );

  return (
    <div 
      className="flex-1 w-full h-full bg-light-grey relative" 
      ref={reactFlowWrapper} 
      data-testid="workflow-canvas"
      style={{ 
        position: 'relative',
        overflow: 'visible',
        zIndex: 1
      }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={handleConnect}
        onInit={setReactFlowInstance}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onNodeClick={onNodeClick}
        nodeTypes={customNodeTypes}
        fitView
        className="canvas-grid"
        connectionLineType={ConnectionLineType.SmoothStep}
        defaultEdgeOptions={{
          type: 'smoothstep',
          animated: false,
          style: { 
            strokeWidth: 2, 
            stroke: 'hsl(248 53% 67%)',
            strokeDasharray: '5,5'
          }
        }}
        attributionPosition="bottom-left"
        proOptions={{ hideAttribution: true }}
        panOnDrag={true}
        panOnScroll={false}
        zoomOnScroll={true}
        zoomOnPinch={true}
        zoomOnDoubleClick={false}
        preventScrolling={true}
        nodesDraggable={true}
        nodesConnectable={true}
        elementsSelectable={true}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="hsl(210 18% 87%)"
        />
        <Controls
          className="bg-white border-2 border-gray-200 shadow-lg rounded-lg p-1"
          data-testid="canvas-controls"
        />
      </ReactFlow>
      
      <PropertyPanel
        node={selectedNode}
        isOpen={showPropertyPanel}
        onClose={() => setShowPropertyPanel(false)}
        onSave={onPropertySave}
      />
    </div>
  );
}

