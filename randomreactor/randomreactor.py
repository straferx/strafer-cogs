import discord
import random
from redbot.core import commands, Config
from redbot.core.bot import Red
import asyncio


class RandomReactor(commands.Cog):
    """Randomly reacts to new messages with random emojis from the guild."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=654321, force_registration=True)
        self.config.register_guild(
            enabled=False,
            chance=0.05,              # 5% chance to react
            delay_range=(1, 5)        # seconds
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        if message.author.bot:
            return

        guild = message.guild
        settings = await self.config.guild(guild).all()

        if not settings["enabled"]:
            return

        # Roll the dice
        if random.random() > settings["chance"]:
            return

        emojis = [e for e in guild.emojis if e.available]
        if not emojis:
            return

        delay = random.randint(*settings["delay_range"])
        await asyncio.sleep(delay)

        try:
            emoji = random.choice(emojis)
            await message.add_reaction(emoji)
        except discord.HTTPException:
            pass

    # === CONFIG COMMANDS ===

    @commands.group()
    @commands.guild_only()
    async def randreact(self, ctx):
        """Configure random emoji reacting."""
        pass

    @randreact.command()
    async def enable(self, ctx):
        """Enable random reacting in this server."""
        await self.config.guild(ctx.guild).enabled.set(True)
        await ctx.send("✅ Random emoji reactions enabled.")

    @randreact.command()
    async def disable(self, ctx):
        """Disable random reacting in this server."""
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("❌ Random emoji reactions disabled.")

    @randreact.command()
    async def chance(self, ctx, chance: float):
        """Set the chance to react (0.0 to 1.0)."""
        if not 0.0 <= chance <= 1.0:
            await ctx.send("❗ Chance must be between 0.0 and 1.0")
            return
        await self.config.guild(ctx.guild).chance.set(chance)
        await ctx.send(f"🎲 Reaction chance set to `{chance * 100:.1f}%`.")

    @randreact.command(name="delayrange")
    async def delay_range(self, ctx, min_delay: int, max_delay: int):
        """Set random delay range in seconds before reacting."""
        if min_delay < 0 or max_delay < min_delay:
            await ctx.send("❗ Invalid delay range.")
            return
        await self.config.guild(ctx.guild).delay_range.set((min_delay, max_delay))
        await ctx.send(f"⏱️ Delay range set to `{min_delay}-{max_delay}` seconds.")
