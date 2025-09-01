# FlowForge Python API - Enterprise Automation Platform

## 🎯 Overview

FlowForge is a comprehensive enterprise-grade automation platform inspired by n8n, featuring a React/ReactFlow frontend and a hybrid Python/Node.js backend. This Python API serves as the powerful core engine that executes complex workflows with high performance and reliability.

### ✨ Key Features

- **🔄 Advanced Workflow Engine**: DAG-based execution with parallel processing and error recovery
- **🎯 22+ Built-in Integrations**: HTTP, AI (OpenAI, Claude, Gemini), Email, Data Processing, Storage, Notion, Telegram, Calendar, AI Agent actions
- **🔔 6 Trigger Types**: Webhook, Schedule, File Watch, Notion, Telegram, Calendar event triggers
- **⚡ High Performance**: Async operations, connection pooling, Redis caching, horizontal scaling
- **🔒 Enterprise Security**: JWT authentication, input validation, sandboxed execution, encrypted credentials
- **📊 Comprehensive Monitoring**: Health checks, metrics collection, structured logging, distributed tracing
- **🧪 Extensive Testing**: 1000+ unit tests, integration tests, E2E scenarios with 80%+ coverage
- **📚 Complete Documentation**: API reference, deployment guides, troubleshooting, examples
- **🔧 Production Ready**: Docker support, Kubernetes manifests, load balancing, backup/recovery

### Core Architecture
- **Frontend**: React 18 + TypeScript + ReactFlow for workflow visualization
- **Backend API Gateway**: Node.js with Express + Socket.io for real-time communication
- **Backend Core Engine**: Python with FastAPI for workflow execution, triggers, and actions
- **Database**: PostgreSQL (primary) + Redis (caching/sessions)
- **Authentication**: JWT with Redis session storage
- **File Storage**: S3/MinIO for user files
- **Message Queue**: Celery with Redis broker for Python, Bull/BullMQ for Node.js

### 🚀 Integrations & Actions (22+)

| **Category** | **Actions** | **Description** |
|-------------|-------------|-----------------|
| **🤖 AI** | OpenAI, Claude, Gemini, Structured Output | GPT-4, Claude-3, Gemini integration, AI agent memory |
| **📧 Communication** | Send Email, Parse Email, Telegram Chat | SMTP email, IMAP parsing, Telegram bot integration |
| **📊 Data Processing** | Transform, Filter, Aggregate | JSON/CSV conversion, data filtering, aggregation |
| **💾 Storage** | Google Drive, S3 Upload | Cloud file storage, document management |
| **🌐 Web** | HTTP Request, Webhook Response | REST API calls, webhook handling |
| **📅 Productivity** | Notion Database, Notion Page, Calendar Event | Notion CRUD, Google Calendar integration |
| **🤖 AI Agent** | Memory Management | Conversation memory, context persistence |

### 🎣 Triggers (6 Types)

- **🌐 Webhook**: HTTP webhook triggers with signature verification
- **⏰ Schedule**: Cron-based time triggers with timezone support
- **📁 File Watch**: Filesystem monitoring with pattern matching
- **📝 Notion**: Database item creation/modification triggers
- **💬 Telegram**: Message-based triggers for bots
- **📅 Calendar**: Event-based triggers for scheduling

### 📋 Recent Major Updates

✅ **Complete Integration Suite**: 22 actions across 7 categories
✅ **Advanced Workflow Engine**: DAG execution with parallel processing
✅ **Comprehensive Testing**: 1000+ unit tests, integration & E2E tests
✅ **Production Documentation**: API reference, deployment guides, troubleshooting
✅ **Security Hardening**: JWT auth, input validation, rate limiting
✅ **Monitoring & Observability**: Health checks, metrics, structured logging
✅ **Docker & Kubernetes**: Production-ready containerization
✅ **Real-world Examples**: E-commerce fulfillment, marketing automation

## Critical Project Context

