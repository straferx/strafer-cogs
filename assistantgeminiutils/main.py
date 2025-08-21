import logging
from typing import Dict, Any

from redbot.core import commands
from redbot.core.bot import Red

from .abc import CompositeMetaClass

log = logging.getLogger("red.vrt.assistantgeminiutils")


class AssistantGeminiUtils(commands.Cog, metaclass=CompositeMetaClass):
    """
    AssistantGemini Utils adds pre-baked functions to the AssistantGemini cog.
    
    This cog registers useful functions that the AI assistant can call,
    extending its capabilities beyond basic chat.
    """

    __author__ = "[vertyco](https://github.com/vertyco/vrt-cogs)"
    __version__ = "1.0.0"

    def __init__(self, bot: Red):
        self.bot = bot
        self.assistant_cog = None

    async def cog_load(self):
        """Register functions when the cog loads"""
        await self.register_functions()

    async def cog_unload(self):
        """Unregister functions when the cog unloads"""
        await self.unregister_functions()

    async def register_functions(self):
        """Register utility functions with the AssistantGemini cog"""
        # Wait for the bot to be ready
        await self.bot.wait_until_red_ready()
        
        # Try to get the AssistantGemini cog
        self.assistant_cog = self.bot.get_cog("AssistantGemini")
        
        if not self.assistant_cog:
            log.warning("AssistantGemini cog not found. Functions will not be registered.")
            return
        
        try:
            # Register utility functions
            await self._register_utility_functions()
            log.info("Successfully registered utility functions with AssistantGemini")
        except Exception as e:
            log.error(f"Failed to register utility functions: {e}")

    async def unregister_functions(self):
        """Unregister utility functions from the AssistantGemini cog"""
        if not self.assistant_cog:
            return
        
        try:
            # Unregister all functions from this cog
            for func_name in self._get_function_names():
                self.assistant_cog.unregister_function("assistantgeminiutils", func_name)
            log.info("Successfully unregistered utility functions from AssistantGemini")
        except Exception as e:
            log.error(f"Failed to unregister utility functions: {e}")

    async def _register_utility_functions(self):
        """Register the actual utility functions"""
        if not self.assistant_cog:
            return
        
        # Get current time function
        get_time_schema = {
            "name": "get_current_time",
            "description": "Get the current date and time",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone to get time for (e.g., 'UTC', 'America/New_York')",
                        "enum": ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"]
                    }
                },
                "required": []
            }
        }
        
        # Get member balance function
        get_balance_schema = {
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
        
        # Search internet function
        search_internet_schema = {
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
        
        # Register all functions
        functions = [
            ("get_current_time", get_time_schema),
            ("get_member_balance", get_balance_schema),
            ("search_internet", search_internet_schema)
        ]
        
        for func_name, schema in functions:
            self.assistant_cog.register_function(
                "assistantgeminiutils",
                func_name,
                schema,
                "user"
            )

    def _get_function_names(self) -> list:
        """Get list of function names registered by this cog"""
        return [
            "get_current_time",
            "get_member_balance", 
            "search_internet"
        ] 