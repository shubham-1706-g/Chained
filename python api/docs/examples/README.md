# FlowForge Workflow Examples

This directory contains comprehensive examples of FlowForge workflows for various business domains and use cases. Each example includes:

- **Complete workflow definitions** with all nodes and connections
- **Configuration details** for each action and trigger
- **Real-world scenarios** with practical applications
- **Implementation notes** and best practices
- **Code samples** in multiple programming languages

## Table of Contents

### Business Domains

1. **[E-commerce](./ecommerce/)** - Order processing, inventory management, customer notifications
2. **[Customer Support](./support/)** - Ticket routing, automated responses, escalation workflows
3. **[Marketing](./marketing/)** - Email campaigns, social media automation, lead nurturing
4. **[HR & Recruitment](./hr/)** - Job applications, onboarding, employee communications
5. **[Finance](./finance/)** - Invoice processing, payment reminders, financial reporting
6. **[Healthcare](./healthcare/)** - Appointment scheduling, patient communications, compliance
7. **[Education](./education/)** - Course enrollment, grading automation, student notifications

### Technical Examples

8. **[API Orchestration](./api-orchestration/)** - Complex API chaining and data transformation
9. **[Data Processing](./data-processing/)** - ETL pipelines, data validation, reporting
10. **[Integration Workflows](./integrations/)** - Connecting multiple SaaS platforms
11. **[Scheduled Tasks](./scheduled-tasks/)** - Time-based automation and maintenance
12. **[Error Handling](./error-handling/)** - Robust error handling and recovery patterns

### Quick Start Examples

13. **[Hello World](./hello-world/)** - Your first FlowForge workflow
14. **[Webhook Processing](./webhook-processing/)** - Basic webhook handling
15. **[Email Automation](./email-automation/)** - Simple email workflows

## How to Use These Examples

### 1. Choose Your Domain

Select an example that matches your business needs:

```bash
# E-commerce order processing
cd examples/ecommerce/order-fulfillment

# Customer support ticket handling
cd examples/support/ticket-routing

# Marketing email campaigns
cd examples/marketing/lead-nurturing
```

### 2. Review the Workflow Structure

Each example contains:

- **`workflow.json`** - Complete workflow definition
- **`README.md`** - Detailed explanation and setup instructions
- **`config.json`** - Configuration templates
- **`test-data.json`** - Sample input data for testing

### 3. Customize for Your Needs

```json
{
  "name": "My Custom Workflow",
  "description": "Adapted from FlowForge example",
  "nodes": [
    {
      "id": "custom-trigger",
      "type": "trigger",
      "trigger_type": "webhook",
      "config": {
        "webhook_id": "my-custom-webhook",
        "secret": "your-webhook-secret"
      }
    }
  ],
  "connections": []
}
```

### 4. Test and Deploy

```bash
# Test the workflow
curl -X POST "http://localhost:8000/api/v1/flows/validate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d @workflow.json

# Deploy the workflow
curl -X POST "http://localhost:8000/api/v1/flows/execute" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d @workflow.json
```

## Example Categories

### 🚀 Getting Started

| Example | Description | Difficulty |
|---------|-------------|------------|
| [Hello World](./hello-world/) | Basic workflow with HTTP request | Beginner |
| [Webhook Handler](./webhook-processing/) | Process incoming webhooks | Beginner |
| [Email Notification](./email-automation/) | Send automated emails | Beginner |

### 💼 Business Workflows

| Example | Description | Use Case |
|---------|-------------|----------|
| [Order Fulfillment](./ecommerce/order-fulfillment/) | Complete e-commerce order processing | Retail |
| [Customer Onboarding](./hr/employee-onboarding/) | New employee setup and notifications | HR |
| [Invoice Processing](./finance/invoice-automation/) | Automated invoice handling | Finance |
| [Lead Nurturing](./marketing/lead-nurturing/) | Marketing automation for leads | Marketing |

### 🔧 Technical Workflows

| Example | Description | Purpose |
|---------|-------------|----------|
| [API Orchestration](./api-orchestration/) | Chain multiple API calls | Integration |
| [Data Pipeline](./data-processing/etl-pipeline/) | Extract, transform, load data | Data Engineering |
| [Error Recovery](./error-handling/retry-logic/) | Robust error handling patterns | Reliability |
| [Scheduled Maintenance](./scheduled-tasks/database-backup/) | Automated maintenance tasks | Operations |

## Workflow Patterns

### Sequential Processing

