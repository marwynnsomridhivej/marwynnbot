import discord
import json
from discord.ext import commands
import customerrors
from globalcommands import GlobalCMDS


gcmds = GlobalCMDS()


class Tags(commands.Cog):
    
    def __init__(self, client):
        self.client = client

    async def tag_help(self, ctx) -> discord.Message:
        return

    @commands.group(aliases=['tags'])
    async def tag(self, ctx, *, arg: str = None):
        await gcmds.invkDelete(ctx)
        if not ctx.invoked_subcommand:
            return await self.tag_help(ctx)

    @tag.command()
    async def list(self, ctx):
        return

    @tag.command(aliases=['make'])
    async def create(self, ctx):
        return

    @tag.command()
    async def edit(self, ctx):
        return

    @tag.command(aliaes=['remove'])
    async def delete(self, ctx):
        return


def setup(client):
    client.add_cog(Tags(client))