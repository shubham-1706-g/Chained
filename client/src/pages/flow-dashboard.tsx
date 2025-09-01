import { useQuery } from "@tanstack/react-query";
import { useRoute } from "wouter";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Play, Pause, Square, Settings, AlertCircle, CheckCircle, Clock, TrendingUp, Workflow, Activity, Zap } from "lucide-react";
import { Link } from "wouter";
import { Workflow as WorkflowType } from "@shared/schema";

export default function FlowDashboardPage() {
  const [match, params] = useRoute("/flows/:id/dashboard");
  const flowId = params?.id;

  const { data: workflow, isLoading } = useQuery<WorkflowType>({
    queryKey: ['/api/workflows', flowId],
    enabled: !!flowId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-lg text-gray-600">Loading flow dashboard...</div>
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-lg text-gray-600">Flow not found</div>
      </div>
    );
  }

  // Mock execution data - would come from API
  const executions = [
    { id: '1', status: 'success', startTime: new Date(Date.now() - 300000), duration: 2.3, trigger: 'Manual' },
    { id: '2', status: 'success', startTime: new Date(Date.now() - 1800000), duration: 1.8, trigger: 'Webhook' },
    { id: '3', status: 'failed', startTime: new Date(Date.now() - 3600000), duration: 0.5, trigger: 'Schedule', error: 'API timeout' },
    { id: '4', status: 'success', startTime: new Date(Date.now() - 7200000), duration: 3.1, trigger: 'Manual' },
  ];

  const successRate = (executions.filter(e => e.status === 'success').length / executions.length) * 100;
  const avgDuration = executions.reduce((acc, e) => acc + e.duration, 0) / executions.length;

  return (
    <div className="p-6 bg-light-grey min-h-full overflow-visible" data-testid="flow-dashboard-page">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-text-dark mb-2 flex items-center">
              <Workflow className="w-8 h-8 text-coral mr-3" />
              {workflow.name}
            </h1>
            <p className="text-gray-600">{workflow.description}</p>
          </div>
          <div className="flex items-center space-x-3">
            <Badge 
              variant={workflow.isActive ? "default" : "secondary"}
              className={`border-2 ${workflow.isActive ? 'border-green-200 bg-green-100 text-green-800' : 'border-gray-200 bg-gray-100 text-gray-600'}`}
            >
              {workflow.isActive ? "Active" : "Inactive"}
            </Badge>
            <Link href={`/flows/${workflow.id}/edit`}>
              <Button 
                variant="outline" 
                className="border-2 border-gray-200 hover:border-coral hover:bg-coral hover:text-white transition-all duration-200"
                data-testid="button-edit-flow"
              >
                <Settings className="w-4 h-4 mr-2" />
                Edit Flow
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Control Panel */}
      <Card className="mb-6 border-2 border-gray-200 hover:border-gray-300 hover:shadow-lg transition-all duration-200">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg flex items-center">
            <Zap className="w-5 h-5 text-coral mr-2" />
            Flow Controls
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="flex items-center space-x-4">
            <Button 
              className="bg-coral hover:bg-red-600 text-white border-2 border-coral hover:border-red-500 transition-all duration-200" 
              data-testid="button-run-flow"
            >
              <Play className="w-4 h-4 mr-2" />
              Run Flow
            </Button>
            <Button 
              variant="outline" 
              className="border-2 border-gray-200 hover:border-gray-400 hover:bg-gray-50 transition-all duration-200"
              data-testid="button-pause-flow"
            >
              <Pause className="w-4 h-4 mr-2" />
              Pause
            </Button>
            <Button 
              variant="outline" 
              className="border-2 border-gray-200 hover:border-gray-400 hover:bg-gray-50 transition-all duration-200"
              data-testid="button-stop-flow"
            >
              <Square className="w-4 h-4 mr-2" />
              Stop
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid - Using main dashboard color references */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="bg-gradient-to-br from-coral-50 to-white border-2 border-coral-200 hover:border-coral hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-700">Total Executions</CardTitle>
            <div className="w-10 h-10 bg-coral rounded-xl flex items-center justify-center shadow-lg">
              <TrendingUp className="h-5 w-5 text-white" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-text-dark">{executions.length}</div>
            <p className="text-sm text-coral font-medium mt-2">
              Last 24 hours
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
            <div className="text-3xl font-bold text-text-dark">{successRate.toFixed(1)}%</div>
            <p className="text-sm text-emerald-600 font-medium mt-2">
              {executions.filter(e => e.status === 'success').length} successful
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-white border-2 border-blue-200 hover:border-blue-500 hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-700">Avg. Duration</CardTitle>
            <div className="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center shadow-lg">
              <Clock className="h-5 w-5 text-white" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-text-dark">{avgDuration.toFixed(1)}s</div>
            <p className="text-sm text-blue-600 font-medium mt-2">
              Per execution
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-50 to-white border-2 border-red-200 hover:border-red-500 hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-700">Failed Runs</CardTitle>
            <div className="w-10 h-10 bg-red-500 rounded-xl flex items-center justify-center shadow-lg">
              <AlertCircle className="h-5 w-5 text-white" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-text-dark">
              {executions.filter(e => e.status === 'failed').length}
            </div>
            <p className="text-sm text-red-600 font-medium mt-2">
              Needs attention
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Executions */}
        <Card className="border-2 border-gray-200 hover:border-gray-300 hover:shadow-lg transition-all duration-200">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg flex items-center">
              <Activity className="w-5 h-5 text-blue-600 mr-2" />
              Recent Executions
            </CardTitle>
            <CardDescription>Latest workflow runs and their status</CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="space-y-3">
              {executions.map((execution) => (
                <div 
                  key={execution.id} 
                  className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-sm transition-all duration-200"
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      execution.status === 'success' ? 'bg-green-100' : 'bg-red-100'
                    }`}>
                      {execution.status === 'success' ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-red-600" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-text-dark">
                          {execution.status === 'success' ? 'Successful' : 'Failed'}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {execution.trigger}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-500">
                        {execution.startTime.toLocaleTimeString()} • {execution.duration}s
                      </p>
                      {execution.error && (
                        <p className="text-xs text-red-600 mt-1">{execution.error}</p>
                      )}
                    </div>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="border-2 border-gray-200 hover:border-coral hover:bg-coral hover:text-white transition-all duration-200"
                    data-testid={`button-view-execution-${execution.id}`}
                  >
                    View
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Flow Structure with Better UI Components */}
        <Card className="border-2 border-gray-200 hover:border-gray-300 hover:shadow-lg transition-all duration-200">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg flex items-center">
              <Workflow className="w-5 h-5 text-purple-600 mr-2" />
              Flow Structure
            </CardTitle>
            <CardDescription>Overview of nodes and connections</CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="space-y-4">
              {/* Node Type Containers */}
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-gradient-to-br from-green-50 to-white border-2 border-green-200 hover:border-green-400 rounded-xl hover:shadow-md transition-all duration-200 text-center">
                  <div className="text-2xl font-bold text-green-600 mb-2">
                    {workflow.nodes?.filter(n => n.data.category === 'trigger').length || 0}
                  </div>
                  <div className="text-sm text-gray-600 font-medium">Triggers</div>
                </div>
                <div className="p-4 bg-gradient-to-br from-blue-50 to-white border-2 border-blue-200 hover:border-blue-400 rounded-xl hover:shadow-md transition-all duration-200 text-center">
                  <div className="text-2xl font-bold text-blue-600 mb-2">
                    {workflow.nodes?.filter(n => n.data.category === 'action').length || 0}
                  </div>
                  <div className="text-sm text-gray-600 font-medium">Actions</div>
                </div>
                <div className="p-4 bg-gradient-to-br from-purple-50 to-white border-2 border-purple-200 hover:border-purple-400 rounded-xl hover:shadow-md transition-all duration-200 text-center">
                  <div className="text-2xl font-bold text-purple-600 mb-2">
                    {workflow.nodes?.filter(n => n.data.category === 'transform').length || 0}
                  </div>
                  <div className="text-sm text-gray-600 font-medium">Transforms</div>
                </div>
              </div>
              
              {/* Flow Info Containers */}
              <div className="pt-4 border-t border-gray-200 space-y-3">
                <div className="flex justify-between items-center p-3 bg-gradient-to-r from-gray-50 to-white border-2 border-gray-200 hover:border-gray-300 rounded-lg transition-all duration-200 pr-6">
                  <span className="text-gray-600 font-medium">Total Nodes:</span>
                  <span className="font-bold text-text-dark">{workflow.nodes?.length || 0}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gradient-to-r from-gray-50 to-white border-2 border-gray-200 hover:border-gray-300 rounded-lg transition-all duration-200 pr-6">
                  <span className="text-gray-600 font-medium">Connections:</span>
                  <span className="font-bold text-text-dark">{workflow.edges?.length || 0}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gradient-to-r from-gray-50 to-white border-2 border-gray-200 hover:border-gray-300 rounded-lg transition-all duration-200 pr-6">
                  <span className="text-gray-600 font-medium">Last Updated:</span>
                  <span className="font-bold text-text-dark">
                    {workflow.updatedAt ? new Date(workflow.updatedAt).toLocaleDateString() : 'Never'}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}