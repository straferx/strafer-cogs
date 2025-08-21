import logging
from typing import Dict, List, Optional, Any

from redbot.core import commands
from redbot.core.i18n import Translator, cog_i18n

log = logging.getLogger("red.vrt.assistantgemini.functions")
_ = Translator("AssistantGemini", __file__)


@cog_i18n(_)
class AssistantFunctions:
    def __init__(self):
        super().__init__()
        # {cog_name: {function_name: {"permission_level": "user", "schema": function_json_schema}}}
        self.registry: Dict[str, Dict[str, dict]] = {}

    def register_function(
        self, 
        cog_name: str, 
        function_name: str, 
        function_schema: Dict[str, Any],
        permission_level: str = "user"
    ):
        """Register a function with the assistant"""
        if cog_name not in self.registry:
            self.registry[cog_name] = {}
        
        self.registry[cog_name][function_name] = {
            "permission_level": permission_level,
            "schema": function_schema
        }
        
        log.info(f"Registered function {function_name} from cog {cog_name}")

    def unregister_function(self, cog_name: str, function_name: str):
        """Unregister a function from the assistant"""
        if cog_name in self.registry and function_name in self.registry[cog_name]:
            del self.registry[cog_name][function_name]
            log.info(f"Unregistered function {function_name} from cog {cog_name}")

    def get_available_functions(self, member=None) -> List[Dict[str, Any]]:
        """Get all available functions for a member"""
        functions = []
        
        for cog_name, cog_functions in self.registry.items():
            for func_name, func_data in cog_functions.items():
                # Check permission level
                if func_data["permission_level"] == "admin" and not member.guild_permissions.administrator:
                    continue
                
                functions.append({
                    "name": func_name,
                    "description": func_data["schema"].get("description", ""),
                    "parameters": func_data["schema"].get("parameters", {}),
                    "cog": cog_name
                })
        
        return functions

    async def execute_function(
        self, 
        function_name: str, 
        arguments: Dict[str, Any],
        member=None
    ) -> str:
        """Execute a registered function"""
        # Find the function in the registry
        for cog_name, cog_functions in self.registry.items():
            if function_name in cog_functions:
                func_data = cog_functions[function_name]
                
                # Check permissions
                if func_data["permission_level"] == "admin" and not member.guild_permissions.administrator:
                    return "You don't have permission to use this function."
                
                # Execute the function (this would need to be implemented based on the cog)
                return f"Function {function_name} executed with arguments: {arguments}"
        
        return f"Function {function_name} not found."

    def get_function_schema(self, function_name: str) -> Optional[Dict[str, Any]]:
        """Get the schema for a specific function"""
        for cog_functions in self.registry.values():
            if function_name in cog_functions:
                return cog_functions[function_name]["schema"]
        return None