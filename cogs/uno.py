import discord
from discord.ext import commands
import json
import os


class Uno(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "uno" has been loaded')

    def incrCounter(self, cmdName):
        with open('counters.json', 'r') as f:
            values = json.load(f)
            values[str(cmdName)] += 1
        with open('counters.json', 'w') as f:
            json.dump(values, f, indent=4)

    async def buildEmbed(self, ctx, title='Friendship Destroyer (aka. Uno)', description=None,
                         color=discord.Color.blue(), user1=None, val1=None, user2=None, val2=None, user3=None,
                         val3=None, user4=None, val4=None):
        embed = discord.Embed(title=title,
                              description=description,
                              color=color)
        embed.add_field(name=user1,
                        value=val1)
        embed.add_field(name=user2,
                        value=val2)
        if user3 is not None:
            embed.add_field(name=user3,
                            value=val3)
        if user4 is not None:
            embed.add_field(name=user4,
                            value=val4)
        await ctx.channel.send(embed=embed)

    @commands.group()
    async def uno(self, ctx, *, member: discord.Member = None):
        await ctx.message.delete()
        if member is not None:
            self.incrCounter("uno")
            return
        else:
            self.incrCounter("uno")
            return


def setup(client):
    client.add_cog(Uno(client))
