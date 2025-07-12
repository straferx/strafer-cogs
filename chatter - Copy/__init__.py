from .chatter import Chatter

async def setup(bot):
    await bot.add_cog(Chatter(bot))