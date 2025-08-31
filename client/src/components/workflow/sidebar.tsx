import { NodeLibrary } from "./node-library";

export function WorkflowSidebar() {
return (
    <div className="w-80 bg-sidebar-dark text-white flex flex-col shadow-2xl flex-shrink-0" data-testid="workflow-sidebar">
    {/* Node Library */}
    <div className="flex-1 overflow-y-auto">
        <NodeLibrary />
    </div>
    </div>
);
}
