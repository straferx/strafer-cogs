"""
Example function for searching the internet.
This demonstrates how to create functions that access external APIs.
"""

from typing import Dict, Any, Optional
import asyncio


async def search_internet(query: str, max_results: int = 3) -> str:
    """
    Search the internet for current information.
    
    Args:
        query (str): Search query to look up
        max_results (int): Maximum number of results to return (1-5)
        
    Returns:
        str: Formatted search results
    """
    try:
        # Validate max_results
        if not 1 <= max_results <= 5:
            max_results = 3
        
        # This is a placeholder - in a real implementation, you would:
        # 1. Use a search API (like DuckDuckGo, Google, etc.)
        # 2. Make the actual search request
        # 3. Parse and format the results
        
        # For demonstration purposes, return a mock response
        results = []
        for i in range(min(max_results, 3)):
            results.append(f"Result {i+1}: Information about '{query}'")
        
        formatted_results = "\n".join(results)
        return f"Search results for '{query}':\n{formatted_results}"
        
    except Exception as e:
        return f"Error performing internet search: {str(e)}"


# Function schema for the AI assistant
FUNCTION_SCHEMA = {
    "name": "search_internet",
    "description": "Search the internet for current information",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query to look up"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (1-5)",
                "minimum": 1,
                "maximum": 5
            }
        },
        "required": ["query"]
    }
}


# Example usage
if __name__ == "__main__":
    async def test():
        print(await search_internet("artificial intelligence"))
        print(await search_internet("Python programming", 2))
    
    asyncio.run(test()) 