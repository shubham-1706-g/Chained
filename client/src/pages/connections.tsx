import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plug, Search, Plus, CheckCircle, AlertCircle, Settings, Trash2, Key, Globe } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

interface Connection {
  id: string;
  name: string;
  type: string;
  status: 'connected' | 'disconnected' | 'error';
  lastUsed: Date;
  description: string;
  icon: string;
  color: string;
}

// Mock connections data
const mockConnections: Connection[] = [
  {
    id: '1',
    name: 'Gmail',
    type: 'email',
    status: 'connected',
    lastUsed: new Date(Date.now() - 300000),
    description: 'Send emails via Gmail API',
    icon: 'fas fa-envelope',
    color: 'bg-red-500'
  },
  {
    id: '2',
    name: 'Slack',
    type: 'messaging',
    status: 'connected',
    lastUsed: new Date(Date.now() - 1800000),
    description: 'Send messages to Slack channels',
    icon: 'fab fa-slack',
    color: 'bg-purple-500'
  },
  {
    id: '3',
    name: 'PostgreSQL Database',
    type: 'database',
    status: 'error',
    lastUsed: new Date(Date.now() - 3600000),
    description: 'Connect to PostgreSQL database',
    icon: 'fas fa-database',
    color: 'bg-blue-500'
  },
  {
    id: '4',
    name: 'Stripe',
    type: 'payment',
    status: 'connected',
    lastUsed: new Date(Date.now() - 7200000),
    description: 'Process payments and subscriptions',
    icon: 'fab fa-stripe',
    color: 'bg-indigo-500'
  },
  {
    id: '5',
    name: 'REST API',
    type: 'api',
    status: 'disconnected',
    lastUsed: new Date(Date.now() - 86400000),
    description: 'Custom REST API endpoint',
    icon: 'fas fa-globe',
    color: 'bg-green-500'
  }
];

