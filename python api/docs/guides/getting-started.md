# Getting Started with FlowForge Python API

Welcome to FlowForge Python API! This guide will walk you through everything you need to know to get started with building powerful automation workflows.

## Table of Contents

1. [What is FlowForge?](#what-is-flowforge)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Your First API Call](#your-first-api-call)
5. [Understanding Workflows](#understanding-workflows)
6. [Building Your First Workflow](#building-your-first-workflow)
7. [Working with Triggers](#working-with-triggers)
8. [Advanced Features](#advanced-features)
9. [Best Practices](#best-practices)
10. [Next Steps](#next-steps)

## What is FlowForge?

FlowForge is an enterprise-grade automation platform that allows you to build complex workflows through a visual interface. The Python API serves as the powerful backend engine that executes these workflows with high performance and reliability.

### Key Capabilities

- **🔄 Visual Workflow Builder**: Drag-and-drop interface for building workflows
- **⚡ High-Performance Execution**: Async processing with parallel execution
- **🔗 20+ Built-in Integrations**: Connect to popular services out-of-the-box
- **🔔 Smart Triggers**: React to events from webhooks, schedules, files, and more
- **📊 Real-time Monitoring**: Track execution status and performance metrics
- **🔒 Enterprise Security**: Built-in authentication, validation, and audit logging

### Use Cases

- **API Orchestration**: Chain multiple API calls with conditional logic
- **Data Processing Pipelines**: ETL workflows with transformation and validation
- **Notification Systems**: Automated alerts based on events or schedules
- **Integration Workflows**: Connect disparate systems and services
- **Business Process Automation**: Streamline repetitive business processes

## Prerequisites

Before getting started, ensure you have:

### System Requirements

- **Python**: 3.8 or higher
- **RAM**: Minimum 2GB, recommended 4GB+
- **Disk Space**: 500MB for installation + space for logs and data
- **Network**: Stable internet connection for external API calls

### Development Environment

- **Operating System**: Linux, macOS, or Windows
- **Git**: For cloning repositories and version control
- **Text Editor/IDE**: VS Code, PyCharm, or your preferred editor
- **Terminal/Command Line**: For running commands

### API Access

- **API Key**: You'll need an API key to authenticate requests
- **Base URL**: Know which environment you're targeting:
  - Development: `http://localhost:8000`
  - Staging: `https://api-staging.flowforge.com`
  - Production: `https://api.flowforge.com`

## Installation

### Option 1: Using pip (Recommended)

```bash
# Create a virtual environment
python -m venv flowforge-env
source flowforge-env/bin/activate  # On Windows: flowforge-env\Scripts\activate

# Install the SDK
pip install flowforge-sdk

# Or install from source
git clone https://github.com/flowforge/python-api.git
cd python-api
pip install -e .
```

### Option 2: Docker Installation

```bash
# Pull the official Docker image
docker pull flowforge/python-api:latest

# Run the container
docker run -p 8000:8000 \
  -e API_KEY=your-api-key \
  -e DATABASE_URL=postgresql://user:pass@localhost/db \
  flowforge/python-api:latest
```

### Option 3: Local Development Setup

```bash
# Clone the repository
git clone https://github.com/flowforge/python-api.git
cd python-api

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the development server
python main.py
```

### Verifying Installation

Test your installation by checking the health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Your First API Call

Let's start with a simple API call to verify everything is working.

### Using Python SDK

```python
from flowforge import FlowForgeClient

# Initialize the client
client = FlowForgeClient(
    api_key="your-api-key",
    base_url="http://localhost:8000"
)

# Make your first API call - get available action types
actions = client.actions.get_types()
print("Available actions:", actions.keys())
```

### Using cURL

```bash
# Get API information
curl -X GET "http://localhost:8000/api/v1/info" \
  -H "Authorization: Bearer your-api-key"
```

### Using JavaScript/Node.js

```javascript
const { FlowForgeClient } = require('flowforge-sdk');

const client = new FlowForgeClient({
  apiKey: 'your-api-key',
  baseURL: 'http://localhost:8000'
});

// Get system information
const info = await client.getInfo();
console.log('FlowForge version:', info.version);
```

## Understanding Workflows

### Workflow Concepts

A workflow in FlowForge is composed of:

1. **Nodes**: Individual steps in your workflow
2. **Connections**: Links between nodes defining execution flow
3. **Triggers**: Events that start workflow execution
4. **Actions**: Operations performed at each step
5. **Data Flow**: Information passed between nodes

### Node Types

```json
{
  "nodes": [
    {
      "id": "webhook-trigger",
      "type": "trigger",
      "trigger_type": "webhook",
      "config": {
        "webhook_id": "user-signup"
      }
    },
    {
      "id": "validate-data",
      "type": "action",
      "action_type": "data_transform",
      "config": {
        "transform_type": "json_to_object"
      }
    }
  ]
}
```

### Execution Flow

```mermaid
graph LR
    A[Trigger] --> B[Action 1]
    B --> C[Action 2]
    C --> D{Condition}
    D -->|True| E[Action 3]
    D -->|False| F[Action 4]
    E --> G[End]
    F --> G
```

## Building Your First Workflow

Let's create a simple workflow that processes user registration data.

### Step 1: Define the Workflow Structure

```python
from flowforge import FlowForgeClient

client = FlowForgeClient(api_key="your-api-key")

# Define the workflow
workflow = {
    "name": "User Registration Processor",
    "description": "Process new user registrations with validation and email",
    "nodes": [
        {
            "id": "webhook-trigger",
            "type": "trigger",
            "trigger_type": "webhook",
            "config": {
                "webhook_id": "user-registration",
                "secret": "webhook-secret-key"
            }
        },
        {
            "id": "validate-user",
            "type": "action",
            "action_type": "http",
            "config": {
                "method": "POST",
                "url": "https://api.myapp.com/validate-user",
                "headers": {
                    "Authorization": "Bearer internal-api-key",
                    "Content-Type": "application/json"
                }
            },
            "dependencies": ["webhook-trigger"]
        },
        {
            "id": "send-welcome-email",
            "type": "action",
            "action_type": "send_email",
            "config": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "noreply@mycompany.com",
                "password": "app-password",
                "use_tls": True
            },
            "dependencies": ["validate-user"]
        }
    ],
    "connections": [
        {
            "from": "webhook-trigger",
            "to": "validate-user"
        },
        {
            "from": "validate-user",
            "to": "send-welcome-email",
            "condition": "result.success == true"
        }
    ]
}
```

### Step 2: Execute the Workflow

```python
# Execute the workflow
result = client.flows.execute(
    flow_data=workflow,
    input_variables={
        "user_email": "john@example.com",
        "user_name": "John Doe"
    }
)

print(f"Workflow execution started: {result['execution_id']}")

# Monitor execution
status = client.flows.get_execution_status(result["execution_id"])
print(f"Status: {status['status']}")

# Wait for completion (in production, you'd use webhooks)
import time
while status["status"] == "running":
    time.sleep(2)
    status = client.flows.get_execution_status(result["execution_id"])

print(f"Final status: {status['status']}")
print(f"Duration: {status['duration']:.2f}s")
```

### Step 3: Handle the Webhook

Set up a webhook endpoint to receive the workflow trigger:

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

def verify_signature(payload, signature, secret):
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

@app.route('/webhooks/user-registration', methods=['POST'])
def user_registration_webhook():
    payload = request.get_data()
    signature = request.headers.get('X-Signature')

    # Verify webhook signature
    if not verify_signature(payload, signature, 'webhook-secret-key'):
        return jsonify({'error': 'Invalid signature'}), 401

    data = request.get_json()

    # Execute workflow with webhook data
    client.flows.execute(
        flow_data=workflow,
        input_variables={
            "user_email": data["email"],
            "user_name": data["name"],
            "user_id": data["id"]
        }
    )

    return jsonify({'status': 'accepted'}), 200

if __name__ == '__main__':
    app.run(port=5000)
```

## Working with Triggers

### Webhook Triggers

Webhooks allow external services to trigger your workflows.

```python
# Create a webhook trigger
webhook_trigger = client.triggers.create(
    trigger_type="webhook",
    config={
        "webhook_id": "order-processing",
        "secret": "secure-webhook-secret",
        "validate_signature": True,
        "allowed_ips": ["192.168.1.0/24"]
    },
    flow_id="flow-order-processing"
)

print(f"Webhook URL: {webhook_trigger['webhook_url']}")

# Test the webhook
test_result = client.triggers.test(
    trigger_type="webhook",
    config={
        "webhook_id": "order-processing",
        "secret": "secure-webhook-secret"
    }
)

print(f"Test successful: {test_result['success']}")
```

### Schedule Triggers

Execute workflows on a schedule using cron expressions.

```python
# Create a scheduled trigger (runs every day at 9 AM)
schedule_trigger = client.triggers.create(
    trigger_type="schedule",
    config={
        "schedule_type": "cron",
        "cron_expression": "0 9 * * *",  # Every day at 9:00 AM
        "timezone": "America/New_York",
        "description": "Daily report generation"
    },
    flow_id="flow-daily-reports"
)

# Create an interval trigger (runs every 30 minutes)
interval_trigger = client.triggers.create(
    trigger_type="schedule",
    config={
        "schedule_type": "interval",
        "interval_seconds": 1800,  # 30 minutes
        "description": "Health check monitoring"
    },
    flow_id="flow-health-checks"
)
```

### File Watch Triggers

Monitor file system changes and trigger workflows.

```python
# Create a file watch trigger
file_trigger = client.triggers.create(
    trigger_type="file_watch",
    config={
        "watch_path": "/var/data/uploads",
        "file_pattern": "*.csv",
        "watch_events": ["created", "modified"],
        "recursive": True,
        "ignore_patterns": ["*.tmp", "*.log"]
    },
    flow_id="flow-data-processing"
)
```

## Advanced Features

### Conditional Logic

Add conditional branching to your workflows.

```python
workflow_with_conditions = {
    "nodes": [
        {
            "id": "check-payment",
            "type": "action",
            "action_type": "http",
            "config": {"method": "GET", "url": "https://api.payment.com/status"}
        },
        {
            "id": "process-success",
            "type": "action",
            "action_type": "data_transform",
            "config": {"transform_type": "extract_fields"}
        },
        {
            "id": "process-failure",
            "type": "action",
            "action_type": "send_email",
            "config": {"subject": "Payment Failed", "template": "payment-failed"}
        }
    ],
    "connections": [
        {
            "from": "check-payment",
            "to": "process-success",
            "condition": "result.status == 'completed'"
        },
        {
            "from": "check-payment",
            "to": "process-failure",
            "condition": "result.status == 'failed'"
        }
    ]
}
```

### Error Handling

Implement robust error handling in your workflows.

```python
workflow_with_error_handling = {
    "nodes": [
        {
            "id": "api-call",
            "type": "action",
            "action_type": "http",
            "config": {
                "method": "POST",
                "url": "https://api.external.com/process",
                "timeout": 30,
                "retry_count": 3,
                "retry_delay": 5
            }
        },
        {
            "id": "success-handler",
            "type": "action",
            "action_type": "data_transform"
        },
        {
            "id": "error-handler",
            "type": "action",
            "action_type": "send_email",
            "config": {
                "subject": "Workflow Error Alert",
                "template": "error-notification"
            }
        }
    ],
    "connections": [
        {
            "from": "api-call",
            "to": "success-handler",
            "condition": "result.success == true"
        },
        {
            "from": "api-call",
            "to": "error-handler",
            "condition": "result.success == false"
        }
    ]
}
```

### Parallel Execution

Execute multiple actions in parallel for better performance.

```python
parallel_workflow = {
    "nodes": [
        {
            "id": "validate-user",
            "type": "action",
            "action_type": "http",
            "config": {"method": "POST", "url": "https://api.auth.com/validate"}
        },
        {
            "id": "check-inventory",
            "type": "action",
            "action_type": "http",
            "config": {"method": "GET", "url": "https://api.inventory.com/check"}
        },
        {
            "id": "calculate-pricing",
            "type": "action",
            "action_type": "data_transform",
            "config": {"transform_type": "calculate_total"}
        },
        {
            "id": "process-payment",
            "type": "action",
            "action_type": "http",
            "config": {"method": "POST", "url": "https://api.payment.com/charge"}
        }
    ],
    "connections": [
        # Parallel branches
        {"from": "validate-user", "to": "process-payment"},
        {"from": "check-inventory", "to": "calculate-pricing"},
        {"from": "calculate-pricing", "to": "process-payment"}
    ]
}
```

## Best Practices

### Performance Optimization

1. **Use Parallel Execution**: Run independent actions in parallel
2. **Implement Caching**: Cache frequently accessed data
3. **Batch Operations**: Group similar operations together
4. **Connection Pooling**: Reuse connections to external services
5. **Resource Limits**: Set appropriate timeouts and limits

### Error Handling

1. **Graceful Degradation**: Handle service failures gracefully
2. **Retry Logic**: Implement exponential backoff for retries
3. **Circuit Breakers**: Prevent cascade failures
4. **Monitoring**: Monitor error rates and patterns
5. **Fallbacks**: Provide fallback mechanisms for critical services

### Security

1. **Input Validation**: Always validate and sanitize inputs
2. **API Key Management**: Rotate keys regularly
3. **Webhook Security**: Verify webhook signatures
4. **Rate Limiting**: Implement appropriate rate limits
5. **Audit Logging**: Log all sensitive operations

### Monitoring

1. **Health Checks**: Implement comprehensive health checks
2. **Metrics Collection**: Collect relevant metrics
3. **Alerting**: Set up alerts for critical issues
4. **Logging**: Use structured logging
5. **Tracing**: Implement distributed tracing

## Next Steps

Now that you have the basics down, here are some next steps:

### 1. Explore Advanced Actions

```python
# AI-powered actions
ai_workflow = {
    "nodes": [
        {
            "id": "analyze-sentiment",
            "type": "action",
            "action_type": "openai",
            "config": {
                "model": "gpt-4",
                "system_prompt": "Analyze the sentiment of the following text and return a JSON response with 'sentiment' (positive/negative/neutral) and 'confidence' (0-1)."
            }
        }
    ]
}

# Database operations
db_workflow = {
    "nodes": [
        {
            "id": "query-database",
            "type": "action",
            "action_type": "notion_database",
            "config": {
                "database_id": "your-database-id",
                "api_key": "your-notion-api-key",
                "filter": {"property": "Status", "select": {"equals": "Active"}}
            }
        }
    ]
}
```

### 2. Learn About Integrations

Explore our extensive library of integrations:

- **AI Services**: OpenAI, Claude, Gemini
- **Communication**: Email (SMTP), Telegram, Slack
- **Productivity**: Notion, Google Calendar, Google Drive
- **Storage**: AWS S3, Google Cloud Storage
- **Databases**: PostgreSQL, MongoDB, Redis
- **APIs**: REST APIs, GraphQL, Webhooks

### 3. Build Complex Workflows

Combine multiple services into sophisticated automation:

```python
# E-commerce order processing workflow
ecommerce_workflow = {
    "description": "Complete order processing with inventory, payment, and shipping",
    "nodes": [
        {"id": "validate-order", "type": "action", "action_type": "http"},
        {"id": "check-inventory", "type": "action", "action_type": "http"},
        {"id": "process-payment", "type": "action", "action_type": "http"},
        {"id": "update-database", "type": "action", "action_type": "data_transform"},
        {"id": "send-confirmation", "type": "action", "action_type": "send_email"},
        {"id": "create-shipping", "type": "action", "action_type": "http"}
    ],
    "connections": [
        {"from": "validate-order", "to": "check-inventory"},
        {"from": "check-inventory", "to": "process-payment"},
        {"from": "process-payment", "to": "update-database"},
        {"from": "update-database", "to": "send-confirmation"},
        {"from": "send-confirmation", "to": "create-shipping"}
    ]
}
```

### 4. Set Up Monitoring and Alerting

```python
# Workflow monitoring
monitoring_workflow = {
    "nodes": [
        {
            "id": "check-system-health",
            "type": "action",
            "action_type": "http",
            "config": {"method": "GET", "url": "https://api.flowforge.com/health"}
        },
        {
            "id": "analyze-metrics",
            "type": "action",
            "action_type": "data_transform",
            "config": {"transform_type": "extract_metrics"}
        },
        {
            "id": "send-alert",
            "type": "action",
            "action_type": "send_email",
            "config": {"subject": "System Alert", "template": "alert-template"}
        }
    ],
    "connections": [
        {"from": "check-system-health", "to": "analyze-metrics"},
        {"from": "analyze-metrics", "to": "send-alert", "condition": "result.alert_required == true"}
    ]
}
```

### 5. Join the Community

- **Documentation**: Explore our comprehensive API docs
- **GitHub**: Check out examples and contribute to the project
- **Discord**: Join our community for support and discussions
- **Blog**: Read about best practices and new features

## Troubleshooting

### Common Issues

1. **API Key Issues**
   ```python
   # Verify your API key
   try:
       client = FlowForgeClient(api_key="your-key")
       info = client.get_info()
       print("API connection successful!")
   except Exception as e:
       print(f"API connection failed: {e}")
   ```

2. **Workflow Execution Errors**
   ```python
   # Check execution status
   status = client.flows.get_execution_status("execution-id")
   if status["status"] == "error":
       print(f"Error: {status['error_message']}")
       # Check individual node statuses
       for node in status["executed_nodes"]:
           if node["status"] == "error":
               print(f"Node {node['node_id']} failed: {node['error']}")
   ```

3. **Webhook Issues**
   ```python
   # Test webhook configuration
   test_result = client.triggers.test(
       trigger_type="webhook",
       config={"webhook_id": "your-webhook-id"}
   )
   print(f"Webhook test: {test_result}")
   ```

---

🎉 **Congratulations!** You've completed the FlowForge Python API getting started guide. You're now ready to build powerful automation workflows. Remember to check our [API Reference](../api/API.md) for detailed documentation and our [Examples](../examples/) directory for more sample workflows.

Happy automating! 🚀

