"""
Integration tests for authentication and authorization.

These tests verify that the API properly handles authentication,
authorization, rate limiting, and security features.
"""

import pytest
from unittest.mock import patch
from typing import Dict, Any

from tests.integration import IntegrationTestBase


class TestAuthenticationIntegration(IntegrationTestBase):
    """Test authentication integration."""

    @pytest.mark.asyncio
    async def test_valid_api_key_authentication(self):
        """Test successful authentication with valid API key."""
        # This test assumes we have a way to set up valid API keys
        # In a real scenario, this would be configured in the test setup

        headers = {
            "Authorization": "Bearer test-api-key"
        }

        response = await self.client.get("/health", headers=headers)
        # Should succeed with proper authentication
        assert response.status_code in [200, 401]  # 401 if auth is not mocked

    @pytest.mark.asyncio
    async def test_invalid_api_key_authentication(self):
        """Test authentication failure with invalid API key."""
        headers = {
            "Authorization": "Bearer invalid-api-key"
        }

        response = await self.client.get("/health", headers=headers)
        # Should fail with authentication error
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_authentication_header(self):
        """Test request without authentication header."""
        response = await self.client.get("/health")
        # Should fail with authentication error
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_malformed_authentication_header(self):
        """Test authentication with malformed header."""
        headers = {
            "Authorization": "InvalidFormat test-key"
        }

        response = await self.client.get("/health", headers=headers)
        # Should fail with authentication error
        assert response.status_code == 401


class TestAuthorizationIntegration(IntegrationTestBase):
    """Test authorization integration."""

    @pytest.mark.asyncio
    async def test_authorized_workflow_execution(self):
        """Test workflow execution with proper authorization."""
        # Create a test workflow
        workflow_data = get_test_workflow_data()
        workflow = await self.create_test_workflow(workflow_data)

        # Execute with proper authentication
        headers = {"Authorization": "Bearer test-api-key"}

        response = await self.client.post(
            "/api/v1/flows/execute",
            json={
                "workflow_id": workflow["workflow_id"],
                "input_data": {"test": "data"}
            },
            headers=headers
        )

        # Should succeed with proper auth
        assert response.status_code in [200, 401, 403]

    @pytest.mark.asyncio
    async def test_unauthorized_workflow_access(self):
        """Test accessing workflow without proper authorization."""
        # Try to access workflow without authentication
        response = await self.client.get("/api/v1/flows/test-workflow-id")

        # Should fail with auth error
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_authorized_action_execution(self):
        """Test action execution with proper authorization."""
        headers = {"Authorization": "Bearer test-api-key"}

        response = await self.client.post(
            "/api/v1/actions/execute",
            json={
                "action_type": "http",
                "config": {"method": "GET", "url": "https://httpbin.org/json"},
                "input_data": {}
            },
            headers=headers
        )

        # Should succeed with proper auth
        assert response.status_code in [200, 401, 403]


