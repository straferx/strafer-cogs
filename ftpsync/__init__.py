from .ftpsync import Ftpsync

async def setup(bot):
    await bot.add_cog(Ftpsync(bot))