### Project Structure
```
automation-platform/
├── frontend/                 # React + TypeScript + ReactFlow
├── backend/
│   ├── node-service/        # Real-time, WebSocket, API Gateway
│   └── python-service/      # Core engine, triggers, actions, AI
├── shared/                  # Shared types, proto files
└── infrastructure/          # Docker, K8s configs
```

### Key Implementation Decisions
1. **Python** handles ALL business logic: triggers, actions, workflow execution, AI integrations
2. **Node.js** handles real-time communication, authentication, session management, API routing
3. **Frontend** uses ReactFlow for visual workflow building with custom nodes
4. **Security**: JWT tokens with Redis sessions, sandboxed code execution, encrypted credentials
5. **Scalability**: Microservices architecture with message queues, horizontal scaling ready

## Code Style Guidelines

### Python Code Standards
- Use Python 3.11+ with type hints ALWAYS
- Follow PEP 8 strictly
- Use `async/await` for all I/O operations
- Use Pydantic for data validation
- Structure: Class-based for triggers/actions, functional for utilities
- Error handling: Always use try/except with specific exceptions
- Logging: Use structured logging with `loguru` or Python's logging module

```python
# ALWAYS write Python code like this:
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import asyncio
from abc import ABC, abstractmethod

class WorkflowNode(BaseModel):
    """Always include docstrings"""
    id: str = Field(..., description="Unique node identifier")
    type: str = Field(..., pattern="^(trigger|action|operation)$")
    config: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "node_123",
                "type": "action",
                "config": {"key": "value"}
            }
        }

async def execute_node(node: WorkflowNode, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a workflow node.
    
    Args:
        node: The node to execute
        context: Execution context with variables and previous outputs
        
    Returns:
        Dict containing execution results
        
    Raises:
        NodeExecutionError: If node execution fails
    """
    try:
        # Implementation
        pass
    except Exception as e:
        logger.error(f"Node execution failed: {str(e)}", extra={"node_id": node.id})
        raise NodeExecutionError(f"Failed to execute node {node.id}") from e
```

### TypeScript/Node.js Standards
- Use TypeScript 5+ with strict mode
- Prefer interfaces over types for objects
- Use arrow functions for callbacks
- Always handle Promise rejections
- Use Express middleware pattern
- Implement proper error boundaries

```typescript
// ALWAYS write TypeScript code like this:
interface IFlowExecution {
  flowId: string;
  userId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startedAt: Date;
  completedAt?: Date;
  error?: string;
}

class FlowExecutionService {
  private readonly pythonServiceUrl: string;
  private readonly redisClient: Redis;
  
  constructor(deps: ServiceDependencies) {
    this.pythonServiceUrl = deps.pythonServiceUrl;
    this.redisClient = deps.redisClient;
  }
  
  async executeFlow(flowId: string, userId: string): Promise<IFlowExecution> {
    try {
      // Validate user permissions
      await this.validatePermissions(userId, flowId);
      
      // Call Python service
      const response = await axios.post<IFlowExecution>(
        `${this.pythonServiceUrl}/execute`,
        { flowId, userId },
        { timeout: 30000 }
      );
      
      // Emit real-time update
      this.emitUpdate(userId, response.data);
      
      return response.data;
    } catch (error) {
      logger.error('Flow execution failed', { flowId, userId, error });
      throw new FlowExecutionError('Failed to execute flow', error);
    }
  }
}
```

### React/Frontend Standards
- Use functional components with hooks exclusively
- Implement proper error boundaries
- Use React.memo for expensive components
- Custom hooks for business logic
- Zustand or Redux Toolkit for state management
- React Query/TanStack Query for server state

