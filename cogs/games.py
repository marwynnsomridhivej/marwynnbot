import json

import discord
import typing
from discord.ext import commands
from globalcommands import GlobalCMDS as gcmds


class Games(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "games" has been loaded')

    @commands.command(aliases=['bal'])
    async def balance(self, ctx, addArgs: typing.Optional[str] = None, toMember: typing.Optional[discord.Member] = None):
        await ctx.message.delete()

        init = {'Balance': {}}
        gcmds.json_load(gcmds, 'balance.json', init)
        with open('balance.json', 'r') as f:
            file = json.load(f)
            try:
                file['Balance'][str(ctx.author.id)]
            except KeyError:
                file['Balance'][str(ctx.author.id)] = 1000
                balance = 1000
                f.close()
            else:
                balance = file['Balance'][str(ctx.author.id)]
                f.close()
        with open('balance.json', 'w') as f:
            json.dump(file, f, indent=4)
            f.close()
        if balance != 1:
            spelling = "credits"
        elif balance == 1:
            spelling = 'credit'
        if balance > 0:
            color = discord.Color.blue()
        else:
            color = discord.Color.dark_red()

        balanceEmbed = discord.Embed(title="Your Current Balance",
                                     description=f"{ctx.author.mention}, your current balance is: ```{balance} {spelling}```",
                                     color=color)
        balanceEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/734962101432615006/738390147514499163"
                                       "/chips.png")
        await ctx.channel.send(embed=balanceEmbed, delete_after=60)
        gcmds.incrCounter(gcmds, ctx, 'balance')

    @commands.command(aliases=['gamestats', 'stats'])
    async def gameStats(self, ctx, gameName=None):
        await ctx.message.delete()
        with open('gamestats.json', 'r') as f:
            file = json.load(f)
            if gameName is not None:
                try:
                    stats = file[str(gameName)][str(ctx.author.id)]
                    statsEmbed = discord.Embed(title=f"Stats for {str(gameName).capitalize()}",
                                               color=discord.Color.blue())
                except KeyError:
                    errorEmbed = discord.Embed(title="No Stats Available",
                                               description=f"{ctx.author.mention}, you have no stats for this game",
                                               color=discord.Color.dark_red())
                    await ctx.channel.send(embed=errorEmbed, delete_after=5)
                else:
                    for item in stats:
                        value = file[str(gameName)][str(ctx.author.id)][item]
                        if value == 1:
                            spell = "time"
                        else:
                            spell = "times"
                        statsEmbed.add_field(name=str(item).capitalize(),
                                             value=f"**{value}** {spell}",
                                             inline=False)
                    await ctx.channel.send(embed=statsEmbed)
                    gcmds.incrCounter(gcmds, ctx, 'gameStats')
            else:
                statsEmbed = discord.Embed(title=f"Stats for All Games",
                                           color=discord.Color.blue())
                for game in file:
                    try:
                        user_data = file[str(game)][str(ctx.author.id)]
                    except KeyError:
                        statsEmbed.add_field(name=game,
                                             value="No Data Available")
                    else:
                        value = ""
                        for item in user_data:
                            if file[str(game)][str(ctx.author.id)][str(item)] == 1:
                                spell = "time"
                            else:
                                spell = "times"
                            value += f"**{str(item).capitalize()}:** `{str(file[str(game)][str(ctx.author.id)][str(item)])}` {spell}\n"
                        statsEmbed.add_field(name=game,
                                             value=value)
                await ctx.channel.send(embed=statsEmbed)
                gcmds.incrCounter(gcmds, ctx, 'gameStats')


def setup(client):
    client.add_cog(Games(client))
