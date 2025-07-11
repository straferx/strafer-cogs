import discord
import random
import aiosqlite
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path
from typing import Dict, List
import re
import os
import psutil
import asyncio

class Chatter(commands.Cog):
    """A chat simulator that learns from user messages and occasionally replies."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=20250711, force_registration=True)
        self.config.register_guild(
            chance=5,
            excluded_channels=[],
            log_channel=None
        )
        self.data_path = cog_data_path(self)
        self.db_path = self.data_path / "messages.db"
        self.model: Dict[str, List[str]] = {}
        self.message_count: int = 0
        self.bot.loop.create_task(self._load_model())

    async def _load_model(self):
        self.data_path.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT
                )
            """)
            await db.commit()

            async with db.execute("SELECT content FROM messages") as cursor:
                async for row in cursor:
                    self._train(row[0])
                    self.message_count += 1

    def _train(self, message: str):
        tokens = message.strip().split()
        for i in range(len(tokens) - 1):
            key = tokens[i]
            next_word = tokens[i + 1]
            if key not in self.model:
                self.model[key] = []
            self.model[key].append(next_word)

    def _generate_message(self, max_words=30) -> str:
        if not self.model:
            return "I haven't learned anything yet."
        word = random.choice(list(self.model.keys()))
        result = [word]
        for _ in range(max_words - 1):
            next_words = self.model.get(word)
            if not next_words:
                break
            word = random.choice(next_words)
            result.append(word)
        return " ".join(result)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        guild = message.guild
        conf = await self.config.guild(guild).all()
        excluded = conf["excluded_channels"]
        if message.channel.id in excluded:
            return

        content = message.clean_content.strip()
        if len(content.split()) >= 3:
            self._train(content)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("INSERT INTO messages (content) VALUES (?)", (content,))
                await db.commit()
            self.message_count += 1

        mentioned = self.bot.user in message.mentions
        replied = message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user

        if mentioned or replied:
            reply = self._generate_message()
            await message.channel.send(reply)
            return

        if random.randint(1, 100) <= conf["chance"]:
            reply = self._generate_message()
            await message.channel.send(reply)

    @commands.group()
    async def chatter(self, ctx: commands.Context):
        """Commands for the chatter simulator."""
        pass

    @chatter.command()
    @commands.has_permissions(administrator=True)
    async def channelexclude(self, ctx: commands.Context):
        """Toggle this channel to be excluded from chatter replies."""
        cid = ctx.channel.id
        conf = self.config.guild(ctx.guild)
        current = await conf.excluded_channels()
        if cid in current:
            current.remove(cid)
            await ctx.send("🟢 This channel is now included for chatter replies.")
        else:
            current.append(cid)
            await ctx.send("🔴 This channel is now excluded from chatter replies.")
        await conf.excluded_channels.set(current)

    @chatter.command()
    @commands.has_permissions(administrator=True)
    async def chance(self, ctx: commands.Context, percent: int):
        """Set the reply chance percentage (0–100) for random chatter messages."""
        percent = max(0, min(100, percent))
        await self.config.guild(ctx.guild).chance.set(percent)
        await ctx.send(f"📊 Random reply chance set to {percent}%.")

    @chatter.command()
    async def stats(self, ctx: commands.Context):
        """Show statistics about the chatter model and memory usage."""
        word_count = sum(len(v) for v in self.model.values())
        node_count = len(self.model)
        memory_usage = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        db_size = os.path.getsize(self.db_path) / 1024 / 1024 if self.db_path.exists() else 0

        embed = discord.Embed(title="🧠 Chatter Stats", color=discord.Color.green())
        embed.add_field(name="Messages", value=f"{self.message_count:,}")
        embed.add_field(name="Nodes", value=f"{node_count:,}")
        embed.add_field(name="Words", value=f"{word_count:,}")
        embed.add_field(name="Memory", value=f"{memory_usage:.2f} MB")
        embed.add_field(name="Database", value=f"{db_size:.2f} MB")
        await ctx.send(embed=embed)

    @chatter.command()
    @commands.has_permissions(administrator=True)
    async def feed(self, ctx: commands.Context, channel: discord.TextChannel, amount: int = 5000):
        """Train the chatter bot on messages from a specified channel. Optionally set amount (1–5000)."""
        amount = max(1, min(5000, amount))
        progress_msg = await ctx.send(f"📥 Reading messages from {channel.mention} (max {amount})...")

        count = 0
        skipped_bots = 0
        skipped_short = 0

        async for msg in channel.history(limit=amount, oldest_first=True):
            if msg.author.bot:
                skipped_bots += 1
                continue
            content = msg.clean_content.strip()
            if len(content.split()) < 3:
                skipped_short += 1
                continue
            self._train(content)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("INSERT INTO messages (content) VALUES (?)", (content,))
            count += 1

            if count % 500 == 0:
                try:
                    await progress_msg.edit(content=f"⏳ {count} messages processed out of {amount}...")
                except discord.HTTPException:
                    pass

        self.message_count += count
        try:
            await progress_msg.edit(content=(
            f"✅ Trained on {count} messages from {channel.mention} (limit: {amount}).\n"
            f"⛔ Skipped: {skipped_bots} bot messages, {skipped_short} too short."
        ))

        except discord.HTTPException:
            await ctx.send(
                f"✅ Trained on {count} messages from {channel.mention} (limit: {amount}).
"
                f"⛔ Skipped: {skipped_bots} bot messages, {skipped_short} too short."
            )

        return

        await ctx.send(f"📥 Reading messages from {channel.mention} (max {amount})...")
        count = 0
        skipped_bots = 0
        skipped_short = 0
        amount = max(1, min(5000, amount))

        async for msg in channel.history(limit=amount, oldest_first=True):
            if msg.author.bot:
                skipped_bots += 1
                continue
            content = msg.clean_content.strip()
            if len(content.split()) < 3:
                skipped_short += 1
                continue
            self._train(content)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("INSERT INTO messages (content) VALUES (?)", (content,))
            count += 1

            # Progress feedback every 1000 messages
            if count > 0 and count % 1000 == 0:
                await ctx.send(f"⏳ {count} messages processed...")

        self.message_count += count
        await ctx.send(
            f"✅ Trained on {count} messages from {channel.mention} (limit: {amount}).
"
            f"⛔ Skipped: {skipped_bots} bot messages, {skipped_short} too short."
        )

    @chatter.command()
    @commands.has_permissions(administrator=True)
    async def export(self, ctx: commands.Context):
        """Export the chatter training database as a file attachment."""
        if not self.db_path.exists():
            await ctx.send("❌ Database file does not exist.")
            return
        await ctx.send("📦 Exporting database...", file=discord.File(self.db_path, filename="messages.db"))

    @chatter.command()
    @commands.has_permissions(administrator=True)
    async def logchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel where chatter reset logs and backups will be sent."""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"📋 Log channel set to {channel.mention}.")

    @chatter.command()
    @commands.has_permissions(administrator=True)
    async def reset(self, ctx: commands.Context):
        """Reset the chatter database. Requires typed confirmation."""
        log_channel_id = await self.config.guild(ctx.guild).log_channel()
        log_channel = ctx.guild.get_channel(log_channel_id) if log_channel_id else None

        if log_channel is None:
            await ctx.send("❌ You must set a log channel with `.chatter logchannel <channel>` before resetting the database.")
            return

        await ctx.send("⚠️ Are you sure you want to reset the chatter database?\nType `yes, reset the database` to confirm.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.strip().lower() == "yes, reset the database"

        try:
            await self.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("❌ Timed out. Database was not reset.")
            return

        if self.db_path.exists():
            await log_channel.send("📁 Backup before reset:", file=discord.File(self.db_path, filename="messages_backup.db"))
            os.remove(self.db_path)

        self.model.clear()
        self.message_count = 0
        await ctx.send("🧹 Database has been reset.")
