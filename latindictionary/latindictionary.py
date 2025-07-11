import discord
from redbot.core import commands
from redbot.core.bot import Red
import aiohttp


class LatinDictionary(commands.Cog):
    """Look up Latin words using freedictionaryapi.com."""

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
                    await ctx.send("❌ Error contacting the dictionary API.")
                    return

                try:
                    data = await resp.json()
                except Exception:
                    await ctx.send("❌ Could not parse API response.")
                    return

        if not data or not isinstance(data, dict) or "entries" not in data:
            await ctx.send(f"❌ No dictionary entry found for `{word}`.")
            return

        entries = data["entries"]
        if not entries:
            await ctx.send(f"❌ No dictionary entry found for `{word}`.")
            return

        embed = discord.Embed(
            title=f"📖 Latin Dictionary: `{data.get('word', word)}`",
            color=discord.Color.teal()
        )

        for entry in entries[:3]:  # Limit to 3 entries max to avoid overload
            pos = entry.get("partOfSpeech", "—").capitalize()
            senses = entry.get("senses", [])
            definitions = []

            for sense in senses:
                definition = sense.get("definition", "")
                translations = sense.get("translations", [])
                translated = [
                    f"{t.get('word')} ({t.get('language', {}).get('name', '')})"
                    for t in translations if t.get("word")
                ]
                if translated:
                    definition += f"\n↪ " + ", ".join(translated)
                definitions.append(definition)

            if definitions:
                embed.add_field(
                    name=pos,
                    value="\n".join(definitions[:3]),  # Show up to 3 definitions per part of speech
                    inline=False
                )

        await ctx.send(embed=embed)
