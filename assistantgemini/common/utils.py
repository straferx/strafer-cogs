import json
import logging
from typing import Dict, Any, Optional

log = logging.getLogger("red.vrt.assistantgemini.utils")


def json_schema_invalid(schema: Dict[str, Any]) -> Optional[str]:
    """Check if a JSON schema is invalid"""
    try:
        # Basic validation
        required_fields = ["name", "description", "parameters"]
        for field in required_fields:
            if field not in schema:
                return f"Missing required field: {field}"
        
        # Validate parameters structure
        if "parameters" in schema:
            params = schema["parameters"]
            if not isinstance(params, dict):
                return "Parameters must be a dictionary"
            
            if "type" not in params:
                return "Parameters must have a 'type' field"
            
            if "properties" not in params:
                return "Parameters must have a 'properties' field"
        
        return None
        
    except Exception as e:
        log.error(f"Error validating JSON schema: {e}")
        return f"Schema validation error: {str(e)}"


def format_function_schema(schema: Dict[str, Any]) -> str:
    """Format a function schema for display"""
    try:
        name = schema.get("name", "Unknown")
        description = schema.get("description", "No description")
        parameters = schema.get("parameters", {})
        
        param_type = parameters.get("type", "object")
        properties = parameters.get("properties", {})
        
        formatted = f"**Function:** {name}\n"
        formatted += f"**Description:** {description}\n"
        formatted += f"**Parameters:** {param_type}\n"
        
        if properties:
            formatted += "**Properties:**\n"
            for prop_name, prop_details in properties.items():
                prop_type = prop_details.get("type", "unknown")
                prop_desc = prop_details.get("description", "No description")
                formatted += f"  • {prop_name} ({prop_type}): {prop_desc}\n"
        
        return formatted
        
    except Exception as e:
        log.error(f"Error formatting function schema: {e}")
        return f"Error formatting schema: {str(e)}"


def safe_json_loads(json_str: str) -> Optional[Dict[str, Any]]:
    """Safely load JSON string"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        log.error(f"JSON decode error: {e}")
        return None
    except Exception as e:
        log.error(f"Error loading JSON: {e}")
        return None


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to a maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..." 