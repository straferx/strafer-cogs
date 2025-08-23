from .ftpsync import ftpsync

async def setup(bot):
    await bot.add_cog(ftpsync(bot)) 