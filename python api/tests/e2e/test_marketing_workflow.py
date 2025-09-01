"""
End-to-end tests for marketing automation workflow.

This test suite verifies the complete marketing automation workflow including
lead capture, validation, CRM integration, email marketing, and analytics.
"""

import pytest
import json
from unittest.mock import patch, AsyncMock
from typing import Dict, Any

from tests.e2e import E2ETestBase, get_marketing_automation_workflow, get_sample_lead_data


class TestMarketingAutomationWorkflow(E2ETestBase):
    """Test complete marketing automation workflow."""

    @pytest.mark.asyncio
    async def test_successful_lead_capture_and_nurturing(self):
        """Test successful lead capture and nurturing workflow."""
        with self._mock_marketing_services():
            # Create the marketing workflow
            workflow_data = get_marketing_automation_workflow()
            workflow = await self.create_workflow(workflow_data)

            # Get test lead data
            lead_data = get_sample_lead_data()

            # Execute the workflow (simulating webhook trigger)
            result = await self.execute_workflow(workflow["workflow_id"], lead_data)

            # Wait for completion
            final_status = await self.wait_for_execution_completion(result["execution_id"], timeout=45)

            # Verify workflow completed successfully
            assert final_status["status"] == "completed"

            # Verify all expected steps were executed
            expected_steps = [
                "validate-lead",
                "check-existing",
                "create-lead",
                "send-welcome",
                "add-to-segment"
            ]

            await self.verify_workflow_results(final_status, expected_steps)

    @pytest.mark.asyncio
    async def test_existing_lead_handling(self):
        """Test handling of leads that already exist in the system."""
        with self._mock_existing_lead():
            workflow_data = get_marketing_automation_workflow()
            workflow = await self.create_workflow(workflow_data)

            lead_data = get_sample_lead_data()

            result = await self.execute_workflow(workflow["workflow_id"], lead_data)
            final_status = await self.wait_for_execution_completion(result["execution_id"])

            assert final_status["status"] == "completed"

            executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]

            # Should validate and check existing
            assert "validate-lead" in executed_nodes
            assert "check-existing" in executed_nodes

            # Should skip lead creation for existing leads
            assert "create-lead" not in executed_nodes

            # Should still send welcome and add to segment
            assert "send-welcome" in executed_nodes
            assert "add-to-segment" in executed_nodes

    @pytest.mark.asyncio
    async def test_invalid_lead_data_handling(self):
        """Test handling of invalid lead data."""
        workflow_data = get_marketing_automation_workflow()
        workflow = await self.create_workflow(workflow_data)

        # Invalid lead data (missing required fields)
        invalid_lead_data = {
            "source": "website"
            # Missing email and name
        }

        result = await self.execute_workflow(workflow["workflow_id"], invalid_lead_data)
        final_status = await self.wait_for_execution_completion(result["execution_id"])

        assert final_status["status"] == "completed"

        executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]

        # Should have executed validation
        assert "validate-lead" in executed_nodes

        # Should not have proceeded with other steps
        assert "check-existing" not in executed_nodes
        assert "create-lead" not in executed_nodes
        assert "send-welcome" not in executed_nodes

    @pytest.mark.asyncio
    async def test_crm_integration_failure_handling(self):
        """Test handling of CRM integration failures."""
        with self._mock_crm_failure():
            workflow_data = get_marketing_automation_workflow()
            workflow = await self.create_workflow(workflow_data)

            lead_data = get_sample_lead_data()

            result = await self.execute_workflow(workflow["workflow_id"], lead_data)
            final_status = await self.wait_for_execution_completion(result["execution_id"])

            # Workflow should handle CRM failure gracefully
            assert final_status["status"] == "completed"

            executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]

            # Should have reached CRM step
            assert "create-lead" in executed_nodes

            # Should still attempt email and segment steps
            # (depending on error handling logic)

    @pytest.mark.asyncio
    async def test_email_service_failure_handling(self):
        """Test handling of email service failures."""
        with self._mock_email_failure():
            workflow_data = get_marketing_automation_workflow()
            workflow = await self.create_workflow(workflow_data)

            lead_data = get_sample_lead_data()

            result = await self.execute_workflow(workflow["workflow_id"], lead_data)
            final_status = await self.wait_for_execution_completion(result["execution_id"])

            assert final_status["status"] == "completed"

            executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]

            # Should have executed steps before email
            assert "validate-lead" in executed_nodes
            assert "check-existing" in executed_nodes
            assert "create-lead" in executed_nodes

            # Email step should have been attempted
            assert "send-welcome" in executed_nodes

            # Segment addition might still work
            # (depending on whether it depends on email success)

    @pytest.mark.asyncio
    async def test_segmentation_service_integration(self):
        """Test email segmentation service integration."""
        with self._mock_segmentation_service():
            workflow_data = get_marketing_automation_workflow()
            workflow = await self.create_workflow(workflow_data)

            lead_data = get_sample_lead_data()

            result = await self.execute_workflow(workflow["workflow_id"], lead_data)
            final_status = await self.wait_for_execution_completion(result["execution_id"])

            assert final_status["status"] == "completed"

            executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
            assert "add-to-segment" in executed_nodes

    @pytest.mark.asyncio
    async def test_lead_scoring_and_qualification(self):
        """Test lead scoring and qualification logic."""
        workflow_data = self._get_lead_scoring_workflow()
        workflow = await self.create_workflow(workflow_data)

        # High-value lead
        high_value_lead = {
            "email": "ceo@bigcompany.com",
            "name": "Jane CEO",
            "company": "Big Tech Corp",
            "job_title": "CEO",
            "company_size": "1000+",
            "budget": "high"
        }

        result = await self.execute_workflow(workflow["workflow_id"], high_value_lead)
        final_status = await self.wait_for_execution_completion(result["execution_id"])

        assert final_status["status"] == "completed"

        # Verify high-priority handling
        executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
        assert "high-priority-routing" in executed_nodes

    @pytest.mark.asyncio
    async def test_multi_channel_lead_nurturing(self):
        """Test multi-channel lead nurturing workflow."""
        workflow_data = self._get_multi_channel_workflow()
        workflow = await self.create_workflow(workflow_data)

        lead_data = get_sample_lead_data()
        lead_data["preferred_channel"] = "email"

        result = await self.execute_workflow(workflow["workflow_id"], lead_data)
        final_status = await self.wait_for_execution_completion(result["execution_id"])

        assert final_status["status"] == "completed"

        executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
        assert "email-nurture" in executed_nodes

    @pytest.mark.asyncio
    async def test_abandoned_cart_recovery(self):
        """Test abandoned cart recovery workflow."""
        workflow_data = self._get_cart_recovery_workflow()
        workflow = await self.create_workflow(workflow_data)

        cart_data = {
            "cart_id": "cart-123",
            "customer_email": "customer@example.com",
            "customer_name": "John Customer",
            "items": [
                {"name": "Product A", "price": 99.99},
                {"name": "Product B", "price": 49.99}
            ],
            "total": 149.98,
            "abandoned_at": "2024-01-15T10:00:00Z"
        }

        result = await self.execute_workflow(workflow["workflow_id"], cart_data)
        final_status = await self.wait_for_execution_completion(result["execution_id"])

        assert final_status["status"] == "completed"

        executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
        assert "send-recovery-email" in executed_nodes

    @pytest.mark.asyncio
    async def test_lead_qualification_workflow(self):
        """Test lead qualification and routing workflow."""
        workflow_data = self._get_lead_qualification_workflow()
        workflow = await self.create_workflow(workflow_data)

        # Marketing qualified lead
        mql_data = {
            "email": "lead@example.com",
            "name": "Marketing Lead",
            "score": 85,
            "source": "webinar",
            "interests": ["product-a", "enterprise"],
            "timeline": "3-6 months"
        }

        result = await self.execute_workflow(workflow["workflow_id"], mql_data)
        final_status = await self.wait_for_execution_completion(result["execution_id"])

        assert final_status["status"] == "completed"

        executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
        assert "mql-routing" in executed_nodes

    @pytest.mark.asyncio
    async def test_newsletter_subscription_workflow(self):
        """Test newsletter subscription and welcome series."""
        workflow_data = self._get_newsletter_workflow()
        workflow = await self.create_workflow(workflow_data)

        subscription_data = {
            "email": "subscriber@example.com",
            "name": "Newsletter Reader",
            "interests": ["technology", "business"],
            "source": "website-footer"
        }

        result = await self.execute_workflow(workflow["workflow_id"], subscription_data)
        final_status = await self.wait_for_execution_completion(result["execution_id"])

        assert final_status["status"] == "completed"

        executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
        assert "welcome-email" in executed_nodes
        assert "tag-subscriber" in executed_nodes

    # Context managers for mocking marketing services
    def _mock_marketing_services(self):
        """Mock all marketing-related external services."""
        from unittest.mock import patch

        def mock_crm_response(*args, **kwargs):
            # Mock CRM lead creation
            class MockResponse:
                status_code = 201
                def json(self):
                    return {"id": "lead-123", "status": "created"}
            return MockResponse()

        def mock_email_response(*args, **kwargs):
            # Mock email sending
            return {"success": True, "message_id": "email-123"}

        def mock_segment_response(*args, **kwargs):
            # Mock segmentation service
            class MockResponse:
                status_code = 200
                def json(self):
                    return {"segment_id": "new-leads", "added": True}
            return MockResponse()

        return patch.multiple(
            'aiohttp.ClientSession',
            request=mock_crm_response
        ), patch.multiple(
            'smtplib.SMTP',
            sendmail=mock_email_response
        )

    def _mock_existing_lead(self):
        """Mock CRM returning existing lead."""
        from unittest.mock import patch

        def mock_existing_lead(*args, **kwargs):
            if "check" in str(args[0]).lower():
                # Mock existing lead found
                class MockResponse:
                    status_code = 200
                    def json(self):
                        return {
                            "id": "existing-lead-123",
                            "email": "jane.smith@example.com",
                            "status": "active"
                        }
                return MockResponse()
            else:
                # Default success for other calls
                class MockResponse:
                    status_code = 200
                    def json(self):
                        return {"success": True}
                return MockResponse()

        return patch('aiohttp.ClientSession.request', side_effect=mock_existing_lead)

    def _mock_crm_failure(self):
        """Mock CRM service failure."""
        from unittest.mock import patch

        def mock_crm_failure(*args, **kwargs):
            if "crm" in str(args[0]).lower():
                class MockResponse:
                    status_code = 503
                    def json(self):
                        return {"error": "CRM service unavailable"}
                return MockResponse()
            else:
                class MockResponse:
                    status_code = 200
                    def json(self):
                        return {"success": True}
                return MockResponse()

        return patch('aiohttp.ClientSession.request', side_effect=mock_crm_failure)

    def _mock_email_failure(self):
        """Mock email service failure."""
        from unittest.mock import patch

        def mock_email_failure(*args, **kwargs):
            # Mock successful services except email
            if "email" in str(args[0]).lower():
                raise Exception("SMTP connection failed")
            else:
                class MockResponse:
                    status_code = 200
                    def json(self):
                        return {"success": True}
                return MockResponse()

        return patch('aiohttp.ClientSession.request', side_effect=mock_email_failure)

    def _mock_segmentation_service(self):
        """Mock email segmentation service."""
        from unittest.mock import patch

        def mock_segment_response(*args, **kwargs):
            if "segment" in str(args[0]).lower():
                class MockResponse:
                    status_code = 200
                    def json(self):
                        return {
                            "segment_id": "new-subscribers",
                            "contact_count": 1,
                            "added": True
                        }
                return MockResponse()
            else:
                class MockResponse:
                    status_code = 200
                    def json(self):
                        return {"success": True}
                return MockResponse()

        return patch('aiohttp.ClientSession.request', side_effect=mock_segment_response)

    # Helper methods for specialized workflows
    def _get_lead_scoring_workflow(self):
        """Get lead scoring and qualification workflow."""
        return {
            "name": "Lead Scoring Workflow",
            "description": "Score and qualify leads based on criteria",
            "nodes": [
                {
                    "id": "score-lead",
                    "type": "action",
                    "action_type": "data_transform",
                    "name": "Score Lead",
                    "config": {
                        "transform_type": "add_fields",
                        "fields": {
                            "score": "85",
                            "qualification": "MQL"
                        }
                    }
                },
                {
                    "id": "high-priority-routing",
                    "type": "action",
                    "action_type": "send_email",
                    "name": "High Priority Routing",
                    "config": {
                        "to_email": "sales@company.com",
                        "subject": "High Priority Lead: ${input_data.name}",
                        "body": "New high-value lead requires immediate attention."
                    }
                }
            ],
            "connections": [
                {"from": "score-lead", "to": "high-priority-routing"}
            ]
        }

    def _get_multi_channel_workflow(self):
        """Get multi-channel marketing workflow."""
        return {
            "name": "Multi-Channel Marketing",
            "description": "Engage leads across multiple channels",
            "nodes": [
                {
                    "id": "channel-router",
                    "type": "action",
                    "action_type": "data_filter",
                    "name": "Route by Channel",
                    "config": {
                        "filter_condition": "input_data.preferred_channel == 'email'"
                    }
                },
                {
                    "id": "email-nurture",
                    "type": "action",
                    "action_type": "send_email",
                    "name": "Email Nurture",
                    "config": {
                        "to_email": "${input_data.email}",
                        "subject": "Welcome to our community!",
                        "body": "Personalized email content..."
                    }
                }
            ],
            "connections": [
                {"from": "channel-router", "to": "email-nurture", "condition": "result.passed == true"}
            ]
        }

    def _get_cart_recovery_workflow(self):
        """Get abandoned cart recovery workflow."""
        return {
            "name": "Cart Recovery Workflow",
            "description": "Recover abandoned shopping carts",
            "nodes": [
                {
                    "id": "send-recovery-email",
                    "type": "action",
                    "action_type": "send_email",
                    "name": "Send Recovery Email",
                    "config": {
                        "to_email": "${input_data.customer_email}",
                        "subject": "Complete Your Purchase",
                        "body": "We noticed you left items in your cart..."
                    }
                },
                {
                    "id": "update-cart-status",
                    "type": "action",
                    "action_type": "http",
                    "name": "Update Cart Status",
                    "config": {
                        "method": "PUT",
                        "url": "https://api.ecommerce.com/carts/${input_data.cart_id}",
                        "body": {"status": "recovery_sent"}
                    }
                }
            ],
            "connections": [
                {"from": "send-recovery-email", "to": "update-cart-status"}
            ]
        }

    def _get_lead_qualification_workflow(self):
        """Get lead qualification workflow."""
        return {
            "name": "Lead Qualification",
            "description": "Qualify leads and route to appropriate teams",
            "nodes": [
                {
                    "id": "mql-routing",
                    "type": "action",
                    "action_type": "send_email",
                    "name": "MQL Routing",
                    "config": {
                        "to_email": "sales@company.com",
                        "subject": "New Marketing Qualified Lead",
                        "body": "Lead details: ${JSON.stringify(input_data)}"
                    }
                }
            ],
            "connections": []
        }

    def _get_newsletter_workflow(self):
        """Get newsletter subscription workflow."""
        return {
            "name": "Newsletter Subscription",
            "description": "Handle newsletter subscriptions and welcome series",
            "nodes": [
                {
                    "id": "welcome-email",
                    "type": "action",
                    "action_type": "send_email",
                    "name": "Welcome Email",
                    "config": {
                        "to_email": "${input_data.email}",
                        "subject": "Welcome to our newsletter!",
                        "body": "Thanks for subscribing, ${input_data.name}!"
                    }
                },
                {
                    "id": "tag-subscriber",
                    "type": "action",
                    "action_type": "http",
                    "name": "Tag Subscriber",
                    "config": {
                        "method": "POST",
                        "url": "https://api.email.com/contacts/${input_data.email}/tags",
                        "body": {"tags": ["newsletter", "new-subscriber"]}
                    }
                }
            ],
            "connections": [
                {"from": "welcome-email", "to": "tag-subscriber"}
            ]
        }

