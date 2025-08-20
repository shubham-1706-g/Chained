export interface NodeType {
  id: string;
  name: string;
  description: string;
  category: 'trigger' | 'action' | 'transform';
  icon: string;
  color: string;
  config?: Record<string, any>;
}

export const nodeTypes: NodeType[] = [
  {
    id: 'webhook',
    name: 'Webhook',
    description: 'Listens for HTTP requests',
    category: 'trigger',
    icon: 'fas fa-satellite-dish',
    color: 'bg-green-500',
    config: {
      method: 'POST',
      path: '/webhook/new'
    }
  },
  {
    id: 'schedule',
    name: 'Schedule',
    description: 'Triggers on a schedule',
    category: 'trigger',
    icon: 'fas fa-clock',
    color: 'bg-blue-500',
    config: {
      cron: '0 0 * * *'
    }
  },
  {
    id: 'http-request',
    name: 'HTTP Request',
    description: 'Make HTTP API calls',
    category: 'action',
    icon: 'fas fa-globe',
    color: 'bg-purple-500',
    config: {
      method: 'GET',
      url: ''
    }
  },
  {
    id: 'email',
    name: 'Send Email',
    description: 'Send email notifications',
    category: 'action',
    icon: 'fas fa-envelope',
    color: 'bg-red-500',
    config: {
      to: '',
      subject: '',
      body: ''
    }
  },
  {
    id: 'database',
    name: 'Database',
    description: 'Database operations',
    category: 'action',
    icon: 'fas fa-database',
    color: 'bg-orange-500',
    config: {
      operation: 'SELECT',
      table: ''
    }
  },
  {
    id: 'filter',
    name: 'Filter',
    description: 'Filter and validate data',
    category: 'transform',
    icon: 'fas fa-filter',
    color: 'bg-yellow-500',
    config: {
      condition: ''
    }
  },
  {
    id: 'transform',
    name: 'Transform',
    description: 'Transform data structure',
    category: 'transform',
    icon: 'fas fa-magic',
    color: 'bg-indigo-500',
    config: {
      mapping: {}
    }
  }
];

export interface ExecutionStatus {
  status: 'idle' | 'running' | 'paused' | 'stopped' | 'completed' | 'error';
  lastExecution?: Date;
  message?: string;
}
