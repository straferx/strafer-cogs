import logging

import discord
from redbot.core import commands
from redbot.core.i18n import Translator, cog_i18n
from redbot.core.utils.chat_formatting import box, pagify

from ..common.models import GuildSettings
from ..common.constants import DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS

log = logging.getLogger("red.vrt.assistantgemini.admin")
_ = Translator("AssistantGemini", __file__)


@cog_i18n(_)
class AdminCommands:
    @commands.group(name="assistantgeminiadmin", aliases=["aga"])
    @commands.admin()
    @commands.guild_only()
    async def assistantgeminiadmin(self, ctx: commands.Context):
        """Admin commands for managing the Gemini assistant"""
        pass

    @assistantgeminiadmin.command(name="enable")
    async def enable_assistant(self, ctx: commands.Context):
        """Enable the Gemini assistant for this server"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.db.guilds:
            await ctx.send("❌ Please run `[p]assistantgemini setup` first!")
            return
        
        conf = self.db.guilds[guild_id]
        conf.enabled = True
        
        await self.save_conf()
        
        embed = discord.Embed(
            title="✅ Assistant Enabled",
            description="The Gemini AI assistant has been enabled for this server!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

    @assistantgeminiadmin.command(name="disable")
    async def disable_assistant(self, ctx: commands.Context):
        """Disable the Gemini assistant for this server"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.db.guilds:
            await ctx.send("❌ Assistant not set up!")
            return
        
        conf = self.db.guilds[guild_id]
        conf.enabled = False
        
        await self.save_conf()
        
        embed = discord.Embed(
            title="❌ Assistant Disabled",
            description="The Gemini AI assistant has been disabled for this server!",
            color=discord.Color.red()
        )
        
        await ctx.send(embed=embed)

    @assistantgeminiadmin.command(name="temperature")
    async def set_temperature(self, ctx: commands.Context, temperature: float):
        """Set the temperature for responses (0.0 to 2.0)"""
        if not 0.0 <= temperature <= 2.0:
            await ctx.send("❌ Temperature must be between 0.0 and 2.0!")
            return
        
        guild_id = ctx.guild.id
        
        if guild_id not in self.db.guilds:
            await ctx.send("❌ Please run `[p]assistantgemini setup` first!")
            return
        
        conf = self.db.guilds[guild_id]
        conf.temperature = temperature
        
        await self.save_conf()
        
        embed = discord.Embed(
            title="🌡️ Temperature Updated",
            description=f"Temperature has been set to **{temperature}**!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="What this means",
            value="Lower values = more focused responses\nHigher values = more creative responses",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @assistantgeminiadmin.command(name="maxtokens")
    async def set_max_tokens(self, ctx: commands.Context, max_tokens: int):
        """Set the maximum tokens for responses"""
        if max_tokens < 1 or max_tokens > 10000:
            await ctx.send("❌ Max tokens must be between 1 and 10000!")
            return
        
        guild_id = ctx.guild.id
        
        if guild_id not in self.db.guilds:
            await ctx.send("❌ Please run `[p]assistantgemini setup` first!")
            return
        
        conf = self.db.guilds[guild_id]
        conf.max_tokens = max_tokens
        
        await self.save_conf()
        
        embed = discord.Embed(
            title="🔢 Max Tokens Updated",
            description=f"Maximum tokens has been set to **{max_tokens}**!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

    @assistantgeminiadmin.command(name="maxconvotokens")
    async def set_max_conversation_tokens(self, ctx: commands.Context, max_tokens: int):
        """Set the maximum tokens for conversation history"""
        if max_tokens < 1000 or max_tokens > 1000000:
            await ctx.send("❌ Max conversation tokens must be between 1000 and 1000000!")
            return
        
        guild_id = ctx.guild.id
        
        if guild_id not in self.db.guilds:
            await ctx.send("❌ Please run `[p]assistantgemini setup` first!")
            return
        
        conf = self.db.guilds[guild_id]
        conf.max_conversation_tokens = max_tokens
        
        await self.save_conf()
        
        embed = discord.Embed(
            title="💬 Max Conversation Tokens Updated",
            description=f"Maximum conversation tokens has been set to **{max_tokens}**!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

    @assistantgeminiadmin.command(name="reset")
    async def reset_settings(self, ctx: commands.Context):
        """Reset all assistant settings to defaults"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.db.guilds:
            await ctx.send("❌ Assistant not set up!")
            return
        
        # Keep the API key but reset other settings
        api_key = self.db.guilds[guild_id].api_key
        
        self.db.guilds[guild_id] = GuildSettings()
        self.db.guilds[guild_id].api_key = api_key
        self.db.guilds[guild_id].enabled = True
        
        await self.save_conf()
        
        embed = discord.Embed(
            title="🔄 Settings Reset",
            description="All assistant settings have been reset to defaults!",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="What was reset",
            value="• Model: gemini-2.5-flash\n"
                  "• Temperature: 0.7\n"
                  "• Max Tokens: 1000\n"
                  "• Max Conversation Tokens: 4000\n"
                  "• System Prompt: Default",
            inline=False
        )
        embed.add_field(
            name="What was kept",
            value="• API Key\n• Enabled status",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @assistantgeminiadmin.command(name="clearallconversations")
    async def clear_all_conversations(self, ctx: commands.Context):
        """Clear all conversations for this server"""
        guild_id = ctx.guild.id
        
        # Count conversations to be cleared
        conversations_to_clear = 0
        for key in list(self.db.conversations.keys()):
            if key.split("-")[1] == str(guild_id):
                conversations_to_clear += 1
        
        if conversations_to_clear == 0:
            await ctx.send("ℹ️ No conversations to clear!")
            return
        
        # Clear conversations
        for key in list(self.db.conversations.keys()):
            if key.split("-")[1] == str(guild_id):
                del self.db.conversations[key]
        
        await self.save_conf()
        
        embed = discord.Embed(
            title="🗑️ All Conversations Cleared",
            description=f"Cleared **{conversations_to_clear}** conversations for this server!",
            color=discord.Color.orange()
        )
        
        await ctx.send(embed=embed)

    @assistantgeminiadmin.command(name="status")
    async def show_detailed_status(self, ctx: commands.Context):
        """Show detailed status of the assistant"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.db.guilds:
            await ctx.send("❌ Assistant not set up! Run `[p]assistantgemini setup` first!")
            return
        
        conf = self.db.guilds[guild_id]
        
        # Count conversations for this server
        server_conversations = 0
        total_messages = 0
        total_tokens = 0
        
        for key, conv in self.db.conversations.items():
            if key.split("-")[1] == str(guild_id):
                server_conversations += 1
                total_messages += conv.message_count
                total_tokens += conv.token_count
        
        embed = discord.Embed(
            title="📊 Detailed Assistant Status",
            color=discord.Color.blue()
        )
        
        # Basic settings
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
            name="API Key",
            value="✅ Configured" if conf.api_key else "❌ Not configured",
            inline=True
        )
        
        # Advanced settings
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
            name="Max Conv Tokens",
            value=str(conf.max_conversation_tokens),
            inline=True
        )
        
        # Usage statistics
        embed.add_field(
            name="Active Conversations",
            value=str(server_conversations),
            inline=True
        )
        
        embed.add_field(
            name="Total Messages",
            value=str(total_messages),
            inline=True
        )
        
        embed.add_field(
            name="Total Tokens",
            value=str(total_tokens),
            inline=True
        )
        
        # System prompt
        embed.add_field(
            name="System Prompt",
            value=box(conf.system_prompt[:500] + ("..." if len(conf.system_prompt) > 500 else "")),
            inline=False
        )
        
        await ctx.send(embed=embed)