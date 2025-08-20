import { Handle, Position } from 'reactflow';
import { useState, useCallback } from 'react';
import { nodeTypes } from '../../types/workflow';

interface CustomNodeProps {
  data: {
    label: string;
    description?: string;
    config?: Record<string, any>;
    category: 'trigger' | 'action' | 'transform';
  };
  type: string;
  selected: boolean;
}

export function CustomWorkflowNode({ data, type, selected }: CustomNodeProps) {
  const nodeType = nodeTypes.find(n => n.id === type);
  
  if (!nodeType) return null;

  const showInputHandle = data.category !== 'trigger';
  const showOutputHandle = true;

  return (
    <div 
      className={`bg-white rounded-xl shadow-lg border-2 p-4 w-56 workflow-node ${
        selected ? 'border-coral ring-2 ring-coral' : 'border-border-light'
      }`}
      data-testid={`workflow-node-${type}`}
    >
      {/* Add a drag handle area - only this area will be draggable */}
      <div 
        className="drag-handle w-full h-2 absolute top-0 left-0 cursor-move"
        style={{ background: 'transparent' }}
      />
      
      {/* Node content area - not draggable */}
      <div className="nodrag relative z-10">
        {showInputHandle && (
          <Handle
            type="target"
            position={Position.Left}
            className="react-flow__handle"
            data-testid={`handle-input-${type}`}
          />
        )}
        
        <div className="flex items-center space-x-3 mb-3">
          <div className={`w-10 h-10 ${nodeType.color} rounded-lg flex items-center justify-center`}>
            <i className={`${nodeType.icon} text-white`}></i>
          </div>
          <div>
            <h4 className="font-semibold text-text-dark text-sm">{data.label}</h4>
            <p className="text-gray-500 text-xs">{data.description}</p>
          </div>
        </div>
        
        {data.config && (
          <div className="text-xs text-gray-600">
            {Object.entries(data.config).slice(0, 2).map(([key, value]) => (
              <div key={key} className="flex justify-between mb-1">
                <span className="capitalize">{key}:</span>
                <span className="font-medium">{String(value)}</span>
              </div>
            ))}
          </div>
        )}
        
        {showOutputHandle && (
          <Handle
            type="source"
            position={Position.Right}
            className="react-flow__handle"
            data-testid={`handle-output-${type}`}
          />
        )}
      </div>
    </div>
  );
}
