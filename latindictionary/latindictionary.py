import discord
from redbot.core import commands
from redbot.core.bot import Red
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
        raw_words = [w.strip().lower() for w in text.replace(",", " ").split()]
        if not raw_words:
            await ctx.send("❌ You must provide at least one Latin word.")
            return

        all_results = []

        for word in raw_words:
            result = await self._get_word_definition(word)
            all_results.append((word, result))
            await asyncio.sleep(0.2)  # avoid rate-limiting

        # Build formatted output
        pages = []
        for word, result in all_results:
            if not result:
                pages.append(f"❌ **{word}**: not found.")
                continue

            entry_text = f"📖 **{word}**\n"
            for entry in result.get("entries", [])[:3]:
                pos = entry.get("partOfSpeech", "—").capitalize()
                senses = entry.get("senses", [])

                translated_senses = []
                structural_senses = []

                for sense in senses:
                    definition = sense.get("definition", "").strip()
                    translations = sense.get("translations", [])

                    if translations:
                        english_tr = [
                            t.get("word")
                            for t in translations
                            if t.get("word") and (
                                t.get("language", {}).get("code") == "en"
                                or t.get("language", {}).get("name", "").lower() == "english"
                            )
                        ]
                        if english_tr:
                            definition += "\n↪ " + ", ".join(english_tr)
                            translated_senses.append(definition)
                        else:
                            structural_senses.append(definition)
                    else:
                        structural_senses.append(definition)

                # Prioritize definitions with translations
                lines = translated_senses[:3] + structural_senses[:3 - len(translated_senses[:3])]

                if lines:
                    entry_text += f"__{pos}__\n" + "\n".join(f"• {d}" for d in lines) + "\n"

            pages.append(entry_text.strip())

        # Send result(s)
        if len(pages) == 1:
            embed = discord.Embed(
                title=f"Latin Dictionary: `{raw_words[0]}`",
                description=pages[0],
                color=discord.Color(0x36393F)
            )
            await ctx.send(embed=embed)
        else:
            embeds = []
            for i, page in enumerate(pages, start=1):
                embed = discord.Embed(
                    title="Latin Dictionary Results",
                    description=page,
                    color=discord.Color(0x36393F)
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
        if not embeds:
            return

        if len(embeds) == 1:
            await ctx.send(embed=embeds[0])
            return

        try:
            from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
            await menu(ctx, embeds, controls=DEFAULT_CONTROLS, timeout=60)
        except Exception:
            for embed in embeds:
                await ctx.send(embed=embed)
                await asyncio.sleep(1)
