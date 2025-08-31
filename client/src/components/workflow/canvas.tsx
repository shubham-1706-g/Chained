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
  applyNodeChanges
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
}: WorkflowCanvasProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [showPropertyPanel, setShowPropertyPanel] = useState(false);

  const customNodeTypes = useMemo(() => {
    const types: Record<string, React.ComponentType<any>> = {};
    nodeTypes.forEach((nodeType) => {
      types[nodeType.id] = CustomWorkflowNode;
    });
    return types;
  }, []);

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
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

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

  return (
    <div className="flex-1 w-full h-full bg-light-grey" ref={reactFlowWrapper} data-testid="workflow-canvas">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onInit={setReactFlowInstance}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onNodeClick={onNodeClick}
        nodeTypes={customNodeTypes}
        fitView
        className="canvas-grid"
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="hsl(210 18% 87%)"
        />
        <Controls
          className="bg-white border border-border-light shadow-lg"
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

