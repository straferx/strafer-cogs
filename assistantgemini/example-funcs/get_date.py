"""
Example function for getting current date and time.
This demonstrates how to create functions that the AI assistant can call.
"""

import datetime
import pytz
from typing import Dict, Any


async def get_current_time(timezone: str = "UTC") -> str:
    """
    Get the current date and time for a specified timezone.
    
    Args:
        timezone (str): Timezone to get time for (default: UTC)
        
    Returns:
        str: Formatted date and time string
    """
    try:
        # Get the timezone
        tz = pytz.timezone(timezone)
        
        # Get current time in that timezone
        current_time = datetime.datetime.now(tz)
        
        # Format the time
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        
        return f"Current time in {timezone}: {formatted_time}"
        
    except pytz.exceptions.UnknownTimeZoneError:
        return f"Error: Unknown timezone '{timezone}'. Please use a valid timezone like 'UTC', 'America/New_York', etc."
    except Exception as e:
        return f"Error getting time: {str(e)}"


# Function schema for the AI assistant
FUNCTION_SCHEMA = {
    "name": "get_current_time",
    "description": "Get the current date and time for a specified timezone",
    "parameters": {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "Timezone to get time for (e.g., 'UTC', 'America/New_York')",
                "enum": ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo", "Australia/Sydney"]
            }
        },
        "required": []
    }
}


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print(await get_current_time())
        print(await get_current_time("America/New_York"))
        print(await get_current_time("Europe/London"))
    
    asyncio.run(test()) 