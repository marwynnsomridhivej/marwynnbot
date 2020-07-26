import discord
import json
from discord.ext import commands
import globalcommands
from globalcommands import GlobalCMDS

gcmds = globalcommands.GlobalCMDS


class Debug(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "debug" has been loaded')

    @commands.command()
    async def ping(self, ctx):
        await ctx.message.delete()
        ping = discord.Embed(title='Ping', color=discord.colour.Color.blue())
        ping.set_thumbnail(url='https://cdn1.iconfinder.com/data/icons/travel-and-leisure-vol-1/512/16-512.png')
        ping.add_field(name="MarwynnBot", value=f'{round(self.client.latency * 1000)}ms')
        await ctx.send(embed=ping, delete_after=10)
        gcmds.incrCounter(gcmds, 'ping')

    @commands.command()
    async def shard(self, ctx, option=None):
        await ctx.message.delete()
        if option != 'count':
            shardDesc = f"This server is running on shard: {ctx.guild.shard_id}"
        else:
            shardDesc = f"**Shards:** {self.client.shard_count}"
        shardEmbed = discord.Embed(title="Shard Info",
                                   description=shardDesc,
                                   color=discord.Color.blue())
        await ctx.channel.send(embed=shardEmbed, delete_after=30)
        gcmds.incrCounter(gcmds, 'shard')


def setup(client):
    client.add_cog(Debug(client))
