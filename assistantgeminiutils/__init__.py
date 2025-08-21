from .main import AssistantGeminiUtils

async def setup(bot):
    cog = AssistantGeminiUtils(bot)
    await bot.add_cog(cog) 