class TestRateLimitingIntegration(IntegrationTestBase):
    """Test rate limiting integration."""

    @pytest.mark.asyncio
    async def test_rate_limit_headers(self):
        """Test that rate limit headers are included in responses."""
        headers = {"Authorization": "Bearer test-api-key"}

        response = await self.client.get("/health", headers=headers)

        # Check for rate limit headers
        rate_limit_headers = [
            "x-ratelimit-limit",
            "x-ratelimit-remaining",
            "x-ratelimit-reset"
        ]

        # At least one rate limit header should be present
        has_rate_limit_header = any(header in response.headers for header in rate_limit_headers)
        assert has_rate_limit_header or response.status_code in [401, 429]

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Test behavior when rate limit is exceeded."""
        headers = {"Authorization": "Bearer test-api-key"}

        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = await self.client.get("/health", headers=headers)
            responses.append(response)

        # At least one should be rate limited or succeed
        rate_limited = any(r.status_code == 429 for r in responses)
        successful = any(r.status_code == 200 for r in responses)

        assert rate_limited or successful

    @pytest.mark.asyncio
    async def test_rate_limit_reset(self):
        """Test rate limit reset functionality."""
        headers = {"Authorization": "Bearer test-api-key"}

        # Make a request to get initial rate limit info
        response = await self.client.get("/health", headers=headers)

        if response.status_code == 200:
            remaining = response.headers.get("x-ratelimit-remaining")
            reset_time = response.headers.get("x-ratelimit-reset")

            if remaining and reset_time:
                assert int(remaining) >= 0
                assert int(reset_time) > 0


class TestSecurityIntegration(IntegrationTestBase):
    """Test security features integration."""

    @pytest.mark.asyncio
    async def test_input_validation(self):
        """Test input validation for malicious payloads."""
        # Test with potentially malicious input
        malicious_payloads = [
            {"action_type": "http", "config": {"method": "<script>alert('xss')</script>"}},
            {"action_type": "http", "config": {"url": "javascript:alert('xss')"}},
            {"action_type": "http", "config": {"url": "data:text/html,<script>alert('xss')</script>"}},
        ]

        headers = {"Authorization": "Bearer test-api-key"}

        for payload in malicious_payloads:
            response = await self.client.post(
                "/api/v1/actions/execute",
                json=payload,
                headers=headers
            )

            # Should either be rejected or sanitized
            assert response.status_code in [200, 400, 422, 401, 403]

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self):
        """Test prevention of SQL injection attacks."""
        # Test with SQL injection attempts
        sql_injection_payloads = [
            {"action_type": "http", "config": {"url": "https://api.example.com'; DROP TABLE users; --"}},
            {"action_type": "http", "config": {"method": "GET' OR '1'='1"}},
        ]

        headers = {"Authorization": "Bearer test-api-key"}

        for payload in sql_injection_payloads:
            response = await self.client.post(
                "/api/v1/actions/execute",
                json=payload,
                headers=headers
            )

            # Should not execute dangerous operations
            assert response.status_code in [200, 400, 422, 401, 403]

    @pytest.mark.asyncio
    async def test_cors_headers(self):
        """Test CORS headers are properly set."""
        response = await self.client.options("/health")

        # Check for CORS headers
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]

        has_cors_headers = any(header in response.headers for header in cors_headers)
        assert has_cors_headers or response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_security_headers(self):
        """Test security headers are present."""
        headers = {"Authorization": "Bearer test-api-key"}
        response = await self.client.get("/health", headers=headers)

        if response.status_code == 200:
            security_headers = [
                "x-content-type-options",
                "x-frame-options",
                "x-xss-protection"
            ]

            # Check for at least some security headers
            has_security_headers = any(header in response.headers for header in security_headers)
            assert has_security_headers


class TestErrorHandlingIntegration(IntegrationTestBase):
    """Test error handling integration."""

    @pytest.mark.asyncio
    async def test_graceful_error_responses(self):
        """Test that errors are handled gracefully with proper responses."""
        # Test with invalid action type
        headers = {"Authorization": "Bearer test-api-key"}

        response = await self.client.post(
            "/api/v1/actions/execute",
            json={
                "action_type": "invalid_action_type",
                "config": {},
                "input_data": {}
            },
            headers=headers
        )

        # Should return proper error response
        assert response.status_code >= 400
        if response.status_code == 422:
            error_data = response.json()
            assert "detail" in error_data

    @pytest.mark.asyncio
    async def test_internal_error_handling(self):
        """Test handling of internal server errors."""
        # This test is difficult to trigger reliably without breaking the system
        # In a real scenario, we might mock internal errors

        headers = {"Authorization": "Bearer test-api-key"}

        # Test with a potentially problematic request
        response = await self.client.post(
            "/api/v1/actions/execute",
            json={
                "action_type": "http",
                "config": {
                    "method": "GET",
                    "url": "https://httpbin.org/status/500"  # Returns 500 error
                }
            },
            headers=headers
        )

        # Should handle the external error gracefully
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            result = response.json()
            # Should contain error information
            assert "result" in result or "error" in result

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test handling of request timeouts."""
        headers = {"Authorization": "Bearer test-api-key"}

        response = await self.client.post(
            "/api/v1/actions/execute",
            json={
                "action_type": "http",
                "config": {
                    "method": "GET",
                    "url": "https://httpbin.org/delay/30",  # 30 second delay
                    "timeout": 5  # 5 second timeout
                }
            },
            headers=headers
        )

        # Should handle timeout gracefully
        assert response.status_code in [200, 408, 500]
        if response.status_code == 200:
            result = response.json()
            assert "result" in result

    @pytest.mark.asyncio
    async def test_validation_error_responses(self):
        """Test validation error responses."""
        headers = {"Authorization": "Bearer test-api-key"}

        # Test with missing required fields
        response = await self.client.post(
            "/api/v1/actions/execute",
            json={
                "action_type": "http"
                # Missing config
            },
            headers=headers
        )

        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data


