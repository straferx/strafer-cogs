from .kolbaska import Kolbaska


async def setup(bot):
    await bot.add_cog(Kolbaska(bot))
