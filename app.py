import discord
import config
import asyncio
import aiomysql
from time import time

# NEXT LEVEL XP FORMULA:
# (current level) * (current level + 1) * 20

__NAME__ = "XPer"
__AUTHOR__ = "@glitchedlime"
__VERSION__ = "v1.0"

bot = discord.Bot()
uptime = time()

# Asyncio stuff / DB

pool = None
loop = asyncio.get_event_loop()

async def exec(sql, vars=None):
    async with pool.acquire() as con:
        async with con.cursor() as cur:
            if vars != "" and vars != None:
                await cur.execute(sql, vars)
            else:
                await cur.execute(sql)
            if sql.startswith("SELECT"):
                return await cur.fetchall()

async def main():
    global pool
    pool = await aiomysql.create_pool(
        **config.dbconfig,
        loop=loop,
        autocommit=True
    )

loop.run_until_complete(main())

async def getColumn(guild_id, column, table="servers"):
    try:
        settings = await exec(f"SELECT {column} FROM {table} WHERE server_id={guild_id}")
        return settings[0][0] if settings else None
    except:
        pass

# Admin check
async def isAdmin(ctx): # ctx can be ApplicationContext or Interaction
    if not ctx.user.guild_permissions.administrator:
        if isinstance(ctx, discord.ApplicationContext):
            await ctx.respond(embed=config.noadmin, ephemeral=True)
        else:
            await ctx.response.send_message(embed=config.noadmin, ephemeral=True)
    
    return ctx.user.guild_permissions.administrator

# Check if a channel is blacklisted
async def isBlacklisted(server_id, channel_id):
    blacklist = await exec("SELECT item FROM blacklist WHERE server_id=%s", (server_id))
    blacklist = [x[0] for x in blacklist]
    return channel_id in blacklist

# Show list items / rewards
async def showListItems(guild_id, table="blacklist"):
    # I didn't use ternary form because it would't be clear (too long)
    if table == "blacklist":
        items = await exec("SELECT item FROM blacklist WHERE server_id=%s", (guild_id, ))
    elif table == "rewards":
        items = await exec("SELECT item, req_level FROM rewards WHERE server_id=%s ORDER BY req_level ASC", (guild_id, ))
    else:
        items = await exec("SELECT item, rate FROM boosters WHERE server_id=%s ORDER BY rate ASC", (guild_id, ))
    
    _str = f"**Items ({len(items)}/15):**\n"
    _str += "There are currently no items added." if items == () else ""

    for item in items:
        # And here too
        if table == "blacklist":
            _str += f"- <#{item[0]}>\n"
        elif table == "rewards":
            _str += f"- <@&{item[0]}> *(Requires level **{item[1]}**)*\n"
        else:
            _str += f"- <@&{item[0]}> *(+**{item[1]}** XP)*\n"

    return _str

# Add list item / reward
async def addToList(ctx, interaction, item, table, messageUpdate): # item will be list if table is "rewards" - [role_id, req_level]
    if await isAdmin(interaction) and interaction.user.id == ctx.user.id:
        items = await exec(f"SELECT * FROM {table} WHERE server_id=%s", (ctx.guild.id, )) # We don't have to worry about SQL injections because user won't have access to this function
        is_already_added = await exec(f"SELECT COUNT(*) FROM {table} WHERE server_id=%s AND item=%s", (ctx.guild.id, item if table == "blacklist" else item[0]))

        # If the limit was exceeded
        if len(items) == 15:
            embed = config.err.copy()
            embed.description = "You've reached the maximum allowed number of items."
            await interaction.response.send_message(embed=embed, ephemeral=True)

        # If an item with the same value already exists
        elif is_already_added[0][0] != 0:
            embed = config.err.copy()
            embed.description = "An item with the same value already exists."
            await interaction.response.send_message(embed=embed, ephemeral=True)

        else:
            if table == "blacklist":
                await exec("INSERT INTO blacklist VALUES (%s, %s)", (ctx.guild.id, item))
            else: # If rewards
                await exec(f"INSERT INTO {table} VALUES (%s, %s, %s)", (ctx.guild.id, item[0], item[1]))
            try:
                await messageUpdate(interaction)
            except:
                pass

# Remove list item / reward
async def removeFromList(ctx, interaction, item, table, messageUpdate):
    if await isAdmin(interaction) and interaction.user.id == ctx.user.id:
        await exec(f"DELETE FROM {table} WHERE server_id=%s AND item=%s", (ctx.guild.id, item))
        try:
            await messageUpdate(interaction)
        except:
            pass

