import discord
from discord.ext import commands
import config
import app

this_bot = None

class OtherEvents(commands.Cog):
    def __init__(self, bot):
        global this_bot
        this_bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await this_bot.change_presence(activity=discord.Game(app.__VERSION__))
        print("Ready!")

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx, err):
        if isinstance(err, commands.errors.NoPrivateMessage):
            await ctx.respond(embed=config.err)

def setup(bot):
    bot.add_cog(OtherEvents(bot))