```json
{
  "name": "Sequential Workflow",
  "nodes": [
    {"id": "step1", "type": "action", "action_type": "http"},
    {"id": "step2", "type": "action", "action_type": "data_transform"},
    {"id": "step3", "type": "action", "action_type": "send_email"}
  ],
  "connections": [
    {"from": "step1", "to": "step2"},
    {"from": "step2", "to": "step3"}
  ]
}
```

### Parallel Processing

```json
{
  "name": "Parallel Workflow",
  "nodes": [
    {"id": "trigger", "type": "trigger", "trigger_type": "webhook"},
    {"id": "task1", "type": "action", "action_type": "http"},
    {"id": "task2", "type": "action", "action_type": "data_transform"},
    {"id": "task3", "type": "action", "action_type": "send_email"}
  ],
  "connections": [
    {"from": "trigger", "to": "task1"},
    {"from": "trigger", "to": "task2"},
    {"from": "task1", "to": "task3"},
    {"from": "task2", "to": "task3"}
  ]
}
```

### Conditional Branching

```json
{
  "name": "Conditional Workflow",
  "nodes": [
    {"id": "check-condition", "type": "action", "action_type": "http"},
    {"id": "success-path", "type": "action", "action_type": "send_email"},
    {"id": "failure-path", "type": "action", "action_type": "send_email"}
  ],
  "connections": [
    {
      "from": "check-condition",
      "to": "success-path",
      "condition": "result.status == 'success'"
    },
    {
      "from": "check-condition",
      "to": "failure-path",
      "condition": "result.status == 'error'"
    }
  ]
}
```

### Loop Processing

```json
{
  "name": "Loop Workflow",
  "nodes": [
    {"id": "get-batch", "type": "action", "action_type": "http"},
    {"id": "process-item", "type": "action", "action_type": "data_transform"},
    {"id": "check-more", "type": "action", "action_type": "data_filter"}
  ],
  "connections": [
    {"from": "get-batch", "to": "process-item"},
    {"from": "process-item", "to": "check-more"},
    {
      "from": "check-more",
      "to": "get-batch",
      "condition": "result.has_more == true"
    }
  ]
}
```

## Common Integration Patterns

### Database Operations

```json
{
  "nodes": [
    {
      "id": "query-data",
      "type": "action",
      "action_type": "http",
      "config": {
        "method": "GET",
        "url": "https://api.database.com/query",
        "headers": {
          "Authorization": "Bearer ${API_KEY}",
          "Content-Type": "application/json"
        }
      }
    },
    {
      "id": "transform-data",
      "type": "action",
      "action_type": "data_transform",
      "config": {
        "transform_type": "json_to_csv",
        "field_mapping": {
          "customer_name": "full_name",
          "customer_email": "email_address"
        }
      }
    }
  ]
}
```

### External API Integration

```json
{
  "nodes": [
    {
      "id": "call-external-api",
      "type": "action",
      "action_type": "http",
      "config": {
        "method": "POST",
        "url": "https://api.externalservice.com/webhook",
        "headers": {
          "Authorization": "Bearer ${EXTERNAL_API_KEY}",
          "Content-Type": "application/json"
        },
        "body": {
          "event": "workflow_triggered",
          "data": "${input_data}"
        }
      }
    }
  ]
}
```

### File Processing

```json
{
  "nodes": [
    {
      "id": "download-file",
      "type": "action",
      "action_type": "http",
      "config": {
        "method": "GET",
        "url": "${file_url}"
      }
    },
    {
      "id": "upload-to-storage",
      "type": "action",
      "action_type": "s3_upload",
      "config": {
        "bucket_name": "my-processed-files",
        "key": "processed/${filename}",
        "aws_access_key_id": "${AWS_ACCESS_KEY}",
        "aws_secret_access_key": "${AWS_SECRET_KEY}"
      }
    }
  ]
}
```

## Configuration Management

### Environment Variables

```json
{
  "nodes": [
    {
      "id": "api-call",
      "type": "action",
      "action_type": "http",
      "config": {
        "method": "GET",
        "url": "${API_BASE_URL}/users",
        "headers": {
          "Authorization": "Bearer ${API_KEY}",
          "X-API-Version": "${API_VERSION}"
        }
      }
    }
  ]
}
```

### Dynamic Configuration

```json
{
  "nodes": [
    {
      "id": "conditional-action",
      "type": "action",
      "action_type": "http",
      "config": {
        "method": "${input_data.method || 'GET'}",
        "url": "${input_data.url}",
        "headers": "${input_data.headers || {}}"
      }
    }
  ]
}
```

## Testing Workflows

### Unit Testing Actions

