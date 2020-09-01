import discord
from discord.ext import commands


class Disboard(commands.Cog):
    
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" has been loaded')


def setup(client):
    client.add_cog(Disboard(client))
