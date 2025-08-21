import asyncio
import logging
from typing import List, Dict, Optional, Any

import discord
from redbot.core import commands
from redbot.core.i18n import Translator, cog_i18n
from redbot.core.utils.chat_formatting import pagify

from .models import GuildSettings, Conversation

log = logging.getLogger("red.vrt.assistantgemini.chat")
_ = Translator("AssistantGemini", __file__)


@cog_i18n(_)
class ChatHandler:
    async def get_conversation(self, channel_id: int, user_id: int) -> Conversation:
        """Get or create a conversation for a user in a channel"""
        key = f"{user_id}-{channel_id}"
        if key not in self.db.conversations:
            self.db.conversations[key] = Conversation()
        return self.db.conversations[key]

    async def add_message_to_conversation(
        self, 
        channel_id: int, 
        user_id: int, 
        role: str, 
        content: str
    ):
        """Add a message to the conversation history"""
        conv = await self.get_conversation(channel_id, user_id)
        conv.messages.append({"role": role, "content": content})
        conv.message_count += 1
        
        # Update token count (rough estimation)
        conv.token_count += len(content) // 4

    async def clear_conversation(self, channel_id: int, user_id: int):
        """Clear a user's conversation in a channel"""
        key = f"{user_id}-{channel_id}"
        if key in self.db.conversations:
            del self.db.conversations[key]

    async def get_conversation_stats(self, channel_id: int, user_id: int) -> Dict[str, Any]:
        """Get conversation statistics for a user in a channel"""
        conv = await self.get_conversation(channel_id, user_id)
        return {
            "message_count": conv.message_count,
            "token_count": conv.token_count,
            "conversation_length": len(conv.messages)
        }

    async def format_messages_for_api(
        self, 
        conversation: Conversation, 
        system_prompt: str,
        user_message: str
    ) -> List[Dict[str, str]]:
        """Format conversation messages for the API"""
        messages = []
        
        # Add system prompt as first message
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history
        for msg in conversation.messages[-10:]:  # Keep last 10 messages
            messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages

    async def handle_chat_response(
        self, 
        ctx: commands.Context, 
        response: Dict[str, Any]
    ) -> str:
        """Handle the chat response from Gemini"""
        try:
            if "choices" in response and response["choices"]:
                choice = response["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
            
            # Fallback
            return "I apologize, but I couldn't generate a proper response."
            
        except Exception as e:
            log.error(f"Error handling chat response: {e}")
            return "An error occurred while processing the response."

    async def send_chunked_response(
        self, 
        ctx: commands.Context, 
        content: str, 
        max_length: int = 2000
    ):
        """Send a response in chunks if it's too long"""
        if len(content) <= max_length:
            await ctx.send(content)
        else:
            # Split into chunks
            chunks = list(pagify(content, delims=["\n", " "], page_length=max_length))
            for chunk in chunks:
                if chunk.strip():
                    await ctx.send(chunk)
                    await asyncio.sleep(1)  # Small delay between chunks