```tsx
// ALWAYS write React code like this:
import { useState, useCallback, useMemo } from 'react';
import { useFlowStore } from '@/stores/flowStore';
import { FlowNode, FlowEdge } from '@/types/flow';

interface FlowCanvasProps {
  flowId: string;
  readonly?: boolean;
  onNodeClick?: (node: FlowNode) => void;
}

export const FlowCanvas: React.FC<FlowCanvasProps> = React.memo(({ 
  flowId, 
  readonly = false,
  onNodeClick 
}) => {
  const { nodes, edges, updateNode, addNode } = useFlowStore();
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  
  const handleNodeChange = useCallback((nodeId: string, data: Partial<FlowNode>) => {
    if (readonly) return;
    
    try {
      updateNode(nodeId, data);
    } catch (error) {
      console.error('Failed to update node:', error);
      toast.error('Failed to update node');
    }
  }, [readonly, updateNode]);
  
  const flowData = useMemo(() => ({
    nodes: nodes.map(transformNode),
    edges: edges.map(transformEdge)
  }), [nodes, edges]);
  
  return (
    <div className="flow-canvas-container">
      <ReactFlow
        nodes={flowData.nodes}
        edges={flowData.edges}
        onNodeClick={onNodeClick}
        // ... other props
      />
    </div>
  );
});

FlowCanvas.displayName = 'FlowCanvas';
```

## Database and API Design Patterns

### Database Conventions
- Use UUID for all primary keys
- Always include created_at, updated_at timestamps
- Soft delete with deleted_at instead of hard delete
- Use JSONB for flexible schema data
- Index foreign keys and frequently queried columns
- Use database transactions for multi-table operations

```sql
-- ALWAYS structure tables like this:
CREATE TABLE flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    flow_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT false,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    
    CONSTRAINT flows_name_length CHECK (char_length(name) >= 3)
);

CREATE INDEX idx_flows_user_id ON flows(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_flows_is_active ON flows(is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_flows_created_at ON flows(created_at DESC);
```

### API Design Patterns
- RESTful endpoints with proper HTTP methods
- Version all APIs (/api/v1/)
- Consistent error responses
- Pagination for list endpoints
- Request validation with middleware
- Rate limiting on all endpoints

```typescript
// API Response Structure
interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  metadata?: {
    timestamp: string;
    requestId: string;
    version: string;
  };
}

// Pagination Structure
interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
}
```

## Security Requirements

### CRITICAL Security Rules
1. **NEVER** store sensitive credentials in code or plain text
2. **ALWAYS** validate and sanitize user input
3. **ALWAYS** use parameterized queries, never string concatenation for SQL
4. **ALWAYS** implement rate limiting on APIs
5. **NEVER** execute user code without sandboxing
6. **ALWAYS** encrypt sensitive data in database (credentials, API keys)
7. **ALWAYS** use HTTPS in production
8. **IMPLEMENT** CORS properly, don't use wildcard in production

### Code Execution Sandboxing
```python
# ALWAYS sandbox user code execution:
import RestrictedPython
from RestrictedPython import compile_restricted, safe_globals
import resource
import signal

def execute_user_code(code: str, context: Dict[str, Any], timeout: int = 5) -> Any:
    """Execute user code in sandboxed environment"""
    
    # Set resource limits
    resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
    resource.setrlimit(resource.RLIMIT_AS, (100 * 1024 * 1024, 100 * 1024 * 1024))  # 100MB memory
    
    # Compile with restrictions
    try:
        byte_code = compile_restricted(code, '<user_code>', 'exec')
    except SyntaxError as e:
        raise CodeExecutionError(f"Syntax error: {e}")
    
    # Limited built-ins
    safe_builtins = {
        'len': len, 'range': range, 'str': str, 'int': int,
        'float': float, 'list': list, 'dict': dict, 'set': set,
        'tuple': tuple, 'bool': bool, 'min': min, 'max': max,
        'sum': sum, 'sorted': sorted, 'enumerate': enumerate
    }
    
    restricted_globals = {
        '__builtins__': safe_builtins,
        '__name__': 'restricted_module',
        '__metaclass__': type,
        '_getattr_': getattr,
    }
    
    restricted_locals = context.copy()
    
    # Execute with timeout
    def timeout_handler(signum, frame):
        raise TimeoutError("Code execution timed out")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        exec(byte_code, restricted_globals, restricted_locals)
        return restricted_locals.get('result')
    finally:
        signal.alarm(0)
```

