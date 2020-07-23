import discord
from discord.ext import commands


class Games(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "games" has been loaded')

    @commands.group()
    async def uno(self, ctx, *, member: discord.Member = None):
        await ctx.message.delete()
        if member is not None:
            return
        else:
            return


def setup(client):
    client.add_cog(Games(client))
