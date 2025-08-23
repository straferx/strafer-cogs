from .ftpsync import FtpSync

async def setup(bot):
    await bot.add_cog(FtpSync(bot)) 