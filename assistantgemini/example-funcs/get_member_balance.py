"""
Example function for getting a Discord member's balance.
This demonstrates how to create functions that interact with other cogs.
"""

from typing import Dict, Any, Optional


async def get_member_balance(member_id: str) -> str:
    """
    Get a Discord member's balance from economy cogs.
    
    Args:
        member_id (str): Discord user ID to get balance for
        
    Returns:
        str: Formatted balance information
    """
    try:
        # Convert string to int
        user_id = int(member_id)
        
        # This is a placeholder - in a real implementation, you would:
        # 1. Get the economy cog
        # 2. Query the member's balance
        # 3. Return the actual balance
        
        # For demonstration purposes, return a mock response
        return f"Member {user_id} has a balance of 1000 credits."
        
    except ValueError:
        return f"Error: Invalid member ID '{member_id}'. Please provide a valid Discord user ID."
    except Exception as e:
        return f"Error getting member balance: {str(e)}"


# Function schema for the AI assistant
FUNCTION_SCHEMA = {
    "name": "get_member_balance",
    "description": "Get a Discord member's balance from the economy cog",
    "parameters": {
        "type": "object",
        "properties": {
            "member_id": {
                "type": "string",
                "description": "Discord user ID to get balance for"
            }
        },
        "required": ["member_id"]
    }
}


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print(await get_member_balance("123456789"))
        print(await get_member_balance("invalid_id"))
    
    asyncio.run(test()) 