## Testing Requirements

### Test Coverage Requirements
- Minimum 80% code coverage
- 100% coverage for critical paths (auth, execution engine)
- Integration tests for all API endpoints
- Unit tests for all business logic
- E2E tests for critical user flows

### Test Structure
```python
# ALWAYS write tests like this:
import pytest
from unittest.mock import Mock, patch
from app.core.engine import WorkflowEngine

class TestWorkflowEngine:
    @pytest.fixture
    def engine(self):
        """Provide clean engine instance for each test"""
        return WorkflowEngine()
    
    @pytest.fixture
    def sample_flow(self):
        """Provide sample flow data"""
        return {
            "nodes": [
                {"id": "1", "type": "trigger", "config": {"type": "manual"}},
                {"id": "2", "type": "action", "config": {"type": "http"}}
            ],
            "edges": [{"source": "1", "target": "2"}]
        }
    
    @pytest.mark.asyncio
    async def test_execute_simple_flow(self, engine, sample_flow):
        """Test successful execution of simple flow"""
        # Arrange
        context = ExecutionContext(user_id="user_123")
        
        # Act
        result = await engine.execute_flow(sample_flow, context)
        
        # Assert
        assert result.status == "completed"
        assert len(result.node_outputs) == 2
        
    @pytest.mark.asyncio
    async def test_execute_flow_with_error(self, engine):
        """Test flow execution with error handling"""
        # Test implementation
        pass
```

## Performance Optimization Rules

### Frontend Performance
- Lazy load components with React.lazy()
- Virtualize long lists with react-window
- Memoize expensive computations
- Debounce user input handlers
- Use React.memo for pure components
- Implement proper loading states

### Backend Performance
- Use connection pooling for databases
- Implement caching with Redis
- Use pagination for large datasets
- Batch operations when possible
- Implement circuit breakers for external services
- Use async/await for all I/O operations

### Database Performance
- Add appropriate indexes
- Use EXPLAIN ANALYZE for query optimization
- Implement database connection pooling
- Use read replicas for read-heavy operations
- Batch inserts/updates when possible

## Error Handling Patterns

### Python Error Handling
```python
class BaseError(Exception):
    """Base exception for application"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class NodeExecutionError(BaseError):
    """Raised when node execution fails"""
    pass

class ValidationError(BaseError):
    """Raised when validation fails"""
    pass

# Usage
try:
    result = await execute_node(node, context)
except ValidationError as e:
    logger.warning(f"Validation failed: {e.message}", extra=e.details)
    return {"error": e.message, "code": "VALIDATION_ERROR"}
except NodeExecutionError as e:
    logger.error(f"Node execution failed: {e.message}", extra=e.details)
    return {"error": e.message, "code": "EXECUTION_ERROR"}
except Exception as e:
    logger.exception("Unexpected error occurred")
    return {"error": "Internal server error", "code": "INTERNAL_ERROR"}
```

### TypeScript Error Handling
```typescript
class ApplicationError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
    public details?: any
  ) {
    super(message);
    this.name = this.constructor.name;
  }
}

class ValidationError extends ApplicationError {
  constructor(message: string, details?: any) {
    super(message, 'VALIDATION_ERROR', 400, details);
  }
}

// Global error handler middleware
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  if (err instanceof ApplicationError) {
    return res.status(err.statusCode).json({
      success: false,
      error: {
        code: err.code,
        message: err.message,
        details: err.details
      }
    });
  }
  
  logger.error('Unhandled error:', err);
  return res.status(500).json({
    success: false,
    error: {
      code: 'INTERNAL_ERROR',
      message: 'Internal server error'
    }
  });
});
```

## Specific Implementation Guidelines

