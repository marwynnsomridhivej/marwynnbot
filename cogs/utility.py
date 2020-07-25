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
        client = self.client
        guild = client.get_guild(ctx.guild.id)
        totalMembers = guild.member_count
        totalChannels = int(len(guild.channels))
        totalText = int(len(guild.text_channels))
        totalVoice = int(len(guild.voice_channels))
        totalRole = int(len(guild.roles))
        totalEmoji = int(len(guild.emojis))
        overwrite = discord.PermissionOverwrite()
        overwrite.connect = False
        category = await guild.create_category(name="📊Server Stats📊")
        await category.set_permissions(guild.default_role, overwrite=overwrite)
        await category.edit(position=0)
        totalMembersVC = await category.create_voice_channel(name=f"👥Members: {totalMembers}",
                                                             position=1,
                                                             sync_permission=True)
        totalChannelsVC = await category.create_voice_channel(name=f"📖Total Channels: {totalChannels}",
                                                              position=2,
                                                              sync_permission=True)
        totalTextVC = await category.create_voice_channel(name=f"📑Text Channels: {totalText}",
                                                          position=3,
                                                          sync_permission=True)
        totalVoiceVC = await category.create_voice_channel(name=f"🎧Voice Channels: {totalVoice}",
                                                           position=4,
                                                           sync_permission=True)
        totalRoleVC = await category.create_voice_channel(name=f"📜Roles: {totalRole}",
                                                          position=5,
                                                          sync_permission=True)
        totalEmojiVC = await category.create_voice_channel(name=f"😄Custom Emotes: {totalEmoji}",
                                                           position=6,
                                                           sync_permission=True)

    @tasks.loop(minutes=10)
    async def timer(self, ctx):


    @commands.command(aliases=['tz'])
    @commands.bot_has_permissions(administrator=True)
    async def timezone(self, ctx):
        return


def setup(client):
    client.add_cog(Utility(client))
