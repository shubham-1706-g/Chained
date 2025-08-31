import { Play, Pause, Square, Save, Settings, Share2, ArrowLeft, Workflow } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "wouter";

interface WorkflowHeaderProps {
  workflowName: string;
  onExecute: () => void;
  onPause: () => void;
  onStop: () => void;
  onSave: () => void;
}

export function WorkflowHeader({
  workflowName,
  onExecute,
  onPause,
  onStop,
  onSave,
}: WorkflowHeaderProps) {
  return (
    <div className="bg-white border-b border-border-light p-4 flex items-center justify-between shadow-sm">
      <div className="flex items-center space-x-4">
        <Link href="/flows">
          <Button
            variant="outline"
            size="sm"
            className="text-coral hover:text-white hover:bg-coral/20 border border-coral/30 transition-all duration-200"
            data-testid="button-back-to-flows-header"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back
          </Button>
        </Link>
        <div className="flex items-center space-x-2">
            <div className="w-6 h-6 bg-coral rounded flex items-center justify-center">
              <Workflow className="w-4 h-4 text-white" />
            </div>
          <h2 className="text-lg font-semibold text-text-dark" data-testid="text-workflow-name">
            {workflowName}
          </h2>
        </div>

      </div>

      <div className="flex items-center space-x-2">
        <Button
            className="bg-coral hover:bg-red-600 text-white transition-all duration-200 shadow-md hover:shadow-lg"
            size="sm"
            onClick={onExecute}
            data-testid="button-run-workflow"
          >
            <Play className="w-4 h-4 mr-2" />
            Run
          </Button>
          <Button
            className="bg-gray-600 hover:bg-gray-500 text-white transition-all duration-200 shadow-md hover:shadow-lg"
            size="sm"
            onClick={onPause}
            data-testid="button-pause-workflow"
          >
            <Pause className="w-4 h-4 mr-2" />
            Pause
          </Button>
          <Button
            className="bg-gray-600 hover:bg-gray-500 text-white"
            size="sm"
            onClick={onStop}
            data-testid="button-stop-workflow"
          >
            <Square className="w-4 h-4 mr-2" />
            Stop
          </Button>
        <Button
            variant="outline"
            size="sm"
            onClick={onSave}
            className="text-gray-500 hover:text-white hover:bg-gray-700 transition-all duration-200 border border-gray-600"
            data-testid="button-save-sidebar"
          >
            <Save className="w-4 h-4 mr-2" />
            Save
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="text-gray-500 hover:text-gray-700"
            data-testid="button-settings-sidebar"
          >
            <Settings className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="text-gray-500 hover:text-gray-700"
            data-testid="button-share-sidebar"
          >
            <Share2 className="w-4 h-4" />
          </Button>
      </div>
    </div>
  );
}