export default function ConnectionsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");

  const filteredConnections = mockConnections.filter(connection => {
    const matchesSearch = connection.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         connection.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "all" || connection.status === statusFilter;
    const matchesType = typeFilter === "all" || connection.type === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  const connectionTypes = Array.from(new Set(mockConnections.map(c => c.type)));

  return (
    <div className="p-6 bg-light-grey min-h-full overflow-auto" data-testid="connections-page">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-text-dark mb-2">Connections</h1>
          <p className="text-gray-600">Manage your external service integrations and API connections</p>
        </div>
        <Button 
          className="bg-coral hover:bg-red-600 text-white"
          data-testid="button-add-connection"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Connection
        </Button>
      </div>

      {/* Connection Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card className="border-2 border-gray-200 hover:border-coral hover:shadow-lg transition-all duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Connections</CardTitle>
            <Plug className="h-4 w-4 text-coral" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-text-dark">{mockConnections.length}</div>
            <p className="text-xs text-gray-500 mt-1">
              Across all services
            </p>
          </CardContent>
        </Card>

        <Card className="border-2 border-gray-200 hover:border-green-500 hover:shadow-lg transition-all duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Active Connections</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-text-dark">
              {mockConnections.filter(c => c.status === 'connected').length}
            </div>
            <p className="text-xs text-green-600 mt-1">
              Working properly
            </p>
          </CardContent>
        </Card>

        <Card className="border-2 border-gray-200 hover:border-red-500 hover:shadow-lg transition-all duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Issues</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-text-dark">
              {mockConnections.filter(c => c.status === 'error' || c.status === 'disconnected').length}
            </div>
            <p className="text-xs text-red-600 mt-1">
              Need attention
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search connections..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
                data-testid="input-search-connections"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[160px]" data-testid="select-status-filter">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="connected">Connected</SelectItem>
                <SelectItem value="disconnected">Disconnected</SelectItem>
                <SelectItem value="error">Error</SelectItem>
              </SelectContent>
            </Select>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[160px]" data-testid="select-type-filter">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {connectionTypes.map(type => (
                  <SelectItem key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Add New Connection Templates */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Popular Integrations</CardTitle>
          <CardDescription>Quick setup for commonly used services</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              { name: 'Gmail', icon: 'fas fa-envelope', color: 'bg-red-500', gradient: 'from-red-50 to-white', border: 'border-red-200', hover: 'hover:border-red-500' },
              { name: 'Slack', icon: 'fab fa-slack', color: 'bg-purple-500', gradient: 'from-purple-50 to-white', border: 'border-purple-200', hover: 'hover:border-purple-500' },
              { name: 'Webhook', icon: 'fas fa-globe', color: 'bg-blue-500', gradient: 'from-blue-50 to-white', border: 'border-blue-200', hover: 'hover:border-blue-500' },
              { name: 'Database', icon: 'fas fa-database', color: 'bg-green-500', gradient: 'from-green-50 to-white', border: 'border-green-200', hover: 'hover:border-green-500' }
            ].map((service) => (
              <Card key={service.name} className={`cursor-pointer bg-gradient-to-br ${service.gradient} border-2 ${service.border} ${service.hover} hover:shadow-lg hover:scale-[1.02] transition-all duration-200`}>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className={`w-14 h-14 ${service.color} rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg`}>
                      <i className={`${service.icon} text-white text-lg`}></i>
                    </div>
                    <h3 className="font-semibold text-text-dark mb-2">{service.name}</h3>
                    <p className="text-sm text-gray-600">Connect to {service.name}</p>
                    <div className="mt-3 text-xs font-medium" style={{color: service.color.replace('bg-', '').replace('-500', '')}}>
                      Quick Setup →
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Connections List */}
      <div className="space-y-4">
        {filteredConnections.length === 0 ? (
          <Card>
            <CardContent className="py-12">
              <div className="text-center">
                <Plug className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-medium text-gray-900 mb-2">
                  {searchTerm || statusFilter !== "all" || typeFilter !== "all" ? "No connections found" : "No connections yet"}
                </h3>
                <p className="text-gray-500 mb-6">
                  {searchTerm || statusFilter !== "all" || typeFilter !== "all" 
                    ? "Try adjusting your search or filters" 
                    : "Connect your first external service to get started"}
                </p>
                {!searchTerm && statusFilter === "all" && typeFilter === "all" && (
                  <Button className="bg-coral hover:bg-red-600" data-testid="button-add-first-connection">
                    <Plus className="w-4 h-4 mr-2" />
                    Add First Connection
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredConnections.map((connection) => (
            <Card key={connection.id} className="border-2 border-gray-200 hover:border-gray-300 hover:shadow-lg transition-all duration-200">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className={`w-14 h-14 ${connection.color} rounded-xl flex items-center justify-center shadow-sm`}>
                      <i className={`${connection.icon} text-white text-lg`}></i>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-text-dark hover:text-coral transition-colors cursor-pointer">{connection.name}</h3>
                      <p className="text-gray-500 text-sm">{connection.description}</p>
                      <div className="flex items-center space-x-4 mt-2">
                        <Badge 
                          variant={connection.status === 'connected' ? "default" : 
                                 connection.status === 'error' ? "destructive" : "secondary"}
                          className={
                            connection.status === 'connected' ? "bg-green-100 text-green-800 border-2 border-green-200 hover:bg-green-200 hover:border-green-400 transition-all duration-200" :
                            connection.status === 'error' ? "bg-red-100 text-red-800 border-2 border-red-200 hover:bg-red-200 hover:border-red-400 transition-all duration-200" :
                            "bg-gray-100 text-gray-800 border-2 border-gray-200 hover:bg-gray-200 hover:border-gray-400 transition-all duration-200"
                          }
                        >
                          {connection.status === 'connected' ? 'Connected' : 
                           connection.status === 'error' ? 'Error' : 'Disconnected'}
                        </Badge>
                        <span className="text-xs text-gray-600 capitalize bg-gray-100 border-2 border-gray-200 hover:border-gray-400 hover:bg-gray-200 px-2 py-1 rounded transition-all duration-200">
                          {connection.type}
                        </span>
                        <span className="text-xs text-gray-400">
                          Last used {connection.lastUsed.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {connection.status === 'connected' && (
                      <div className="flex items-center space-x-2 text-green-600 bg-green-50 border-2 border-green-200 hover:border-green-400 px-3 py-1 rounded-lg transition-all duration-200">
                        <CheckCircle className="w-4 h-4" />
                        <span className="text-sm font-medium">Active</span>
                      </div>
                    )}
                    
                    {connection.status === 'error' && (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="border-2 border-red-200 text-red-600 hover:border-red-500 hover:bg-red-50 hover:text-red-700 transition-all duration-200"
                      >
                        Fix Issue
                      </Button>
                    )}
                    
                    {connection.status === 'disconnected' && (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="border-2 border-blue-200 text-blue-600 hover:border-blue-500 hover:bg-blue-50 hover:text-blue-700 transition-all duration-200"
                      >
                        Reconnect
                      </Button>
                    )}
                    
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="border-2 border-gray-200 hover:border-gray-400 hover:bg-gray-50 transition-all duration-200"
                          data-testid={`button-more-${connection.id}`}
                        >
                          <Settings className="w-4 h-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <Key className="w-4 h-4 mr-2" />
                          Update Credentials
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Globe className="w-4 h-4 mr-2" />
                          Test Connection
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Settings className="w-4 h-4 mr-2" />
                          Settings
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-red-600 hover:bg-red-50 focus:bg-red-50 hover:text-red-700 focus:text-red-700">
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