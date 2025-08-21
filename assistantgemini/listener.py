import logging

import discord
from redbot.core import commands
from redbot.core.i18n import Translator, cog_i18n

from .abc import MixinMeta
from .common.models import GuildSettings

log = logging.getLogger("red.vrt.assistantgemini.listener")
_ = Translator("AssistantGemini", __file__)


@cog_i18n(_)
class AssistantListener(MixinMeta):
    def __init__(self):
        super().__init__()
        self._listener_registered = False

    async def cog_load(self):
        """Register the listener when the cog loads"""
        if not self._listener_registered:
            self.bot.add_listener(self.on_message, "on_message")
            self._listener_registered = True

    async def cog_unload(self):
        """Remove the listener when the cog unloads"""
        if self._listener_registered:
            self.bot.remove_listener(self.on_message, "on_message")
            self._listener_registered = False

    async def on_message(self, message: discord.Message):
        """Handle incoming messages for potential AI responses"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Ignore DMs
        if not message.guild:
            return
        
        # Check if assistant is enabled for this guild
        guild_id = message.guild.id
        if guild_id not in self.db.guilds:
            return
        
        conf = self.db.guilds[guild_id]
        if not conf.enabled or not conf.api_key:
            return
        
        # Check if message mentions the bot or is a reply to the bot
        bot_mentioned = (
            self.bot.user in message.mentions or
            (message.reference and message.reference.resolved and 
             message.reference.resolved.author == self.bot.user)
        )
        
        # Check if message starts with a command prefix
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return  # This is a command, let the command handler deal with it
        
        # If bot is mentioned or message is a reply, process it
        if bot_mentioned:
            await self.process_ai_message(message, conf)

    async def process_ai_message(self, message: discord.Message, conf: GuildSettings):
        """Process a message for AI response"""
        try:
            # Extract the actual message content (remove bot mention)
            content = message.content
            if self.bot.user.mentioned_in(message):
                # Remove bot mention from content
                content = content.replace(f"<@{self.bot.user.id}>", "").replace(f"<@!{self.bot.user.id}>", "").strip()
            
            if not content:
                return
            
            # Add user message to conversation
            await self.add_message_to_conversation(
                message.channel.id,
                message.author.id,
                "user",
                content
            )
            
            # Get conversation
            conversation = await self.get_conversation(message.channel.id, message.author.id)
            
            # Format messages for API
            messages = await self.format_messages_for_api(
                conversation,
                conf.system_prompt,
                content
            )
            
            # Show typing indicator
            async with message.channel.typing():
                # Get response from Gemini
                response = await self.request_response(
                    messages=messages,
                    conf=conf,
                    member=message.author
                )
                
                # Extract response text
                response_text = await self.handle_chat_response(None, response)
                
                # Add assistant response to conversation
                await self.add_message_to_conversation(
                    message.channel.id,
                    message.author.id,
                    "assistant",
                    response_text
                )
                
                # Send response
                await self.send_chunked_response(None, response_text, message.channel)
                
        except Exception as e:
            log.error(f"Error processing AI message: {e}")
            await message.channel.send(f"❌ An error occurred while processing your message: {str(e)}")

    async def send_chunked_response(self, ctx, content: str, channel=None, max_length: int = 2000):
        """Send a response in chunks if it's too long"""
        target_channel = channel or ctx.channel
        
        if len(content) <= max_length:
            await target_channel.send(content)
        else:
            # Split into chunks
            from redbot.core.utils.chat_formatting import pagify
            chunks = list(pagify(content, delims=["\n", " "], page_length=max_length))
            for chunk in chunks:
                if chunk.strip():
                    await target_channel.send(chunk)
                    import asyncio
                    await asyncio.sleep(1)  # Small delay between chunks