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
        self.suggest_url = "https://freedictionaryapi.com/api/v1/suggest/la/"
        self._cache = {}

    @commands.command(name="latin")
    async def define_latin(self, ctx: commands.Context, *, text: str):
        """Look up one or more Latin words (comma or space separated)."""
        raw_words = [w.strip().lower() for w in text.replace(",", " ").split()]
        if not raw_words:
            await ctx.send("❌ You must provide at least one Latin word.")
            return

        all_results = []

        for word in raw_words:
            result = await self._get_word_definition(word)
            suggestions = []
            if not result:
                suggestions = await self._get_suggestions(word)
            all_results.append((word, result, suggestions))
            await asyncio.sleep(0.2)

        pages = []
        for word, result, suggestions in all_results:
            if not result or not result.get("entries"):
                suggestion_text = ""
                if suggestions:
                    suggestion_text = f"\n🛈 Did you mean: " + ", ".join(f"`{s}`" for s in suggestions[:5])
                pages.append(f"`❌` Such word isn't listed in Latin dictionary.{suggestion_text}")
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

                lines = translated_senses[:3] + structural_senses[:3 - len(translated_senses[:3])]

                if lines:
                    entry_text += f"__{pos}__\n" + "\n".join(f"• {d}" for d in lines) + "\n"

            pages.append(entry_text.strip())

        if len(pages) == 1:
            word, _, _ = all_results[0]
            wiktionary_url = f"https://en.wiktionary.org/wiki/{word}#Latin"
            is_missing = pages[0].startswith("`❌`")

            embed = discord.Embed(
                title=f'Dictionary – "{word}"',
                url=wiktionary_url,
                description=pages[0],
                color=discord.Color.red() if is_missing else discord.Color(0x36393F)
            )
            await ctx.send(embed=embed)
        else:
            embeds = []
            for i, (page, (word, _, _)) in enumerate(zip(pages, all_results), start=1):
                wiktionary_url = f"https://en.wiktionary.org/wiki/{word}#Latin"
                embed = discord.Embed(
                    title=f'Dictionary – "{word}"',
                    url=wiktionary_url,
                    description=page,
                    color=discord.Color.red() if page.startswith("`❌`") else discord.Color(0x36393F)
                )
                embed.set_footer(text=f"Page {i}/{len(pages)}")
                embeds.append(embed)
            await self._send_paginated_embeds(ctx, embeds)

    async def _get_word_definition(self, word: str):
        """Return cached or fetched word definition from the API."""
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

    async def _get_suggestions(self, word: str):
        """Return a list of close word suggestions from the API."""
        url = f"{self.suggest_url}{word}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    return data.get("suggestions", [])
        except Exception:
            return []

    async def _send_paginated_embeds(self, ctx, embeds):
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
