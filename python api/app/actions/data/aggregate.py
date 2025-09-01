"""Data Aggregate Action

This module implements an action for aggregating data collections.
It can perform various aggregation operations like sum, count, average,
grouping, and statistical calculations on data arrays.
"""

import logging
from typing import Any, Dict, Optional, List, Union
from collections import defaultdict
import statistics

from ..base import BaseAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class DataAggregateAction(BaseAction):
    """Action for aggregating data collections.

    This action supports:
    - Basic aggregations (sum, count, min, max, avg)
    - Grouping and group-wise aggregations
    - Statistical functions (median, mode, std_dev)
    - Custom aggregation expressions
    - Multiple aggregation operations in one pass
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.group_by = config.get("group_by", [])  # Fields to group by
        self.aggregations = config.get("aggregations", {})  # Aggregation definitions
        self.input_format = config.get("input_format", "array")  # array, object
        self.output_format = config.get("output_format", "object")  # object, array
        self.include_original_data = config.get("include_original_data", False)

    async def validate_config(self) -> bool:
        """Validate data aggregate action configuration."""
        if not isinstance(self.aggregations, dict):
            raise ValueError("aggregations must be a dictionary")

        if not self.aggregations:
            raise ValueError("At least one aggregation must be defined")

        if self.input_format not in ["array", "object"]:
            raise ValueError("input_format must be 'array' or 'object'")

        if self.output_format not in ["object", "array"]:
            raise ValueError("output_format must be 'object' or 'array'")

        # Validate aggregation functions
        valid_functions = [
            "sum", "count", "min", "max", "avg", "median", "mode",
            "std_dev", "variance", "first", "last", "concat", "unique_count"
        ]

        for agg_name, agg_config in self.aggregations.items():
            if isinstance(agg_config, str):
                func_name = agg_config
                field = None
            elif isinstance(agg_config, dict):
                func_name = agg_config.get("function", "")
                field = agg_config.get("field")
            else:
                raise ValueError(f"Invalid aggregation configuration for {agg_name}")

            if func_name not in valid_functions:
                raise ValueError(f"Unknown aggregation function: {func_name}")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the data aggregation."""
        try:
            data = input_data.get("data", [])

            if self.input_format == "object":
                data = [data] if data else []

            if not isinstance(data, list):
                raise ValueError("Data must be an array for aggregation")

            # Perform aggregation
            result = self._aggregate_data(data)

            return {
                "success": True,
                "result": result,
                "input_count": len(data),
                "grouped": bool(self.group_by),
                "aggregation_count": len(self.aggregations)
            }

        except Exception as e:
            logger.error(f"Data aggregation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "result": None
            }

    def _aggregate_data(self, data: List[Dict[str, Any]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Aggregate data based on configuration."""
        if not data:
            return {} if not self.group_by else []

        if self.group_by:
            return self._group_and_aggregate(data)
        else:
            return self._aggregate_all(data)

    def _aggregate_all(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate all data without grouping."""
        result = {}

        for agg_name, agg_config in self.aggregations.items():
            if isinstance(agg_config, str):
                func_name = agg_config
                field = None
            else:
                func_name = agg_config.get("function", "")
                field = agg_config.get("field")

            result[agg_name] = self._apply_aggregation(data, func_name, field)

        return result

    def _group_and_aggregate(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group data and aggregate within each group."""
        groups = defaultdict(list)

        # Group data
        for item in data:
            group_key = self._get_group_key(item)
            groups[group_key].append(item)

        # Aggregate each group
        results = []
        for group_key, group_data in groups.items():
            group_result = {}

            # Add group key fields
            if isinstance(group_key, tuple):
                for i, field in enumerate(self.group_by):
                    group_result[field] = group_key[i]
            else:
                group_result[self.group_by[0]] = group_key

            # Add aggregations
            for agg_name, agg_config in self.aggregations.items():
                if isinstance(agg_config, str):
                    func_name = agg_config
                    field = None
                else:
                    func_name = agg_config.get("function", "")
                    field = agg_config.get("field")

                group_result[agg_name] = self._apply_aggregation(group_data, func_name, field)

            # Add original data if requested
            if self.include_original_data:
                group_result["_data"] = group_data

            results.append(group_result)

        return results

    def _get_group_key(self, item: Dict[str, Any]) -> Union[str, tuple]:
        """Get the group key for an item."""
        if len(self.group_by) == 1:
            field = self.group_by[0]
            return self._get_nested_value(item, field)
        else:
            return tuple(self._get_nested_value(item, field) for field in self.group_by)

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested data structure using dot notation."""
        if not path:
            return data

        keys = path.split(".")
        current = data

        try:
            for key in keys:
                if isinstance(current, dict):
                    current = current[key]
                elif isinstance(current, list) and key.isdigit():
                    current = current[int(key)]
                else:
                    return None
            return current
        except (KeyError, IndexError, TypeError):
            return None

    def _apply_aggregation(self, data: List[Dict[str, Any]], func_name: str, field: Optional[str]) -> Any:
        """Apply an aggregation function to data."""
        if not data:
            return None

        try:
            if func_name == "count":
                return len(data)

            if field is None:
                # Count aggregation doesn't need field
                if func_name == "count":
                    return len(data)
                return None

            # Extract values from the specified field
            values = []
            for item in data:
                value = self._get_nested_value(item, field)
                if value is not None:
                    # Try to convert to numeric for mathematical operations
                    if func_name in ["sum", "avg", "min", "max", "median", "std_dev", "variance"]:
                        try:
                            if isinstance(value, str):
                                # Try to convert string numbers
                                if '.' in value:
                                    value = float(value)
                                else:
                                    value = int(value)
                            values.append(value)
                        except (ValueError, TypeError):
                            continue  # Skip non-numeric values
                    else:
                        values.append(value)

            if not values:
                return None

            # Apply aggregation function
            if func_name == "sum":
                return sum(values)
            elif func_name == "count":
                return len(values)
            elif func_name == "min":
                return min(values)
            elif func_name == "max":
                return max(values)
            elif func_name == "avg":
                return sum(values) / len(values)
            elif func_name == "median":
                return statistics.median(values)
            elif func_name == "mode":
                return statistics.mode(values)
            elif func_name == "std_dev":
                return statistics.stdev(values) if len(values) > 1 else 0
            elif func_name == "variance":
                return statistics.variance(values) if len(values) > 1 else 0
            elif func_name == "first":
                return values[0]
            elif func_name == "last":
                return values[-1]
            elif func_name == "concat":
                return "".join(str(v) for v in values)
            elif func_name == "unique_count":
                return len(set(values))
            else:
                return None

        except Exception as e:
            logger.warning(f"Error applying aggregation {func_name}: {e}")
            return None

    async def test_connection(self) -> bool:
        """Test data aggregate action (no external connections needed)."""
        return True

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        return {
            "type": "object",
            "properties": {
                "data": {
                    "oneOf": [
                        {"type": "array", "description": "Array of objects to aggregate"},
                        {"type": "object", "description": "Single object to aggregate"}
                    ]
                }
            },
            "required": ["data"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action output."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "result": {
                    "description": "Aggregated data (object or array depending on grouping)"
                },
                "input_count": {"type": "integer"},
                "grouped": {"type": "boolean"},
                "aggregation_count": {"type": "integer"},
                "error": {"type": "string"}
            },
            "required": ["success"]
        }