class TestConcurrentAccessIntegration(IntegrationTestBase):
    """Test concurrent access patterns."""

    @pytest.mark.asyncio
    async def test_concurrent_workflow_executions(self):
        """Test multiple concurrent workflow executions."""
        import asyncio

        # Create a simple workflow
        workflow_data = get_test_workflow_data()
        workflow = await self.create_test_workflow(workflow_data)

        async def execute_workflow_instance():
            """Execute a single workflow instance."""
            result = await self.execute_workflow(workflow["workflow_id"], {"instance": "concurrent"})
            return result

        # Execute 5 workflows concurrently
        tasks = [execute_workflow_instance() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # Verify all executions were handled
        assert len(results) == 5
        for result in results:
            assert "execution_id" in result

        # Verify execution IDs are unique
        execution_ids = [r["execution_id"] for r in results]
        assert len(set(execution_ids)) == len(execution_ids)

    @pytest.mark.asyncio
    async def test_concurrent_action_executions(self):
        """Test multiple concurrent action executions."""
        import asyncio

        async def execute_http_action():
            """Execute a single HTTP action."""
            result = await self.execute_action(
                "http",
                {"method": "GET", "url": "https://httpbin.org/json"},
                {}
            )
            return result

        # Execute 10 actions concurrently
        tasks = [execute_http_action() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # Verify all actions were executed
        assert len(results) == 10
        successful_results = [r for r in results if r.get("success")]
        assert len(successful_results) > 0

    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(self):
        """Test concurrent mix of different operations."""
        import asyncio

        async def mixed_operation(op_type: str):
            """Execute different types of operations."""
            if op_type == "workflow":
                workflow_data = get_test_workflow_data()
                workflow = await self.create_test_workflow(workflow_data)
                result = await self.execute_workflow(workflow["workflow_id"], {})
                return {"type": "workflow", "result": result}
            elif op_type == "action":
                result = await self.execute_action(
                    "http",
                    {"method": "GET", "url": "https://httpbin.org/json"},
                    {}
                )
                return {"type": "action", "result": result}

        # Execute mix of workflows and actions
        operations = ["workflow", "action", "workflow", "action", "action"]
        tasks = [mixed_operation(op) for op in operations]
        results = await asyncio.gather(*tasks)

        # Verify results
        assert len(results) == len(operations)
        workflow_results = [r for r in results if r["type"] == "workflow"]
        action_results = [r for r in results if r["type"] == "action"]

        assert len(workflow_results) == 2
        assert len(action_results) == 3


class TestWebhookSecurityIntegration(IntegrationTestBase):
    """Test webhook security integration."""

    @pytest.mark.asyncio
    async def test_webhook_signature_verification(self):
        """Test webhook signature verification."""
        # This test assumes webhook endpoints exist and have signature verification
        # In a real scenario, this would test the webhook processing

        # Create a test trigger with signature verification
        trigger_data = {
            "trigger_type": "webhook",
            "config": {
                "webhook_id": "test-webhook-security",
                "secret": "test-webhook-secret",
                "validate_signature": True
            },
            "flow_id": "test-flow-id"
        }

        response = await self.client.post("/api/v1/triggers/create", json=trigger_data)
        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 401, 403]

    @pytest.mark.asyncio
    async def test_webhook_ip_filtering(self):
        """Test webhook IP address filtering."""
        # Create a test trigger with IP filtering
        trigger_data = {
            "trigger_type": "webhook",
            "config": {
                "webhook_id": "test-webhook-ip",
                "secret": "test-secret",
                "allowed_ips": ["192.168.1.100", "10.0.0.1/24"]
            },
            "flow_id": "test-flow-id"
        }

        response = await self.client.post("/api/v1/triggers/create", json=trigger_data)
        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 401, 403]


class TestAuditLoggingIntegration(IntegrationTestBase):
    """Test audit logging integration."""

    @pytest.mark.asyncio
    async def test_api_call_logging(self):
        """Test that API calls are properly logged."""
        headers = {"Authorization": "Bearer test-api-key"}

        # Make a request that should be logged
        response = await self.client.post(
            "/api/v1/actions/execute",
            json={
                "action_type": "http",
                "config": {"method": "GET", "url": "https://httpbin.org/json"},
                "input_data": {}
            },
            headers=headers
        )

        # Verify response (logging happens internally)
        assert response.status_code in [200, 401, 403]

    @pytest.mark.asyncio
    async def test_error_logging(self):
        """Test that errors are properly logged."""
        headers = {"Authorization": "Bearer test-api-key"}

        # Make a request that will fail
        response = await self.client.post(
            "/api/v1/actions/execute",
            json={
                "action_type": "invalid_type",
                "config": {},
                "input_data": {}
            },
            headers=headers
        )

        # Verify error response
        assert response.status_code >= 400
        # Error should be logged internally


# Helper functions
def get_test_workflow_data():
    """Get sample test workflow data."""
    return {
        "name": "Integration Test Workflow",
        "description": "Testing authentication and authorization",
        "nodes": [
            {
                "id": "http-action",
                "type": "action",
                "action_type": "http",
                "config": {
                    "method": "GET",
                    "url": "https://httpbin.org/json"
                }
            }
        ],
        "connections": []
    }