### Trigger Implementation Pattern
```python
# ALWAYS implement triggers following this pattern:
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional
import asyncio

class BaseTrigger(ABC):
    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        self.config = config
        self.connection_id = connection_id
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate trigger configuration"""
        pass
        
    @abstractmethod
    async def start(self, callback: Callable) -> None:
        """Start the trigger"""
        pass
        
    async def stop(self) -> None:
        """Stop the trigger"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if trigger can connect to its source"""
        pass
```

### Action Implementation Pattern
```python
# ALWAYS implement actions following this pattern:
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class ActionInput(BaseModel):
    """Define input schema for action"""
    pass

class ActionOutput(BaseModel):
    """Define output schema for action"""
    pass

class BaseAction(ABC):
    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        self.config = config
        self.connection_id = connection_id
        
    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate action configuration"""
        pass
        
    @abstractmethod
    async def execute(self, input_data: ActionInput, context: Dict[str, Any]) -> ActionOutput:
        """Execute the action"""
        pass
        
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if action can connect to its service"""
        pass
        
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for the action"""
        return {
            "input": ActionInput.schema(),
            "output": ActionOutput.schema()
        }
```

### WebSocket Communication Pattern
```typescript
// ALWAYS implement WebSocket communication like this:
import { Server, Socket } from 'socket.io';

interface IWebSocketManager {
  handleConnection(socket: Socket): void;
  emitToUser(userId: string, event: string, data: any): void;
  emitToFlow(flowId: string, event: string, data: any): void;
}

class WebSocketManager implements IWebSocketManager {
  private userSockets: Map<string, Set<string>> = new Map();
  private flowSubscriptions: Map<string, Set<string>> = new Map();
  
  handleConnection(socket: Socket): void {
    socket.on('authenticate', async (token: string) => {
      try {
        const user = await this.validateToken(token);
        socket.data.userId = user.id;
        
        // Track user socket
        if (!this.userSockets.has(user.id)) {
          this.userSockets.set(user.id, new Set());
        }
        this.userSockets.get(user.id)!.add(socket.id);
        
        socket.emit('authenticated', { userId: user.id });
      } catch (error) {
        socket.emit('auth_error', { message: 'Invalid token' });
        socket.disconnect();
      }
    });
    
    socket.on('subscribe_flow', (flowId: string) => {
      if (!this.flowSubscriptions.has(flowId)) {
        this.flowSubscriptions.set(flowId, new Set());
      }
      this.flowSubscriptions.get(flowId)!.add(socket.id);
      socket.join(`flow:${flowId}`);
    });
    
    socket.on('disconnect', () => {
      // Clean up subscriptions
      this.cleanupSocket(socket);
    });
  }
  
  emitToUser(userId: string, event: string, data: any): void {
    const sockets = this.userSockets.get(userId);
    if (sockets) {
      sockets.forEach(socketId => {
        io.to(socketId).emit(event, data);
      });
    }
  }
  
  emitToFlow(flowId: string, event: string, data: any): void {
    io.to(`flow:${flowId}`).emit(event, data);
  }
}
```

## Development Workflow

### Git Commit Messages
Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Code style (formatting, missing semicolons, etc)
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `test:` Tests
- `chore:` Maintenance tasks

