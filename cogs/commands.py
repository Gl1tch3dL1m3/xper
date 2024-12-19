import discord
from discord.ext import commands
import config
import app
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
from os import remove
import app
from app import exec, XPToLevel
from time import time
from math import floor

this_bot = None

async def autocomplete(actx):
    server_id = actx.interaction.guild.id
    msg = await exec("SELECT level_up_message FROM servers WHERE server_id=%s", (server_id, ))
    return [msg[0][0] if msg != () and msg[0][0] else "Great job, {user}! Now you're level **{level}**!"]

class Commands(commands.Cog):
    def __init__(self, bot: discord.Bot):
        global this_bot
        this_bot = bot

    manage = discord.SlashCommandGroup("manage", "Manages the server settings and lists.")
    xp_group = discord.SlashCommandGroup("xp", "XP stuff for admins.")

    @discord.slash_command(description="Shows your level card.")
    @commands.guild_only()
    async def level(self, ctx, user: discord.Option(discord.User, "Enter the user whose level you want to see.", required=False)): # type: ignore
        await ctx.defer()
        try:
            user = user if user else ctx.user

            # Get values from DB
            xp = await exec("SELECT xp FROM users WHERE server_id=%s AND user_id=%s", (ctx.guild.id, user.id))
            xp = xp[0][0] if xp != () else 0
            next_xp = XPToLevel(xp) * (XPToLevel(xp) + 1) * 20

            # Make a card
            color = (0,255,144)
            with Image.new("RGB", (600,300), (0,0,0)) as img: # Create black image 600x300
                draw = ImageDraw.Draw(img) # Make a draw object (it's needed to insert text and shapes)
                draw.rectangle([(0,200), (53+(492/(next_xp-((XPToLevel(xp)-1)*XPToLevel(xp)*20)))*(xp-((XPToLevel(xp)-1)*XPToLevel(xp)*20)),249)], fill=(38,255,157)) # XP bar
                with Image.open(BytesIO(await user.avatar.read())).resize((100,100)) as avatar: # Get user's avatar
                    with Image.open("imgs/themes/classic.png").convert("RGBA") as theme: # Open the card template (RGBA because there're some empty spaces we need to fill (like the user's avatar))
                        font = ImageFont.truetype("fonts/Quicksand.ttf", 30) # Load the font
                        img.paste(avatar, (250,20)) # Paste the user's avatar on the black image
                        img.paste(theme, (0,0), theme) # Paste the template on the previous image with the user's avatar

                        draw.text((300, 147), user.name, font=font, anchor="mm", fill=color) # Write the user's name on their card
                        draw.text((50, 250), f"{(XPToLevel(xp)-1)*XPToLevel(xp)*20} XP", font=font, fill=color) # Show their starting XP
                        draw.text((549, 250), f"{next_xp} XP", font=font, anchor="ra", fill=color) # Show their required XP to reach the next level
                        draw.text((300, 221), f"Level {XPToLevel(xp)}: {xp} XP", font=font, anchor="mm", fill=(0,115,85)) # Show their level and XP
                        img.save(f"imgs/{user.id}_level.png", "PNG") # Save the image

            file = discord.File(f"imgs/{user.id}_level.png")
            await ctx.respond(file=file)
            del file

        except:
            pass

        remove(f"imgs/{ctx.user.id}_level.png")

    @manage.command(description="Manages the server settings.")
    @commands.guild_only()
    async def settings(self, ctx):
        try:
            if await app.isAdmin(ctx):
                msg = await app.showSettings(ctx)
                view = discord.ui.View()

                if msg[1]: # If makeview from showSettings is True, make the message's view
                    class ServerSettings(discord.ui.View):
                        @discord.ui.select(
                            placeholder="Change a setting...",
                            options=[discord.SelectOption(label=x[0], emoji="👈", value=x[1]) for x in config.rows]
                        )

                        async def changesettingsselect(self, select, interaction):
                            if await app.isAdmin(interaction) and ctx.user.id == interaction.user.id:
                                value = select.values[0]
                                if value == "level_up_channel":
                                    await exec(f"UPDATE servers SET level_up_channel=NULL WHERE server_id=%s", (ctx.guild.id, ))
                                    msg = await app.showSettings(ctx)
                                    await interaction.message.edit(embed=msg[0])
                                    await interaction.response.defer()

                                elif value == "level_up_message":
                                    class SetMessage(discord.ui.Modal):
                                        def __init__(self, *args, **kwargs):
                                            super().__init__(*args, **kwargs)
                                            self.add_item(discord.ui.InputText(label="Enter the message:", max_length=255, style=discord.InputTextStyle.long, placeholder="Leave this blank to use the default message...", required=False))

                                        async def callback(self, interaction: discord.Interaction):
                                            value = self.children[0].value
                                            await exec("UPDATE servers SET level_up_message=%s WHERE server_id=%s", (value if value != "" else None, ctx.guild.id))
                                            msg = await app.showSettings(ctx)
                                            await interaction.message.edit(embed=msg[0])
                                            await interaction.response.defer()

                                    await interaction.response.send_modal(SetMessage(title="Set Message"))

                                else:
                                    await exec(f"UPDATE servers SET {value}=CASE WHEN {value}=1 THEN 0 ELSE 1 END WHERE server_id=%s", (ctx.guild.id, ))
                                    msg = await app.showSettings(ctx)
                                    await interaction.message.edit(embed=msg[0])
                                    await interaction.response.defer()

                        @discord.ui.select(
                            placeholder="Change the Level-Up Channel...",
                            select_type=discord.ComponentType.channel_select, channel_types=[discord.ChannelType.text, discord.ChannelType.news]
                        )

                        async def levelupchannelselect(self, select, interaction):
                            if await app.isAdmin(interaction) and ctx.user.id == interaction.user.id:
                                await exec("UPDATE servers SET level_up_channel=%s WHERE server_id=%s", (select.values[0].id, ctx.guild.id))
                                msg = await app.showSettings(ctx)
                                await interaction.message.edit(embed=msg[0])
                                await interaction.response.defer()
                    view = ServerSettings()

                await ctx.respond(embed=msg[0], ephemeral=not msg[1], view=view)

        except:
            pass

    @manage.command(description="Manages the server ignorelist.")
    @commands.guild_only()
    async def ignorelist(self, ctx):
        try:
            if await app.isAdmin(ctx):
                embed = discord.Embed(
                    author=discord.EmbedAuthor(name=ctx.user.display_name, icon_url=ctx.user.display_avatar),
                    title="Ignorelist 📜",
                    description=await app.showListItems(ctx.guild.id),
                    color=discord.Colour(16759941)
                )

                async def messageUpdate(interaction):
                    embed.description = await app.showListItems(ctx.guild.id)
                    await interaction.message.edit(embed=embed)
                    await interaction.response.defer()

                class IgnorelistView(discord.ui.View):
                    @discord.ui.select(
                        select_type=discord.ComponentType.channel_select,
                        channel_types=[discord.ChannelType.text, discord.ChannelType.news],
                        placeholder="Add a channel..."
                    )

                    async def callback1(self, select, interaction):
                        if await app.isAdmin(interaction):
                            await app.addToList(ctx, interaction, select.values[0].id, "blacklist", messageUpdate)

                    @discord.ui.select(
                        select_type=discord.ComponentType.channel_select,
                        channel_types=[discord.ChannelType.text, discord.ChannelType.news],
                        placeholder="Remove a channel...",
                    )

                    async def callback2(self, select, interaction):
                        if await app.isAdmin(interaction):
                            await app.removeFromList(ctx, interaction, select.values[0].id, "blacklist", messageUpdate)

                    @discord.ui.button(
                        label="Delete All Items",
                        style=discord.ButtonStyle.gray,
                        emoji="⛔"
                    )

                    async def callback3(self, button, interaction):
                        if await app.isAdmin(interaction):
                            await app.deleteAllItems(ctx, interaction, "blacklist", messageUpdate)
                
                await ctx.respond(embed=embed, view=IgnorelistView())

        except:
            pass

    @manage.command(description="Manages the server rewards.")
    @commands.guild_only()
    async def rewards(self, ctx):
        try:
            if await app.isAdmin(ctx):
                embed = discord.Embed(
                    author=discord.EmbedAuthor(name=ctx.user.display_name, icon_url=ctx.user.display_avatar),
                    title="Rewards 👑",
                    description=await app.showListItems(ctx.guild.id, "rewards"),
                    color=discord.Colour.yellow()
                )

                async def messageUpdate(interaction):
                    embed.description = await app.showListItems(ctx.guild.id, "rewards")
                    await interaction.message.edit(embed=embed)
                    await interaction.response.defer()

                class RewardsView(discord.ui.View):
                    @discord.ui.select(
                        select_type=discord.ComponentType.role_select,
                        placeholder="Add a reward..."
                    )

                    async def callback1(self, select, interaction):
                        if await app.isAdmin(interaction):
                            class SetReqLevel(discord.ui.Modal):
                                def __init__(self, *args, **kwargs):
                                    super().__init__(*args, **kwargs)
                                    self.add_item(discord.ui.InputText(label="Enter the required level (max. 14654 level):", max_length=9))

                                async def callback(self, interaction: discord.Interaction):
                                    try:
                                        value = int(self.children[0].value)
                                        if value > 14654 or value < 1: # 14654 is the max. level to get (because 4294967295 is the max value of INT type in MySQL and xp column is INT)
                                            raise Exception("")

                                        await app.addToList(ctx, interaction, [select.values[0].id, value], "rewards", messageUpdate)

                                    except:
                                        embed = config.err.copy()
                                        embed.description = "Something went wrong. Make sure you typed in a number between 0 and 14654."
                                        await interaction.response.send_message(embed=embed, ephemeral=True)

                            await interaction.response.send_modal(SetReqLevel(title="Set Required Level"))

                    @discord.ui.select(
                        select_type=discord.ComponentType.role_select,
                        placeholder="Remove a reward...",
                    )

                    async def callback2(self, select, interaction):
                        if await app.isAdmin(interaction):
                            await app.removeFromList(ctx, interaction, select.values[0].id, "rewards", messageUpdate)

                    @discord.ui.button(
                        label="Delete All Items",
                        style=discord.ButtonStyle.gray,
                        emoji="⛔"
                    )

                    async def callback3(self, button, interaction):
                        if await app.isAdmin(interaction):
                            await app.deleteAllItems(ctx, interaction, "rewards", messageUpdate)
                
                await ctx.respond(embed=embed, view=RewardsView())

        except:
            pass

    @manage.command(description="Manages the server boosters.")
    @commands.guild_only()
    async def boosters(self, ctx):
        try:
            if await app.isAdmin(ctx):
                embed = discord.Embed(
                    author=discord.EmbedAuthor(name=ctx.user.display_name, icon_url=ctx.user.display_avatar),
                    title="Boosters 🚀",
                    description=await app.showListItems(ctx.guild.id, "boosters"),
                    color=discord.Colour(16747253)
                )

                async def messageUpdate(interaction):
                    embed.description = await app.showListItems(ctx.guild.id, "boosters")
                    await interaction.message.edit(embed=embed)
                    await interaction.response.defer()

                class BoostersView(discord.ui.View):
                    @discord.ui.select(
                        select_type=discord.ComponentType.role_select,
                        placeholder="Add a booster..."
                    )

                    async def callback1(self, select, interaction):
                        if await app.isAdmin(interaction):
                            class SetBooster(discord.ui.Modal):
                                def __init__(self, *args, **kwargs):
                                    super().__init__(*args, **kwargs)
                                    self.add_item(discord.ui.InputText(label="Enter the XP boost (max. 30 XP):", max_length=2))

                                async def callback(self, interaction: discord.Interaction):
                                    try:
                                        value = int(self.children[0].value)
                                        if value > 30 or value < 1:
                                            raise Exception("")

                                        await app.addToList(ctx, interaction, [select.values[0].id, value], "boosters", messageUpdate)

                                    except:
                                        embed = config.err.copy()
                                        embed.description = "Something went wrong. Make sure you typed in a number between 0 and 30."
                                        await interaction.response.send_message(embed=embed, ephemeral=True)

                            await interaction.response.send_modal(SetBooster(title="Set XP Boost"))

                    @discord.ui.select(
                        select_type=discord.ComponentType.role_select,
                        placeholder="Remove a booster...",
                    )

                    async def callback2(self, select, interaction):
                        if await app.isAdmin(interaction):
                            await app.removeFromList(ctx, interaction, select.values[0].id, "boosters", messageUpdate)

                    @discord.ui.button(
                        label="Delete All Items",
                        style=discord.ButtonStyle.gray,
                        emoji="⛔"
                    )

                    async def callback3(self, button, interaction):
                        if await app.isAdmin(interaction):
                            await app.deleteAllItems(ctx, interaction, "boosters", messageUpdate)
                
                await ctx.respond(embed=embed, view=BoostersView())

        except:
            pass

    @discord.slash_command(name="boosters", description="Shows your active boosters.")
    @commands.guild_only()
    async def showboosters(self, ctx):
        try:
            boosters = await exec("SELECT item, rate FROM boosters WHERE server_id=%s ORDER BY rate ASC", (ctx.guild.id, ))
            msg = ""
            xp_per_msg = 1

            for booster in boosters:
                if ctx.user.get_role(booster[0]):
                    xp_per_msg += booster[1]
                    msg += f"- <@&{booster[0]}> (+**{booster[1]}** XP)"

            msg = "You currently have no active boosters." if msg == "" else msg
            msg += f"\n\n*You get +**{xp_per_msg}** XP per message.*"

            embed = discord.Embed(
                author=discord.EmbedAuthor(name=ctx.user.name, icon_url=ctx.user.avatar.url),
                title="Active Boosters 🚀",
                description=msg,
                color=discord.Colour(16747253)
            )
            await ctx.respond(embed=embed)

        except:
            pass

    @discord.slash_command(description="Shows the server leaderboard.")
    @commands.guild_only()
    async def leaderboard(self, ctx):
        try:
            lb = await exec("SELECT user_id, xp FROM users WHERE server_id=%s ORDER BY xp DESC LIMIT 20", (ctx.guild.id, ))
            msg = "Here is a list of the TOP 20 members with the most XP:\n\n"
            place = 0

            for member in lb:
                place += 1
                msg += f"{"🥇" if place == 1 else "🥈" if place == 2 else "🥉" if place == 3 else "🥔" if place == 4 else str(place)+". place"}: <@{member[0]}> *({member[1]} XP)*\n"

            msg = "There is no one here at the moment..." if msg == "Here is a list of the TOP 20 members with the most XP:\n\n" else msg

            embed = discord.Embed(
                author=discord.EmbedAuthor(name=ctx.user.name, icon_url=ctx.user.avatar.url),
                title="Leaderboard 🏆",
                description=msg,
                color=discord.Colour.yellow()
            )
            await ctx.respond(embed=embed)

        except:
            pass

    @xp_group.command(description="Adds XP to a user.")
    @commands.guild_only()
    async def add(self, ctx, user: discord.Option(discord.User, "Enter the user you want to add XP to."), xp_to_add: discord.Option(int, "Enter the number of XP you want to add.")): # type: ignore
        if await app.isAdmin(ctx):
            try:
                if user.bot:
                    raise Exception("You can't add XP to a bot.")
                await app.addXP(user, ctx.guild, xp_to_add, None, False, False)
                xp = await exec("SELECT xp FROM users WHERE user_id=%s AND server_id=%s", (user.id, ctx.guild.id))

                embed = discord.Embed(
                    author=discord.EmbedAuthor(name=ctx.user.name, icon_url=ctx.user.avatar.url),
                    title="Success ✅",
                    description=f"You have successfully added **{xp_to_add}** XP to <@{user.id}>. The user now has **{xp[0][0]}** XP.",
                    color=discord.Colour.green()
                )

                await ctx.respond(embed=embed)

            except Exception as e:
                embed = config.err.copy()
                embed.description = f"Something went wrong. Error: `{e}`"
                await ctx.respond(embed=embed, ephemeral=True)

    @xp_group.command(description="Removes XP from a user.")
    @commands.guild_only()
    async def remove(self, ctx, user: discord.Option(discord.User, "Enter the user you want to remove XP from."), xp_to_remove: discord.Option(int, "Enter the number of XP you want to remove.")): # type: ignore
        if await app.isAdmin(ctx):
            try:
                if user.bot:
                    raise Exception("You can't remove XP from a bot.")
                try:
                    await exec("UPDATE users SET xp=CASE WHEN xp<%s THEN 0 ELSE xp-%s END WHERE user_id=%s AND server_id=%s", (xp_to_remove, xp_to_remove, user.id, ctx.guild.id))
                except:
                    pass
                xp = await exec("SELECT xp FROM users WHERE user_id=%s AND server_id=%s", (user.id, ctx.guild.id))

                embed = discord.Embed(
                    author=discord.EmbedAuthor(name=ctx.user.name, icon_url=ctx.user.avatar.url),
                    title="Success ✅",
                    description=f"You have successfully removed **{xp_to_remove}** XP from <@{user.id}>. The user now has **{xp[0][0] if xp != () else 0}** XP.",
                    color=discord.Colour.green()
                )

                await ctx.respond(embed=embed)

            except Exception as e:
                embed = config.err.copy()
                embed.description = f"Something went wrong. Error: `{e}`"
                await ctx.respond(embed=embed, ephemeral=True)

    @xp_group.command(description="Sets a user's XP to a certain number.")
    @commands.guild_only()
    async def set(self, ctx, user: discord.Option(discord.User, "Enter the user you want to remove XP from."), xp_to_set: discord.Option(int, "Enter the number of XP you want to set.")): # type: ignore
        if await app.isAdmin(ctx):
            try:
                if user.bot:
                    raise Exception("You can't set XP to a bot.")
                val = await exec("SELECT xp FROM users WHERE user_id=%s AND server_id=%s", (user.id, ctx.guild.id))
                if val == ():
                    await exec("INSERT IGNORE INTO users VALUES (%s, %s, %s)", (user.id, ctx.guild.id, xp_to_set))
                else:
                    await exec("UPDATE users SET xp=%s WHERE user_id=%s AND server_id=%s", (xp_to_set, user.id, ctx.guild.id))

                embed = discord.Embed(
                    author=discord.EmbedAuthor(name=ctx.user.name, icon_url=ctx.user.avatar.url),
                    title="Success ✅",
                    description=f"You have successfully set **{xp_to_set}** XP to <@{user.id}>.",
                    color=discord.Colour.green()
                )

                await ctx.respond(embed=embed)

            except Exception as e:
                embed = config.err.copy()
                embed.description = f"Something went wrong. Error: `{e}`"
                await ctx.respond(embed=embed, ephemeral=True)

    @discord.slash_command(description="Sends the help message.")
    async def help(self, ctx):
        embed = discord.Embed(
            author=discord.EmbedAuthor(name=ctx.user.display_name, icon_url=ctx.user.avatar.url),
            title="Help ❓",
            description=f"Hello! I'm **{app.__NAME__}** and I'm here to make your community more active! If you've invited me for the first time, please run `/set-up` to set-up my functions. You can view a list of commands by typing `/`.\n\nThank you for choosing **{app.__NAME__}** as your leveling bot! 📈",
            color=discord.Colour.red()
        )
        
        class helpView(discord.ui.View):
            def __init__(self):
                super().__init__()
                btn = discord.ui.Button(label="Invite", style=discord.ButtonStyle.gray, url="https://discord.com/oauth2/authorize?client_id=1270365392853794870&permissions=268471296&integration_type=0&scope=bot")
                self.add_item(btn)
                btn = discord.ui.Button(label="Support", style=discord.ButtonStyle.gray, url="https://discord.com/invite/tr55DGHEwN")
                self.add_item(btn)
                btn = discord.ui.Button(label="GitHub", style=discord.ButtonStyle.gray, url="https://github.com/Gl1tch3dL1m3/xper")
                self.add_item(btn)
                
        await ctx.respond(embed=embed, view=helpView())

    @discord.slash_command(description="Shows the bot statistics.")
    async def statistics(self, ctx):
        uptime = time() - app.uptime
        
        days = floor(uptime / 86400)
        uptime -= 86400 * days
        hours = floor(uptime / 3600)
        uptime -= 3600 * hours
        minutes = floor(uptime / 60)
        uptime -= 60 * minutes

        embed = discord.Embed(
            author=discord.EmbedAuthor(name=ctx.user.display_name, icon_url=ctx.user.display_avatar),
            title="Statistics 📊",
            description=f"The bot's version is **{app.__VERSION__}**.\nThe bot is in **{len(this_bot.guilds)}** servers.\nThe bot is online for **{days}d {hours}h {minutes}m {round(uptime)}s**.\nThe bot's latency is **{round(this_bot.latency * 1000)}ms**.",
            color=discord.Colour.teal()
        )
        
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Commands(bot))