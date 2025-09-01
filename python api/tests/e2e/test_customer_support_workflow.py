"""
End-to-end tests for customer support workflow.

This test suite verifies the complete customer support ticket processing workflow
including ticket categorization, priority assessment, automated responses, and escalation.
"""

import pytest
import json
from unittest.mock import patch, AsyncMock
from typing import Dict, Any

from tests.e2e import E2ETestBase, get_customer_support_workflow, get_sample_support_ticket


class TestCustomerSupportWorkflow(E2ETestBase):
    """Test complete customer support workflow."""

    @pytest.mark.asyncio
    async def test_successful_ticket_processing(self):
        """Test successful customer support ticket processing."""
        with self._mock_support_services():
            # Create the support workflow
            workflow_data = get_customer_support_workflow()
            workflow = await self.create_workflow(workflow_data)

            # Get test ticket data
            ticket_data = get_sample_support_ticket()

            # Execute the workflow
            result = await self.execute_workflow(workflow["workflow_id"], ticket_data)

            # Wait for completion
            final_status = await self.wait_for_execution_completion(result["execution_id"], timeout=60)

            # Verify workflow completed successfully
            assert final_status["status"] == "completed"

            # Verify all expected steps were executed
            expected_steps = [
                "categorize-ticket",
                "check-urgency",
                "generate-response",
                "send-response"
            ]

            await self.verify_workflow_results(final_status, expected_steps)

    @pytest.mark.asyncio
    async def test_high_priority_ticket_escalation(self):
        """Test high-priority ticket escalation."""
        with self._mock_support_services():
            workflow_data = get_customer_support_workflow()
            workflow = await self.create_workflow(workflow_data)

            # High-priority ticket
            urgent_ticket = get_sample_support_ticket()
            urgent_ticket["priority"] = "high"
            urgent_ticket["subject"] = "URGENT: System Down"

            result = await self.execute_workflow(workflow["workflow_id"], urgent_ticket)
            final_status = await self.wait_for_execution_completion(result["execution_id"])

            assert final_status["status"] == "completed"

            executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]

            # Should have executed urgency check
            assert "check-urgency" in executed_nodes

            # Should have routed to high-priority handling
            assert "route-high-priority" in executed_nodes

            # Should not have generated automated response
            assert "generate-response" not in executed_nodes

    @pytest.mark.asyncio
    async def test_ai_powered_ticket_categorization(self):
        """Test AI-powered ticket categorization."""
        with self._mock_ai_services():
            workflow_data = get_customer_support_workflow()
            workflow = await self.create_workflow(workflow_data)

            ticket_data = get_sample_support_ticket()

            result = await self.execute_workflow(workflow["workflow_id"], ticket_data)
            final_status = await self.wait_for_execution_completion(result["execution_id"])

            assert final_status["status"] == "completed"

            # Verify AI categorization was executed
            executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
            assert "categorize-ticket" in executed_nodes

    @pytest.mark.asyncio
    async def test_automated_response_generation(self):
        """Test automated response generation for tickets."""
        with self._mock_ai_services():
            workflow_data = get_customer_support_workflow()
            workflow = await self.create_workflow(workflow_data)

            ticket_data = get_sample_support_ticket()

            result = await self.execute_workflow(workflow["workflow_id"], ticket_data)
            final_status = await self.wait_for_execution_completion(result["execution_id"])

            assert final_status["status"] == "completed"

            executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
            assert "generate-response" in executed_nodes
            assert "send-response" in executed_nodes

    @pytest.mark.asyncio
    async def test_ticket_escalation_workflow(self):
        """Test ticket escalation to human agents."""
        workflow_data = self._get_escalation_workflow()
        workflow = await self.create_workflow(workflow_data)

        # Complex ticket requiring escalation
        complex_ticket = {
            "ticket_id": "TICK-999",
            "customer_email": "enterprise@example.com",
            "subject": "Complex Integration Issue",
            "description": "We're experiencing issues with the API integration that requires immediate attention from a senior engineer.",
            "priority": "high",
            "category": "technical",
            "company_size": "enterprise",
            "contract_level": "premium"
        }

        result = await self.execute_workflow(workflow["workflow_id"], complex_ticket)
        final_status = await self.wait_for_execution_completion(result["execution_id"])

        assert final_status["status"] == "completed"

        executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
        assert "escalate-to-senior" in executed_nodes

    @pytest.mark.asyncio
    async def test_customer_satisfaction_followup(self):
        """Test customer satisfaction follow-up workflow."""
        workflow_data = self._get_satisfaction_workflow()
        workflow = await self.create_workflow(workflow_data)

        # Resolved ticket data
        resolved_ticket = {
            "ticket_id": "TICK-456",
            "customer_email": "customer@example.com",
            "resolution_time": "2 hours",
            "satisfaction_score": 4
        }

        result = await self.execute_workflow(workflow["workflow_id"], resolved_ticket)
        final_status = await self.wait_for_execution_completion(result["execution_id"])

        assert final_status["status"] == "completed"

        executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
        assert "send-satisfaction-survey" in executed_nodes

    @pytest.mark.asyncio
    async def test_knowledge_base_integration(self):
        """Test knowledge base integration for self-service."""
        workflow_data = self._get_knowledge_workflow()
        workflow = await self.create_workflow(workflow_data)

        # Common issue ticket
        common_issue = {
            "ticket_id": "TICK-789",
            "customer_email": "user@example.com",
            "subject": "Password Reset",
            "description": "I forgot my password and need to reset it.",
            "category": "account"
        }

        result = await self.execute_workflow(workflow["workflow_id"], common_issue)
        final_status = await self.wait_for_execution_completion(result["execution_id"])

        assert final_status["status"] == "completed"

        executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
        assert "search-knowledge-base" in executed_nodes
        assert "send-self-service-link" in executed_nodes

    @pytest.mark.asyncio
    async def test_multi_channel_support_routing(self):
        """Test routing tickets across multiple support channels."""
        workflow_data = self._get_multi_channel_workflow()
        workflow = await self.create_workflow(workflow_data)

        # Ticket with multiple contact preferences
        multi_channel_ticket = {
            "ticket_id": "TICK-111",
            "customer_email": "customer@example.com",
            "phone": "+1234567890",
            "preferred_contact": "phone",
            "urgency": "high",
            "subject": "Urgent Technical Issue"
        }

        result = await self.execute_workflow(workflow["workflow_id"], multi_channel_ticket)
        final_status = await self.wait_for_execution_completion(result["execution_id"])

        assert final_status["status"] == "completed"

        executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
        assert "phone-escalation" in executed_nodes

    @pytest.mark.asyncio
    async def test_support_analytics_and_reporting(self):
        """Test support analytics and reporting workflow."""
        workflow_data = self._get_analytics_workflow()
        workflow = await self.create_workflow(workflow_data)

        # Support metrics data
        metrics_data = {
            "period": "daily",
            "total_tickets": 150,
            "resolved_tickets": 142,
            "average_resolution_time": "4.2 hours",
            "customer_satisfaction": 4.3,
            "top_categories": ["technical", "billing", "account"]
        }

        result = await self.execute_workflow(workflow["workflow_id"], metrics_data)
        final_status = await self.wait_for_execution_completion(result["execution_id"])

        assert final_status["status"] == "completed"

        executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
        assert "generate-report" in executed_nodes
        assert "send-management-report" in executed_nodes

    @pytest.mark.asyncio
    async def test_support_sla_monitoring(self):
        """Test SLA monitoring and breach alerts."""
        workflow_data = self._get_sla_workflow()
        workflow = await self.create_workflow(workflow_data)

        # SLA breach scenario
        sla_breach = {
            "ticket_id": "TICK-222",
            "customer_email": "vip@example.com",
            "priority": "high",
            "created_at": "2024-01-15T08:00:00Z",
            "sla_deadline": "2024-01-15T12:00:00Z",
            "current_time": "2024-01-15T12:30:00Z",
            "breach_duration": "30 minutes"
        }

        result = await self.execute_workflow(workflow["workflow_id"], sla_breach)
        final_status = await self.wait_for_execution_completion(result["execution_id"])

        assert final_status["status"] == "completed"

        executed_nodes = [node["node_id"] for node in final_status["executed_nodes"]]
        assert "sla-breach-alert" in executed_nodes

    # Context managers for mocking support services
    def _mock_support_services(self):
        """Mock all support-related external services."""
        from unittest.mock import patch

        def mock_ai_response(*args, **kwargs):
            # Mock OpenAI categorization
            class MockResponse:
                status_code = 200
                def json(self):
                    return {
                        "choices": [{
                            "message": {
                                "content": "billing"
                            }
                        }]
                    }
            return MockResponse()

        def mock_email_response(*args, **kwargs):
            # Mock email sending
            return {"success": True, "message_id": "email-123"}

        return patch.multiple(
            'aiohttp.ClientSession',
            request=mock_ai_response
        ), patch.multiple(
            'smtplib.SMTP',
            sendmail=mock_email_response
        )

    def _mock_ai_services(self):
        """Mock AI services for support automation."""
        from unittest.mock import patch

        def mock_openai_response(*args, **kwargs):
            if "categorize" in str(args[0]).lower():
                class MockResponse:
                    status_code = 200
                    def json(self):
                        return {
                            "choices": [{
                                "message": {
                                    "content": "billing"
                                }
                            }]
                        }
                return MockResponse()
            elif "generate" in str(args[0]).lower():
                class MockResponse:
                    status_code = 200
                    def json(self):
                        return {
                            "choices": [{
                                "message": {
                                    "content": "Thank you for your billing inquiry. I'll help you resolve this issue."
                                }
                            }]
                        }
                return MockResponse()
            else:
                class MockResponse:
                    status_code = 200
                    def json(self):
                        return {"success": True}
                return MockResponse()

        return patch('aiohttp.ClientSession.request', side_effect=mock_openai_response)

    # Helper methods for specialized support workflows
    def _get_escalation_workflow(self):
        """Get ticket escalation workflow."""
        return {
            "name": "Ticket Escalation",
            "description": "Escalate complex tickets to appropriate teams",
            "nodes": [
                {
                    "id": "assess-complexity",
                    "type": "action",
                    "action_type": "data_filter",
                    "name": "Assess Complexity",
                    "config": {
                        "filter_condition": "input_data.company_size == 'enterprise' || input_data.contract_level == 'premium'"
                    }
                },
                {
                    "id": "escalate-to-senior",
                    "type": "action",
                    "action_type": "send_email",
                    "name": "Escalate to Senior Engineer",
                    "config": {
                        "to_email": "senior-engineers@company.com",
                        "subject": "ESCALATION: Enterprise Customer Issue",
                        "body": "Enterprise customer requires senior engineer attention."
                    }
                }
            ],
            "connections": [
                {"from": "assess-complexity", "to": "escalate-to-senior", "condition": "result.passed == true"}
            ]
        }

    def _get_satisfaction_workflow(self):
        """Get customer satisfaction follow-up workflow."""
        return {
            "name": "Customer Satisfaction",
            "description": "Follow up with customers after ticket resolution",
            "nodes": [
                {
                    "id": "send-satisfaction-survey",
                    "type": "action",
                    "action_type": "send_email",
                    "name": "Send Satisfaction Survey",
                    "config": {
                        "to_email": "${input_data.customer_email}",
                        "subject": "How did we do? Share your feedback!",
                        "body": "We resolved your ticket in ${input_data.resolution_time}. Please take a moment to rate your experience."
                    }
                }
            ],
            "connections": []
        }

    def _get_knowledge_workflow(self):
        """Get knowledge base integration workflow."""
        return {
            "name": "Knowledge Base Integration",
            "description": "Search knowledge base for self-service solutions",
            "nodes": [
                {
                    "id": "search-knowledge-base",
                    "type": "action",
                    "action_type": "http",
                    "name": "Search Knowledge Base",
                    "config": {
                        "method": "GET",
                        "url": "https://api.knowledge.com/search",
                        "params": {"query": "${input_data.subject}"}
                    }
                },
                {
                    "id": "send-self-service-link",
                    "type": "action",
                    "action_type": "send_email",
                    "name": "Send Self-Service Link",
                    "config": {
                        "to_email": "${input_data.customer_email}",
                        "subject": "Quick Solution for: ${input_data.subject}",
                        "body": "We found a solution in our knowledge base: [Link]"
                    }
                }
            ],
            "connections": [
                {"from": "search-knowledge-base", "to": "send-self-service-link"}
            ]
        }

    def _get_multi_channel_workflow(self):
        """Get multi-channel support routing workflow."""
        return {
            "name": "Multi-Channel Support",
            "description": "Route tickets across multiple support channels",
            "nodes": [
                {
                    "id": "assess-channel",
                    "type": "action",
                    "action_type": "data_filter",
                    "name": "Assess Preferred Channel",
                    "config": {
                        "filter_condition": "input_data.preferred_contact == 'phone' && input_data.urgency == 'high'"
                    }
                },
                {
                    "id": "phone-escalation",
                    "type": "action",
                    "action_type": "http",
                    "name": "Phone Escalation",
                    "config": {
                        "method": "POST",
                        "url": "https://api.phone.com/calls",
                        "body": {
                            "to": "${input_data.phone}",
                            "message": "Urgent support call from ${input_data.subject}"
                        }
                    }
                }
            ],
            "connections": [
                {"from": "assess-channel", "to": "phone-escalation", "condition": "result.passed == true"}
            ]
        }

    def _get_analytics_workflow(self):
        """Get support analytics workflow."""
        return {
            "name": "Support Analytics",
            "description": "Generate support performance reports",
            "nodes": [
                {
                    "id": "generate-report",
                    "type": "action",
                    "action_type": "data_transform",
                    "name": "Generate Report",
                    "config": {
                        "transform_type": "add_fields",
                        "fields": {
                            "resolution_rate": "${input_data.resolved_tickets / input_data.total_tickets * 100}%",
                            "report_date": "${timestamp}"
                        }
                    }
                },
                {
                    "id": "send-management-report",
                    "type": "action",
                    "action_type": "send_email",
                    "name": "Send Management Report",
                    "config": {
                        "to_email": "management@company.com",
                        "subject": "Daily Support Report - ${input_data.period}",
                        "body": "Support metrics summary..."
                    }
                }
            ],
            "connections": [
                {"from": "generate-report", "to": "send-management-report"}
            ]
        }

    def _get_sla_workflow(self):
        """Get SLA monitoring workflow."""
        return {
            "name": "SLA Monitoring",
            "description": "Monitor and alert on SLA breaches",
            "nodes": [
                {
                    "id": "sla-breach-alert",
                    "type": "action",
                    "action_type": "send_email",
                    "name": "SLA Breach Alert",
                    "config": {
                        "to_email": "support-manager@company.com",
                        "subject": "SLA BREACH ALERT: ${input_data.ticket_id}",
                        "body": "SLA breach detected for ticket ${input_data.ticket_id}. Breach duration: ${input_data.breach_duration}"
                    }
                }
            ],
            "connections": []
        }

