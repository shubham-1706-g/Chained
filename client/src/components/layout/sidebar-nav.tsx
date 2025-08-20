import { Home, Workflow, Plug, Settings, Plus } from "lucide-react";
import { Link, useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Flows', href: '/flows', icon: Workflow },
  { name: 'Connections', href: '/connections', icon: Plug },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function SidebarNav() {
  const [location] = useLocation();

  return (
    <div className="w-64 bg-sidebar-dark text-white flex flex-col shadow-2xl" data-testid="sidebar-nav">
      {/* Brand Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-coral rounded-lg flex items-center justify-center">
            <Workflow className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-semibold">WorkflowHub</h1>
        </div>
      </div>

      {/* Create Flow Button */}
      <div className="p-4 border-b border-gray-700">
        <Link href="/flows/create">
          <Button 
            className="w-full bg-coral hover:bg-red-600 text-white"
            data-testid="button-create-flow"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Flow
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
                      "flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors cursor-pointer",
                      isActive
                        ? "bg-coral text-white"
                        : "text-gray-300 hover:bg-gray-700 hover:text-white"
                    )}
                    data-testid={`nav-${item.name.toLowerCase()}`}
                  >
                    <item.icon className="w-5 h-5" />
                    <span className="font-medium">{item.name}</span>
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-700">
        <div className="text-xs text-gray-400 text-center">
          WorkflowHub v1.0
        </div>
      </div>
    </div>
  );
}