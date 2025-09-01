"""
End-to-end tests for FlowForge Python API.

These tests verify complete workflow execution scenarios from trigger to final action,
testing real-world use cases like e-commerce order fulfillment, marketing automation,
customer support workflows, and complex business processes.

E2E tests are the most comprehensive but also the slowest. They should be run
less frequently than unit or integration tests.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from httpx import AsyncClient

from main import app
from app.core.config import get_settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def e2e_client():
    """Create E2E test client with real dependencies."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@asynccontextmanager
async def mock_external_services(services: Dict[str, Any]):
    """Context manager for mocking multiple external services."""
    # This would be implemented to mock various external services
    # like payment gateways, email services, etc.
    yield


class E2ETestBase:
    """Base class for end-to-end tests with common utilities."""

    def __init__(self):
        self.client = None

    @pytest.fixture(autouse=True)
    async def setup_method(self, e2e_client):
        """Setup method run before each test."""
        self.client = e2e_client

    async def create_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a workflow for testing."""
        response = await self.client.post("/api/v1/flows/create", json=workflow_data)
        assert response.status_code == 200
        return response.json()

    async def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow and return the result."""
        response = await self.client.post(
            "/api/v1/flows/execute",
            json={
                "workflow_id": workflow_id,
                "input_data": input_data
            }
        )
        assert response.status_code == 200
        return response.json()

    async def wait_for_execution_completion(self, execution_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Wait for workflow execution to complete."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            response = await self.client.get(f"/api/v1/flows/execution/{execution_id}")
            assert response.status_code == 200

            status = response.json()
            if status["status"] in ["completed", "error"]:
                return status

            await asyncio.sleep(1)

        raise TimeoutError(f"Workflow execution {execution_id} did not complete within {timeout} seconds")

    async def simulate_webhook_trigger(self, webhook_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate a webhook trigger (would normally come from external service)."""
        # In a real scenario, this would be an actual HTTP request to a webhook endpoint
        # For testing, we'll simulate the workflow execution directly

        # Find workflows that use this webhook trigger
        # This is a simplified version - in reality you'd have a webhook processing system
        workflow_data = self._get_workflow_for_webhook(webhook_id)
        if workflow_data:
            workflow = await self.create_workflow(workflow_data)
            result = await self.execute_workflow(workflow["workflow_id"], payload)
            return await self.wait_for_execution_completion(result["execution_id"])

        return {"error": "No workflow found for webhook"}

    def _get_workflow_for_webhook(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow definition for a webhook (helper method)."""
        # This would normally query the database or configuration
        # For testing, return a predefined workflow
        return None

    async def verify_workflow_results(self, execution_result: Dict[str, Any], expected_steps: List[str]):
        """Verify that workflow executed the expected steps."""
        assert execution_result["status"] == "completed"

        executed_nodes = execution_result.get("executed_nodes", [])
        executed_node_ids = [node["node_id"] for node in executed_nodes]

        for step in expected_steps:
            assert step in executed_node_ids, f"Expected step '{step}' not found in execution"

        # Verify all nodes completed successfully
        for node in executed_nodes:
            assert node["status"] == "completed", f"Node {node['node_id']} failed: {node.get('error', 'Unknown error')}"

    async def verify_external_service_calls(self, execution_result: Dict[str, Any], expected_calls: List[Dict[str, Any]]):
        """Verify that external services were called as expected."""
        # This would check logs or mock call records
        # For now, just verify the execution completed
        assert execution_result["status"] == "completed"


# Test data helpers
def get_ecommerce_order_workflow():
    """Get a complete e-commerce order fulfillment workflow."""
    return {
        "name": "E-commerce Order Fulfillment",
        "description": "Complete order processing workflow",
        "version": "1.0.0",
        "nodes": [
            {
                "id": "order-webhook",
                "type": "trigger",
                "trigger_type": "webhook",
                "name": "Order Webhook",
                "description": "Receives new order webhooks",
                "config": {
                    "webhook_id": "order-fulfillment",
                    "secret": "webhook-secret",
                    "validate_signature": True
                }
            },
            {
                "id": "validate-order",
                "type": "action",
                "action_type": "data_filter",
                "name": "Validate Order",
                "description": "Validate order data structure",
                "config": {
                    "filter_condition": "input_data.order_id && input_data.customer_email && input_data.items",
                    "error_message": "Invalid order data"
                }
            },
            {
                "id": "check-inventory",
                "type": "action",
                "action_type": "http",
                "name": "Check Inventory",
                "description": "Check product availability",
                "config": {
                    "method": "POST",
                    "url": "https://api.inventory.com/check",
                    "headers": {"Authorization": "Bearer inventory-key"},
                    "body": {
                        "order_id": "${input_data.order_id}",
                        "items": "${input_data.items}"
                    }
                }
            },
            {
                "id": "process-payment",
                "type": "action",
                "action_type": "http",
                "name": "Process Payment",
                "description": "Process payment through gateway",
                "config": {
                    "method": "POST",
                    "url": "https://api.payment.com/charge",
                    "headers": {"Authorization": "Bearer payment-key"},
                    "body": {
                        "amount": "${input_data.total_amount}",
                        "currency": "USD",
                        "order_id": "${input_data.order_id}"
                    }
                }
            },
            {
                "id": "update-inventory",
                "type": "action",
                "action_type": "http",
                "name": "Update Inventory",
                "description": "Update inventory levels",
                "config": {
                    "method": "POST",
                    "url": "https://api.inventory.com/update",
                    "headers": {"Authorization": "Bearer inventory-key"},
                    "body": {
                        "order_id": "${input_data.order_id}",
                        "items": "${input_data.items}",
                        "operation": "fulfill"
                    }
                }
            },
            {
                "id": "create-shipping",
                "type": "action",
                "action_type": "http",
                "name": "Create Shipping",
                "description": "Create shipping label",
                "config": {
                    "method": "POST",
                    "url": "https://api.shipping.com/create",
                    "headers": {"Authorization": "Bearer shipping-key"},
                    "body": {
                        "order_id": "${input_data.order_id}",
                        "address": "${input_data.shipping_address}"
                    }
                }
            },
            {
                "id": "send-confirmation",
                "type": "action",
                "action_type": "send_email",
                "name": "Send Confirmation",
                "description": "Send order confirmation email",
                "config": {
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "orders@store.com",
                    "password": "smtp-password",
                    "from_email": "orders@store.com",
                    "to_email": "${input_data.customer_email}",
                    "subject": "Order Confirmation #${input_data.order_id}",
                    "body": "Your order has been confirmed and is being processed."
                }
            }
        ],
        "connections": [
            {"from": "order-webhook", "to": "validate-order"},
            {"from": "validate-order", "to": "check-inventory", "condition": "result.passed == true"},
            {"from": "check-inventory", "to": "process-payment", "condition": "result.available == true"},
            {"from": "process-payment", "to": "update-inventory"},
            {"from": "update-inventory", "to": "create-shipping"},
            {"from": "create-shipping", "to": "send-confirmation"}
        ],
        "settings": {
            "timeout": 300,
            "max_retries": 3,
            "fail_fast": False
        }
    }


def get_marketing_automation_workflow():
    """Get a marketing automation workflow."""
    return {
        "name": "Marketing Automation",
        "description": "Lead nurturing and email marketing workflow",
        "nodes": [
            {
                "id": "lead-webhook",
                "type": "trigger",
                "trigger_type": "webhook",
                "name": "Lead Webhook",
                "config": {"webhook_id": "lead-capture"}
            },
            {
                "id": "validate-lead",
                "type": "action",
                "action_type": "data_filter",
                "name": "Validate Lead",
                "config": {
                    "filter_condition": "input_data.email && input_data.name",
                    "error_message": "Invalid lead data"
                }
            },
            {
                "id": "check-existing",
                "type": "action",
                "action_type": "http",
                "name": "Check Existing",
                "config": {
                    "method": "GET",
                    "url": "https://api.crm.com/leads/${input_data.email}"
                }
            },
            {
                "id": "create-lead",
                "type": "action",
                "action_type": "http",
                "name": "Create Lead",
                "config": {
                    "method": "POST",
                    "url": "https://api.crm.com/leads",
                    "body": {
                        "email": "${input_data.email}",
                        "name": "${input_data.name}",
                        "source": "${input_data.source || 'website'}"
                    }
                }
            },
            {
                "id": "send-welcome",
                "type": "action",
                "action_type": "send_email",
                "name": "Send Welcome Email",
                "config": {
                    "to_email": "${input_data.email}",
                    "subject": "Welcome to Our Newsletter!",
                    "body": "Welcome ${input_data.name}! Thanks for subscribing."
                }
            },
            {
                "id": "add-to-segment",
                "type": "action",
                "action_type": "http",
                "name": "Add to Segment",
                "config": {
                    "method": "POST",
                    "url": "https://api.email.com/segments/new-leads/contacts",
                    "body": {"email": "${input_data.email}"}
                }
            }
        ],
        "connections": [
            {"from": "lead-webhook", "to": "validate-lead"},
            {"from": "validate-lead", "to": "check-existing"},
            {"from": "check-existing", "to": "create-lead", "condition": "result.status_code == 404"},
            {"from": "create-lead", "to": "send-welcome"},
            {"from": "send-welcome", "to": "add-to-segment"}
        ]
    }


def get_customer_support_workflow():
    """Get a customer support ticket workflow."""
    return {
        "name": "Customer Support Automation",
        "description": "Automated customer support ticket processing",
        "nodes": [
            {
                "id": "support-webhook",
                "type": "trigger",
                "trigger_type": "webhook",
                "name": "Support Webhook",
                "config": {"webhook_id": "support-ticket"}
            },
            {
                "id": "categorize-ticket",
                "type": "action",
                "action_type": "openai",
                "name": "Categorize Ticket",
                "config": {
                    "model": "gpt-3.5-turbo",
                    "system_prompt": "Categorize customer support tickets into: billing, technical, account, other",
                    "max_tokens": 50
                }
            },
            {
                "id": "check-urgency",
                "type": "action",
                "action_type": "data_filter",
                "name": "Check Urgency",
                "config": {
                    "filter_condition": "input_data.priority == 'high' || input_data.subject.includes('urgent')"
                }
            },
            {
                "id": "route-high-priority",
                "type": "action",
                "action_type": "send_email",
                "name": "Route High Priority",
                "config": {
                    "to_email": "urgent-support@company.com",
                    "subject": "URGENT: ${input_data.subject}",
                    "body": "High priority ticket requires immediate attention."
                }
            },
            {
                "id": "generate-response",
                "type": "action",
                "action_type": "openai",
                "name": "Generate Response",
                "config": {
                    "model": "gpt-4",
                    "system_prompt": "Generate a helpful customer support response",
                    "max_tokens": 200
                }
            },
            {
                "id": "send-response",
                "type": "action",
                "action_type": "send_email",
                "name": "Send Response",
                "config": {
                    "to_email": "${input_data.customer_email}",
                    "subject": "Re: ${input_data.subject}",
                    "body": "${previous_outputs.generate-response.result.response}"
                }
            }
        ],
        "connections": [
            {"from": "support-webhook", "to": "categorize-ticket"},
            {"from": "categorize-ticket", "to": "check-urgency"},
            {"from": "check-urgency", "to": "route-high-priority", "condition": "result.passed == true"},
            {"from": "check-urgency", "to": "generate-response", "condition": "result.passed == false"},
            {"from": "generate-response", "to": "send-response"}
        ]
    }


def get_sample_order_data():
    """Get sample order data for testing."""
    return {
        "order_id": "ORD-2024-001234",
        "customer_id": "CUST-567890",
        "customer_name": "John Doe",
        "customer_email": "john.doe@example.com",
        "total_amount": 149.99,
        "currency": "USD",
        "shipping_address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345",
            "country": "US"
        },
        "items": [
            {
                "sku": "WIDGET-001",
                "name": "Wonder Widget",
                "quantity": 2,
                "unit_price": 49.99,
                "total_price": 99.98
            },
            {
                "sku": "GADGET-002",
                "name": "Super Gadget",
                "quantity": 1,
                "unit_price": 50.01,
                "total_price": 50.01
            }
        ]
    }


def get_sample_lead_data():
    """Get sample lead data for testing."""
    return {
        "email": "jane.smith@example.com",
        "name": "Jane Smith",
        "source": "website",
        "interests": ["product-a", "newsletter"],
        "company": "Tech Corp",
        "timestamp": "2024-01-15T10:30:00Z"
    }


def get_sample_support_ticket():
    """Get sample support ticket data."""
    return {
        "ticket_id": "TICK-789",
        "customer_email": "support.customer@example.com",
        "subject": "Billing question",
        "description": "I have a question about my recent bill",
        "priority": "medium",
        "category": "billing",
        "timestamp": "2024-01-15T10:30:00Z"
    }
