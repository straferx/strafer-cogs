from .randomreactor import RandomReactor

async def setup(bot):
    await bot.add_cog(RandomReactor(bot))
