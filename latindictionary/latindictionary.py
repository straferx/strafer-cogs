import discord
from redbot.core import commands
from redbot.core.bot import Red
import aiohttp


class LatinDictionary(commands.Cog):
    """Look up Latin words using a free online dictionary API."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.api_url = "https://latin-dictionary-api.vercel.app/api/v1/entries?word="

    @commands.command(name="latin")
    async def define_latin(self, ctx: commands.Context, word: str):
        """Look up a Latin word from a public dictionary API."""
        url = self.api_url + word.lower()

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await ctx.send("❌ Error contacting the dictionary API.")
                    return

                data = await resp.json()

        if not data:
            await ctx.send(f"❌ No definition found for `{word}`.")
            return

        entry = data[0]
        embed = discord.Embed(
            title=f"📖 Latin Dictionary: `{entry['word']}`",
            color=discord.Color.dark_gold()
        )

        for definition in entry.get("definitions", []):
            part = definition.get("partOfSpeech", "—").capitalize()
            meaning = definition.get("meaning", "—")
            embed.add_field(name=part, value=meaning, inline=False)

        await ctx.send(embed=embed)