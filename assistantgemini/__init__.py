from .assistantgemini import AssistantGemini

__red_end_user_data_statement__ = "This cog stores prompts and Gemini API keys on a per server basis. If enabled, conversations with the bot are also persistently stored."

async def setup(bot):
    cog = AssistantGemini(bot)
    await bot.add_cog(cog) 