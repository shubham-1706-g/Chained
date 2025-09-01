"""
End-to-end performance tests for FlowForge workflows.

This test suite verifies system performance under various load conditions,
testing concurrent executions, resource usage, and scalability.
"""

import pytest
import asyncio
import time
import statistics
from typing import Dict, Any, List
from unittest.mock import patch

from tests.e2e import E2ETestBase, get_ecommerce_order_workflow


class TestWorkflowPerformance(E2ETestBase):
    """Test workflow performance under various conditions."""

    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution_performance(self):
        """Test performance with multiple concurrent workflow executions."""
        with self._mock_fast_services():
            workflow_data = get_ecommerce_order_workflow()
            workflow = await self.create_workflow(workflow_data)

            # Test with different concurrency levels
            concurrency_levels = [5, 10, 20]
            performance_results = {}

            for concurrency in concurrency_levels:
                execution_times = await self._run_concurrent_workflows(
                    workflow["workflow_id"], concurrency
                )

                performance_results[concurrency] = {
                    "execution_times": execution_times,
                    "average_time": statistics.mean(execution_times),
                    "median_time": statistics.median(execution_times),
                    "min_time": min(execution_times),
                    "max_time": max(execution_times),
                    "total_time": sum(execution_times)
                }

            # Verify performance metrics
            for concurrency, metrics in performance_results.items():
                # Average execution time should be reasonable
                assert metrics["average_time"] < 10.0  # Less than 10 seconds

                # No execution should take too long
                assert metrics["max_time"] < 30.0  # Less than 30 seconds

                print(f"Concurrency {concurrency}: Avg {metrics['average_time']:.2f}s, Max {metrics['max_time']:.2f}s")

    @pytest.mark.asyncio
    async def test_workflow_execution_throughput(self):
        """Test workflow execution throughput over time."""
        with self._mock_fast_services():
            workflow_data = get_ecommerce_order_workflow()
            workflow = await self.create_workflow(workflow_data)

            # Run continuous workflow executions for 30 seconds
            start_time = time.time()
            end_time = start_time + 30
            execution_count = 0
            execution_times = []

            while time.time() < end_time:
                batch_start = time.time()
                result = await self.execute_workflow(workflow["workflow_id"], {"batch": execution_count})
                final_status = await self.wait_for_execution_completion(result["execution_id"], timeout=10)

                if final_status["status"] == "completed":
                    execution_time = time.time() - batch_start
                    execution_times.append(execution_time)
                    execution_count += 1

            # Calculate throughput metrics
            total_time = time.time() - start_time
            throughput_per_second = execution_count / total_time
            average_execution_time = statistics.mean(execution_times) if execution_times else 0

            print(f"Throughput: {throughput_per_second:.2f} workflows/second")
            print(f"Average execution time: {average_execution_time:.3f}s")
            print(f"Total executions: {execution_count}")

            # Verify reasonable throughput
            assert throughput_per_second > 0.5  # At least 0.5 workflows per second
            assert average_execution_time < 5.0  # Average under 5 seconds

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage patterns under load."""
        import psutil
        import os

        with self._mock_fast_services():
            workflow_data = get_ecommerce_order_workflow()
            workflow = await self.create_workflow(workflow_data)

            # Get initial memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Run multiple concurrent workflows
            concurrency = 10
            tasks = []
            for i in range(concurrency):
                result = await self.execute_workflow(workflow["workflow_id"], {"test": i})
                tasks.append(self.wait_for_execution_completion(result["execution_id"]))

            # Wait for all to complete
            await asyncio.gather(*tasks)

            # Check memory usage after load
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            print(f"Initial memory: {initial_memory:.1f}MB")
            print(f"Final memory: {final_memory:.1f}MB")
            print(f"Memory increase: {memory_increase:.1f}MB")

            # Memory increase should be reasonable
            assert memory_increase < 100  # Less than 100MB increase

    @pytest.mark.asyncio
    async def test_database_connection_pool_performance(self):
        """Test database connection pool performance under load."""
        with self._mock_database_services():
            workflow_data = get_ecommerce_order_workflow()
            workflow = await self.create_workflow(workflow_data)

            # Run multiple workflows that interact with database
            concurrency = 15
            start_time = time.time()

            tasks = []
            for i in range(concurrency):
                result = await self.execute_workflow(workflow["workflow_id"], {"db_test": i})
                tasks.append(self.wait_for_execution_completion(result["execution_id"]))

            await asyncio.gather(*tasks)

            total_time = time.time() - start_time
            avg_time_per_workflow = total_time / concurrency

            print(f"Database test - Total time: {total_time:.2f}s")
            print(f"Average time per workflow: {avg_time_per_workflow:.2f}s")

            # Should handle database load efficiently
            assert avg_time_per_workflow < 8.0  # Under 8 seconds average

    @pytest.mark.asyncio
    async def test_external_api_rate_limiting_performance(self):
        """Test performance with external API rate limiting."""
        with self._mock_rate_limited_services():
            workflow_data = get_ecommerce_order_workflow()
            workflow = await self.create_workflow(workflow_data)

            # Run workflows that hit rate-limited services
            concurrency = 5
            tasks = []
            for i in range(concurrency):
                result = await self.execute_workflow(workflow["workflow_id"], {"rate_test": i})
                tasks.append(self.wait_for_execution_completion(result["execution_id"], timeout=60))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Some may fail due to rate limiting, but system should handle gracefully
            successful_executions = [r for r in results if isinstance(r, dict) and r.get("status") == "completed"]
            failed_executions = [r for r in results if isinstance(r, dict) and r.get("status") == "error"]

            print(f"Successful executions: {len(successful_executions)}")
            print(f"Failed executions: {len(failed_executions)}")

            # At least some should succeed
            assert len(successful_executions) > 0

    @pytest.mark.asyncio
    async def test_workflow_error_recovery_performance(self):
        """Test performance of error recovery mechanisms."""
        with self._mock_intermittent_failures():
            workflow_data = get_ecommerce_order_workflow()
            workflow = await self.create_workflow(workflow_data)

            # Run workflows with intermittent failures
            concurrency = 8
            tasks = []
            for i in range(concurrency):
                result = await self.execute_workflow(workflow["workflow_id"], {"error_test": i})
                tasks.append(self.wait_for_execution_completion(result["execution_id"], timeout=45))

            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time

            successful_executions = [r for r in results if isinstance(r, dict) and r.get("status") == "completed"]

            print(f"Error recovery test - Total time: {total_time:.2f}s")
            print(f"Successful executions: {len(successful_executions)}/{concurrency}")

            # Should handle errors and still complete most workflows
            assert len(successful_executions) >= concurrency * 0.6  # At least 60% success rate

    @pytest.mark.asyncio
    async def test_long_running_workflow_performance(self):
        """Test performance of long-running workflows."""
        workflow_data = self._get_long_running_workflow()
        workflow = await self.create_workflow(workflow_data)

        start_time = time.time()
        result = await self.execute_workflow(workflow["workflow_id"], {"long_test": True})
        final_status = await self.wait_for_execution_completion(result["execution_id"], timeout=120)

        total_time = time.time() - start_time

        assert final_status["status"] == "completed"
        print(f"Long-running workflow completed in {total_time:.2f}s")

        # Should complete within reasonable time
        assert total_time < 90  # Under 90 seconds

    @pytest.mark.asyncio
    async def test_workflow_scaling_with_increasing_load(self):
        """Test how system scales with increasing load."""
        with self._mock_fast_services():
            workflow_data = get_ecommerce_order_workflow()
            workflow = await self.create_workflow(workflow_data)

            # Test with increasing concurrency levels
            scale_levels = [1, 2, 5, 10, 15]
            scaling_results = {}

            for level in scale_levels:
                start_time = time.time()

                tasks = []
                for i in range(level):
                    result = await self.execute_workflow(workflow["workflow_id"], {"scale_test": i})
                    tasks.append(self.wait_for_execution_completion(result["execution_id"], timeout=30))

                await asyncio.gather(*tasks)
                total_time = time.time() - start_time

                scaling_results[level] = {
                    "total_time": total_time,
                    "avg_time_per_workflow": total_time / level,
                    "throughput": level / total_time
                }

                print(f"Scale level {level}: {total_time:.2f}s total, {scaling_results[level]['throughput']:.2f} workflows/s")

            # Verify scaling behavior
            for level in scale_levels[1:]:  # Skip first level
                prev_level = scale_levels[scale_levels.index(level) - 1]
                prev_result = scaling_results[prev_level]

                # Throughput should be relatively stable or improve with scaling
                throughput_ratio = scaling_results[level]["throughput"] / prev_result["throughput"]
                print(f"Throughput ratio {level}/{prev_level}: {throughput_ratio:.2f}")

                # Allow some degradation but not complete failure
                assert throughput_ratio > 0.3  # At least 30% of previous throughput

    # Helper methods
    async def _run_concurrent_workflows(self, workflow_id: str, concurrency: int) -> List[float]:
        """Run multiple workflows concurrently and return execution times."""
        execution_times = []

        async def execute_and_time():
            start_time = time.time()
            result = await self.execute_workflow(workflow_id, {"concurrent": True})
            final_status = await self.wait_for_execution_completion(result["execution_id"], timeout=30)

            if final_status["status"] == "completed":
                execution_time = time.time() - start_time
                execution_times.append(execution_time)

        tasks = [execute_and_time() for _ in range(concurrency)]
        await asyncio.gather(*tasks)

        return execution_times

    def _mock_fast_services(self):
        """Mock services with fast response times."""
        from unittest.mock import patch

        def fast_response(*args, **kwargs):
            class MockResponse:
                status_code = 200
                def json(self):
                    return {"success": True, "fast": True}
            return MockResponse()

        return patch.multiple(
            'aiohttp.ClientSession',
            request=fast_response
        ), patch.multiple(
            'smtplib.SMTP',
            sendmail=lambda *args, **kwargs: None
        )

    def _mock_database_services(self):
        """Mock database services for performance testing."""
        from unittest.mock import patch

        def db_response(*args, **kwargs):
            class MockResponse:
                status_code = 200
                def json(self):
                    return {"success": True, "data": "db_response"}
            return MockResponse()

        return patch('aiohttp.ClientSession.request', side_effect=db_response)

    def _mock_rate_limited_services(self):
        """Mock services with rate limiting."""
        from unittest.mock import patch

        call_count = 0

        def rate_limited_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count % 3 == 0:  # Every 3rd call fails
                class MockResponse:
                    status_code = 429
                    def json(self):
                        return {"error": "Rate limit exceeded"}
                return MockResponse()
            else:
                class MockResponse:
                    status_code = 200
                    def json(self):
                        return {"success": True}
                return MockResponse()

        return patch('aiohttp.ClientSession.request', side_effect=rate_limited_response)

    def _mock_intermittent_failures(self):
        """Mock services with intermittent failures."""
        from unittest.mock import patch

        call_count = 0

        def intermittent_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count % 4 == 0:  # Every 4th call fails
                class MockResponse:
                    status_code = 500
                    def json(self):
                        return {"error": "Intermittent failure"}
                return MockResponse()
            else:
                class MockResponse:
                    status_code = 200
                    def json(self):
                        return {"success": True}
                return MockResponse()

        return patch('aiohttp.ClientSession.request', side_effect=intermittent_failure)

    def _get_long_running_workflow(self):
        """Get a workflow designed to run for longer periods."""
        return {
            "name": "Long Running Workflow",
            "description": "Workflow with multiple steps and delays",
            "nodes": [
                {
                    "id": "step1",
                    "type": "action",
                    "action_type": "http",
                    "config": {"method": "GET", "url": "https://httpbin.org/delay/2"}
                },
                {
                    "id": "step2",
                    "type": "action",
                    "action_type": "data_transform",
                    "config": {"transform_type": "add_fields", "fields": {"processed": True}}
                },
                {
                    "id": "step3",
                    "type": "action",
                    "action_type": "http",
                    "config": {"method": "GET", "url": "https://httpbin.org/delay/3"}
                },
                {
                    "id": "step4",
                    "type": "action",
                    "action_type": "send_email",
                    "config": {
                        "to_email": "test@example.com",
                        "subject": "Long running workflow completed",
                        "body": "Workflow completed successfully"
                    }
                }
            ],
            "connections": [
                {"from": "step1", "to": "step2"},
                {"from": "step2", "to": "step3"},
                {"from": "step3", "to": "step4"}
            ],
            "settings": {
                "timeout": 120,
                "max_retries": 2
            }
        }