Example: `feat(engine): add retry logic for failed nodes`

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No console.logs left
- [ ] Error handling implemented
- [ ] Security considerations addressed
```

## Environment-Specific Rules

### Development Environment
- Use Docker Compose for all services
- Enable hot reloading
- Use verbose logging
- Disable rate limiting
- Use local file storage

### Production Environment
- Use Kubernetes for orchestration
- Implement health checks
- Use structured logging (JSON)
- Enable rate limiting
- Use S3/Cloud storage
- Implement monitoring (Prometheus/Grafana)
- Use Redis for sessions
- Enable CORS with specific origins

## Common Pitfalls to Avoid

1. **NEVER** commit secrets or API keys
2. **NEVER** use any() type in TypeScript without explicit reason
3. **NEVER** use var in JavaScript/TypeScript
4. **NEVER** ignore error handling
5. **NEVER** use synchronous operations in Node.js for I/O
6. **NEVER** trust user input without validation
7. **NEVER** use string concatenation for SQL queries
8. **NEVER** store passwords in plain text
9. **NEVER** use console.log in production code
10. **NEVER** skip writing tests for critical paths

## AI Assistant Instructions

When generating code for this project:

1. **ALWAYS** follow the patterns and conventions defined above
2. **ALWAYS** include proper error handling
3. **ALWAYS** add type hints (Python) or types (TypeScript)
4. **ALWAYS** consider security implications
5. **ALWAYS** write testable code
6. **ALWAYS** include logging for debugging
7. **ALWAYS** validate inputs
8. **PREFER** composition over inheritance
9. **PREFER** async/await over callbacks
10. **PREFER** specific errors over generic ones

## Quick Reference

### Service URLs
- Frontend: http://localhost:3000
- Node.js API: http://localhost:3001
- Python API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Key Libraries Versions
- React: 18.x
- Node.js: 20.x
- Python: 3.11+
- FastAPI: 0.100+
- Express: 4.x
- Socket.io: 4.x
- PostgreSQL: 15+
- Redis: 7+

### NPM Scripts (Node.js)
```json
{
  "scripts": {
    "dev": "nodemon --exec ts-node src/app.ts",
    "build": "tsc",
    "start": "node dist/app.js",
    "test": "jest",
    "lint": "eslint . --ext .ts",
    "format": "prettier --write ."
  }
}
```

### Python Commands
```bash
# Development
uvicorn app.main:app --reload --port 8000

# Testing
pytest tests/ -v --cov=app

# Linting
black app/ tests/
flake8 app/ tests/
mypy app/

# Production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Remember

This is a production-grade system. Every piece of code should be:
- **Secure**: Validate inputs, handle errors, sanitize outputs
- **Scalable**: Use async operations, implement caching, design for horizontal scaling
- **Maintainable**: Clear naming, proper documentation, follow patterns
- **Testable**: Dependency injection, pure functions where possible
- **Observable**: Proper logging, metrics, health checks

When in doubt, prioritize security and reliability over features.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 14+
- Redis 7+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/flowforge/python-api.git
cd python-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# For systems with Rust compilation issues
pip install -r requirements-no-rust.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the application
python main.py
```

### Your First Workflow

```python
from flowforge import FlowForgeClient

# Initialize client
client = FlowForgeClient(api_key="your-api-key")

# Create a simple workflow
workflow = {
    "name": "Hello World",
    "nodes": [
        {
            "id": "webhook",
            "type": "trigger",
            "trigger_type": "webhook",
            "config": {"webhook_id": "hello-world"}
        },
        {
            "id": "http-action",
            "type": "action",
            "action_type": "http",
            "config": {"method": "GET", "url": "https://httpbin.org/json"}
        }
    ],
    "connections": [{"from": "webhook", "to": "http-action"}]
}

# Execute workflow
result = client.flows.execute(flow_data=workflow)
print(f"Workflow executed: {result['execution_id']}")
```

## 📚 Documentation

| **Guide** | **Description** | **Link** |
|-----------|-----------------|----------|
| **🚀 Getting Started** | Complete setup and first workflow | [Guide](./docs/guides/getting-started.md) |
| **📖 API Reference** | Comprehensive endpoint documentation | [API Docs](./docs/api/API.md) |
| **🏗️ Architecture** | System design and patterns | [Architecture](./docs/guides/architecture.md) |
| **🚢 Deployment** | Production deployment guides | [Deployment](./docs/guides/deployment.md) |
| **🔧 Troubleshooting** | Common issues and solutions | [Troubleshooting](./docs/guides/troubleshooting.md) |
| **💡 Examples** | Real-world workflow examples | [Examples](./docs/examples/) |

### Key Documentation Sections

- **🔰 [Hello World Example](./docs/examples/hello-world/)** - Your first FlowForge workflow
- **🛒 [E-commerce Fulfillment](./docs/examples/ecommerce/order-fulfillment/)** - Complete order processing workflow
- **📧 [Email Automation](./docs/examples/email-automation/)** - Marketing and transactional emails
- **🤖 [AI Integration](./docs/examples/ai-integration/)** - OpenAI, Claude, Gemini workflows
- **📱 [API Orchestration](./docs/examples/api-orchestration/)** - Complex API chaining patterns

## 🧪 Testing

### Run Test Suite

```bash
# Run all tests
pytest tests/ -v --cov=app --cov-report=html

