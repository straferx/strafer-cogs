import discord
import random
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path
from discord.ext import tasks
import asyncio


class RandomReactor(commands.Cog):
    """Randomly reacts to random messages with random emojis at random times."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=654321, force_registration=True)
        self.config.register_guild(enabled=False)
        self.reactor_loop.start()

    def cog_unload(self):
        self.reactor_loop.cancel()

    @tasks.loop(seconds=60)
    async def reactor_loop(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            enabled = await self.config.guild(guild).enabled()
            if not enabled:
                continue

            # Pick a random text channel with read & history perms
            channels = [
                c for c in guild.text_channels
                if c.permissions_for(guild.me).read_messages and c.permissions_for(guild.me).read_message_history
            ]
            if not channels:
                continue

            channel = random.choice(channels)

            try:
                messages = [msg async for msg in channel.history(limit=100)]
                messages = [m for m in messages if not m.author.bot]
                if not messages:
                    continue

                message = random.choice(messages)
                emojis = [e for e in guild.emojis if e.available]

                if not emojis:
                    continue

                emoji = random.choice(emojis)
                await message.add_reaction(emoji)

            except Exception as e:
                print(f"RandomReactor failed in {guild.name}: {e}")

        # Wait a random amount of time between 30–300 seconds before next run
        self.reactor_loop.change_interval(seconds=random.randint(30, 300))

    # === CONFIG COMMANDS ===

    @commands.group()
    @commands.guild_only()
    async def randreact(self, ctx):
        """Random emoji reaction config."""
        pass

    @randreact.command()
    async def enable(self, ctx):
        """Enable random emoji reactions in this server."""
        await self.config.guild(ctx.guild).enabled.set(True)
        await ctx.send("✅ Random emoji reacting enabled.")

    @randreact.command()
    async def disable(self, ctx):
        """Disable random emoji reactions in this server."""
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("❌ Random emoji reacting disabled.")