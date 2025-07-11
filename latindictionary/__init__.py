from .latindictionary import LatinDictionary

async def setup(bot):
    await bot.add_cog(LatinDictionary(bot))