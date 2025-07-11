import discord
from redbot.core import commands
from redbot.core.bot import Red
import aiohttp


class LatinDictionary(commands.Cog):
    """Look up Latin words using FreeDictionaryAPI."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.api_base = "https://freedictionaryapi.com/api/v1/entries/la/"

    @commands.command(name="latin")
    async def define_latin(self, ctx: commands.Context, word: str):
        """Look up a Latin word from freedictionaryapi.com."""
        url = f"{self.api_base}{word.lower()}?translations=true"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await ctx.send("❌ Could not reach the dictionary API.")
                    return
                try:
                    data = await resp.json()
                except Exception:
                    await ctx.send("❌ Error parsing dictionary response.")
                    return

        if not data or not isinstance(data, list):
            await ctx.send(f"❌ No entry found for `{word}`.")
            return

        entry = data[0]
        latin_word = entry.get("word", word)
        definitions = entry.get("meanings", [])

        if not definitions:
            await ctx.send(f"❌ No definitions found for `{latin_word}`.")
            return

        embed = discord.Embed(
            title=f"📖 Latin Dictionary: `{latin_word}`",
            color=discord.Color.dark_gold()
        )

        for meaning in definitions:
            part = meaning.get("partOfSpeech", "—").capitalize()
            definition = meaning.get("definition", "—")
            embed.add_field(name=part, value=definition, inline=False)

        await ctx.send(embed=embed)
