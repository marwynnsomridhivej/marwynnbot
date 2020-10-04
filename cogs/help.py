import random
from collections import namedtuple
from datetime import datetime

import discord
from discord.ext import commands
from utils import customerrors, globalcommands

gcmds = globalcommands.GlobalCMDS()
DEFAULT_THUMBNAIL = "https://www.jing.fm/clipimg/full/71-716621_transparent-clip-art-open-book-frame-line-art.png"
SUPPORT_SERVER_INVITE = "https://discord.gg/78XXt3Q"
CogCommands = namedtuple("CogCommands", ['cog_name', 'cog'])


class Help(commands.Cog):

    def __init__(self, bot):
        global gcmds
        self.bot = bot
        self.mb_cogs = [CogCommands(cog.title(), self.bot.get_cog(cog))
                        for cog in self.bot.cogs
                        if cog not in ['Blackjack', 'Coinflip', 'ConnectFour', 'Slots', 'UNO']]
        gcmds = globalcommands.GlobalCMDS(self.bot)

    async def dispatch(self, ctx, command: commands.Command):
        pfx = await gcmds.prefix(ctx)
        kwargs = command.__original_kwargs__
        embed = discord.Embed(title=command.name.title(), description=f"```{kwargs['desc']}```", color=discord.Color.blue())
        embed.add_field(name="Usage", value=f"```{pfx}{command.usage}```", inline=False)
        for attr in [key for key in kwargs.keys() if not key in ['name', 'desc', 'usage', 'invoke_without_command']]:
            if attr == 'uperms':
                name = "User Permissions"
                value = f"`{'` `'.join(kwargs[attr])}`"
            elif attr == 'bperms':
                name = "Bot Permissions"
                value = f"`{'` `'.join(kwargs[attr])}`"
            elif attr == 'aliases':
                name = attr.title()
                value = f"`{'` `'.join([alias for alias in command.aliases if alias != command.name.lower()])}`"
            elif attr == 'note':
                name = attr.title()
                value = f"*{kwargs[attr]}*"
            else:
                name = attr.title()
                value = kwargs[attr]
            embed.add_field(name=name, value=value, inline=False)
        embed.set_thumbnail(url=kwargs.get("thumb", DEFAULT_THUMBNAIL))
        return await ctx.channel.send(embed=embed)

    @commands.command(aliases=['h'],
                      desc="The help command for the help command",
                      usage="help (command)",
                      note="If `(command)` is specified, it will show the detailed"
                      " help for that command")
    async def help(self, ctx, *, name: str = None):
        if name:
            command = self.bot.get_command(name)
            if not command:
                raise customerrors.CommandNotFound(name)
            try:
                return await self.dispatch(ctx, self.bot.get_command(name))
            except KeyError:
                raise customerrors.CommandHelpDirectlyCalled(name)
        timestamp = f"Executed by {ctx.author.display_name} " + "at: {:%m/%d/%Y %H:%M:%S}".format(datetime.now())
        embed = discord.Embed(title="MarwynnBot Help Menu",
                              color=discord.Color.blue(),
                              url=SUPPORT_SERVER_INVITE,
                              description="These are all the commands I currently support! Type"
                              f"\n```{await gcmds.prefix(ctx)}help [command]```\n to get help on "
                              f"that specific command")
        embed.set_thumbnail(url=DEFAULT_THUMBNAIL)
        embed.set_author(name="MarwynnBot", icon_url=ctx.me.avatar_url)
        embed.set_footer(text=timestamp, icon_url=ctx.author.avatar_url)
        return await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
