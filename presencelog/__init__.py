from .presencelog import PresenceLog

async def setup(bot):
    await bot.add_cog(PresenceLog(bot))
