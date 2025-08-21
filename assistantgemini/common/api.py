import asyncio
import logging
from typing import List, Optional, Dict, Any

import discord
from redbot.core import commands
from redbot.core.i18n import Translator, cog_i18n
from redbot.core.utils.chat_formatting import box, humanize_number

from ..abc import MixinMeta
from .calls import request_chat_completion_raw, request_embedding_raw, count_tokens
from .constants import MODELS, DEFAULT_MODEL
from .models import GuildSettings

log = logging.getLogger("red.vrt.assistantgemini.api")
_ = Translator("AssistantGemini", __file__)


@cog_i18n(_)
class API(MixinMeta):
    async def gemini_status(self) -> str:
        """Check Gemini API status"""
        try:
            # Simple status check - Gemini is generally reliable
            return "Operational"
        except Exception as e:
            log.error("Failed to check Gemini API status", exc_info=e)
            return _("Failed to check: {}").format(str(e))

    async def request_response(
        self,
        messages: List[Dict[str, str]],
        conf: GuildSettings,
        functions: Optional[List[Dict[str, Any]]] = None,
        member: Optional[discord.Member] = None,
        response_token_override: int = None,
        model_override: Optional[str] = None,
        temperature_override: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Request a response from Gemini"""
        model = model_override or conf.get_user_model(member)
        
        # Ensure model is supported
        if model not in MODELS:
            log.warning(f"Model {model} not supported, using {DEFAULT_MODEL}")
            model = DEFAULT_MODEL
        
        # Get max tokens
        max_response_tokens = response_token_override or conf.get_user_max_response_tokens(member)
        
        # Count current conversation tokens
        current_convo_tokens = await self.count_payload_tokens(messages, model)
        if functions:
            current_convo_tokens += await self.count_function_tokens(functions, model)
        
        # Check if conversation is too long
        max_convo_tokens = conf.max_conversation_tokens
        if current_convo_tokens > max_convo_tokens:
            # Truncate messages to fit within token limit
            messages = await self.truncate_messages(messages, max_convo_tokens, model)
        
        # Make the API call
        response = await request_chat_completion_raw(
            model=model,
            messages=messages,
            temperature=temperature_override if temperature_override is not None else conf.temperature,
            api_key=conf.api_key,
            max_tokens=max_response_tokens,
            functions=functions,
        )
        
        return response

    async def count_payload_tokens(self, messages: List[Dict[str, str]], model: str) -> int:
        """Count tokens in the message payload"""
        total_tokens = 0
        for message in messages:
            content = message.get("content", "")
            total_tokens += await count_tokens(content, model)
        return total_tokens

    async def count_function_tokens(self, functions: List[Dict[str, Any]], model: str) -> int:
        """Count tokens in function definitions"""
        total_tokens = 0
        for func in functions:
            func_str = str(func)
            total_tokens += await count_tokens(func_str, model)
        return total_tokens

    async def truncate_messages(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int, 
        model: str
    ) -> List[Dict[str, str]]:
        """Truncate messages to fit within token limit"""
        # Keep system message if present
        system_message = None
        if messages and messages[0].get("role") == "system":
            system_message = messages[0]
            messages = messages[1:]
        
        # Start from most recent messages and work backwards
        truncated_messages = []
        current_tokens = 0
        
        for message in reversed(messages):
            message_tokens = await count_tokens(message.get("content", ""), model)
            if current_tokens + message_tokens <= max_tokens:
                truncated_messages.insert(0, message)
                current_tokens += message_tokens
            else:
                break
        
        # Add system message back if we have room
        if system_message:
            system_tokens = await count_tokens(system_message.get("content", ""), model)
            if current_tokens + system_tokens <= max_tokens:
                truncated_messages.insert(0, system_message)
        
        return truncated_messages

    async def get_embedding(self, text: str, conf: GuildSettings) -> List[float]:
        """Get embedding for text"""
        return await request_embedding_raw(text, conf.api_key)

    def get_max_tokens(self, conf: GuildSettings, member: Optional[discord.Member] = None) -> int:
        """Get maximum tokens for conversation"""
        return conf.max_conversation_tokens

    async def save_conf(self):
        """Save configuration"""
        await self.config.db.set(self.db.model_dump()) 