import { Button } from "@/components/ui/button";
import { Workflow } from "lucide-react";

interface NodeLibraryToggleProps {
  onOpen: () => void;
}

export function NodeLibraryToggle({ onOpen }: NodeLibraryToggleProps) {
  return (
    <div className="absolute left-4 top-16 z-10">
      <Button
        onClick={onOpen}
        className="bg-coral hover:bg-red-600 text-white border-2 border-coral hover:border-red-500 transition-all duration-200 shadow-lg hover:shadow-xl rounded-lg px-4 py-3"
        data-testid="node-library-toggle"
      >
        <Workflow className="w-4 h-4 mr-2" />
        <span className="text-sm font-medium">Node Library</span>
      </Button>
    </div>
  );
}
