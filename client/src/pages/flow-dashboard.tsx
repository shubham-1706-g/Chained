import { useQuery } from "@tanstack/react-query";
import { useRoute } from "wouter";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Play, Pause, Square, Settings, AlertCircle, CheckCircle, Clock, TrendingUp } from "lucide-react";
import { Link } from "wouter";
import { Workflow } from "@shared/schema";

export default function FlowDashboardPage() {
  const [match, params] = useRoute("/flows/:id/dashboard");
  const flowId = params?.id;

  const { data: workflow, isLoading } = useQuery<Workflow>({
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
    <div className="p-6 bg-light-grey min-h-full overflow-auto" data-testid="flow-dashboard-page">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-4">
          <Link href="/flows">
            <Button variant="ghost" size="sm" data-testid="button-back-to-flows">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Flows
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-text-dark">{workflow.name}</h1>
            <p className="text-gray-600">{workflow.description}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={workflow.isActive ? "default" : "secondary"}>
            {workflow.isActive ? "Active" : "Inactive"}
          </Badge>
          <Link href={`/flows/${workflow.id}/edit`}>
            <Button variant="outline" data-testid="button-edit-flow">
              <Settings className="w-4 h-4 mr-2" />
              Edit Flow
            </Button>
          </Link>
        </div>
      </div>

      {/* Control Panel */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Flow Controls</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <Button className="bg-coral hover:bg-red-600 text-white" data-testid="button-run-flow">
              <Play className="w-4 h-4 mr-2" />
              Run Flow
            </Button>
            <Button variant="outline" data-testid="button-pause-flow">
              <Pause className="w-4 h-4 mr-2" />
              Pause
            </Button>
            <Button variant="outline" data-testid="button-stop-flow">
              <Square className="w-4 h-4 mr-2" />
              Stop
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Executions</CardTitle>
            <TrendingUp className="h-4 w-4 text-coral" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-text-dark">{executions.length}</div>
            <p className="text-xs text-gray-500 mt-1">
              Last 24 hours
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Success Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-text-dark">{successRate.toFixed(1)}%</div>
            <p className="text-xs text-green-600 mt-1">
              {executions.filter(e => e.status === 'success').length} successful
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Avg. Duration</CardTitle>
            <Clock className="h-4 w-4 text-slate-blue" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-text-dark">{avgDuration.toFixed(1)}s</div>
            <p className="text-xs text-slate-blue mt-1">
              Per execution
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Failed Runs</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-text-dark">
              {executions.filter(e => e.status === 'failed').length}
            </div>
            <p className="text-xs text-red-600 mt-1">
              Needs attention
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Executions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Executions</CardTitle>
            <CardDescription>Latest workflow runs and their status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {executions.map((execution) => (
                <div key={execution.id} className="flex items-center justify-between p-3 border border-border-light rounded-lg">
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
                  <Button variant="ghost" size="sm" data-testid={`button-view-execution-${execution.id}`}>
                    View
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Flow Structure */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Flow Structure</CardTitle>
            <CardDescription>Overview of nodes and connections</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="p-3 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {workflow.nodes?.filter(n => n.data.category === 'trigger').length || 0}
                  </div>
                  <div className="text-sm text-gray-600">Triggers</div>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {workflow.nodes?.filter(n => n.data.category === 'action').length || 0}
                  </div>
                  <div className="text-sm text-gray-600">Actions</div>
                </div>
                <div className="p-3 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {workflow.nodes?.filter(n => n.data.category === 'transform').length || 0}
                  </div>
                  <div className="text-sm text-gray-600">Transforms</div>
                </div>
              </div>
              
              <div className="pt-4 border-t border-border-light">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">Total Nodes:</span>
                  <span className="font-medium">{workflow.nodes?.length || 0}</span>
                </div>
                <div className="flex justify-between items-center text-sm mt-2">
                  <span className="text-gray-600">Connections:</span>
                  <span className="font-medium">{workflow.edges?.length || 0}</span>
                </div>
                <div className="flex justify-between items-center text-sm mt-2">
                  <span className="text-gray-600">Last Updated:</span>
                  <span className="font-medium">
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