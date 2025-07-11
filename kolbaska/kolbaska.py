from redbot.core import commands

class Kolbaska (commands.Cog):
    """sends kolbaska"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def kolbaska(self, ctx):
        """sends kolbaska"""
        # Your code will go here
        await ctx.send("https://media.discordapp.net/attachments/524652203064033280/1064847268466937926/kolbaspin-1-1.gif?ex=6656fd4c&is=6655abcc&hm=ce7e7bdf3395536aca889011c74b554b5b8ca003e4d6bf2f6578b5e7022d0e25&")
