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
    <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between shadow-sm">
      <div className="flex items-center space-x-4">
        <Link href="/flows">
          <Button
            variant="outline"
            size="sm"
            className="border-2 border-gray-200 hover:border-coral hover:bg-coral hover:text-white transition-all duration-200"
            data-testid="button-back-to-flows-header"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Flows
          </Button>
        </Link>
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-coral rounded-xl flex items-center justify-center shadow-lg">
            <Workflow className="w-5 h-5 text-white" />
          </div>
          <h2 className="text-xl font-bold text-text-dark" data-testid="text-workflow-name">
            {workflowName}
          </h2>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        <Button
          className="bg-coral hover:bg-red-600 text-white border-2 border-coral hover:border-red-500 transition-all duration-200 shadow-md hover:shadow-lg"
          size="sm"
          onClick={onExecute}
          data-testid="button-run-workflow"
        >
          <Play className="w-4 h-4 mr-2" />
          Run
        </Button>
        <Button
          className="bg-coral hover:bg-red-600 text-white border-2 border-coral hover:border-red-500 transition-all duration-200 shadow-md hover:shadow-lg"
          size="sm"
          onClick={onPause}
          data-testid="button-pause-workflow"
        >
          <Pause className="w-4 h-4 mr-2" />
          Pause
        </Button>
        <Button
          className="bg-coral hover:bg-red-600 text-white border-2 border-coral hover:border-red-500 transition-all duration-200 shadow-md hover:shadow-lg"
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
          className="border-2 border-gray-200 hover:border-coral hover:bg-coral hover:text-white transition-all duration-200"
          data-testid="button-save-sidebar"
        >
          <Save className="w-4 h-4 mr-2" />
          Save
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-all duration-200"
          data-testid="button-settings-sidebar"
        >
          <Settings className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-all duration-200"
          data-testid="button-share-sidebar"
        >
          <Share2 className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}