import { useState } from "react";
import { Play, Pause, Square, Save, FolderOpen, Settings, Share2, ArrowLeft, Workflow } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "wouter";
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
      {/* Sidebar Header with Actions */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Link href="/flows">
              <Button 
                variant="ghost" 
                size="sm" 
                className="text-coral hover:text-white hover:bg-coral/20 border border-coral/30 transition-all duration-200"
                data-testid="button-back-to-flows-sidebar"
              >
                <ArrowLeft className="w-4 h-4 mr-1" />
                Back
              </Button>
            </Link>
            <div className="w-6 h-6 bg-coral rounded flex items-center justify-center">
              <Workflow className="w-4 h-4 text-white" />
            </div>
          </div>
          <div className="flex items-center space-x-1">
            <Button 
              variant="ghost"
              size="sm"
              onClick={onSave}
              className="text-gray-300 hover:text-white hover:bg-gray-700 transition-all duration-200 border border-gray-600"
              data-testid="button-save-sidebar"
            >
              <Save className="w-4 h-4" />
            </Button>
            <Button 
              variant="ghost"
              size="sm"
              className="text-gray-300 hover:text-white hover:bg-gray-700 transition-all duration-200 border border-gray-600"
              data-testid="button-settings-sidebar"
            >
              <Settings className="w-4 h-4" />
            </Button>
            <Button 
              variant="ghost"
              size="sm"
              className="text-gray-300 hover:text-white hover:bg-gray-700 transition-all duration-200 border border-gray-600"
              data-testid="button-share-sidebar"
            >
              <Share2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
        <div>
          <h1 className="text-lg font-semibold truncate">{workflowName}</h1>
          <p className="text-sm text-gray-400">Edit workflow</p>
        </div>
      </div>
      
      {/* Workflow Controls */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex space-x-2 mb-4">
          <Button 
            className="flex-1 bg-coral hover:bg-red-600 text-white transition-all duration-200 shadow-md hover:shadow-lg" 
            size="sm"
            onClick={onExecute}
            data-testid="button-run-workflow"
          >
            <Play className="w-4 h-4 mr-2" />
            Run
          </Button>
          <Button 
            className="flex-1 bg-gray-600 hover:bg-gray-500 text-white transition-all duration-200 shadow-md hover:shadow-lg" 
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
