import { Handle, Position } from 'reactflow';
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
  dragging?: boolean;
}

export function CustomWorkflowNode({ data, type, selected, dragging }: CustomNodeProps) {
  const nodeType = nodeTypes.find(n => n.id === type);
  
  if (!nodeType) return null;

  const showInputHandle = data.category !== 'trigger';
  const showOutputHandle = true;

  // Show minimal icon-only version when dragging from library
  if (dragging) {
    return (
      <div className="bg-white rounded-xl shadow-xl border-2 border-coral p-3 w-16 h-16 flex items-center justify-center">
        <div className={`w-10 h-10 ${nodeType.color} rounded-xl flex items-center justify-center shadow-lg`}>
          <i className={`${nodeType.icon} text-white text-sm`}></i>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Input handle */}
      {showInputHandle && (
        <Handle
          type="target"
          position={Position.Left}
          data-testid={`handle-input-${type}`}
          style={{ 
            background: 'hsl(248 53% 67%)',
            border: '2px solid white',
            width: '12px',
            height: '12px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}
        />
      )}
      
      <div 
        className={`bg-white rounded-xl shadow-lg border-2 p-4 w-64 workflow-node transition-all duration-200 ${
          selected 
            ? 'border-coral ring-2 ring-coral/20 shadow-xl scale-105' 
            : 'border-gray-200 hover:border-gray-300 hover:shadow-xl'
        }`}
        data-testid={`workflow-node-${type}`}
      >
        <div className="flex items-center space-x-3 mb-3">
          <div className={`w-12 h-12 ${nodeType.color} rounded-xl flex items-center justify-center shadow-lg`}>
            <i className={`${nodeType.icon} text-white text-lg`}></i>
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold text-text-dark text-sm mb-1">{data.label}</h4>
            {data.description && (
              <p className="text-gray-500 text-xs line-clamp-2">{data.description}</p>
            )}
          </div>
        </div>
        
        {data.config && Object.keys(data.config).length > 0 && (
          <div className="pt-3 border-t border-gray-100">
            <div className="text-xs text-gray-600 space-y-1">
              {Object.entries(data.config).slice(0, 3).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center">
                  <span className="capitalize text-gray-500">{key}:</span>
                  <span className="font-medium text-gray-700 truncate ml-2">{String(value)}</span>
                </div>
              ))}
              {Object.keys(data.config).length > 3 && (
                <div className="text-xs text-gray-400 text-center pt-1">
                  +{Object.keys(data.config).length - 3} more
                </div>
              )}
            </div>
          </div>
        )}

        {/* Category badge */}
        <div className="mt-3 flex justify-between items-center">
          <div className={`text-xs px-2 py-1 rounded-full font-medium ${
            data.category === 'trigger' 
              ? 'bg-green-100 text-green-700' 
              : data.category === 'action' 
                ? 'bg-blue-100 text-blue-700' 
                : 'bg-purple-100 text-purple-700'
          }`}>
            {data.category}
          </div>
          {selected && (
            <div className="w-2 h-2 bg-coral rounded-full"></div>
          )}
        </div>
      </div>
      
      {/* Output handle */}
      {showOutputHandle && (
        <Handle
          type="source"
          position={Position.Right}
          data-testid={`handle-output-${type}`}
          style={{ 
            background: 'hsl(248 53% 67%)',
            border: '2px solid white',
            width: '12px',
            height: '12px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}
        />
      )}
    </>
  );
}
