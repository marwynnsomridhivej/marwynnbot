import datetime
import discord
from discord.ext import commands
from globalcommands import GlobalCMDS as gcmds


class Debug(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "debug" has been loaded')

    @commands.command()
    async def ping(self, ctx):
        await gcmds.invkDelete(gcmds, ctx)
        ping = discord.Embed(title='Ping', color=discord.colour.Color.blue())
        ping.set_thumbnail(url='https://cdn1.iconfinder.com/data/icons/travel-and-leisure-vol-1/512/16-512.png')
        ping.add_field(name="MarwynnBot", value=f'{round(self.client.latency * 1000)}ms')
        await ctx.send(embed=ping, delete_after=10)
        gcmds.incrCounter(gcmds, ctx, 'ping')

    @commands.group(aliases=['flag'])
    async def report(self, ctx):
        await gcmds.invkDelete(gcmds, ctx)

    @report.command(aliases=['issue'])
    async def bug(self, ctx, *, bug_message):
        await gcmds.invkDelete(gcmds, ctx)
        try:
            marwynnbot_channel = commands.AutoShardedBot.get_channel(self.client, 742899140320821367)

        except discord.NotFound:
            invalid = discord.Embed(title="Logging Channel Does Not Exist",
                                    description=f"{ctx.author.mention}, this feature is not available",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid)
            return
        else:
            timestamp = "Timestamp: {:%m/%d/%Y %H:%M:%S}".format(datetime.datetime.now())
            bug_string = str(bug_message)
            bugEmbed = discord.Embed(title=f"Bug Report by {ctx.author}",
                                     description=bug_string,
                                     color=discord.Color.blue())
            bugEmbed.set_footer(text=timestamp,
                                icon_url=ctx.author.avatar_url)
            message = await marwynnbot_channel.send(embed=bugEmbed)
            await message.publish()

    @report.command(aliases=['server', 'guild'])
    async def serverAbuse(self, ctx, *, abuse_message):
        return

    @report.command(aliases=['user', 'member'])
    async def userAbuse(self, ctx, *, abuse_message):
        return

    @report.command(aliases=['fix', 'patch'])
    async def update(self, ctx, *, update_message):
        if not await self.client.is_owner(ctx.author):
            insuf = discord.Embed(title="Insufficient User Permissions",
                                  description=f"{ctx.author.mention}, you must be the bot owner to use this command",
                                  color=discord.Color.dark_red())
            await ctx.channel.send(embed=insuf, delete_after=10)
            return

        try:
            marwynnbot_channel = commands.AutoShardedBot.get_channel(self.client, 742899140320821367)

        except discord.NotFound:
            invalid = discord.Embed(title="Logging Channel Does Not Exist",
                                    description=f"{ctx.author.mention}, this feature is not available",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid)
            return
        else:
            timestamp = "Timestamp: {:%m/%d/%Y %H:%M:%S}".format(datetime.datetime.now())
            update_string = str(update_message)
            updateEmbed = discord.Embed(title="Bot Update",
                                        description=update_string,
                                        color=discord.Color.blue())
            updateEmbed.set_footer(text=timestamp,
                                   icon_url=ctx.author.avatar_url)
            message = await marwynnbot_channel.send(embed=updateEmbed)
            await message.publish()

    @commands.command()
    async def shard(self, ctx, option=None):
        await gcmds.invkDelete(gcmds, ctx)
        if option != 'count':
            shardDesc = f"This server is running on shard: {ctx.guild.shard_id}"
        else:
            shardDesc = f"**Shards:** {self.client.shard_count}"
        shardEmbed = discord.Embed(title="Shard Info",
                                   description=shardDesc,
                                   color=discord.Color.blue())
        await ctx.channel.send(embed=shardEmbed, delete_after=30)
        gcmds.incrCounter(gcmds, ctx, 'shard')


def setup(client):
    client.add_cog(Debug(client))
