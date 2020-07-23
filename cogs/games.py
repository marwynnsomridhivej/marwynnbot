import discord
from discord.ext import commands

class Games(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "games" has been loaded')


    @commands.command()
    async def uno(self, ctx):
        return



def setup(client):
    client.add_cog(Games(client))