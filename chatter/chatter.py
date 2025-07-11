import discord
import random
import aiosqlite
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path
from typing import Dict, List
import re
import os

class Chatter(commands.Cog):
    """A chat simulator that learns from user messages and occasionally replies."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=20250711, force_registration=True)
        self.config.register_guild(
            chance=5,
            excluded_channels=[]
        )
        self.db_path = cog_data_path(self) / "messages.db"
        self.model: Dict[str, List[str]] = {}
        self.bot.loop.create_task(self._load_model())

    async def _load_model(self):
        if not self.db_path.exists():
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content TEXT
                    )
                """)
                await db.commit()
        else:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT content FROM messages") as cursor:
                    async for row in cursor:
                        self._train(row[0])

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

        # Train on every normal message
        content = message.clean_content.strip()
        if len(content.split()) >= 3:
            self._train(content)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("INSERT INTO messages (content) VALUES (?)", (content,))
                await db.commit()

        # Reply if bot is mentioned or replied to
        mentioned = self.bot.user in message.mentions
        replied = message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user

        if mentioned or replied:
            reply = self._generate_message()
            await message.channel.send(reply)
            return

        # Random chance reply (if configured)
        if random.randint(1, 100) <= conf["chance"]:
            reply = self._generate_message()
            await message.channel.send(reply)

    @commands.group()
    async def chatter(self, ctx: commands.Context):
        """Commands for the chatter simulator."""
        pass

    @chatter.command()
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
    async def chance(self, ctx: commands.Context, percent: int):
        """Set the chance (0-100) the bot replies randomly."""
        percent = max(0, min(100, percent))
        await self.config.guild(ctx.guild).chance.set(percent)
        await ctx.send(f"📊 Random reply chance set to {percent}%.")

    @chatter.command()
    async def stats(self, ctx: commands.Context):
        """View chatter model stats."""
        word_count = len(self.model)
        chain_size = sum(len(v) for v in self.model.values())
        await ctx.send(f"📚 Learned {word_count} unique words with {chain_size} chain links.")

    @chatter.command()
    async def feed(self, ctx: commands.Context, channel: discord.TextChannel):
        """Feed messages from a channel into the chatter (up to 5000)."""
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
        await ctx.send(f"✅ Trained on {count} messages from {channel.mention}.")
