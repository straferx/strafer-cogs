import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from discord.ext import tasks
import datetime
from typing import Dict, List


class PresenceLog(commands.Cog):
    """Log presence and activity updates of members."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.config.register_guild(
            enabled=False,
            log_channel=None
        )
        self.presence_updates: Dict[int, List[str]] = {}
        self.flush_presence_logs.start()

    def cog_unload(self):
        self.flush_presence_logs.cancel()

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        if after.bot or before.guild is None:
            return

        guild = before.guild
        settings = await self.config.guild(guild).all()
        if not settings["enabled"]:
            return

        # Prepare updates
        updates = []

        if before.status != after.status:
            updates.append(
                f"🟢 **{after.display_name}** changed status: `{before.status.name}` → `{after.status.name}`"
            )

        before_act = before.activities[0].name if before.activities else None
        after_act = after.activities[0].name if after.activities else None

        if before_act != after_act:
            updates.append(
                f"🎮 **{after.display_name}** changed activity: `{before_act or 'None'}` → `{after_act or 'None'}`"
            )

        if not updates:
            return

        # Buffer the update per guild
        self.presence_updates.setdefault(guild.id, []).extend(updates)

    @tasks.loop(seconds=15)
    async def flush_presence_logs(self):
        for guild_id, updates in list(self.presence_updates.items()):
            if not updates:
                continue

            guild = self.bot.get_guild(guild_id)
            if guild is None:
                continue

            settings = await self.config.guild(guild).all()
            channel = guild.get_channel(settings["log_channel"])
            if not isinstance(channel, discord.TextChannel):
                continue

            try:
                chunks = [updates[i:i + 10] for i in range(0, len(updates), 10)]
                for chunk in chunks:
                    embed = discord.Embed(
                        title="🔄 Presence Updates",
                        description="\n".join(chunk),
                        color=discord.Color.blurple(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    await channel.send(embed=embed)
            except Exception as e:
                print(f"Error sending presence updates to {guild.name}: {e}")

            self.presence_updates[guild_id] = []

    @commands.group()
    @commands.guild_only()
    async def presence_log(self, ctx: commands.Context):
        """Configure presence logging."""
        pass

    @presence.command()
    async def enable(self, ctx: commands.Context):
        """Enable presence logging."""
        await self.config.guild(ctx.guild).enabled.set(True)
        await ctx.send("✅ Presence logging enabled.")

    @presence.command()
    async def disable(self, ctx: commands.Context):
        """Disable presence logging."""
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("❌ Presence logging disabled.")

    @presence.command(name="setchannel")
    async def set_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel where presence logs will be sent."""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"📋 Presence log channel set to {channel.mention}.")
