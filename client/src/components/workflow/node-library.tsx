import { useState } from "react";
import { nodeTypes } from "../../types/workflow";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Workflow, X } from "lucide-react";

interface NodeLibraryProps {
  nodes: any[];
  isOpen: boolean;
  onClose: () => void;
}

export function NodeLibrary({ nodes, isOpen, onClose }: NodeLibraryProps) {
  const [searchTerm, setSearchTerm] = useState("");

  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const filteredNodeTypes = nodeTypes.filter(node => 
    node.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    node.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    node.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const triggerNodes = filteredNodeTypes.filter(node => node.category === 'trigger');
  const actionNodes = filteredNodeTypes.filter(node => node.category === 'action');
  const transformNodes = filteredNodeTypes.filter(node => node.category === 'transform');

  // Check if a node type is connected (has instances in the canvas)
  const isNodeTypeConnected = (nodeTypeId: string) => {
    return nodes.some(node => node.type === nodeTypeId);
  };

  if (!isOpen) return null;

  return (
    <div className="w-96 bg-white border-r border-gray-200 flex flex-col shadow-lg h-full" data-testid="node-library">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-white flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-coral rounded-lg flex items-center justify-center">
              <Workflow className="w-4 h-4 text-white" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Node Library</h3>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-8 w-8 rounded-full hover:bg-gray-100 transition-all duration-200"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="p-4 border-b border-gray-200 flex-shrink-0">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder="Search nodes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 border border-gray-200 hover:border-gray-300 focus:border-coral-400 focus:ring-2 focus:ring-coral-100 focus:outline-none transition-all duration-200"
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4" style={{ maxHeight: 'calc(100vh - 200px)' }}>
        {/* Triggers Category */}
        {triggerNodes.length > 0 && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-gray-700 uppercase tracking-wide">Triggers</h4>
              <Badge variant="outline" className="text-xs border-green-200 text-green-600 bg-green-50">
                {triggerNodes.length}
              </Badge>
            </div>
            <div className="space-y-2">
              {triggerNodes.map((node) => (
                <div
                  key={node.id}
                  className="group p-3 rounded-lg cursor-pointer transition-all duration-200 bg-gray-50 hover:bg-gray-100 border border-gray-200 hover:border-coral/50"
                  draggable
                  onDragStart={(e) => onDragStart(e, node.id)}
                  data-testid={`node-${node.id}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-10 h-10 ${node.color} rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-200`}>
                        <i className={`${node.icon} text-white text-sm`}></i>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900 group-hover:text-coral transition-colors duration-200">
                          {node.name}
                        </div>
                        <div className="text-xs text-gray-500 mt-1 line-clamp-1">
                          {node.description}
                        </div>
                      </div>
                    </div>
                    <Badge 
                      variant="outline" 
                      className={`text-[9px] px-1 py-0.5 whitespace-nowrap ${
                        isNodeTypeConnected(node.id) 
                          ? 'border-green-200 text-green-600 bg-green-50' 
                          : 'border-gray-200 text-gray-500 bg-gray-50'
                      }`}
                    >
                      {isNodeTypeConnected(node.id) ? 'Connected' : 'Not Connected'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Actions Category */}
        {actionNodes.length > 0 && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-gray-700 uppercase tracking-wide">Actions</h4>
              <Badge variant="outline" className="text-xs border-blue-200 text-blue-600 bg-blue-50">
                {actionNodes.length}
              </Badge>
            </div>
            <div className="space-y-2">
              {actionNodes.map((node) => (
                <div
                  key={node.id}
                  className="group p-3 rounded-lg cursor-pointer transition-all duration-200 bg-gray-50 hover:bg-gray-100 border border-gray-200 hover:border-coral/50"
                  draggable
                  onDragStart={(e) => onDragStart(e, node.id)}
                  data-testid={`node-${node.id}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-10 h-10 ${node.color} rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-200`}>
                        <i className={`${node.icon} text-white text-sm`}></i>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900 group-hover:text-coral transition-colors duration-200">
                          {node.name}
                        </div>
                        <div className="text-xs text-gray-500 mt-1 line-clamp-1">
                          {node.description}
                        </div>
                      </div>
                    </div>
                    <Badge 
                      variant="outline" 
                      className={`text-[9px] px-1 py-0.5 whitespace-nowrap ${
                        isNodeTypeConnected(node.id) 
                          ? 'border-green-200 text-green-600 bg-green-50' 
                          : 'border-gray-200 text-gray-500 bg-gray-50'
                      }`}
                    >
                      {isNodeTypeConnected(node.id) ? 'Connected' : 'Not Connected'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Transform Category */}
        {transformNodes.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-gray-700 uppercase tracking-wide">Transform</h4>
              <Badge variant="outline" className="text-xs border-purple-200 text-purple-600 bg-purple-50">
                {transformNodes.length}
              </Badge>
            </div>
            <div className="space-y-2">
              {transformNodes.map((node) => (
                <div
                  key={node.id}
                  className="group p-3 rounded-lg cursor-pointer transition-all duration-200 bg-gray-50 hover:bg-gray-100 border border-gray-200 hover:border-coral/50"
                  draggable
                  onDragStart={(e) => onDragStart(e, node.id)}
                  data-testid={`node-${node.id}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-10 h-10 ${node.color} rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-200`}>
                        <i className={`${node.icon} text-white text-sm`}></i>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900 group-hover:text-coral transition-colors duration-200">
                          {node.name}
                        </div>
                        <div className="text-xs text-gray-500 mt-1 line-clamp-1">
                          {node.description}
                        </div>
                      </div>
                    </div>
                    <Badge 
                      variant="outline" 
                      className={`text-[9px] px-1 py-0.5 whitespace-nowrap ${
                        isNodeTypeConnected(node.id) 
                          ? 'border-green-200 text-green-600 bg-green-50' 
                          : 'border-gray-200 text-gray-500 bg-gray-50'
                      }`}
                    >
                      {isNodeTypeConnected(node.id) ? 'Connected' : 'Not Connected'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {filteredNodeTypes.length === 0 && (
          <div className="text-center py-8">
            <div className="text-gray-400 text-sm">No nodes found matching "{searchTerm}"</div>
          </div>
        )}
      </div>
    </div>
  );
}
