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
from discord.ui import Modal, TextInput, View

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
        percent = max(0, min(100, percent))
        await self.config.guild(ctx.guild).chance.set(percent)
        await ctx.send(f"📊 Random reply chance set to {percent}%.")

    @chatter.command()
    async def stats(self, ctx: commands.Context):
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
    async def feed(self, ctx: commands.Context, channel: discord.TextChannel):
        await ctx.send(f"📥 Reading messages from {channel.mention}...")
        count = 0
        async for msg in channel.history(limit=5000, oldest_first=True):
            if msg.author.bot:
                continue
            content = msg.clean_content.strip()
            if len(content.split()) >= 3:
                self._train(content)
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("INSERT INTO messages (content) VALUES (?)", (content,))
                count += 1
        self.message_count += count
        await ctx.send(f"✅ Trained on {count} messages from {channel.mention}.")

    @chatter.command()
    @commands.has_permissions(administrator=True)
    async def export(self, ctx: commands.Context):
        if not self.db_path.exists():
            await ctx.send("❌ Database file does not exist.")
            return
        await ctx.send("📦 Exporting database...", file=discord.File(self.db_path, filename="messages.db"))

    @chatter.command()
    @commands.has_permissions(administrator=True)
    async def logchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"📋 Log channel set to {channel.mention}.")

    @chatter.command()
    @commands.has_permissions(administrator=True)
    async def reset(self, ctx: commands.Context):
        class ConfirmResetModal(Modal, title="Reset Chatter Database"):
            confirm_input = TextInput(label="Type exactly: yes, reset the database", placeholder="yes, reset the database")

            async def on_submit(self, interaction: discord.Interaction):
                if self.confirm_input.value.strip().lower() == "yes, reset the database":
                    backup_file = discord.File(self.db_path, filename="messages_backup.db") if self.db_path.exists() else None
                    log_channel_id = await self.config.guild(ctx.guild).log_channel()
                    log_channel = ctx.guild.get_channel(log_channel_id) if log_channel_id else ctx.channel
                    if backup_file:
                        await log_channel.send("📁 Backup before reset:", file=backup_file)
                        os.remove(self.db_path)
                    self.model.clear()
                    self.message_count = 0
                    await interaction.response.send_message("🧹 Database has been reset.", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Confirmation failed. Database not reset.", ephemeral=True)

        await ctx.send_modal(ConfirmResetModal())