# Run specific test categories
pytest tests/unit/ -v          # Unit tests
pytest tests/integration/ -v   # Integration tests
pytest tests/e2e/ -v          # End-to-end tests

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run performance tests
pytest tests/ -k "performance" -v
```

### Test Coverage

- **Unit Tests**: 1000+ tests covering all components
- **Integration Tests**: API endpoint testing with mocked services
- **E2E Tests**: Complete workflow execution scenarios
- **Performance Tests**: Load testing and benchmarking
- **Security Tests**: Authentication and authorization testing

## 🏗️ Development

### Project Structure

```
flowforge-python-api/
├── app/
│   ├── core/           # Workflow engine core
│   │   ├── engine.py   # DAG execution engine
│   │   ├── executor.py # Node execution handler
│   │   ├── context.py  # Execution context
│   │   └── scheduler.py # Task scheduler
│   ├── actions/        # 22+ Action implementations
│   │   ├── ai/         # OpenAI, Claude, Gemini
│   │   ├── http/       # HTTP request/response
│   │   ├── email/      # Send/parse email
│   │   ├── storage/    # Google Drive, S3
│   │   └── ...
│   ├── triggers/       # 6 Trigger implementations
│   │   ├── webhook.py  # HTTP webhook triggers
│   │   ├── schedule.py # Cron-based triggers
│   │   └── ...
│   ├── api/            # FastAPI routes & middleware
│   │   ├── routes/     # API endpoints
│   │   └── dependencies.py # Service dependencies
│   └── models/         # Pydantic models
├── tests/              # Comprehensive test suite
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   └── e2e/           # End-to-end tests
├── docs/              # Complete documentation
│   ├── api/           # API reference
│   ├── guides/        # User guides
│   └── examples/      # Workflow examples
├── scripts/           # Utility scripts
├── docker/            # Docker configurations
└── k8s/              # Kubernetes manifests
```

### Development Commands

```bash
# Start development server with hot reload
uvicorn main:app --reload --port 8000

# Run linting and formatting
black app/ tests/
flake8 app/ tests/
mypy app/

# Generate API documentation
python scripts/generate_api_docs.py

# Run security checks
bandit -r app/
safety check

