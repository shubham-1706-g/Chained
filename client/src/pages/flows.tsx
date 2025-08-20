import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Workflow, Search, Filter, Plus, MoreVertical, Play, Pause, Settings, Trash2 } from "lucide-react";
import { Link } from "wouter";
import { Workflow as WorkflowType } from "@shared/schema";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

export default function FlowsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const { data: workflows, isLoading } = useQuery<WorkflowType[]>({
    queryKey: ['/api/workflows'],
  });

  const filteredWorkflows = workflows?.filter(workflow => {
    const matchesSearch = workflow.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         workflow.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "all" || 
                         (statusFilter === "active" && workflow.isActive) ||
                         (statusFilter === "inactive" && !workflow.isActive);
    return matchesSearch && matchesStatus;
  }) || [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-lg text-gray-600">Loading flows...</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-light-grey min-h-full" data-testid="flows-page">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-text-dark mb-2">Flows</h1>
          <p className="text-gray-600">Manage and monitor your workflow automations</p>
        </div>
        <Link href="/flows/create">
          <Button 
            className="bg-coral hover:bg-red-600 text-white"
            data-testid="button-create-flow"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Flow
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search flows..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
                data-testid="input-search-flows"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]" data-testid="select-status-filter">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Create Flow Templates */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Quick Start Templates</CardTitle>
          <CardDescription>Get started quickly with pre-built workflow templates</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link href="/flows/create?template=webhook">
              <Card className="cursor-pointer hover:shadow-md transition-shadow border-dashed border-2 border-coral">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="w-12 h-12 bg-coral rounded-lg flex items-center justify-center mx-auto mb-3">
                      <Workflow className="w-6 h-6 text-white" />
                    </div>
                    <h3 className="font-semibold text-text-dark mb-1">Webhook Trigger</h3>
                    <p className="text-sm text-gray-500">Start with HTTP webhook</p>
                  </div>
                </CardContent>
              </Card>
            </Link>

            <Link href="/flows/create?template=schedule">
              <Card className="cursor-pointer hover:shadow-md transition-shadow border-dashed border-2 border-slate-blue">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="w-12 h-12 bg-slate-blue rounded-lg flex items-center justify-center mx-auto mb-3">
                      <Workflow className="w-6 h-6 text-white" />
                    </div>
                    <h3 className="font-semibold text-text-dark mb-1">Scheduled Flow</h3>
                    <p className="text-sm text-gray-500">Run on schedule</p>
                  </div>
                </CardContent>
              </Card>
            </Link>

            <Link href="/flows/create?template=blank">
              <Card className="cursor-pointer hover:shadow-md transition-shadow border-dashed border-2 border-gray-300">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="w-12 h-12 bg-gray-400 rounded-lg flex items-center justify-center mx-auto mb-3">
                      <Plus className="w-6 h-6 text-white" />
                    </div>
                    <h3 className="font-semibold text-text-dark mb-1">Blank Flow</h3>
                    <p className="text-sm text-gray-500">Start from scratch</p>
                  </div>
                </CardContent>
              </Card>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Flows List */}
      <div className="space-y-4">
        {filteredWorkflows.length === 0 ? (
          <Card>
            <CardContent className="py-12">
              <div className="text-center">
                <Workflow className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-medium text-gray-900 mb-2">
                  {searchTerm || statusFilter !== "all" ? "No flows found" : "No flows yet"}
                </h3>
                <p className="text-gray-500 mb-6">
                  {searchTerm || statusFilter !== "all" 
                    ? "Try adjusting your search or filters" 
                    : "Create your first workflow to get started"}
                </p>
                {!searchTerm && statusFilter === "all" && (
                  <Link href="/flows/create">
                    <Button className="bg-coral hover:bg-red-600" data-testid="button-create-first-flow">
                      <Plus className="w-4 h-4 mr-2" />
                      Create First Flow
                    </Button>
                  </Link>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredWorkflows.map((workflow) => (
            <Card key={workflow.id} className="hover:shadow-md transition-shadow">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-coral rounded-lg flex items-center justify-center">
                      <Workflow className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-text-dark">{workflow.name}</h3>
                      <p className="text-gray-500 text-sm">{workflow.description}</p>
                      <div className="flex items-center space-x-4 mt-2">
                        <Badge variant={workflow.isActive ? "default" : "secondary"}>
                          {workflow.isActive ? "Active" : "Inactive"}
                        </Badge>
                        <span className="text-xs text-gray-400">
                          Updated {workflow.updatedAt ? new Date(workflow.updatedAt).toLocaleDateString() : 'recently'}
                        </span>
                        <span className="text-xs text-gray-400">
                          {workflow.nodes?.length || 0} nodes
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Link href={`/flows/${workflow.id}/dashboard`}>
                      <Button variant="outline" size="sm" data-testid={`button-dashboard-${workflow.id}`}>
                        Dashboard
                      </Button>
                    </Link>
                    <Link href={`/flows/${workflow.id}/edit`}>
                      <Button variant="outline" size="sm" data-testid={`button-edit-${workflow.id}`}>
                        Edit
                      </Button>
                    </Link>
                    
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" data-testid={`button-more-${workflow.id}`}>
                          <MoreVertical className="w-4 h-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <Play className="w-4 h-4 mr-2" />
                          Run Flow
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Pause className="w-4 h-4 mr-2" />
                          Pause Flow
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Settings className="w-4 h-4 mr-2" />
                          Settings
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-red-600">
                          <Trash2 className="w-4 h-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}