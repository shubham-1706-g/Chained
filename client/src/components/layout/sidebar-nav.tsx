import { Home, Workflow, Plug, Settings, Plus, Menu, X } from "lucide-react";
import { Link, useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/contexts/sidebar-context";

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Flows', href: '/flows', icon: Workflow },
  { name: 'Connections', href: '/connections', icon: Plug },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function SidebarNav() {
  const [location] = useLocation();
  const { isMinimized, toggleSidebar } = useSidebar();

  return (
    <div className={cn(
      "bg-sidebar-dark text-white flex flex-col shadow-2xl transition-all duration-300",
      isMinimized ? "w-16" : "w-64"
    )} data-testid="sidebar-nav">
      {/* Brand Header */}
      <div className="p-4 border-b border-gray-700">
        {isMinimized ? (
          <div className="flex flex-col items-center space-y-3">
            <div className="w-8 h-8 bg-coral rounded-lg flex items-center justify-center">
              <Workflow className="w-5 h-5 text-white" />
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleSidebar}
              className="text-gray-400 hover:text-white hover:bg-gray-700 p-1 h-8 w-8 transition-all duration-200 hover:scale-110 border border-gray-600 hover:border-gray-500"
              data-testid="button-toggle-sidebar"
            >
              <Menu className="w-4 h-4" />
            </Button>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-coral rounded-lg flex items-center justify-center">
                <Workflow className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-semibold">WorkflowHub</h1>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleSidebar}
              className="text-gray-400 hover:text-white hover:bg-gray-700 p-1 h-8 w-8 transition-all duration-200 hover:scale-110 border border-gray-600 hover:border-gray-500"
              data-testid="button-toggle-sidebar"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Create Flow Button */}
      <div className="p-4 border-b border-gray-700">
        <Link href="/flows/create">
          <Button 
            className={cn(
              "bg-coral hover:bg-red-600 text-white",
              isMinimized ? "w-full p-2" : "w-full"
            )}
            data-testid="button-create-flow"
            title={isMinimized ? "Create Flow" : undefined}
          >
            <Plus className="w-4 h-4" />
            {!isMinimized && <span className="ml-2">Create Flow</span>}
          </Button>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navigation.map((item) => {
            const isActive = location === item.href || 
              (item.href !== '/' && location.startsWith(item.href));
            
            return (
              <li key={item.name}>
                <Link href={item.href}>
                  <div
                    className={cn(
                      "flex items-center rounded-lg transition-all duration-200 cursor-pointer transform hover:scale-105",
                      isMinimized ? "px-2 py-3 justify-center" : "space-x-3 px-4 py-3",
                      isActive
                        ? "bg-coral text-white shadow-md"
                        : "text-gray-300 hover:bg-gray-700 hover:text-white hover:shadow-md"
                    )}
                    data-testid={`nav-${item.name.toLowerCase()}`}
                    title={isMinimized ? item.name : undefined}
                  >
                    <item.icon className="w-5 h-5" />
                    {!isMinimized && <span className="font-medium">{item.name}</span>}
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      {!isMinimized && (
        <div className="p-4 border-t border-gray-700">
          <div className="text-xs text-gray-400 text-center">
            WorkflowHub v1.0
          </div>
        </div>
      )}
    </div>
  );
}