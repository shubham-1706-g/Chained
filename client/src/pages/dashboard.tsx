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
    <div className="p-6 bg-light-grey min-h-full overflow-visible" data-testid="dashboard-page">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text-dark mb-2">Dashboard</h1>
        <p className="text-gray-600">Monitor and manage your workflow automation</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="bg-gradient-to-br from-coral-50 to-white border-2 border-coral-200 hover:border-coral hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-700">Total Flows</CardTitle>
            <div className="w-10 h-10 bg-coral rounded-xl flex items-center justify-center shadow-lg">
              <Workflow className="h-5 w-5 text-white" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-text-dark">{workflows?.length || 0}</div>
            <p className="text-sm text-coral font-medium mt-2">
              {activeFlows.length} active workflows
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-white border-2 border-green-200 hover:border-green-500 hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-700">Total Runs</CardTitle>
            <div className="w-10 h-10 bg-green-500 rounded-xl flex items-center justify-center shadow-lg">
              <Play className="h-5 w-5 text-white" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-text-dark">{totalRuns}</div>
            <p className="text-sm text-green-600 font-medium mt-2 flex items-center">
              <TrendingUp className="w-4 h-4 mr-1" />
              +12% from last week
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-emerald-50 to-white border-2 border-emerald-200 hover:border-emerald-500 hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-700">Success Rate</CardTitle>
            <div className="w-10 h-10 bg-emerald-500 rounded-xl flex items-center justify-center shadow-lg">
              <CheckCircle className="h-5 w-5 text-white" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-text-dark">{successRate}%</div>
            <p className="text-sm text-emerald-600 font-medium mt-2 flex items-center">
              <TrendingUp className="w-4 h-4 mr-1" />
              +2.1% from last week
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-white border-2 border-blue-200 hover:border-blue-500 hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-700">Avg. Time</CardTitle>
            <div className="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center shadow-lg">
              <Clock className="h-5 w-5 text-white" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-text-dark">{avgExecutionTime}s</div>
            <p className="text-sm text-blue-600 font-medium mt-2 flex items-center">
              <TrendingUp className="w-4 h-4 mr-1 rotate-180" />
              -0.3s from last week
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Flows */}
        <Card className="border-2 border-gray-200 hover:border-gray-300 hover:shadow-lg transition-all duration-200">
          <CardHeader className="bg-gradient-to-r from-gray-50 to-white border-b border-gray-100 rounded-t-lg">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg text-gray-800 flex items-center">
                  <Workflow className="w-5 h-5 text-coral mr-2" />
                  Recent Flows
                </CardTitle>
                <CardDescription className="text-gray-600">Your most recently updated workflows</CardDescription>
              </div>
              <Link href="/flows">
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="border-2 border-gray-200 hover:border-coral hover:bg-coral hover:text-white transition-all duration-200 shadow-sm hover:shadow-md"
                  data-testid="button-view-all-flows"
                >
                  View All
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent className="rounded-b-lg">
            <div className="space-y-4">
              {workflows?.slice(0, 3).map((workflow) => (
                <div key={workflow.id} className="flex items-center justify-between p-4 border-2 border-gray-200 hover:border-gray-300 rounded-xl hover:shadow-md transition-all duration-200 bg-gradient-to-r from-gray-50 to-white">
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-lg ${
                      workflow.isActive ? 'bg-green-500' : 'bg-gray-400'
                    }`}>
                      <Workflow className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-text-dark hover:text-coral transition-colors cursor-pointer">{workflow.name}</h4>
                      <p className="text-sm text-gray-600">{workflow.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Badge 
                      variant={workflow.isActive ? "default" : "secondary"}
                      className={workflow.isActive ? "bg-green-100 text-green-800 border-2 border-green-200" : "bg-gray-100 text-gray-800 border-2 border-gray-200"}
                    >
                      {workflow.isActive ? "Active" : "Inactive"}
                    </Badge>
                    <Link href={`/flows/${workflow.id}/dashboard`}>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="border-2 border-gray-200 hover:border-coral hover:bg-coral hover:text-white transition-all duration-200 shadow-sm hover:shadow-md"
                        data-testid={`button-view-flow-${workflow.id}`}
                      >
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
        <Card className="border-2 border-gray-200 hover:border-gray-300 hover:shadow-lg transition-all duration-200">
          <CardHeader className="bg-gradient-to-r from-gray-50 to-white border-b border-gray-100 rounded-t-lg">
            <CardTitle className="text-lg text-gray-800 flex items-center">
              <Clock className="w-5 h-5 text-blue-600 mr-2" />
              Recent Activity
            </CardTitle>
            <CardDescription className="text-gray-600">Latest workflow executions and events</CardDescription>
          </CardHeader>
          <CardContent className="rounded-b-lg">
            <div className="space-y-3">
              {/* Mock activity data */}
              <div className="flex items-start space-x-4 p-4 border-2 border-gray-200 hover:border-green-300 rounded-xl hover:shadow-md transition-all duration-200 bg-gradient-to-r from-green-50 to-white">
                <div className="w-10 h-10 bg-green-500 rounded-xl flex items-center justify-center shadow-lg">
                  <CheckCircle className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-text-dark">Customer Onboarding completed</p>
                  <p className="text-xs text-green-600 font-medium">2 minutes ago</p>
                </div>
              </div>

              <div className="flex items-start space-x-4 p-4 border-2 border-gray-200 hover:border-yellow-300 rounded-xl hover:shadow-md transition-all duration-200 bg-gradient-to-r from-yellow-50 to-white">
                <div className="w-10 h-10 bg-yellow-500 rounded-xl flex items-center justify-center shadow-lg">
                  <Clock className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-text-dark">Data Sync workflow started</p>
                  <p className="text-xs text-yellow-600 font-medium">5 minutes ago</p>
                </div>
              </div>

              <div className="flex items-start space-x-4 p-4 border-2 border-gray-200 hover:border-red-300 rounded-xl hover:shadow-md transition-all duration-200 bg-gradient-to-r from-red-50 to-white">
                <div className="w-10 h-10 bg-red-500 rounded-xl flex items-center justify-center shadow-lg">
                  <AlertCircle className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-text-dark">Email notification failed</p>
                  <p className="text-xs text-red-600 font-medium">12 minutes ago</p>
                </div>
              </div>

              <div className="flex items-start space-x-4 p-4 border-2 border-gray-200 hover:border-green-300 rounded-xl hover:shadow-md transition-all duration-200 bg-gradient-to-r from-green-50 to-white">
                <div className="w-10 h-10 bg-green-500 rounded-xl flex items-center justify-center shadow-lg">
                  <CheckCircle className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-text-dark">Backup workflow completed</p>
                  <p className="text-xs text-green-600 font-medium">1 hour ago</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}