# Delete all items button
async def deleteAllItems(ctx, interaction, table, messageUpdate):
    if await isAdmin(interaction) and interaction.user.id == ctx.user.id:
        await exec(f"DELETE FROM {table} WHERE server_id=%s", (ctx.guild.id, ))
        try:
            await messageUpdate(interaction)
        except:
            pass

def XPToLevel(xp):
    level = 1

    while xp >= level * (level+1) * 20:
        level += 1

    return level

# Get required XP to reach a new level
def getNextXP(xp):
    return XPToLevel(xp) * (XPToLevel(xp) + 1) * 20

# Add XP
async def addXP(user, server, add_xp, channel=None, send=True, use_boosters=True):
    xp = await exec("SELECT xp FROM users WHERE user_id=%s AND server_id=%s", (user.id, server.id))
    xp = xp[0][0] if xp != () else ()

    if use_boosters:
        boosters = await exec("SELECT item, rate FROM boosters WHERE server_id=%s", (server.id, ))

        for booster in boosters:
            if user.get_role(booster[0]):
                add_xp += booster[1]

    if xp == ():
        await exec("INSERT INTO users VALUES (%s, %s, %s)", (user.id, server.id, add_xp))
        xp = add_xp
    else:
        await exec("UPDATE users SET xp=xp+%s WHERE user_id=%s AND server_id=%s", (add_xp, user.id, server.id))

    if xp + add_xp >= getNextXP(xp): # If current XPs are bigger or equal to the new level required XPs, send notification
        msg: str = await exec("SELECT level_up_message FROM servers WHERE server_id=%s", (server.id, ))
        msg = msg[0][0] if msg[0][0] else "Great job, {user}! Now you're level **{level}**!"
        rewards = await exec("SELECT item FROM rewards WHERE server_id=%s AND req_level<=%s", (server.id, XPToLevel(xp+add_xp)))
        sel = await exec("SELECT level_up_channel FROM servers WHERE server_id=%s", (server.id, ))
        channel = server.get_channel(sel[0][0]) if sel != () else channel

        if channel and send:
            try:
                await channel.send(msg
                           .replace("{user}", f"<@{user.id}>")
                           .replace("{level}", str(XPToLevel(xp + add_xp)))
                           .replace("{xp}", str(xp + add_xp))
                           .replace("{nextlevel}", str(XPToLevel(xp + add_xp) + 1))
                           .replace("{nextlevelxp}", str(XPToLevel(xp + add_xp) * (XPToLevel(xp + add_xp) + 1) * 20)))
            except Exception as e:
                print(e)
            
            # For loop because you can have more roles after reaching a new level
            for reward in rewards:
                reward = server.get_role(reward[0])
                try:
                    await user.add_roles(reward)
                except:
                    pass

async def showSettings(ctx):
    embed = config.err.copy()
    ephemeral = False
    makeview = False
    settings = await exec("SELECT * FROM servers WHERE server_id=%s", (ctx.guild.id, ))
    
    if len(settings) == 0:
        embed.description = "The server isn't set up. Please run `/set-up` to set up " + __NAME__ + " for this server. ❌"
        ephemeral=True
            
    else:
        settings = settings[0]
        settings = list(settings)[1:]
               
        try:   
            index = -1
            msg = ""
            
            for i in config.rows:
                index += 1
                offon = "❌" if settings[index] in [0, None] else "✅"
                        
                if index == 1:
                    offon += f" (<#{settings[1]}>)" if offon == "✅" else ""
                    msg += f"\n{config.rows[index][0]}: {offon}"

                elif index == 2:
                    offon += f" (\"{settings[2]}\")" if offon == "✅" else " (Using the default message)"
                    msg += f"\n{config.rows[index][0]}: {offon}"
                            
                else:
                    msg += f"\n{config.rows[index][0]}: {offon}"
            
            embed = discord.Embed(
                author=discord.EmbedAuthor(name=ctx.user.display_name, icon_url=ctx.user.display_avatar),
                title="Server settings ⚙️",
                description=msg,
                color=discord.Colour.teal()
            )
            makeview = True
            
        except:
            pass
            
    return [embed, makeview, ephemeral]

bot.load_extension("cogs", recursive=True)
bot.run(config.token)
