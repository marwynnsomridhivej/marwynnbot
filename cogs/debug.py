import discord
import json
from discord.ext import commands


class Debug(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "debug" has been loaded')

    def incrCounter(self, cmdName):
        with open('counters.json', 'r') as f:
            values = json.load(f)
            values[str(cmdName)] += 1
        with open('counters.json', 'w') as f:
            json.dump(values, f, indent=4)

    @commands.command()
    async def ping(self, ctx):
        await ctx.message.delete()
        self.incrCounter('ping')
        ping = discord.Embed(title='Ping', color=discord.colour.Color.blue())
        ping.set_thumbnail(url='https://cdn1.iconfinder.com/data/icons/travel-and-leisure-vol-1/512/16-512.png')
        ping.add_field(name="MarwynnBot", value=f'{round(self.client.latency * 1000)}ms')
        await ctx.send(embed=ping)


def setup(client):
    client.add_cog(Debug(client))
