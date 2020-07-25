import discord
import json
import os
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions, MissingPermissions, BotMissingPermissions


class Utility(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.tasks = discord.ext.tasks

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "utility" has been loaded')

    def incrCounter(self, cmdName):
        with open('counters.json', 'r') as f:
            values = json.load(f)
            values[str(cmdName)] += 1
        with open('counters.json', 'w') as f:
            json.dump(values, f, indent=4)

    @commands.command(aliases=['used', 'usedcount'])
    async def counter(self, ctx, commandName=None):
        await ctx.message.delete()

        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)
            serverPrefix = prefixes[str(ctx.guild.id)]
        with open('counters.json', 'r') as f:
            values = json.load(f)
            keyList = values.items()
            if commandName is not None:
                execCount = values[str(commandName)]
                counterEmbed = discord.Embed(title=f"Command \"{str.capitalize(commandName)}\" Counter",
                                             description=f"`{serverPrefix}{commandName}` was executed **{execCount}** "
                                                         "times",
                                             color=discord.Color.blue())
            else:
                counterEmbed = discord.Embed(title="Command Counter",
                                             color=discord.Color.blue())
                for key, execCount in keyList:
                    counterEmbed.add_field(name=f"Command: {str.capitalize(key)}",
                                           value=f"Executed: **{execCount}** times")

        await ctx.channel.send(embed=counterEmbed)
        self.incrCounter('counter')

    @commands.command(aliases=['p', 'checkprefix', 'prefixes'])
    async def prefix(self, ctx):
        await ctx.message.delete()
        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)

        serverPrefix = prefixes[str(ctx.guild.id)]
        prefixEmbed = discord.Embed(title='Prefixes',
                                    color=discord.Color.blue())
        prefixEmbed.add_field(name="Current Server Prefix",
                              value=f"The current server prefix is: `{serverPrefix}`",
                              inline=False)
        prefixEmbed.add_field(name="Global Prefixes",
                              value=f"{self.client.user.mention} or `mb `",
                              inline=False)
        await ctx.channel.send(embed=prefixEmbed)
        self.incrCounter('prefix')

    @commands.command(aliases=['sp', 'setprefix'])
    @commands.has_permissions(manage_guild=True)
    async def setPrefix(self, ctx, prefix):
        await ctx.message.delete()
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
        self.incrCounter('setPrefix')

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
    async def serverStats(self, ctx):
        await ctx.message.delete()

        async def serverstatsupdate(channel: discord.VoiceChannel, name):
            await channel.edit(name=name)

        client = self.client
        guild = client.get_guild(ctx.guild.id)

        totalMembers = guild.member_count
        totalMembersName = f"👥Members: {totalMembers}"

        totalChannels = int(len(guild.channels))
        totalChannelsName = f"📖Total Channels: {totalChannels}"

        totalText = int(len(guild.text_channels))
        totalTextName = f"📑Text Channels: {totalText}"

        totalVoice = int(len(guild.voice_channels))
        totalVoiceName = f"🎧Voice Channels: {totalVoice}"

        totalRole = int(len(guild.roles))
        totalRoleName = f"📜Roles: {totalRole}"

        totalEmoji = int(len(guild.emojis))
        totalEmojiName = f"😄Custom Emotes: {totalEmoji}"

        names = [totalMembersName, totalChannelsName, totalTextName, totalVoiceName, totalRoleName, totalEmojiName]

        overwrite = discord.PermissionOverwrite()
        overwrite.connect = False

        category = await guild.create_category(name="📊Server Stats📊")

        await category.set_permissions(guild.default_role, overwrite=overwrite)
        await category.edit(position=0)
        posIncr = 0
        for name in names:
            posIncr += 1
            await category.create_voice_channel(name=name,
                                                position=posIncr,
                                                sync_permission=True)
        self.incrCounter('serverStats')

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
    async def timezone(self, ctx, name=None):
        if name is not None:
            if "GMT" in name:
                nick = f"{ctx.author.display_name} [{name}]"
                await ctx.author.edit(nick=nick)
                title = "Timezone Update Success"
                description = f"{ctx.author.mention}'s timezone has been added to their nickname"
                color = discord.Color.blue()
                self.incrCounter('timezone')
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
            description = "I can only change the timezone of a user that is a lower role than I am. "\
                          "Please place my role higher than the highest user role assigned (or just put mine at the " \
                          "top) "
            await sendEmbed(ctx, title, description)




def setup(client):
    client.add_cog(Utility(client))
