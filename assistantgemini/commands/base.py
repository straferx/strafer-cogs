import logging

import discord
from redbot.core import commands
from redbot.core.i18n import Translator, cog_i18n
from redbot.core.utils.chat_formatting import box, pagify

from ..abc import MixinMeta
from ..common.models import GuildSettings
from ..common.constants import DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS

log = logging.getLogger("red.vrt.assistantgemini.commands")
_ = Translator("AssistantGemini", __file__)


@cog_i18n(_)
class AssistantCommands(MixinMeta):
    @commands.group(name="assistantgemini", aliases=["ag"])
    @commands.guild_only()
    async def assistantgemini(self, ctx: commands.Context):
        """Configure and manage the Gemini AI assistant"""
        pass

    @assistantgemini.command(name="setup")
    @commands.admin()
    async def setup_assistant(self, ctx: commands.Context):
        """Set up the Gemini assistant for this server"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.db.guilds:
            self.db.guilds[guild_id] = GuildSettings()
        
        conf = self.db.guilds[guild_id]
        conf.enabled = True
        
        await self.save_conf()
        
        embed = discord.Embed(
            title="✅ AssistantGemini Setup Complete",
            description="The Gemini AI assistant has been set up for this server!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Next Steps",
            value="1. Set your Gemini API key with `[p]assistantgemini geminikey <your_key>`\n"
                  "2. Customize the system prompt with `[p]assistantgemini prompt <prompt>`\n"
                  "3. Start chatting with `[p]chat <message>`",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @assistantgemini.command(name="geminikey")
    @commands.admin()
    async def set_gemini_key(self, ctx: commands.Context, api_key: str):
        """Set the Gemini API key for this server"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.db.guilds:
            self.db.guilds[guild_id] = GuildSettings()
        
        conf = self.db.guilds[guild_id]
        conf.api_key = api_key
        conf.enabled = True
        
        await self.save_conf()
        
        embed = discord.Embed(
            title="🔑 Gemini API Key Set",
            description="Your Gemini API key has been configured successfully!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Status",
            value="✅ API Key configured\n✅ Assistant enabled",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @assistantgemini.command(name="prompt")
    @commands.admin()
    async def set_system_prompt(self, ctx: commands.Context, *, prompt: str):
        """Set the system prompt for the assistant"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.db.guilds:
            await ctx.send("❌ Please run `[p]assistantgemini setup` first!")
            return
        
        conf = self.db.guilds[guild_id]
        conf.system_prompt = prompt
        
        await self.save_conf()
        
        embed = discord.Embed(
            title="📝 System Prompt Updated",
            description="The system prompt has been updated successfully!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="New Prompt",
            value=box(prompt[:1000] + ("..." if len(prompt) > 1000 else "")),
            inline=False
        )
        
        await ctx.send(embed=embed)

    @assistantgemini.command(name="model")
    @commands.admin()
    async def set_model(self, ctx: commands.Context, model: str):
        """Set the Gemini model to use"""
        from ..common.constants import MODELS
        
        if model not in MODELS:
            available_models = ", ".join(MODELS.keys())
            await ctx.send(f"❌ Invalid model! Available models: {available_models}")
            return
        
        guild_id = ctx.guild.id
        
        if guild_id not in self.db.guilds:
            await ctx.send("❌ Please run `[p]assistantgemini setup` first!")
            return
        
        conf = self.db.guilds[guild_id]
        conf.model = model
        
        await self.save_conf()
        
        embed = discord.Embed(
            title="🤖 Model Updated",
            description=f"The model has been updated to **{model}**!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

    @assistantgemini.command(name="settings")
    @commands.admin()
    async def show_settings(self, ctx: commands.Context):
        """Show current assistant settings"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.db.guilds:
            await ctx.send("❌ Assistant not set up! Run `[p]assistantgemini setup` first!")
            return
        
        conf = self.db.guilds[guild_id]
        
        embed = discord.Embed(
            title="⚙️ AssistantGemini Settings",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Status",
            value="✅ Enabled" if conf.enabled else "❌ Disabled",
            inline=True
        )
        
        embed.add_field(
            name="Model",
            value=conf.model,
            inline=True
        )
        
        embed.add_field(
            name="Temperature",
            value=str(conf.temperature),
            inline=True
        )
        
        embed.add_field(
            name="Max Tokens",
            value=str(conf.max_tokens),
            inline=True
        )
        
        embed.add_field(
            name="API Key",
            value="✅ Configured" if conf.api_key else "❌ Not configured",
            inline=True
        )
        
        embed.add_field(
            name="System Prompt",
            value=box(conf.system_prompt[:500] + ("..." if len(conf.system_prompt) > 500 else "")),
            inline=False
        )
        
        await ctx.send(embed=embed)

    @assistantgemini.command(name="chat")
    async def chat(self, ctx: commands.Context, *, message: str):
        """Chat with the Gemini AI assistant"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.db.guilds:
            await ctx.send("❌ Assistant not set up! Ask an admin to run `[p]assistantgemini setup`")
            return
        
        conf = self.db.guilds[guild_id]
        
        if not conf.enabled:
            await ctx.send("❌ Assistant is disabled!")
            return
        
        if not conf.api_key:
            await ctx.send("❌ No Gemini API key configured! Ask an admin to set one.")
            return
        
        # Add user message to conversation
        await self.add_message_to_conversation(
            ctx.channel.id, 
            ctx.author.id, 
            "user", 
            message
        )
        
        # Get conversation
        conversation = await self.get_conversation(ctx.channel.id, ctx.author.id)
        
        # Format messages for API
        messages = await self.format_messages_for_api(
            conversation, 
            conf.system_prompt, 
            message
        )
        
        # Show typing indicator
        async with ctx.typing():
            try:
                # Get response from Gemini
                response = await self.request_response(
                    messages=messages,
                    conf=conf,
                    member=ctx.author
                )
                
                # Extract response text
                response_text = await self.handle_chat_response(ctx, response)
                
                # Add assistant response to conversation
                await self.add_message_to_conversation(
                    ctx.channel.id, 
                    ctx.author.id, 
                    "assistant", 
                    response_text
                )
                
                # Send response
                await self.send_chunked_response(ctx, response_text)
                
            except Exception as e:
                log.error(f"Error in chat command: {e}")
                await ctx.send(f"❌ An error occurred: {str(e)}")

    @assistantgemini.command(name="clearconvo")
    async def clear_conversation(self, ctx: commands.Context):
        """Clear your conversation with the assistant"""
        await self.clear_conversation(ctx.channel.id, ctx.author.id)
        await ctx.send("✅ Your conversation has been cleared!")

    @assistantgemini.command(name="convostats")
    async def conversation_stats(self, ctx: commands.Context):
        """Show your conversation statistics"""
        stats = await self.get_conversation_stats(ctx.channel.id, ctx.author.id)
        
        embed = discord.Embed(
            title="📊 Conversation Statistics",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Message Count",
            value=str(stats["message_count"]),
            inline=True
        )
        
        embed.add_field(
            name="Token Count",
            value=str(stats["token_count"]),
            inline=True
        )
        
        embed.add_field(
            name="Conversation Length",
            value=str(stats["conversation_length"]),
            inline=True
        )
        
        await ctx.send(embed=embed)

    @assistantgemini.command(name="chathelp")
    async def chat_help(self, ctx: commands.Context):
        """Show tips for chatting with the assistant"""
        embed = discord.Embed(
            title="💡 Chat Tips",
            description="Here are some tips for getting the best responses from the Gemini AI assistant:",
            color=discord.Color.blue()
        )
        
        tips = [
            "**Be specific**: The more specific your question, the better the answer",
            "**Provide context**: Give relevant background information",
            "**Ask follow-ups**: You can ask for clarification or more details",
            "**Use natural language**: Talk to it like you would to a person",
            "**Be patient**: Complex questions may take longer to process"
        ]
        
        for tip in tips:
            embed.add_field(name="", value=tip, inline=False)
        
        embed.add_field(
            name="Commands",
            value="`[p]chat <message>` - Chat with the assistant\n"
                  "`[p]clearconvo` - Clear your conversation\n"
                  "`[p]convostats` - View conversation statistics",
            inline=False
        )
        
        await ctx.send(embed=embed) 