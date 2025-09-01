"""Data Filter Action

This module implements an action for filtering data collections.
It can filter arrays and objects based on various criteria including
field values, patterns, ranges, and complex logical expressions.
"""

import logging
import re
from typing import Any, Dict, Optional, List, Union
from datetime import datetime
import operator

from ..base import BaseAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class DataFilterAction(BaseAction):
    """Action for filtering data collections.

    This action supports:
    - Field-based filtering with various operators
    - Pattern matching and regular expressions
    - Date range filtering
    - Complex logical expressions (AND, OR, NOT)
    - Array and object filtering
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.filter_criteria = config.get("filter_criteria", [])
        self.logical_operator = config.get("logical_operator", "AND")  # AND, OR
        self.output_format = config.get("output_format", "array")  # array, object, count
        self.case_sensitive = config.get("case_sensitive", True)
        self.max_results = config.get("max_results", None)

    async def validate_config(self) -> bool:
        """Validate data filter action configuration."""
        if not isinstance(self.filter_criteria, list):
            raise ValueError("filter_criteria must be a list")

        if self.logical_operator not in ["AND", "OR"]:
            raise ValueError("logical_operator must be 'AND' or 'OR'")

        if self.output_format not in ["array", "object", "count"]:
            raise ValueError("output_format must be 'array', 'object', or 'count'")

        # Validate each filter criterion
        for criterion in self.filter_criteria:
            if not isinstance(criterion, dict):
                raise ValueError("Each filter criterion must be a dictionary")

            if "field" not in criterion:
                raise ValueError("Each filter criterion must have a 'field' key")

            if "operator" not in criterion:
                raise ValueError("Each filter criterion must have an 'operator' key")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the data filtering."""
        try:
            data = input_data.get("data", [])

            if not isinstance(data, (list, dict)):
                raise ValueError("Data must be a list or dictionary")

            # Filter the data
            filtered_data = self._filter_data(data)

            # Apply max results limit
            if self.max_results and isinstance(filtered_data, list):
                filtered_data = filtered_data[:self.max_results]

            # Format output
            if self.output_format == "count":
                result = len(filtered_data) if isinstance(filtered_data, list) else 1
            elif self.output_format == "object" and isinstance(filtered_data, list):
                result = filtered_data[0] if filtered_data else None
            else:
                result = filtered_data

            return {
                "success": True,
                "result": result,
                "original_count": len(data) if isinstance(data, list) else 1,
                "filtered_count": len(filtered_data) if isinstance(filtered_data, list) else (1 if filtered_data else 0),
                "output_format": self.output_format
            }

        except Exception as e:
            logger.error(f"Data filtering failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "result": None
            }

    def _filter_data(self, data: Union[List[Any], Dict[str, Any]]) -> Union[List[Any], Dict[str, Any]]:
        """Filter data based on criteria."""
        if isinstance(data, dict):
            # Filter single object
            return data if self._matches_criteria(data) else None
        elif isinstance(data, list):
            # Filter array
            filtered = []
            for item in data:
                if isinstance(item, dict) and self._matches_criteria(item):
                    filtered.append(item)
            return filtered
        else:
            return data

    def _matches_criteria(self, item: Dict[str, Any]) -> bool:
        """Check if an item matches all filter criteria."""
        if not self.filter_criteria:
            return True

        results = []

        for criterion in self.filter_criteria:
            field = criterion.get("field", "")
            operator_name = criterion.get("operator", "")
            value = criterion.get("value")
            case_sensitive = criterion.get("case_sensitive", self.case_sensitive)

            # Get field value
            field_value = self._get_nested_value(item, field)

            # Apply operator
            match = self._apply_operator(field_value, operator_name, value, case_sensitive)
            results.append(match)

        # Apply logical operator
        if self.logical_operator == "AND":
            return all(results)
        elif self.logical_operator == "OR":
            return any(results)
        else:
            return False

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

    def _apply_operator(self, field_value: Any, operator_name: str, expected_value: Any, case_sensitive: bool = True) -> bool:
        """Apply a comparison operator."""
        try:
            # Handle None values
            if field_value is None:
                if operator_name in ["is_null", "is_empty"]:
                    return True
                elif operator_name in ["not_null", "not_empty"]:
                    return False
                else:
                    return False

            # String case handling
            if isinstance(field_value, str) and not case_sensitive:
                field_value = field_value.lower()
                if isinstance(expected_value, str):
                    expected_value = expected_value.lower()

            # Apply operator
            if operator_name == "equals" or operator_name == "==":
                return field_value == expected_value
            elif operator_name == "not_equals" or operator_name == "!=":
                return field_value != expected_value
            elif operator_name == "contains":
                return str(expected_value) in str(field_value)
            elif operator_name == "not_contains":
                return str(expected_value) not in str(field_value)
            elif operator_name == "starts_with":
                return str(field_value).startswith(str(expected_value))
            elif operator_name == "ends_with":
                return str(field_value).endswith(str(expected_value))
            elif operator_name == "regex":
                return bool(re.search(str(expected_value), str(field_value)))
            elif operator_name == "greater_than" or operator_name == ">":
                return self._compare_values(field_value, expected_value, operator.gt)
            elif operator_name == "less_than" or operator_name == "<":
                return self._compare_values(field_value, expected_value, operator.lt)
            elif operator_name == "greater_equal" or operator_name == ">=":
                return self._compare_values(field_value, expected_value, operator.ge)
            elif operator_name == "less_equal" or operator_name == "<=":
                return self._compare_values(field_value, expected_value, operator.le)
            elif operator_name == "in":
                if isinstance(expected_value, list):
                    return field_value in expected_value
                return False
            elif operator_name == "not_in":
                if isinstance(expected_value, list):
                    return field_value not in expected_value
                return True
            elif operator_name == "is_null":
                return field_value is None
            elif operator_name == "not_null":
                return field_value is not None
            elif operator_name == "is_empty":
                return not field_value or (isinstance(field_value, str) and field_value.strip() == "")
            elif operator_name == "not_empty":
                return field_value and (not isinstance(field_value, str) or field_value.strip() != "")
            elif operator_name == "length_equals":
                return len(str(field_value)) == int(expected_value)
            elif operator_name == "length_greater":
                return len(str(field_value)) > int(expected_value)
            elif operator_name == "length_less":
                return len(str(field_value)) < int(expected_value)
            else:
                logger.warning(f"Unknown operator: {operator_name}")
                return False

        except Exception as e:
            logger.warning(f"Error applying operator {operator_name}: {e}")
            return False

    def _compare_values(self, value1: Any, value2: Any, op_func) -> bool:
        """Compare two values with type conversion."""
        try:
            # Try numeric comparison first
            if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
                return op_func(value1, value2)

            # Try date comparison
            if isinstance(value1, str) and isinstance(value2, str):
                try:
                    date1 = datetime.fromisoformat(value1.replace('Z', '+00:00'))
                    date2 = datetime.fromisoformat(value2.replace('Z', '+00:00'))
                    return op_func(date1, date2)
                except:
                    pass

            # String comparison
            return op_func(str(value1), str(value2))

        except Exception:
            return False

    async def test_connection(self) -> bool:
        """Test data filter action (no external connections needed)."""
        return True

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        return {
            "type": "object",
            "properties": {
                "data": {
                    "oneOf": [
                        {"type": "array", "description": "Array of objects to filter"},
                        {"type": "object", "description": "Single object to filter"}
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
                    "description": "Filtered data (format depends on output_format)"
                },
                "original_count": {"type": "integer"},
                "filtered_count": {"type": "integer"},
                "output_format": {"type": "string"},
                "error": {"type": "string"}
            },
            "required": ["success"]
        }