```python
import pytest
from flowforge import FlowForgeClient

def test_http_action():
    client = FlowForgeClient(api_key="test-key")

    result = client.actions.test(
        action_type="http",
        config={
            "method": "GET",
            "url": "https://httpbin.org/get"
        }
    )

    assert result["valid"] is True
    assert result["connection_test"] is True

def test_workflow_execution():
    client = FlowForgeClient(api_key="test-key")

    workflow = {
        "nodes": [
            {
                "id": "test-action",
                "type": "action",
                "action_type": "http",
                "config": {
                    "method": "GET",
                    "url": "https://httpbin.org/get"
                }
            }
        ],
        "connections": []
    }

    result = client.flows.execute(
        flow_data=workflow,
        input_variables={}
    )

    assert result["success"] is True
    assert len(result["executed_nodes"]) == 1
```

### Integration Testing

```python
def test_full_workflow():
    """Test complete workflow with all integrations."""
    client = FlowForgeClient(api_key="test-key")

    # Test webhook trigger
    webhook = client.triggers.create(
        trigger_type="webhook",
        config={"webhook_id": "test-webhook"},
        flow_id="test-flow"
    )

    # Execute workflow
    result = client.flows.execute(
        flow_data=get_test_workflow(),
        input_variables={"test_data": "value"}
    )

    # Verify execution
    assert result["success"] is True

    # Check execution status
    status = client.flows.get_execution_status(result["execution_id"])
    assert status["status"] == "completed"
```

## Best Practices for Examples

### 1. Error Handling

```json
{
  "nodes": [
    {
      "id": "api-call",
      "type": "action",
      "action_type": "http",
      "config": {
        "method": "GET",
        "url": "https://api.example.com/data",
        "timeout": 30,
        "retry_count": 3,
        "retry_delay": 5
      }
    },
    {
      "id": "error-handler",
      "type": "action",
      "action_type": "send_email",
      "config": {
        "subject": "API Call Failed",
        "body": "Failed to call API: ${error.message}"
      }
    }
  ],
  "connections": [
    {
      "from": "api-call",
      "to": "error-handler",
      "condition": "result.success == false"
    }
  ]
}
```

### 2. Logging and Monitoring

```json
{
  "nodes": [
    {
      "id": "log-start",
      "type": "action",
      "action_type": "data_transform",
      "config": {
        "transform_type": "add_fields",
        "fields": {
          "workflow_start_time": "${timestamp}",
          "workflow_id": "${execution_id}"
        }
      }
    }
  ]
}
```

### 3. Input Validation

```json
{
  "nodes": [
    {
      "id": "validate-input",
      "type": "action",
      "action_type": "data_filter",
      "config": {
        "filter_condition": "input_data.email && input_data.name",
        "error_message": "Missing required fields: email and name"
      }
    }
  ]
}
```

## Contributing Examples

We welcome contributions of new workflow examples! Here's how to contribute:

### 1. Choose a Category

- Create a new directory under the appropriate category
- Use kebab-case for directory names: `customer-onboarding`

### 2. Required Files

Each example must include:

```
your-example/
├── README.md          # Detailed explanation
├── workflow.json      # Complete workflow definition
├── config.json        # Configuration templates
├── test-data.json     # Sample input data
└── diagrams/          # Visual diagrams (optional)
    ├── flowchart.png
    └── architecture.png
```

### 3. Documentation Standards

**README.md structure:**
```markdown
# Example Title

Brief description of what this workflow does.

## Use Case

Detailed description of the business problem this solves.

## Workflow Overview

High-level explanation of the workflow steps.

## Configuration

### Environment Variables
- `API_KEY`: Your API key
- `WEBHOOK_SECRET`: Webhook secret

### Required Services
- Database connection
- Email service
- External API access

## Implementation Details

Step-by-step breakdown of each node.

## Testing

How to test the workflow with sample data.

## Customization

How to adapt this workflow for different use cases.
```

### 4. Code Quality

- Use descriptive node IDs and names
- Include error handling in all workflows
- Add comments for complex logic
- Validate configurations before submission
- Test workflows with real data when possible

### 5. Submit Your Example

```bash
# Fork the repository
git clone https://github.com/your-username/flowforge-examples.git
cd flowforge-examples

# Create your example
mkdir examples/your-category/your-example
# Add your files...

# Submit pull request
git add .
git commit -m "Add new workflow example: your-example"
git push origin main
```

## Support and Community

- **GitHub Issues**: Report bugs or request features
- **GitHub Discussions**: Ask questions and share ideas
- **Discord**: Join our community for real-time support
- **Documentation**: Check our comprehensive docs

---

Ready to get started? Check out our [Hello World](./hello-world/) example or dive into a specific business domain that matches your needs!

Happy automating! 🚀
