import asyncio
import logging
from multiprocessing.pool import Pool
from time import perf_counter
from typing import Dict

import discord
from discord.ext import tasks
from pydantic import ValidationError
from redbot.core import Config, commands
from redbot.core.bot import Red

from .abc import MixinMeta
from .commands.base import AssistantCommands
from .commands.admin import AdminCommands
from .common.api import API
from .common.chat import ChatHandler
from .common.functions import AssistantFunctions
from .common.models import DB
from .listener import AssistantListener

log = logging.getLogger("red.vrt.assistantgemini")


class AssistantGemini(
    AssistantCommands,
    AdminCommands,
    AssistantFunctions,
    AssistantListener,
    ChatHandler,
    API,
    commands.Cog,
):
    """
    Set up and configure an AI assistant (or chat) cog for your server with Google's Gemini language models.

    Features include configurable prompt injection, dynamic embeddings, custom function calling, and more!

    - **[p]assistantgemini**: base command for setting up the assistant
    - **[p]chat**: talk with the assistant
    - **[p]convostats**: view a user's token usage/conversation message count for the channel
    - **[p]clearconvo**: reset your conversation with the assistant in the channel
    """

    __author__ = "[vertyco](https://github.com/vertyco/vrt-cogs)"
    __version__ = "1.0.0"

    def format_help_for_context(self, ctx):
        helpcmd = super().format_help_for_context(ctx)
        return f"{helpcmd}\nVersion: {self.__version__}\nAuthor: {self.__author__}"

    async def red_delete_data_for_user(self, *, requester, user_id: int):
        """Delete user data when requested"""
        for key in self.db.conversations.copy():
            if key.split("-")[0] == str(user_id):
                del self.db.conversations[key]

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot
        self.config = Config.get_conf(self, 117117118, force_registration=True)
        self.config.register_global(db={})
        self.db: DB = DB()
        self.mp_pool = Pool()

        # {cog_name: {function_name: {"permission_level": "user", "schema": function_json_schema}}}
        self.registry: Dict[str, Dict[str, dict]] = {}

        self.saving = False
        self.first_run = True

    async def cog_load(self) -> None:
        asyncio.create_task(self.init_cog())

    async def cog_unload(self):
        if hasattr(self, 'save_loop'):
            self.save_loop.cancel()
        self.mp_pool.close()
        self.bot.dispatch("assistantgemini_cog_remove")

    async def init_cog(self):
        await self.bot.wait_until_red_ready()
        start = perf_counter()
        data = await self.config.db()
        try:
            self.db = await asyncio.to_thread(DB.model_validate, data)
        except ValidationError:
            # Try clearing conversations
            try:
                old_data = data.copy()
                if "conversations" in old_data:
                    del old_data["conversations"]
                self.db = await asyncio.to_thread(DB.model_validate, old_data)
                await self.save_conf()
            except Exception:
                # If all else fails, start fresh
                self.db = DB()
                await self.save_conf()

        # Start save loop
        self.save_loop.start()
        
        end = perf_counter()
        log.info(f"AssistantGemini cog loaded in {end - start:.2f}s")

    @tasks.loop(minutes=5)
    async def save_loop(self):
        """Save data every 5 minutes"""
        if not self.saving:
            await self.save_conf()

    @save_loop.before_loop
    async def before_save_loop(self):
        """Wait until bot is ready before starting save loop"""
        await self.bot.wait_until_red_ready()

    async def save_conf(self):
        """Save configuration to database"""
        if self.saving:
            return
        
        self.saving = True
        try:
            await self.config.db.set(self.db.model_dump())
        except Exception as e:
            log.error(f"Failed to save configuration: {e}")
        finally:
            self.saving = False