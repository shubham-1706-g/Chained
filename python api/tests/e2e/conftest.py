"""
Pytest configuration for end-to-end tests.

This module provides shared fixtures and configuration for E2E tests.
"""

import pytest
import asyncio
from typing import Dict, Any, AsyncGenerator
from httpx import AsyncClient
from unittest.mock import patch

from main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def e2e_client() -> AsyncGenerator[AsyncClient, None]:
    """Create E2E test client with real dependencies."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture
async def mock_all_external_services():
    """Mock all external services for E2E tests."""
    from unittest.mock import patch

    def mock_http_response(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"success": True, "mocked": True}
        return MockResponse()

    def mock_email_response(*args, **kwargs):
        return {"success": True, "message_id": "mock-email-id"}

    # Mock all external service calls
    with patch.multiple(
        'aiohttp.ClientSession',
        request=mock_http_response
    ), patch.multiple(
        'smtplib.SMTP',
        sendmail=mock_email_response
    ), patch.multiple(
        'boto3.client',
        upload_file=lambda *args, **kwargs: None
    ):
        yield


@pytest.fixture
async def mock_ai_services():
    """Mock AI services (OpenAI, Claude, etc.)."""
    from unittest.mock import patch

    def mock_ai_response(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {
                    "choices": [{
                        "message": {
                            "content": "This is a mocked AI response for testing."
                        }
                    }],
                    "usage": {"tokens": 50}
                }
        return MockResponse()

    with patch('aiohttp.ClientSession.request', side_effect=mock_ai_response):
        yield


@pytest.fixture
async def mock_database_services():
    """Mock database services for testing."""
    from unittest.mock import patch

    def mock_db_response(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"success": True, "data": "mocked_db_response"}
        return MockResponse()

    with patch('aiohttp.ClientSession.request', side_effect=mock_db_response):
        yield


@pytest.fixture
async def mock_payment_services():
    """Mock payment processing services."""
    from unittest.mock import patch

    def mock_payment_response(*args, **kwargs):
        if "charge" in str(args[0]).lower():
            class MockResponse:
                status_code = 200
                def json(self):
                    return {
                        "success": True,
                        "transaction_id": "mock-txn-123",
                        "amount": 99.99
                    }
            return MockResponse()
        else:
            class MockResponse:
                status_code = 200
                def json(self):
                    return {"success": True}
            return MockResponse()

    with patch('aiohttp.ClientSession.request', side_effect=mock_payment_response):
        yield


@pytest.fixture
async def mock_shipping_services():
    """Mock shipping and logistics services."""
    from unittest.mock import patch

    def mock_shipping_response(*args, **kwargs):
        if "create" in str(args[0]).lower():
            class MockResponse:
                status_code = 200
                def json(self):
                    return {
                        "success": True,
                        "tracking_number": "MOCK123456789",
                        "carrier": "Mock Carrier",
                        "estimated_delivery": "2024-01-20T10:00:00Z"
                    }
            return MockResponse()
        else:
            class MockResponse:
                status_code = 200
                def json(self):
                    return {"success": True}
            return MockResponse()

    with patch('aiohttp.ClientSession.request', side_effect=mock_shipping_response):
        yield


@pytest.fixture
async def mock_inventory_services():
    """Mock inventory management services."""
    from unittest.mock import patch

    def mock_inventory_response(*args, **kwargs):
        if "check" in str(args[0]).lower():
            class MockResponse:
                status_code = 200
                def json(self):
                    return {
                        "available": True,
                        "items": [
                            {"sku": "TEST-001", "available": True, "quantity": 10}
                        ]
                    }
            return MockResponse()
        elif "update" in str(args[0]).lower():
            class MockResponse:
                status_code = 200
                def json(self):
                    return {"success": True, "updated": True}
            return MockResponse()
        else:
            class MockResponse:
                status_code = 200
                def json(self):
                    return {"success": True}
            return MockResponse()

    with patch('aiohttp.ClientSession.request', side_effect=mock_inventory_response):
        yield


@pytest.fixture
async def mock_email_services():
    """Mock email service providers."""
    from unittest.mock import patch

    def mock_email_send(*args, **kwargs):
        return {"success": True, "message_id": "mock-email-123"}

    with patch('smtplib.SMTP.sendmail', side_effect=mock_email_send):
        yield


@pytest.fixture
async def mock_crm_services():
    """Mock CRM and customer management services."""
    from unittest.mock import patch

    def mock_crm_response(*args, **kwargs):
        if "leads" in str(args[0]).lower():
            if "POST" in str(args).upper():
                class MockResponse:
                    status_code = 201
                    def json(self):
                        return {"id": "mock-lead-123", "status": "created"}
                return MockResponse()
            else:
                class MockResponse:
                    status_code = 200
                    def json(self):
                        return {"id": "existing-lead-456", "status": "active"}
                return MockResponse()
        else:
            class MockResponse:
                status_code = 200
                def json(self):
                    return {"success": True}
            return MockResponse()

    with patch('aiohttp.ClientSession.request', side_effect=mock_crm_response):
        yield


@pytest.fixture
async def mock_storage_services():
    """Mock cloud storage services (S3, Google Drive)."""
    from unittest.mock import patch

    def mock_storage_response(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"success": True, "file_id": "mock-file-123"}
        return MockResponse()

    with patch.multiple(
        'boto3.client',
        upload_file=lambda *args, **kwargs: None
    ), patch('aiohttp.ClientSession.request', side_effect=mock_storage_response):
        yield


@pytest.fixture
async def mock_notification_services():
    """Mock notification services (SMS, push notifications)."""
    from unittest.mock import patch

    def mock_notification_response(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"success": True, "message_id": "mock-notification-123"}
        return MockResponse()

    with patch('aiohttp.ClientSession.request', side_effect=mock_notification_response):
        yield


# Performance testing fixtures
@pytest.fixture
def performance_config():
    """Configuration for performance tests."""
    return {
        "max_concurrency": 20,
        "test_duration": 60,  # seconds
        "warmup_duration": 10,  # seconds
        "cooldown_duration": 5,  # seconds
        "target_throughput": 10,  # workflows per second
        "max_latency": 30,  # seconds
        "memory_limit": 500,  # MB
    }


@pytest.fixture
async def load_test_setup(performance_config):
    """Setup for load testing with monitoring."""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    yield {
        "process": process,
        "initial_memory": initial_memory,
        "config": performance_config
    }

    # Cleanup and reporting
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    print("
Load Test Results:")
    print(f"Initial Memory: {initial_memory:.1f}MB")
    print(f"Final Memory: {final_memory:.1f}MB")
    print(f"Memory Increase: {memory_increase:.1f}MB")

    if memory_increase > performance_config["memory_limit"]:
        print(f"⚠️  WARNING: Memory usage exceeded limit of {performance_config['memory_limit']}MB")


# Test data fixtures
@pytest.fixture
def sample_order_data():
    """Sample e-commerce order data."""
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
            }
        ]
    }


@pytest.fixture
def sample_lead_data():
    """Sample marketing lead data."""
    return {
        "email": "jane.smith@example.com",
        "name": "Jane Smith",
        "source": "website",
        "company": "Tech Corp",
        "interests": ["product-a", "enterprise"]
    }


@pytest.fixture
def sample_support_ticket():
    """Sample customer support ticket data."""
    return {
        "ticket_id": "TICK-789",
        "customer_email": "support.customer@example.com",
        "subject": "Billing question",
        "description": "I have a question about my recent bill",
        "priority": "medium",
        "category": "billing"
    }


# Test utilities
def assert_workflow_completed_successfully(result: Dict[str, Any], expected_steps: list = None):
    """Assert that a workflow completed successfully."""
    assert result["status"] == "completed"
    assert "executed_nodes" in result
    assert len(result["executed_nodes"]) > 0

    if expected_steps:
        executed_node_ids = [node["node_id"] for node in result["executed_nodes"]]
        for step in expected_steps:
            assert step in executed_node_ids, f"Expected step '{step}' not found in execution"

    # Verify all nodes completed successfully
    for node in result["executed_nodes"]:
        assert node["status"] == "completed", f"Node {node['node_id']} failed: {node.get('error', 'Unknown error')}"


def measure_execution_time(func):
    """Decorator to measure function execution time."""
    import time
    from functools import wraps

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time

        # Add execution time to result if it's a dict
        if isinstance(result, dict):
            result["_execution_time"] = execution_time

        return result

    return wrapper


def create_test_workflow_template(name: str, nodes: list, connections: list) -> Dict[str, Any]:
    """Create a test workflow template."""
    return {
        "name": name,
        "description": f"Test workflow: {name}",
        "version": "1.0.0",
        "nodes": nodes,
        "connections": connections,
        "settings": {
            "timeout": 60,
            "max_retries": 2,
            "fail_fast": False
        }
    }


# Custom test markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "load_test: Load testing")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Add e2e marker to all tests in e2e directory
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Add performance marker to performance tests
        if "performance" in item.name:
            item.add_marker(pytest.mark.performance)

        # Add slow marker to tests that might take longer
        if "concurrent" in item.name or "load" in item.name:
            item.add_marker(pytest.mark.slow)
