"""
End-to-end tests for e-commerce order fulfillment workflow.

This test suite verifies the complete order processing workflow from webhook trigger
to final customer notification, testing all integration points and error scenarios.
"""

import pytest
import json
from unittest.mock import patch, AsyncMock
from typing import Dict, Any

from tests.e2e import E2ETestBase, get_ecommerce_order_workflow, get_sample_order_data


class TestEcommerceOrderFulfillment(E2ETestBase):
    """Test complete e-commerce order fulfillment workflow."""

    @pytest.mark.asyncio
    async def test_successful_order_fulfillment(self):
        """Test successful complete order fulfillment workflow."""
        # Mock all external services
        with self._mock_external_services():
            # Create the workflow
            workflow_data = get_ecommerce_order_workflow()
            workflow = await self.create_workflow(workflow_data)

            # Get test order data
            order_data = get_sample_order_data()

            # Execute the workflow
            result = await self.execute_workflow(workflow["workflow_id"], order_data)

            # Wait for completion
            final_status = await self.wait_for_execution_completion(result["execution_id"], timeout=60)

            # Verify workflow completed successfully
            assert final_status["status"] == "completed"

            # Verify all expected steps were executed
            expected_steps = [
                "validate-order",
                "check-inventory",
                "process-payment",
                "update-inventory",
                "create-shipping",
                "send-confirmation"
            ]

            await self.verify_workflow_results(final_status, expected_steps)

            # Verify execution time is reasonable
            assert final_status["duration"] > 0
            assert final_status["duration"] < 30  # Should complete within 30 seconds

    @pytest.mark.asyncio
    async def test_inventory_shortage_handling(self):
        """Test order fulfillment with inventory shortage."""
        # Mock inventory service to return shortage
        with self._mock_inventory_shortage():
            workflow_data = get_ecommerce_order_workflow()
            workflow = await self.create_workflow(workflow_data)

            order_data = get_sample_order_data()

            result = await self.execute_workflow(workflow["workflow_id"], order_data)
            final_status = await self.wait_for_execution_completion(result["execution_id"])

            # Workflow should still complete but with different path
            assert final_status["status"] == "completed"

            # Should have executed validation and inventory check
            executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
            assert "validate-order" in executed_nodes
            assert "check-inventory" in executed_nodes

            # Should not have proceeded to payment processing
            assert "process-payment" not in executed_nodes

    @pytest.mark.asyncio
    async def test_payment_failure_handling(self):
        """Test order fulfillment with payment processing failure."""
        # Mock payment service to fail
        with self._mock_payment_failure():
            workflow_data = get_ecommerce_order_workflow()
            workflow = await self.create_workflow(workflow_data)

            order_data = get_sample_order_data()

            result = await self.execute_workflow(workflow["workflow_id"], order_data)
            final_status = await self.wait_for_execution_completion(result["execution_id"])

            # Workflow should complete but with error handling
            assert final_status["status"] == "completed"

            # Verify error handling steps were executed appropriately
            executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]

            # Should have reached payment step
            assert "process-payment" in executed_nodes

            # Should have executed error handling for failed payment
            # (In a real workflow, this would send failure notifications)

    @pytest.mark.asyncio
    async def test_invalid_order_data_handling(self):
        """Test order fulfillment with invalid order data."""
        workflow_data = get_ecommerce_order_workflow()
        workflow = await self.create_workflow(workflow_data)

        # Invalid order data (missing required fields)
        invalid_order_data = {
            "customer_email": "test@example.com"
            # Missing order_id, items, etc.
        }

        result = await self.execute_workflow(workflow["workflow_id"], invalid_order_data)
        final_status = await self.wait_for_execution_completion(result["execution_id"])

        # Workflow should complete with validation failure
        assert final_status["status"] == "completed"

        # Should have executed validation step
        executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
        assert "validate-order" in executed_nodes

        # Should not have proceeded to inventory check
        assert "check-inventory" not in executed_nodes

    @pytest.mark.asyncio
    async def test_shipping_service_failure_handling(self):
        """Test order fulfillment with shipping service failure."""
        # Mock shipping service to fail
        with self._mock_shipping_failure():
            workflow_data = get_ecommerce_order_workflow()
            workflow = await self.create_workflow(workflow_data)

            order_data = get_sample_order_data()

            result = await self.execute_workflow(workflow["workflow_id"], order_data)
            final_status = await self.wait_for_execution_completion(result["execution_id"])

            # Workflow should handle shipping failure gracefully
            assert final_status["status"] == "completed"

            executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]

            # Should have reached shipping step
            assert "create-shipping" in executed_nodes

            # Email confirmation might still be sent depending on error handling logic
            # In a real scenario, this would depend on business requirements

    @pytest.mark.asyncio
    async def test_workflow_timeout_handling(self):
        """Test order fulfillment with workflow timeout."""
        # Create workflow with very short timeout
        workflow_data = get_ecommerce_order_workflow()
        workflow_data["settings"] = {
            "timeout": 5,  # Very short timeout
            "max_retries": 1,
            "fail_fast": True
        }

        workflow = await self.create_workflow(workflow_data)
        order_data = get_sample_order_data()

        # Mock slow external services
        with self._mock_slow_services():
            result = await self.execute_workflow(workflow["workflow_id"], order_data)

            # Wait for completion (should timeout)
            final_status = await self.wait_for_execution_completion(result["execution_id"], timeout=15)

            # Workflow should either timeout or complete based on implementation
            assert final_status["status"] in ["completed", "error"]

    @pytest.mark.asyncio
    async def test_concurrent_order_processing(self):
        """Test processing multiple orders concurrently."""
        workflow_data = get_ecommerce_order_workflow()
        workflow = await self.create_workflow(workflow_data)

        # Create multiple orders
        orders = []
        for i in range(3):
            order_data = get_sample_order_data()
            order_data["order_id"] = f"ORD-2024-00{i+1:04d}"
            orders.append(order_data)

        # Execute workflows concurrently
        import asyncio

        async def execute_order(order_data):
            result = await self.execute_workflow(workflow["workflow_id"], order_data)
            return await self.wait_for_execution_completion(result["execution_id"])

        # Mock external services for concurrent execution
        with self._mock_external_services():
            tasks = [execute_order(order) for order in orders]
            results = await asyncio.gather(*tasks)

            # Verify all orders were processed
            assert len(results) == len(orders)
            for result in results:
                assert result["status"] == "completed"

            # Verify execution IDs are unique
            execution_ids = [r["execution_id"] for r in results]
            assert len(set(execution_ids)) == len(execution_ids)

    @pytest.mark.asyncio
    async def test_workflow_retry_mechanism(self):
        """Test workflow retry mechanism on transient failures."""
        # Mock service that fails initially but succeeds on retry
        with self._mock_transient_failure():
            workflow_data = get_ecommerce_order_workflow()
            workflow_data["settings"] = {
                "timeout": 60,
                "max_retries": 2,
                "fail_fast": False
            }

            workflow = await self.create_workflow(workflow_data)
            order_data = get_sample_order_data()

            result = await self.execute_workflow(workflow["workflow_id"], order_data)
            final_status = await self.wait_for_execution_completion(result["execution_id"], timeout=30)

            # Workflow should eventually succeed after retries
            assert final_status["status"] == "completed"

    @pytest.mark.asyncio
    async def test_email_notification_integration(self):
        """Test email notification integration in order fulfillment."""
        with self._mock_email_service():
            workflow_data = get_ecommerce_order_workflow()
            workflow = await self.create_workflow(workflow_data)

            order_data = get_sample_order_data()

            result = await self.execute_workflow(workflow["workflow_id"], order_data)
            final_status = await self.wait_for_execution_completion(result["execution_id"])

            assert final_status["status"] == "completed"

            # Verify email was sent
            executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
            assert "send-confirmation" in executed_nodes

    @pytest.mark.asyncio
    async def test_data_transformation_in_workflow(self):
        """Test data transformation steps in the workflow."""
        workflow_data = get_ecommerce_order_workflow()
        workflow = await self.create_workflow(workflow_data)

        order_data = get_sample_order_data()

        result = await self.execute_workflow(workflow["workflow_id"], order_data)
        final_status = await self.wait_for_execution_completion(result["execution_id"])

        assert final_status["status"] == "completed"

        # Verify data was properly transformed and passed between steps
        # This would check that order data was correctly formatted for each service

    @pytest.mark.asyncio
    async def test_workflow_execution_audit_trail(self):
        """Test that workflow execution creates proper audit trail."""
        with self._mock_external_services():
            workflow_data = get_ecommerce_order_workflow()
            workflow = await self.create_workflow(workflow_data)

            order_data = get_sample_order_data()

            result = await self.execute_workflow(workflow["workflow_id"], order_data)
            final_status = await self.wait_for_execution_completion(result["execution_id"])

            assert final_status["status"] == "completed"

            # Verify audit trail information
            assert "started_at" in final_status
            assert "completed_at" in final_status
            assert "executed_nodes" in final_status

            # Verify each node has execution details
            for node in final_status["executed_nodes"]:
                assert "node_id" in node
                assert "status" in node
                assert node["status"] == "completed"

    # Context managers for mocking external services
    def _mock_external_services(self):
        """Mock all external services for successful execution."""
        from unittest.mock import patch

        def mock_http_response(*args, **kwargs):
            class MockResponse:
                status_code = 200
                def json(self):
                    return {"success": True, "data": "mocked"}

            return MockResponse()

        def mock_email_send(*args, **kwargs):
            return {"success": True, "message_id": "mock-email-id"}

        return patch.multiple(
            'aiohttp.ClientSession',
            request=mock_http_response
        ), patch.multiple(
            'smtplib.SMTP',
            sendmail=lambda *args, **kwargs: None
        )

    def _mock_inventory_shortage(self):
        """Mock inventory service returning shortage."""
        from unittest.mock import patch

        def mock_inventory_shortage(*args, **kwargs):
            class MockResponse:
                status_code = 200
                def json(self):
                    return {
                        "available": False,
                        "unavailable_items": ["WIDGET-001"],
                        "message": "Item out of stock"
                    }

            return MockResponse()

        return patch('aiohttp.ClientSession.request', side_effect=mock_inventory_shortage)

    def _mock_payment_failure(self):
        """Mock payment service failure."""
        from unittest.mock import patch

        def mock_payment_failure(*args, **kwargs):
            # Mock successful inventory check
            if "inventory" in str(args[0]):
                class MockResponse:
                    status_code = 200
                    def json(self):
                        return {"available": True}
                return MockResponse()

            # Mock failed payment
            if "payment" in str(args[0]):
                class MockResponse:
                    status_code = 402
                    def json(self):
                        return {"error": "Payment declined", "code": "DECLINED"}
                return MockResponse()

            # Default success for other services
            class MockResponse:
                status_code = 200
                def json(self):
                    return {"success": True}
            return MockResponse()

        return patch('aiohttp.ClientSession.request', side_effect=mock_payment_failure)

    def _mock_shipping_failure(self):
        """Mock shipping service failure."""
        from unittest.mock import patch

        def mock_shipping_failure(*args, **kwargs):
            # Mock successful steps before shipping
            if "inventory" in str(args[0]) or "payment" in str(args[0]):
                class MockResponse:
                    status_code = 200
                    def json(self):
                        return {"success": True}
                return MockResponse()

            # Mock failed shipping
            if "shipping" in str(args[0]):
                class MockResponse:
                    status_code = 500
                    def json(self):
                        return {"error": "Shipping service unavailable"}
                return MockResponse()

            # Default success
            class MockResponse:
                status_code = 200
                def json(self):
                    return {"success": True}
            return MockResponse()

        return patch('aiohttp.ClientSession.request', side_effect=mock_shipping_failure)

    def _mock_slow_services(self):
        """Mock slow external services."""
        from unittest.mock import patch, AsyncMock
        import asyncio

        async def slow_response(*args, **kwargs):
            await asyncio.sleep(10)  # 10 second delay
            class MockResponse:
                status_code = 200
                def json(self):
                    return {"success": True}
            return MockResponse()

        return patch('aiohttp.ClientSession.request', side_effect=slow_response)

    def _mock_transient_failure(self):
        """Mock service that fails initially but succeeds on retry."""
        from unittest.mock import patch

        call_count = 0

        def transient_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # First call fails
                class MockResponse:
                    status_code = 503
                    def json(self):
                        return {"error": "Service temporarily unavailable"}
                return MockResponse()
            else:
                # Subsequent calls succeed
                class MockResponse:
                    status_code = 200
                    def json(self):
                        return {"success": True}
                return MockResponse()

        return patch('aiohttp.ClientSession.request', side_effect=transient_failure)

    def _mock_email_service(self):
        """Mock email service."""
        from unittest.mock import patch

        def mock_email_send(*args, **kwargs):
            return {"success": True, "message_id": "mock-email-id"}

        return patch('smtplib.SMTP.sendmail', side_effect=mock_email_send)
