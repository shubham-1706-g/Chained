import { useState } from "react";
import { Play, Pause, Square, Save, FolderOpen, Settings, Share2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { NodeLibrary } from "./node-library";
import { ExecutionStatus } from "../../types/workflow";

interface WorkflowSidebarProps {
  workflowName: string;
  executionStatus: ExecutionStatus;
  onExecute: () => void;
  onPause: () => void;
  onStop: () => void;
  onSave: () => void;
  onLoad: () => void;
}

export function WorkflowSidebar({
  workflowName,
  executionStatus,
  onExecute,
  onPause,
  onStop,
  onSave,
  onLoad
}: WorkflowSidebarProps) {
  return (
    <div className="w-80 bg-sidebar-dark text-white flex flex-col shadow-2xl" data-testid="workflow-sidebar">
      {/* Sidebar Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-coral rounded-lg flex items-center justify-center">
            <i className="fas fa-project-diagram text-white text-sm"></i>
          </div>
          <h1 className="text-xl font-semibold">WorkflowHub</h1>
        </div>
      </div>
      
      {/* Workflow Controls */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex space-x-2 mb-4">
          <Button 
            className="flex-1 bg-coral hover:bg-red-600 text-white" 
            size="sm"
            onClick={onExecute}
            data-testid="button-run-workflow"
          >
            <Play className="w-4 h-4 mr-2" />
            Run
          </Button>
          <Button 
            className="flex-1 bg-gray-600 hover:bg-gray-500 text-white" 
            size="sm"
            onClick={onPause}
            data-testid="button-pause-workflow"
          >
            <Pause className="w-4 h-4 mr-2" />
            Pause
          </Button>
          <Button 
            className="flex-1 bg-gray-600 hover:bg-gray-500 text-white" 
            size="sm"
            onClick={onStop}
            data-testid="button-stop-workflow"
          >
            <Square className="w-4 h-4 mr-2" />
            Stop
          </Button>
        </div>
        
        <div className="flex space-x-2">
          <Button 
            className="flex-1 bg-gray-700 hover:bg-gray-600 text-white" 
            size="sm"
            onClick={onSave}
            data-testid="button-save-workflow"
          >
            <Save className="w-4 h-4 mr-2" />
            Save
          </Button>
          <Button 
            className="flex-1 bg-gray-700 hover:bg-gray-600 text-white" 
            size="sm"
            onClick={onLoad}
            data-testid="button-load-workflow"
          >
            <FolderOpen className="w-4 h-4 mr-2" />
            Load
          </Button>
        </div>
      </div>
      
      {/* Node Library */}
      <div className="flex-1 overflow-y-auto">
        <NodeLibrary />
      </div>
      
      {/* Execution Status */}
      <div className="p-4 border-t border-gray-700" data-testid="execution-status">
        <div className="flex items-center space-x-3 text-sm">
          <div 
            className={`w-3 h-3 rounded-full ${
              executionStatus.status === 'running' ? 'bg-green-500 execution-indicator' :
              executionStatus.status === 'completed' ? 'bg-green-500' :
              executionStatus.status === 'error' ? 'bg-red-500' :
              executionStatus.status === 'paused' ? 'bg-yellow-500' :
              'bg-gray-500'
            }`}
          />
          <span className="text-gray-300">
            {executionStatus.status === 'running' ? 'Workflow Running' :
             executionStatus.status === 'completed' ? 'Workflow Completed' :
             executionStatus.status === 'error' ? 'Workflow Error' :
             executionStatus.status === 'paused' ? 'Workflow Paused' :
             'Workflow Ready'}
          </span>
        </div>
        {executionStatus.lastExecution && (
          <div className="mt-2 text-xs text-gray-400">
            Last execution: {executionStatus.lastExecution.toLocaleTimeString()}
          </div>
        )}
        {executionStatus.message && (
          <div className="mt-1 text-xs text-gray-400">
            {executionStatus.message}
          </div>
        )}
      </div>
    </div>
  );
}
