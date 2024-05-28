from .test import Test


async def setup(bot):
    await bot.add_cog(Test(bot))
