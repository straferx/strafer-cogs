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

    async def _insert_message(self, guild_id: int, content: str):
        db_path = self.data_path / f"messages_{guild_id}.db"
        async with aiosqlite.connect(db_path) as db:
            await db.execute("INSERT INTO messages (content) VALUES (?)", (content,))
            await db.commit()
    """A chat simulator that learns from user messages and occasionally replies."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=20250711, force_registration=True)
        self.config.register_guild(
            chance=5,
            excluded_channels=[],
            log_channel=None,
            feed_channels=[]
        )
        self.data_path = cog_data_path(self)
        self.db_paths: Dict[int, str] = {}  # guild_id -> db path
        self.model: Dict[str, List[str]] = {}
        self.message_count: int = 0
        self.bot.loop.create_task(self._load_model())

    async def _load_model(self):
        self.data_path.mkdir(parents=True, exist_ok=True)
        for db_file in self.data_path.glob("messages_*.db"):
            guild_id = int(db_file.stem.replace("messages_", ""))
            self.db_paths[guild_id] = str(db_file)
            async with aiosqlite.connect(db_file) as db:
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
        if not message.guild:
            return
        guild_id = message.guild.id
        db_path = self.data_path / f"messages_{guild_id}.db"
        self.db_paths[guild_id] = str(db_path)
        db_path_str = str(db_path)
        self.data_path.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(db_path_str) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT
                )
            """)
            await db.commit()
        # Persistent feedchannels
        guild = message.guild
        if guild:
            conf = await self.config.guild(guild).all()
            feed_channels = conf.get("feed_channels", [])
            if message.channel.id in feed_channels and not message.author.bot:
                content = message.clean_content.strip()
                self._train(content)
                await self._insert_message(message.guild.id, content)
                self.message_count += 1
        if not message.guild or message.author.bot:
            return

        guild = message.guild
        conf = await self.config.guild(guild).all()
        excluded = conf["excluded_channels"]
        if message.channel.id in excluded:
            return

        mentioned = self.bot.user in message.mentions
        replied = message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user

        if mentioned or replied:
            reply = self._generate_message()
            await message.channel.send(reply)
            return

        if random.randint(1, 100) <= conf["chance"]:
            reply = self._generate_message()
            await message.channel.send(reply)

        # Do NOT consume messages unless this is a configured feed channel
        return
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
        """Show statistics about the chatter model and memory usage for this guild."""
        guild_id = ctx.guild.id
        db_path = self.data_path / f"messages_{guild_id}.db"
        word_count = sum(len(v) for v in self.model.values())
        node_count = len(self.model)
        memory_usage = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        db_size = os.path.getsize(db_path) / 1024 / 1024 if db_path.exists() else 0

        embed = discord.Embed(title="🧠 Chatter Stats", color=discord.Color.blurple())
        embed.add_field(name="Messages", value=f"{self.message_count:,} (this guild)")
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
            
            self._train(content)
            await self._insert_message(ctx.guild.id, content)
            count += 1

            if count % 500 == 0:
                try:
                    await progress_msg.edit(content=f"⏳ {count} messages processed out of {amount}...")
                except discord.HTTPException:
                    pass

        self.message_count += count
        try:
            await progress_msg.edit(content=(
                f"✅ Trained on {count} messages from {channel.mention} (limit: {amount})."
                f"⛔ Skipped: {skipped_bots} bot messages, {skipped_short} too short."
            ))
        except discord.HTTPException:
            await ctx.send(
                f"✅ Trained on {count} messages from {channel.mention} (limit: {amount})."
                f"⛔ Skipped: {skipped_bots} bot messages, {skipped_short} too short."
            )

    @chatter.command()
    @commands.has_permissions(administrator=True)
    async def feedchannels(self, ctx: commands.Context, *channels: discord.TextChannel):
        """Start or stop live training on specified channels (or clear if none)."""
        conf = self.config.guild(ctx.guild)

        if not channels:
            await conf.feed_channels.set([])
            await ctx.send("🛑 Live feed channels cleared. The bot will no longer consume messages.")
            return

        channel_ids = [ch.id for ch in channels]
        await conf.feed_channels.set(channel_ids)
        await ctx.send(f"📡 I will now listen and train from: {', '.join(ch.mention for ch in channels)}")

        @self.bot.listen("on_message")
        async def _feedlistener(msg: discord.Message):
            if msg.channel.id not in [ch.id for ch in channels]:
                return
            if msg.author.bot:
                return
            content = msg.clean_content.strip()
            
            self._train(content)
            await self._insert_message(msg.guild.id, content)
            self.message_count += 1

    @chatter.command()
    @commands.has_permissions(administrator=True)
    async def export(self, ctx: commands.Context):
        """Export the chatter training database as a file attachment."""
        db_path = self.data_path / f"messages_{ctx.guild.id}.db"
        if not db_path.exists():
            await ctx.send("❌ Database file does not exist.")
            return
        await ctx.send("📦 Exporting database...", file=discord.File(db_path, filename=f"messages_{ctx.guild.id}.db"))

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

        db_path = self.data_path / f"messages_{ctx.guild.id}.db"
        if db_path.exists():
            await log_channel.send("📁 Backup before reset:", file=discord.File(db_path, filename=f"messages_{ctx.guild.id}_backup.db"))
            os.remove(db_path)

        self.model.clear()
        self.message_count = 0
        await ctx.send("🧹 Database has been reset.")
