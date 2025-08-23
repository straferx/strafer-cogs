from .FTPSync import FTPSync

async def setup(bot):
    await bot.add_cog(FTPSync(bot))