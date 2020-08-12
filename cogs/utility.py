import json
from asyncio import sleep
import discord
import typing
from discord.ext import commands, tasks
from discord.ext.commands import MissingPermissions, BotMissingPermissions, CommandInvokeError

from globalcommands import GlobalCMDS as gcmds


class Utility(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "utility" has been loaded')

    @commands.command(aliases=['counters', 'used', 'usedcount'])
    async def counter(self, ctx, commandName=None, mode='server'):
        await gcmds.invkDelete(gcmds, ctx)

        gcmds.file_check(gcmds, "counters.json", '{\n\n}')

        if commandName == 'global':
            mode = commandName
            commandName = None

        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)
            serverPrefix = prefixes[str(ctx.guild.id)]

        with open('counters.json', 'r') as f:
            values = json.load(f)
            if commandName is None:
                if mode == 'server':
                    keyList = values['Server'][str(ctx.guild.id)].items()
                else:
                    keyList = values['Global'].items()
            if commandName is not None:
                if mode != 'global':
                    execCount = values['Server'][str(ctx.guild.id)][str(commandName)]
                else:
                    execCount = values['Global'][str(commandName)]
                if execCount != 1:
                    if mode != 'global':
                        description = f"`{serverPrefix}{commandName}` was executed **{execCount}** " \
                                      f"times in *{ctx.guild.name}*"
                    else:
                        description = f"`{serverPrefix}{commandName}` was executed **{execCount}** times globally"
                else:
                    if mode != 'global':
                        description = f"`{serverPrefix}{commandName}` was executed **{execCount}** " \
                                      f"time in *{ctx.guild.name}*"
                    else:
                        description = f"`{serverPrefix}{commandName}` was executed **{execCount}** time globally"
                counterEmbed = discord.Embed(title=f"Command \"{str.capitalize(commandName)}\" Counter",
                                             description=description,
                                             color=discord.Color.blue())
            else:
                if mode == 'server':
                    title = f"{str(ctx.guild.name).capitalize()} Command Counter"
                else:
                    title = "Global Command Counter"
                counterEmbed = discord.Embed(title=title,
                                             color=discord.Color.blue())
                for key, execCount in keyList:
                    if execCount != 1:
                        value = f"Executed: **{execCount}** times"
                    else:
                        value = f"Executed: **{execCount}** time"
                    counterEmbed.add_field(name=f"Command: {str.capitalize(key)}",
                                           value=value)

        await ctx.channel.send(embed=counterEmbed)
        gcmds.incrCounter(gcmds, ctx, 'counter')

    @counter.error
    async def counter_error(self, ctx, error):
        if isinstance(error, CommandInvokeError):
            title = "No Command Found"
            description = "There are no counters for that command"
        else:
            title = "An Error Occured"
            description = f"**Error Thrown:** {error}"
        errorEmbed = discord.Embed(title=title,
                                   description=description,
                                   color=discord.Color.dark_red())
        await ctx.channel.send(embed=errorEmbed)

    @commands.command(aliases=['fleave'])
    @commands.is_owner()
    async def forceleave(self, ctx, guild_id=None):
        await gcmds.invkDelete(gcmds, ctx)
        if guild_id is not None:
            id = guild_id
        else:
            id = ctx.guild.id
        await self.client.get_guild(id).leave()
        leaveEmbed = discord.Embed(title="Successfully Left Server",
                                   description=f"Left guild id: {id}",
                                   color=discord.Color.blue())
        await ctx.author.send(embed=leaveEmbed)
        print("Success")

    @forceleave.error
    async def forceleave_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            error = discord.Embed(title="Insufficient User Permissions",
                                  description=f"{ctx.author.mention}, you must own this bot to use this command",
                                  color=discord.Color.dark_red())
            await ctx.channel.send(embed=error, delete_after=10)

    @commands.command(aliases=['emotes', 'serveremotes', 'serveremote', 'serverEmote', 'emojis', 'emoji'])
    async def serverEmotes(self, ctx, *, search=None):
        await gcmds.invkDelete(gcmds, ctx)
        description = []
        for emoji in ctx.guild.emojis:
            if search is not None:
                if search in emoji.name:
                    description.append(f"\n**{emoji.name}:** \\<:{emoji.name}:{emoji.id}>")
            else:
                description.append(f"\n**{emoji.name}:** \\<:{emoji.name}:{emoji.id}>")
        sort = sorted(description)
        description = ""
        for string in sort:
            description += string

        emojiEmbed = discord.Embed(title="Server Custom Emotes:",
                                   description=description,
                                   color=discord.Color.blue())
        await ctx.channel.send(embed=emojiEmbed)

    @commands.command(aliases=['p', 'checkprefix', 'prefixes'])
    async def prefix(self, ctx):
        await gcmds.invkDelete(gcmds, ctx)
        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)

        serverPrefix = prefixes[str(ctx.guild.id)]
        prefixEmbed = discord.Embed(title='Prefixes',
                                    color=discord.Color.blue())
        prefixEmbed.add_field(name="Current Server Prefix",
                              value=f"The current server prefix is: `{serverPrefix}`",
                              inline=False)
        prefixEmbed.add_field(name="Global Prefixes",
                              value=f"{self.client.user.mention} or `mb ` - *ignorecase*",
                              inline=False)
        await ctx.channel.send(embed=prefixEmbed)
        gcmds.incrCounter(gcmds, ctx, 'prefix')

    @commands.command(aliases=['sp', 'setprefix'])
    @commands.has_permissions(manage_guild=True)
    async def setPrefix(self, ctx, prefix):
        await gcmds.invkDelete(gcmds, ctx)
        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)
            if prefix != 'reset':
                prefixes[str(ctx.guild.id)] = prefix
            else:
                prefixes[str(ctx.guild.id)] = 'm!'
        with open('prefixes.json', 'w') as f:
            json.dump(prefixes, f, indent=4)
        if prefix != 'reset':
            prefixEmbed = discord.Embed(title='Server Prefix Set',
                                        description=f"Server prefix is now set to `{prefix}` \n\n"
                                                    f"You will still be able to use {self.client.user.mention} "
                                                    f"and `mb ` as prefixes",
                                        color=discord.Color.blue())
        else:
            prefixEmbed = discord.Embed(title='Server Prefix Set',
                                        description=f"Server prefix has been reset to `m!`",
                                        color=discord.Color.blue())
        await ctx.channel.send(embed=prefixEmbed)
        gcmds.incrCounter(gcmds, ctx, 'setPrefix')

    @setPrefix.error
    async def setPrefix_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            setPrefixError = discord.Embed(title="Error - Insufficient User Permissions",
                                           description=f"{ctx.author.mention}, you need the `Manage Server` "
                                                       f"permission to change the server prefix!",
                                           color=discord.Color.dark_red())
            await ctx.channel.send(embed=setPrefixError)

    @commands.command(aliases=['ss', 'serverstats', 'serverstatistics'])
    @commands.bot_has_permissions(administrator=True)
    @commands.has_permissions(administrator=True)
    async def serverStats(self, ctx, reset=None):
        await gcmds.invkDelete(gcmds, ctx)

        @tasks.loop(minutes=10)
        async def serverstatsupdate(ctx, names):
            guildSearch = self.client.get_guild(ctx.guild.id)
            for categorySearch in guildSearch.categories:
                if categorySearch.name == "📊Server Stats📊":
                    for vcs in categorySearch.voice_channels:
                        for channelName in names:
                            await vcs.edit(name=channelName)
            await sleep(600)

        serverstatsupdate.stop()

        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)
            serverPrefix = prefixes[str(ctx.guild.id)]

        client = self.client
        guild = client.get_guild(ctx.guild.id)

        if reset == "reset":
            if guild == ctx.author.guild:
                if "📊Server Stats📊" not in guild.categories:
                    resetEmbed = discord.Embed(title="📊Server Stats📊 Category does not exist",
                                               description=f"{ctx.author.mention}, "
                                                           f"do `{serverPrefix}serverstats` "
                                                           "to create the category and stats channels",
                                               color=discord.Color.dark_red())
                    await ctx.channel.send(embed=resetEmbed, delete_after=10)
                    gcmds.incrCounter(gcmds, ctx, 'serverStats')

                for category in guild.categories:
                    if category.name == "📊Server Stats📊":
                        resetEmbed = discord.Embed(title=f"{category.name} Reset",
                                                   description=f"{int(len(category.voice_channels))} Channels to be "
                                                               f"deleted",
                                                   color=discord.Color.blue())
                        for vcs in category.voice_channels:
                            resetEmbed.add_field(name=vcs.name,
                                                 value="Channel deleted",
                                                 inline=False)
                            await vcs.delete()
                        resetEmbed.add_field(name=f"{category.name}",
                                             value="Category deleted",
                                             inline=False)
                        await category.delete()
                await ctx.channel.send(embed=resetEmbed, delete_after=10)
                gcmds.incrCounter(gcmds, ctx, 'serverStats')

            return

        totalMembers = guild.member_count
        totalMembersName = f"👥Members: {totalMembers}"

        totalText = int(len(guild.text_channels))
        totalTextName = f"📑Text Channels: {totalText}"

        totalVoice = int(len(guild.voice_channels))
        totalVoiceName = f"🎧Voice Channels: {totalVoice}"

        totalChannels = totalText + totalVoice
        totalChannelsName = f"📖Total Channels: {totalChannels}"

        totalRole = int(len(guild.roles))
        totalRoleName = f"📜Roles: {totalRole}"

        totalEmoji = int(len(guild.emojis))
        totalEmojiName = f"😄Custom Emotes: {totalEmoji}"

        names = [totalMembersName, totalChannelsName, totalTextName, totalVoiceName, totalRoleName, totalEmojiName]

        if guild == ctx.author.guild:
            for category in guild.categories:
                if category.name == "📊Server Stats📊":
                    statsEmbed = discord.Embed(title="📊Server Stats📊 Channel Already Exists",
                                               description=f"{ctx.author.mention}, there is no need for duplicate "
                                                           f"channels",
                                               color=discord.Color.dark_red())
                    await ctx.channel.send(embed=statsEmbed, delete_after=10)
                    gcmds.incrCounter(gcmds, ctx, 'serverStats')
                    serverstatsupdate.restart(ctx, names)
                    return

        overwrite = discord.PermissionOverwrite()
        overwrite.connect = False

        category = await guild.create_category(name="📊Server Stats📊")

        await category.set_permissions(guild.default_role, overwrite=overwrite)
        await category.edit(position=0)

        statsEmbed = discord.Embed(title="Successfully Created Server Stats Channels",
                                   description="They will be at the top of your discord server",
                                   color=discord.Color.blue())

        for name in names:
            await category.create_voice_channel(name=name,
                                                sync_permission=True)
            statsEmbed.add_field(name=f"Channel: {name}",
                                 value="Successfully created channel",
                                 inline=False)
        await ctx.channel.send(embed=statsEmbed, delete_after=10)
        gcmds.incrCounter(gcmds, ctx, 'serverStats')
        serverstatsupdate.restart(ctx, names)

    @serverStats.error
    async def serverStats_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            name = "Insufficient User Permissions"
            description = f"{ctx.author.mention}, you need the Administrator permission to use this command"
        if isinstance(error, BotMissingPermissions):
            name = "Insufficient Bot Permissions"
            description = "I need the Administrator permission to use this command"
        errorEmbed = discord.Embed(title=name,
                                   description=description,
                                   color=discord.Color.dark_red())
        await ctx.channel.send(embed=errorEmbed, delete_after=5)

    @commands.command(aliases=['tz'])
    @commands.bot_has_permissions(administrator=True)
    @commands.has_permissions(change_nickname=True)
    async def timezone(self, ctx, *, timezoneInput):
        await gcmds.invkDelete(gcmds, ctx)
        nameSpace = str(timezoneInput)
        name = nameSpace.replace(" ", "")
        if name == 'reset' or name == 'r':
            await ctx.author.edit(nick=f"{ctx.author.name}")
            title = "Timezone Reset Success"
            description = f"{ctx.author.mention}'s timezone has been removed from their name"
            color = discord.Color.blue()
        elif name is not None:
            if "GMT" in name:
                nick = f"{ctx.author.display_name} [{name}]"
                await ctx.author.edit(nick=nick)
                title = "Timezone Update Success"
                description = f"{ctx.author.mention}'s timezone has been added to their nickname"
                color = discord.Color.blue()
                gcmds.incrCounter(gcmds, ctx, 'timezone')
            else:
                title = "Invalid Timezone Format"
                description = "Please put your timezone in `GMT+` or `GMT-` format"
                color = discord.Color.dark_red()
        else:
            title = "Invalid Timezone Format"
            description = "Please put your timezone in `GMT+` or `GMT-` format"
            color = discord.Color.dark_red()
        gmt = discord.Embed(title=title,
                            description=description,
                            color=color)
        await ctx.channel.send(embed=gmt, delete_after=10)

    @timezone.error
    async def timezone_error(self, ctx, error):
        async def sendEmbed(ctx, title, description):
            errorEmbed = discord.Embed(title=title,
                                       description=description,
                                       color=discord.Color.dark_red())
            await ctx.channel.send(embed=errorEmbed, delete_after=5)

        if isinstance(error, MissingPermissions):
            title = "Insufficient User Permissions"
            description = "I need the Change Nickname permission to use this command"
            await sendEmbed(ctx, title, description)
        if isinstance(error, BotMissingPermissions):
            title = "Insufficient Bot Permissions"
            description = "I need the Administrator permission to use this command"
            await sendEmbed(ctx, title, description)
        if isinstance(error, discord.Permissions):
            title = "403 Permissions Error"
            description = "I can only change the timezone of a user that is a lower role than I am. " \
                          "Please place my role higher than the highest user role assigned (or just put mine at the " \
                          "top) "
            await sendEmbed(ctx, title, description)


def setup(client):
    client.add_cog(Utility(client))
