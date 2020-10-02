import discord
from discord.ext import commands
from utils import paginator, premium


class FakeData(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    async def send_fakedata_help(self, ctx):
        return


def setup(bot):
    bot.add_cog(FakeData(bot))