# Performance profiling
python -m cProfile -o profile.prof main.py
snakeviz profile.prof
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/python-api.git`
3. Create feature branch: `git checkout -b feature/amazing-feature`
4. Install dependencies: `pip install -r requirements.txt`
5. Run tests: `pytest tests/`
6. Make your changes
7. Run tests again: `pytest tests/`
8. Commit changes: `git commit -m "feat: add amazing feature"`
9. Push to branch: `git push origin feature/amazing-feature`
10. Create Pull Request

### Code Quality Standards

- **Python**: PEP 8, type hints, async/await patterns
- **Testing**: 80%+ coverage, comprehensive test scenarios
- **Documentation**: Inline docs, API documentation, examples
- **Security**: Input validation, secure defaults, audit logging
- **Performance**: Async operations, connection pooling, caching

## 📊 Performance Benchmarks

### Workflow Execution Performance

| **Metric** | **Value** | **Description** |
|------------|-----------|-----------------|
| **Simple Workflow** | <100ms | Single HTTP request workflow |
| **Complex Workflow** | <500ms | Multi-step workflow with 10+ nodes |
| **Parallel Execution** | <200ms | 5 parallel actions |
| **Database Operations** | <50ms | Single database query |
| **External API Calls** | <300ms | Third-party API integration |

### Scalability Metrics

- **Concurrent Workflows**: 1000+ simultaneous executions
- **Throughput**: 10,000+ actions per minute
- **Memory Usage**: <200MB per worker process
- **Database Connections**: 50-100 active connections
- **Redis Operations**: 50,000+ operations per second

## 🔒 Security

### Security Features

- **JWT Authentication**: Secure token-based authentication
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: Configurable rate limits per endpoint
- **Audit Logging**: Complete audit trail of all operations
- **Data Encryption**: Encrypted sensitive data storage
- **CORS Protection**: Configurable cross-origin policies
- **HTTPS Enforcement**: SSL/TLS encryption in production

### Security Best Practices

1. **API Keys**: Rotate regularly, use different keys per environment
2. **Input Sanitization**: All user inputs are validated and sanitized
3. **Error Handling**: Sensitive information never exposed in errors
4. **Logging**: Sensitive data masked in logs
5. **Dependencies**: Regular security updates and vulnerability scanning
6. **Access Control**: Role-based permissions and resource isolation

## 📈 Monitoring & Metrics

### Health Check Endpoints

```bash
# System health
curl http://localhost:8000/health

# Detailed health with service status
curl http://localhost:8000/health/detailed

# Metrics endpoint (Prometheus format)
curl http://localhost:8000/metrics
```

### Key Metrics

- **Workflow Success Rate**: Percentage of successful executions
- **Average Execution Time**: Mean time for workflow completion
- **Error Rate**: Frequency of execution failures
- **Resource Usage**: CPU, memory, and database connection usage
- **API Latency**: Response times for different endpoints
- **Queue Depth**: Number of pending workflow executions

## 🐳 Docker & Containerization

### Docker Commands

```bash
# Build production image
docker build -t flowforge-api .

# Run with environment variables
docker run -p 8000:8000 \
  -e API_KEY=your-key \
  -e DATABASE_URL=postgres://... \
  -e REDIS_URL=redis://... \
  flowforge-api

# Run with Docker Compose
docker-compose up -d

# Scale services
docker-compose up -d --scale flowforge-api=3
```

### Kubernetes Deployment

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Check pod status
kubectl get pods

# View logs
kubectl logs -f deployment/flowforge-api

# Scale deployment
kubectl scale deployment flowforge-api --replicas=5
```

## 📞 Support & Community

- **📚 Documentation**: [docs.flowforge.com](https://docs.flowforge.com)
- **🐛 Issue Tracking**: [GitHub Issues](https://github.com/flowforge/python-api/issues)
- **💬 Community**: [GitHub Discussions](https://github.com/flowforge/python-api/discussions)
- **📧 Email**: support@flowforge.com
- **🗣️ Discord**: [FlowForge Community](https://discord.gg/flowforge)

## 📋 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

- **n8n**: Inspiration for the workflow automation concept
- **FastAPI**: High-performance Python web framework
- **React Flow**: Excellent workflow visualization library
- **Open Source Community**: Contributors and maintainers

---

## 🎯 What's Next?

We're continuously improving FlowForge with new features and integrations. Upcoming enhancements include:

- **Advanced AI Actions**: More LLM integrations and AI agent capabilities
- **Real-time Collaboration**: Multi-user workflow editing
- **Advanced Scheduling**: Complex recurring patterns and calendar integration
- **Workflow Templates**: Pre-built templates for common use cases
- **Advanced Analytics**: Detailed workflow performance insights
- **Mobile SDK**: iOS and Android SDKs for mobile automation

**Ready to get started?** Check out our [Getting Started Guide](./docs/guides/getting-started.md) and create your first workflow! 🚀