"""Data Transform Action

This module implements an action for transforming data structures and formats.
It can convert between different data formats, restructure data, apply mappings,
and perform various data transformation operations.
"""

import logging
import json
import csv
import io
from typing import Any, Dict, Optional, List, Union
import re

from ..base import BaseAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class DataTransformAction(BaseAction):
    """Action for transforming data structures and formats.

    This action supports:
    - Format conversion (JSON, XML, CSV, YAML)
    - Data restructuring and mapping
    - Field transformations and calculations
    - Array/object manipulations
    - Template-based transformations
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.transform_type = config.get("transform_type", "map")  # map, convert, template, calculate
        self.input_format = config.get("input_format", "json")  # json, xml, csv, yaml
        self.output_format = config.get("output_format", "json")  # json, xml, csv, yaml
        self.mappings = config.get("mappings", {})  # Field mappings
        self.transformations = config.get("transformations", {})  # Field transformations
        self.template = config.get("template", "")  # Template string
        self.delimiter = config.get("delimiter", ",")  # CSV delimiter
        self.include_headers = config.get("include_headers", True)  # For CSV output

    async def validate_config(self) -> bool:
        """Validate data transform action configuration."""
        valid_transform_types = ["map", "convert", "template", "calculate"]
        if self.transform_type not in valid_transform_types:
            raise ValueError(f"Invalid transform_type: {self.transform_type}. Must be one of {valid_transform_types}")

        valid_formats = ["json", "xml", "csv", "yaml"]
        if self.input_format not in valid_formats:
            raise ValueError(f"Invalid input_format: {self.input_format}. Must be one of {valid_formats}")

        if self.output_format not in valid_formats:
            raise ValueError(f"Invalid output_format: {self.output_format}. Must be one of {valid_formats}")

        if self.transform_type == "template" and not self.template:
            raise ValueError("template is required when transform_type is 'template'")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the data transformation."""
        try:
            data = input_data.get("data", {})

            if self.transform_type == "map":
                result = self._transform_map(data)
            elif self.transform_type == "convert":
                result = await self._transform_convert(data)
            elif self.transform_type == "template":
                result = self._transform_template(data)
            elif self.transform_type == "calculate":
                result = self._transform_calculate(data)
            else:
                raise ValueError(f"Unsupported transform type: {self.transform_type}")

            return {
                "success": True,
                "result": result,
                "transform_type": self.transform_type,
                "input_format": self.input_format,
                "output_format": self.output_format
            }

        except Exception as e:
            logger.error(f"Data transformation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "transform_type": self.transform_type
            }

    def _transform_map(self, data: Any) -> Any:
        """Transform data using field mappings."""
        if not isinstance(data, (dict, list)):
            return data

        if isinstance(data, list):
            return [self._transform_map(item) for item in data]

        result = {}

        for output_field, mapping_config in self.mappings.items():
            if isinstance(mapping_config, str):
                # Simple field mapping
                result[output_field] = self._get_nested_value(data, mapping_config)
            elif isinstance(mapping_config, dict):
                # Complex mapping with transformation
                input_field = mapping_config.get("field", "")
                transform_func = mapping_config.get("transform", "")
                default_value = mapping_config.get("default", "")

                value = self._get_nested_value(data, input_field) if input_field else data

                if transform_func:
                    value = self._apply_transformation(value, transform_func)

                if value is None and default_value:
                    value = default_value

                result[output_field] = value
            else:
                result[output_field] = mapping_config

        return result

    async def _transform_convert(self, data: Any) -> Any:
        """Convert data between different formats."""
        # First, ensure data is in the expected input format
        if self.input_format == "json" and not isinstance(data, (dict, list)):
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    pass

        # Convert to intermediate format (dict/list)
        intermediate_data = await self._parse_input_data(data)

        # Convert to output format
        if self.output_format == "json":
            return intermediate_data
        elif self.output_format == "xml":
            return self._convert_to_xml(intermediate_data)
        elif self.output_format == "csv":
            return self._convert_to_csv(intermediate_data)
        elif self.output_format == "yaml":
            return self._convert_to_yaml(intermediate_data)
        else:
            return intermediate_data

    def _transform_template(self, data: Any) -> str:
        """Transform data using a template string."""
        if not isinstance(data, dict):
            data = {"data": data}

        result = self.template

        # Replace template variables
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))

        # Replace nested properties
        for match in re.finditer(r"\{([^}]+)\}", result):
            path = match.group(1)
            value = self._get_nested_value(data, path)
            if value is not None:
                result = result.replace(f"{{{path}}}", str(value))

        return result

    def _transform_calculate(self, data: Any) -> Any:
        """Transform data using calculations and expressions."""
        if not isinstance(data, dict):
            return data

        result = data.copy()

        for field_name, calc_config in self.transformations.items():
            if isinstance(calc_config, str):
                # Simple expression
                result[field_name] = self._evaluate_expression(calc_config, data)
            elif isinstance(calc_config, dict):
                # Complex calculation
                expression = calc_config.get("expression", "")
                operation = calc_config.get("operation", "set")

                if operation == "set":
                    result[field_name] = self._evaluate_expression(expression, data)
                elif operation == "add":
                    existing = result.get(field_name, 0)
                    result[field_name] = existing + self._evaluate_expression(expression, data)
                elif operation == "multiply":
                    existing = result.get(field_name, 1)
                    result[field_name] = existing * self._evaluate_expression(expression, data)

        return result

    def _get_nested_value(self, data: Any, path: str) -> Any:
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

    def _apply_transformation(self, value: Any, transform_func: str) -> Any:
        """Apply a transformation function to a value."""
        if not value:
            return value

        try:
            if transform_func == "uppercase":
                return str(value).upper()
            elif transform_func == "lowercase":
                return str(value).lower()
            elif transform_func == "capitalize":
                return str(value).capitalize()
            elif transform_func == "strip":
                return str(value).strip()
            elif transform_func.startswith("substring"):
                # substring(start,end)
                match = re.match(r"substring\((\d+),(\d+)\)", transform_func)
                if match:
                    start, end = int(match.group(1)), int(match.group(2))
                    return str(value)[start:end]
            elif transform_func == "length":
                return len(str(value))
            else:
                return value
        except Exception:
            return value

    async def _parse_input_data(self, data: Any) -> Any:
        """Parse input data based on format."""
        if self.input_format == "json":
            if isinstance(data, str):
                return json.loads(data)
            return data
        elif self.input_format == "csv":
            if isinstance(data, str):
                return self._parse_csv(data)
            return data
        elif self.input_format == "xml":
            if isinstance(data, str):
                return self._parse_xml(data)
            return data
        elif self.input_format == "yaml":
            if isinstance(data, str):
                return self._parse_yaml(data)
            return data
        else:
            return data

    def _parse_csv(self, csv_data: str) -> List[Dict[str, Any]]:
        """Parse CSV data into list of dictionaries."""
        reader = csv.DictReader(io.StringIO(csv_data), delimiter=self.delimiter)
        return list(reader)

    def _parse_xml(self, xml_data: str) -> Dict[str, Any]:
        """Parse XML data into dictionary."""
        # Simplified XML parsing - in production, use xml.etree.ElementTree
        return {"xml_content": xml_data, "parsed": False}

    def _parse_yaml(self, yaml_data: str) -> Any:
        """Parse YAML data."""
        try:
            import yaml
            return yaml.safe_load(yaml_data)
        except ImportError:
            return {"yaml_content": yaml_data, "parsed": False}

    def _convert_to_csv(self, data: Any) -> str:
        """Convert data to CSV format."""
        if not isinstance(data, list):
            data = [data]

        if not data:
            return ""

        # Get field names from first item
        fieldnames = []
        if isinstance(data[0], dict):
            fieldnames = list(data[0].keys())

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=self.delimiter)

        if self.include_headers:
            writer.writeheader()

        for row in data:
            writer.writerow(row)

        return output.getvalue()

    def _convert_to_xml(self, data: Any) -> str:
        """Convert data to XML format."""
        # Simplified XML conversion - in production, use proper XML libraries
        if isinstance(data, dict):
            xml_parts = []
            for key, value in data.items():
                xml_parts.append(f"<{key}>{value}</{key}>")
            return f"<root>{''.join(xml_parts)}</root>"
        else:
            return f"<root>{data}</root>"

    def _convert_to_yaml(self, data: Any) -> str:
        """Convert data to YAML format."""
        try:
            import yaml
            return yaml.dump(data, default_flow_style=False)
        except ImportError:
            return json.dumps(data, indent=2)

    def _evaluate_expression(self, expression: str, data: Dict[str, Any]) -> Any:
        """Safely evaluate a simple expression."""
        # This is a very basic expression evaluator for simple calculations
        # In production, you'd want a more robust solution
        try:
            # Replace field references with values
            safe_expr = expression
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    safe_expr = safe_expr.replace(f"{{{key}}}", str(value))

            # Only allow basic arithmetic for security
            if not re.match(r'^[\d\s\+\-\*\/\(\)\.]+$', safe_expr):
                raise ValueError("Invalid expression")

            return eval(safe_expr, {"__builtins__": {}})
        except Exception:
            return 0

    async def test_connection(self) -> bool:
        """Test data transform action (no external connections needed)."""
        return True

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        return {
            "type": "object",
            "properties": {
                "data": {
                    "description": "The data to transform"
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
                    "description": "The transformed data"
                },
                "transform_type": {"type": "string"},
                "input_format": {"type": "string"},
                "output_format": {"type": "string"},
                "error": {"type": "string"}
            },
            "required": ["success"]
        }
