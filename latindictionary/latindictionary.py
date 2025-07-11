import discord
from redbot.core import commands
from redbot.core.bot import Red
from collections import defaultdict
import aiohttp
import asyncio

class LatinDictionary(commands.Cog):
    """Look up Latin words using freedictionaryapi.com."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.api_base = "https://freedictionaryapi.com/api/v1/entries/la/"
        self._cache = {}  # in-memory simple cache

    @commands.command(name="latin")
    async def define_latin(self, ctx: commands.Context, *, text: str):
        """Look up one or more Latin words (comma/space separated)."""
        # Normalize input
        raw_words = [w.strip().lower() for w in text.replace(",", " ").split()]
        if not raw_words:
            await ctx.send("❌ You must provide at least one Latin word.")
            return

        all_results = []

        for word in raw_words:
            result = await self._get_word_definition(word)
            all_results.append((word, result))
            await asyncio.sleep(0.2)  # To avoid hammering the API too fast

        # Build the output
        pages = []
        for word, result in all_results:
            if not result:
                pages.append(f"❌ **{word}**: not found.")
                continue

            entry_text = f"📖 **{word}**\n"
            for entry in result.get("entries", [])[:3]:
                pos = entry.get("partOfSpeech", "—").capitalize()
                senses = entry.get("senses", [])
                lines = []
                for sense in senses[:3]:
                    definition = sense.get("definition", "")
                    translations = sense.get("translations", [])
                    if translations:
                        tr = [f"{t.get('word')} ({t.get('language', {}).get('name', '')})"
                              for t in translations if t.get("word")]
                        if tr:
                            definition += "\n↪ " + ", ".join(tr)
                    lines.append(definition.strip())
                if lines:
                    entry_text += f"__{pos}__\n" + "\n".join(f"• {d}" for d in lines) + "\n"
            pages.append(entry_text.strip())

# Format embed(s)
if len(pages) == 1:
    embed = discord.Embed(
        title=f"Latin Dictionary: `{raw_words[0]}`",
        description=pages[0],
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)
else:
    embeds = []
    for i, page in enumerate(pages, start=1):
        embed = discord.Embed(
            title="Latin Dictionary Results",
            description=page,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Page {i}/{len(pages)}")
        embeds.append(embed)
        
        await self._send_paginated_embeds(ctx, embeds)


    async def _get_word_definition(self, word: str):
        """Return cached or fetched word definition JSON from the API."""
        if word in self._cache:
            return self._cache[word]

        url = f"{self.api_base}{word}?translations=true"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
        except Exception:
            return None

        if isinstance(data, dict) and "entries" in data:
            self._cache[word] = data
            return data
        return None

    async def _send_paginated_embeds(self, ctx, embeds):
        """Send multiple embeds as pages."""
        if len(embeds) == 0:
            return

        if len(embeds) == 1:
            await ctx.send(embed=embeds[0])
            return

        try:
            from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
            await menu(ctx, embeds, controls=DEFAULT_CONTROLS, timeout=60)
        except Exception:
            # fallback to sending separately
            for embed in embeds:
                await ctx.send(embed=embed)
                await asyncio.sleep(1)
