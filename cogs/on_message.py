from discord.ext import commands
import app

this_bot = None

class OnMessage(commands.Cog):
    def __init__(self, bot):
        global this_bot
        this_bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg):
        try:
            if await app.getColumn(msg.guild.id, "is_enabled") == 1 and not await app.isBlacklisted(msg.guild.id, msg.channel.id) and not msg.author.bot:
                allow_xp = True

                if await app.getColumn(msg.guild.id, "antispam") == 1:
                    count = 0

                    for mess in this_bot.cached_messages:
                        if (msg.created_at - mess.created_at).seconds <= 5:
                            count += 1
                
                    allow_xp = count < 3

                if allow_xp:
                    
                    await app.addXP(msg.author, msg.guild, 1, msg.channel)

        except:
            pass

def setup(bot):
    bot.add_cog(OnMessage(bot))