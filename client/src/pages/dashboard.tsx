import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Workflow, CheckCircle, AlertCircle, Clock, TrendingUp, Play, Plus } from "lucide-react";
import { Link } from "wouter";
import { Workflow as WorkflowType } from "@shared/schema";

export default function DashboardPage() {
  const { data: workflows, isLoading } = useQuery<WorkflowType[]>({
    queryKey: ['/api/workflows'],
  });

  const activeFlows = workflows?.filter(w => w.isActive) || [];
  const totalRuns = 42; // Mock data - would come from API
  const successRate = 95.2; // Mock data
  const avgExecutionTime = 2.3; // Mock data

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-lg text-gray-600">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-light-grey min-h-full overflow-auto" data-testid="dashboard-page">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text-dark mb-2">Dashboard</h1>
        <p className="text-gray-600">Monitor and manage your workflow automation</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Flows</CardTitle>
            <Workflow className="h-4 w-4 text-coral" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-text-dark">{workflows?.length || 0}</div>
            <p className="text-xs text-gray-500 mt-1">
              {activeFlows.length} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Runs</CardTitle>
            <Play className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-text-dark">{totalRuns}</div>
            <p className="text-xs text-green-600 mt-1">
              +12% from last week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Success Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-text-dark">{successRate}%</div>
            <p className="text-xs text-green-600 mt-1">
              +2.1% from last week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Avg. Time</CardTitle>
            <Clock className="h-4 w-4 text-slate-blue" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-text-dark">{avgExecutionTime}s</div>
            <p className="text-xs text-slate-blue mt-1">
              -0.3s from last week
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Flows */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg">Recent Flows</CardTitle>
                <CardDescription>Your most recently updated workflows</CardDescription>
              </div>
              <Link href="/flows">
                <Button variant="outline" size="sm" data-testid="button-view-all-flows">
                  View All
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {workflows?.slice(0, 3).map((workflow) => (
                <div key={workflow.id} className="flex items-center justify-between p-3 border border-border-light rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-coral rounded-lg flex items-center justify-center">
                      <Workflow className="w-4 h-4 text-white" />
                    </div>
                    <div>
                      <h4 className="font-medium text-text-dark">{workflow.name}</h4>
                      <p className="text-sm text-gray-500">{workflow.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={workflow.isActive ? "default" : "secondary"}>
                      {workflow.isActive ? "Active" : "Inactive"}
                    </Badge>
                    <Link href={`/flows/${workflow.id}`}>
                      <Button variant="ghost" size="sm" data-testid={`button-view-flow-${workflow.id}`}>
                        View
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
              
              {!workflows?.length && (
                <div className="text-center py-8">
                  <Workflow className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No flows yet</h3>
                  <p className="text-gray-500 mb-4">Create your first workflow to get started</p>
                  <Link href="/flows/create">
                    <Button className="bg-coral hover:bg-red-600" data-testid="button-create-first-flow">
                      <Plus className="w-4 h-4 mr-2" />
                      Create First Flow
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Activity</CardTitle>
            <CardDescription>Latest workflow executions and events</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Mock activity data */}
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-text-dark">Customer Onboarding completed</p>
                  <p className="text-xs text-gray-500">2 minutes ago</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                  <Clock className="w-4 h-4 text-yellow-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-text-dark">Data Sync workflow started</p>
                  <p className="text-xs text-gray-500">5 minutes ago</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                  <AlertCircle className="w-4 h-4 text-red-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-text-dark">Email notification failed</p>
                  <p className="text-xs text-gray-500">12 minutes ago</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-text-dark">Backup workflow completed</p>
                  <p className="text-xs text-gray-500">1 hour ago</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}