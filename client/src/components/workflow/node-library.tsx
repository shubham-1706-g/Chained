import { nodeTypes } from "../../types/workflow";

export function NodeLibrary() {
  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const triggerNodes = nodeTypes.filter(node => node.category === 'trigger');
  const actionNodes = nodeTypes.filter(node => node.category === 'action');
  const transformNodes = nodeTypes.filter(node => node.category === 'transform');

  return (
    <div className="p-4" data-testid="node-library">
      <h3 className="text-sm font-semibold text-gray-300 mb-3 uppercase tracking-wide">Node Library</h3>
      
      {/* Triggers Category */}
      <div className="mb-4">
        <h4 className="text-xs font-medium text-gray-400 mb-2 uppercase tracking-wide">Triggers</h4>
        <div className="space-y-1">
          {triggerNodes.map((node) => (
            <div
              key={node.id}
              className="sidebar-item p-3 rounded-lg cursor-pointer transition-colors"
              draggable
              onDragStart={(e) => onDragStart(e, node.id)}
              data-testid={`node-${node.id}`}
            >
              <div className="flex items-center space-x-3">
                <div className={`w-8 h-8 ${node.color} rounded-lg flex items-center justify-center`}>
                  <i className={`${node.icon} text-white text-xs`}></i>
                </div>
                <span className="text-sm font-medium">{node.name}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Actions Category */}
      <div className="mb-4">
        <h4 className="text-xs font-medium text-gray-400 mb-2 uppercase tracking-wide">Actions</h4>
        <div className="space-y-1">
          {actionNodes.map((node) => (
            <div
              key={node.id}
              className="sidebar-item p-3 rounded-lg cursor-pointer transition-colors"
              draggable
              onDragStart={(e) => onDragStart(e, node.id)}
              data-testid={`node-${node.id}`}
            >
              <div className="flex items-center space-x-3">
                <div className={`w-8 h-8 ${node.color} rounded-lg flex items-center justify-center`}>
                  <i className={`${node.icon} text-white text-xs`}></i>
                </div>
                <span className="text-sm font-medium">{node.name}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Transform Category */}
      <div className="mb-4">
        <h4 className="text-xs font-medium text-gray-400 mb-2 uppercase tracking-wide">Transform</h4>
        <div className="space-y-1">
          {transformNodes.map((node) => (
            <div
              key={node.id}
              className="sidebar-item p-3 rounded-lg cursor-pointer transition-colors"
              draggable
              onDragStart={(e) => onDragStart(e, node.id)}
              data-testid={`node-${node.id}`}
            >
              <div className="flex items-center space-x-3">
                <div className={`w-8 h-8 ${node.color} rounded-lg flex items-center justify-center`}>
                  <i className={`${node.icon} text-white text-xs`}></i>
                </div>
                <span className="text-sm font-medium">{node.name}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
