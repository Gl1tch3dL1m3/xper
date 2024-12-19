import discord
from discord.ext import commands
import config
import app
from app import exec

this_bot = None

class Setup(commands.Cog):
    def __init__(self, bot):
        global this_bot
        this_bot = bot

    @discord.slash_command(name="set-up", description="Set up XPer for your server.")
    @commands.guild_only()
    async def setupcmd(self, ctx):
        try:
            if await app.isAdmin(ctx):
                # Global variables
                view = discord.ui.View()

                class Values:
                    index = -1
                    level_up_channel = None
                    level_up_message = None
                    antispam = None

                # Callbacks
                async def forwardPage(interaction):
                    if await app.isAdmin(interaction) and interaction.user.id == ctx.user.id:
                        view = await movePage()
                        await interaction.message.edit(embed=pages[Values.index], view=view)
                        await interaction.response.defer()

                async def previousPage(interaction):
                    if await app.isAdmin(interaction) and interaction.user.id == ctx.user.id:
                        view = await movePage(True)
                        await interaction.message.edit(embed=pages[Values.index], view=view)
                        await interaction.response.defer()

                async def page2menu(interaction):
                    if await app.isAdmin(interaction) and interaction.user.id == ctx.user.id:
                        global view
                        channel = view.get_item("page2menu").values[0]
                        permissions = channel.permissions_for(interaction.user)

                        if permissions.view_channel and permissions.send_messages:
                            Values.level_up_channel = channel.id
                            view = await movePage()
                            await interaction.message.edit(embed=pages[Values.index], view=view)
                            await interaction.response.defer()

                        else:
                            embed = config.err.copy()
                            embed.description = "The bot doesn't have access to the channel. Please check if the bot can *view the channel* and *send messages to the channel*."
                            await interaction.response.send_message(embed=embed, ephemeral=True)

                async def page3btn(interaction):
                    if await app.isAdmin(interaction) and interaction.user.id == ctx.user.id:
                        class SetMessage(discord.ui.Modal):
                            def __init__(self, *args, **kwargs):
                                super().__init__(*args, **kwargs)
                                self.add_item(discord.ui.InputText(label="Enter the message:", max_length=255, style=discord.InputTextStyle.long))

                            async def callback(self, interaction: discord.Interaction):
                                Values.level_up_message = self.children[0].value
                                await forwardPage(interaction)

                        await interaction.response.send_modal(SetMessage(title="Set Message"))

                async def page4enablebtn(interaction):
                    if await app.isAdmin(interaction) and interaction.user.id == ctx.user.id:
                        Values.antispam = 1
                        await forwardPage(interaction)

                async def page4disablebtn(interaction):
                    if await app.isAdmin(interaction) and interaction.user.id == ctx.user.id:
                        Values.antispam = 0
                        await forwardPage(interaction)

                async def updateMessage(interaction):
                    pages[4].description = "Are there any channels in which messages should be ignored? If so, add them now!\n\n" + await app.showListItems(ctx.guild.id)
                    await interaction.message.edit(embed=pages[4])
                    await interaction.response.defer()

                async def updateMessage2(interaction):
                    pages[5].description = "Reward server members with special roles they get when they reach a certain level!\n\n" + await app.showListItems(ctx.guild.id, "rewards")
                    await interaction.message.edit(embed=pages[5])
                    await interaction.response.defer()

                async def updateMessage3(interaction):
                    pages[6].description="Booster is a role which gives members more XP per message. Of course, you can set how many XP should the role give!\n\n" + await app.showListItems(ctx.guild.id, "boosters")
                    await interaction.message.edit(embed=pages[6])
                    await interaction.response.defer()

                async def page5add(interaction):
                    if await app.isAdmin(interaction) and interaction.user.id == ctx.user.id:
                        global view
                        await app.addToList(ctx, interaction, view.get_item("page5add").values[0].id, "blacklist", updateMessage)

                async def page5remove(interaction):
                    if await app.isAdmin(interaction) and interaction.user.id == ctx.user.id:
                        global view
                        await app.removeFromList(ctx, interaction, view.get_item("page5remove").values[0].id, "blacklist", updateMessage)

                async def page5deleteall(interaction):
                    if await app.isAdmin(interaction) and interaction.user.id == ctx.user.id:
                        global view
                        await app.deleteAllItems(ctx, interaction, "blacklist", updateMessage)

                async def page6add(interaction):
                    if await app.isAdmin(interaction) and interaction.user.id == ctx.user.id:
                        global view
                        class SetReqLevel(discord.ui.Modal):
                            def __init__(self, *args, **kwargs):
                                super().__init__(*args, **kwargs)
                                self.add_item(discord.ui.InputText(label="Enter the required level (max. 14654 level):", max_length=5))

                            async def callback(self, interaction: discord.Interaction):
                                try:
                                    value = int(self.children[0].value)
                                    if value > 14654 or value < 1: # 14654 is the max. level to get (because 4294967295 is the max value of INT type in MySQL and xp column is INT)
                                        raise Exception("")

                                    await app.addToList(ctx, interaction, [view.get_item("page6add").values[0].id, value], "rewards", updateMessage2)

                                except:
                                    embed = config.err.copy()
                                    embed.description = "Something went wrong. Make sure you typed in a number between 0 and 14654."
                                    await interaction.response.send_message(embed=embed, ephemeral=True)

                        await interaction.response.send_modal(SetReqLevel(title="Set Required Level"))

                async def page6remove(interaction):
                    if await app.isAdmin(interaction) and interaction.user.id == ctx.user.id:
                        global view
                        await app.removeFromList(ctx, interaction, view.get_item("page6remove").values[0].id, "rewards", updateMessage2)

                async def page6deleteall(interaction):
                    if await app.isAdmin(interaction) and interaction.user.id == ctx.user.id:
                        global view
                        await app.deleteAllItems(ctx, interaction, "rewards", updateMessage2)

                async def page7add(interaction):
                    if await app.isAdmin(interaction) and interaction.user.id == ctx.user.id:
                        global view
                        class SetBooster(discord.ui.Modal):
                            def __init__(self, *args, **kwargs):
                                super().__init__(*args, **kwargs)
                                self.add_item(discord.ui.InputText(label="Enter the XP boost (max. 30 XP):", max_length=2))

                            async def callback(self, interaction: discord.Interaction):
                                try:
                                    value = int(self.children[0].value)
                                    if value > 30 or value < 1:
                                        raise Exception("")

                                    await app.addToList(ctx, interaction, [view.get_item("page7add").values[0].id, value], "boosters", updateMessage3)

                                except:
                                    embed = config.err.copy()
                                    embed.description = "Something went wrong. Make sure you typed in a number between 0 and 30."
                                    await interaction.response.send_message(embed=embed, ephemeral=True)

                        await interaction.response.send_modal(SetBooster(title="Set XP Boost"))

                async def page7remove(interaction):
                    if await app.isAdmin(interaction) and interaction.user.id == ctx.user.id:
                        global view
                        await app.removeFromList(ctx, interaction, view.get_item("page7remove").values[0].id, "boosters", updateMessage3)

                async def page7deleteall(interaction):
                    if await app.isAdmin(interaction) and interaction.user.id == ctx.user.id:
                        global view
                        await app.deleteAllItems(ctx, interaction, "boosters", updateMessage3)

                # Set-up pages
                pages = [
                    discord.Embed(
                        title="Welcome to XPer set-up guide! 👋",
                        description="First of all, thank you very much for giving XPer a try! We hope you'll like the bot's functions. If you have any question regarding the bot, please join our [support server](https://discord.com/invite/tr55DGHEwN) and ask for a help (we don't bite)!\n\nThis bot is open-sourced and completely free for everyone to use! You can see the bot's code on [GitHub](https://github.com/Gl1tch3dL1m3/xper).\n\nWe also have another bot — [AutoProtection](https://top.gg/bot/1225485086363881494). It's a security bot which offers quality AntiSpam, AntiRaid, AntiNuke and much more security features for free! If you're interested, you can give it a shot!\n\nLet's jump into the first part of the set-up. Click the button below to go to the next page!\n\n*(Keep in mind that you **MUST** complete this guide to the last page.)*"
                    ),

                    discord.Embed(
                        title="Level-Up Notifications 📢",
                        description="When a user reaches a new level, XPer will send a notification to let them know!\n\nIf you want to set a channel for these notifications, use the select menu. If you don't want to set any channel, just skip this page and notifications will be sent in the channel in which the user is active."
                    ),

                    discord.Embed(
                        title="Level-Up Message :envelope:",
                        description="Now it's time to set the content of said notification. It should be a message that informs the user about reaching a new level.\n\nThe default message looks like this: \"Great job, {user}! Now you're level **{level}**!\"\n\n__Variables you can use:__\n- `{user}` - Inserts the user who reached a new level\n- `{level}` - Insert the user's current level\n- `{xp}` - Inserts the user's current XP\n- `{nextlevel}` - Inserts the user's next level to reach\n- `{nextlevelxp}` - Inserts the number of XP needed to reach the next level\n\nYou can set your own by clicking the \"Set Message\" button or use the default message by skipping this page."
                    ),

                    discord.Embed(
                        title="AntiSpam 💥",
                        description="AntiSpam prevents users from getting XP by spamming messages. If the user is spamming, they won't receive any XP. The user can receive XP again only when they stop spamming.\n\nYou can enable this module by clicking the \"Enable\" button or disable it by skipping this page."
                    ),

                    discord.Embed(
                        title="Ignorelist 📜",
                        description="Are there any channels in which messages should be ignored? Add them to the ignorelist!\n\n" + await app.showListItems(ctx.guild.id)
                    ),

                    discord.Embed(
                        title="Rewards 👑",
                        description="Reward server members with special roles they get when they reach a certain level!\n\n" + await app.showListItems(ctx.guild.id, "rewards")
                    ),

                    discord.Embed(
                        title="Boosters 🚀",
                        description="Booster is a role which gives members more XP per message. Of course, you can set how many XP should the role give!\n\n" + await app.showListItems(ctx.guild.id, "boosters")
                    ),

                    discord.Embed(
                        title="Set-up was successful! 🎉",
                        description="Great job! XPer is now successfully set up and ready to use. If you encounter any issues or have any questions, feel free to reach out to us. Thank you again for choosing XPer! We hope our bot will be helpful! :heart:",
                        color=discord.Colour.green()
                    )
                ]

                # Set-up buttons/menus
                items = [
                    [],
                    [
                        discord.ui.Select(select_type=discord.ComponentType.channel_select, channel_types=[discord.ChannelType.text, discord.ChannelType.news], placeholder="Select a channel...", custom_id="page2menu")
                    ],
                    [
                        discord.ui.Button(label="Set Message", style=discord.ButtonStyle.gray, emoji="✉")
                    ],
                    [
                        discord.ui.Button(label="Enable", style=discord.ButtonStyle.success, emoji="✅")
                    ],
                    [
                        discord.ui.Select(select_type=discord.ComponentType.channel_select, channel_types=[discord.ChannelType.text, discord.ChannelType.news], placeholder="Add a channel...", custom_id="page5add"),
                        discord.ui.Select(select_type=discord.ComponentType.channel_select, channel_types=[discord.ChannelType.text, discord.ChannelType.news], placeholder="Remove a channel...", custom_id="page5remove"),
                        discord.ui.Button(label="Delete All Items", style=discord.ButtonStyle.gray, emoji="⛔")
                    ],
                    [
                        discord.ui.Select(select_type=discord.ComponentType.role_select, placeholder="Add a reward...", custom_id="page6add"),
                        discord.ui.Select(select_type=discord.ComponentType.role_select, placeholder="Remove a reward...", custom_id="page6remove"),
                        discord.ui.Button(label="Delete All Items", style=discord.ButtonStyle.gray, emoji="⛔")
                    ],
                    [
                        discord.ui.Select(select_type=discord.ComponentType.role_select, placeholder="Add a booster...", custom_id="page7add"),
                        discord.ui.Select(select_type=discord.ComponentType.role_select, placeholder="Remove a booster...", custom_id="page7remove"),
                        discord.ui.Button(label="Delete All Items", style=discord.ButtonStyle.gray, emoji="⛔")
                    ],
                    []
                ]

                # Assigned callbacks
                callbacks = [
                    [],
                    [
                        page2menu
                    ],
                    [
                        page3btn
                    ],
                    [
                        page4enablebtn
                    ],
                    [
                        page5add,
                        page5remove,
                        page5deleteall
                    ],
                    [
                        page6add,
                        page6remove,
                        page6deleteall
                    ],
                    [
                        page7add,
                        page7remove,
                        page7deleteall
                    ],
                    []
                ]

                async def movePage(previous=False):
                    global view
                    view = discord.ui.View()
                    Values.index = Values.index - 1 if previous else Values.index + 1

                    pages[Values.index].set_footer(text=f"Page {Values.index+1} of {len(pages)}")
                    pages[Values.index].set_author(name=ctx.user.name, icon_url=ctx.user.avatar.url)
                    pages[Values.index].color = discord.Colour.teal() if Values.index != 7 else pages[Values.index].color

                    prev_btn = discord.ui.Button(label="Previous Page", style=discord.ButtonStyle.red, emoji="👈")
                    skip_btn = discord.ui.Button(label="Skip", style=discord.ButtonStyle.blurple, emoji="⏩")

                    prev_btn.callback = previousPage
                    skip_btn.callback = forwardPage if Values.index != 3 else page4disablebtn

                    def renameSkip():
                        skip_btn.label = "Next Page"
                        skip_btn.emoji = "👉"

                    def addItems():
                        index = -1

                        for callback in callbacks[Values.index]:
                            index += 1
                            items[Values.index][index].callback = callback

                        for item in items[Values.index]:
                            view.add_item(item)

                    if Values.index != 0:
                        if Values.index == 1:
                            Values.level_up_channel = None
                        elif Values.index == 2:
                            Values.level_up_message = None
                        elif Values.index == 3:
                            Values.antispam = 0
                        elif Values.index in [4, 5, 6]:
                            renameSkip()
                        else:
                            await exec("DELETE FROM servers WHERE server_id=%s", (ctx.guild.id, ))
                            await exec("INSERT INTO servers VALUES (%s, 1, %s, %s, %s)", (ctx.guild.id, Values.level_up_channel, Values.level_up_message, Values.antispam))

                        if Values.index != 7:
                            addItems()
                            view.add_item(prev_btn)
                            view.add_item(skip_btn)

                    else:
                        renameSkip()
                        view.add_item(skip_btn)

                    return view
                
                view = await movePage()
                await ctx.respond(embed=pages[Values.index], view=view)

        except:
            pass

def setup(bot):
    bot.add_cog(Setup(bot))