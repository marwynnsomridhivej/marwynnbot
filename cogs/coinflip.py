import asyncio
import discord
import typing
from discord.ext import commands
import json
import numpy as np
from utils import globalcommands

gcmds = globalcommands.GlobalCMDS()


def win(ctx, betAmount):
    load = False
    success = False
    with open('db/balance.json', 'r') as f:
        file = json.load(f)
        file['Balance'][str(ctx.author.id)] += betAmount
        with open('db/balance.json', 'w') as k:
            json.dump(file, k, indent=4)
    init = {'Coinflip': {}}
    gcmds.json_load('db/gamestats.json', init)
    with open('db/gamestats.json', 'r') as f:
        file = json.load(f)
        while not load:
            try:
                file['Coinflip'][str(ctx.author.id)]['win'] += 1
                load = True
                success = False
            except KeyError:
                if not success:
                    try:
                        try:
                            file['Coinflip']
                        except KeyError:
                            file['Coinflip'] = {}
                        file['Coinflip'][str(ctx.author.id)]['win'] = 0
                    except KeyError:
                        file['Coinflip'][str(ctx.author.id)] = {}
                        success = True
        with open('db/gamestats.json', 'w') as f:
            json.dump(file, f, indent=4)
    gcmds.ratio(ctx.author, 'db/gamestats.json', 'Coinflip')


def lose(ctx, betAmount):
    load = False
    success = False
    with open('db/balance.json', 'r') as f:
        file = json.load(f)
        file['Balance'][str(ctx.author.id)] -= betAmount
        with open('db/balance.json', 'w') as k:
            json.dump(file, k, indent=4)
    init = {'Coinflip': {}}
    gcmds.json_load('db/gamestats.json', init)
    with open('db/gamestats.json', 'r') as f:
        file = json.load(f)
        while not load:
            try:
                file['Coinflip'][str(ctx.author.id)]['lose'] += 1
                load = True
                success = False
            except KeyError:
                if not success:
                    try:
                        try:
                            file['Coinflip']
                        except KeyError:
                            file['Coinflip'] = {}
                        file['Coinflip'][str(ctx.author.id)]['lose'] = 0
                    except KeyError:
                        file['Coinflip'][str(ctx.author.id)] = {}
                        success = True
        with open('db/gamestats.json', 'w') as f:
            json.dump(file, f, indent=4)
    gcmds.ratio(ctx.author, 'db/gamestats.json', 'Coinflip')


class Coinflip(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=['cf'])
    async def coinflip(self, ctx, betAmount: typing.Optional[int] = 1, side="heads"):

        init = {'Balance': {}}
        gcmds.json_load('db/balance.json', init)
        with open('db/balance.json', 'r') as f:
            file = json.load(f)
            try:
                file['Balance'][str(ctx.author.id)]
            except KeyError:
                file['Balance'][str(ctx.author.id)] = 1000
                balance = 1000
                initEmbed = discord.Embed(title="Initialised Credit Balance",
                                          description=f"{ctx.author.mention}, you have been credited `1000` credits "
                                                      f"to start!\n\nCheck your current"
                                                      f" balance using `{gcmds.prefix(ctx)}balance`",
                                          color=discord.Color.blue())
                initEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/734962101432615006"
                                            "/738390147514499163/chips.png")
                await ctx.channel.send(embed=initEmbed, delete_after=10)

            else:
                balance = file['Balance'][str(ctx.author.id)]

        with open('db/balance.json', 'w') as f:
            json.dump(file, f, indent=4)

        if balance < betAmount:
            insuf = discord.Embed(title="Insufficient Credit Balance",
                                  description=f"{ctx.author.mention}, you have `{balance}` credits"
                                              f"\nYour bet of `{betAmount}` credits exceeds your current balance",
                                  color=discord.Color.dark_red())
            await ctx.channel.send(embed=insuf, delete_after=10)
            return

        emoji = "<a:Coin_spin:742197823537414254>"
        staticemoji = "<:Coin_spin:742208039310065683>"

        sides = ["heads", "tails"]

        if side == "heads":
            weight = [0.45, 0.55]
        else:
            weight = [0.55, 0.45]

        picked_side = np.random.choice(a=sides, size=1, replace=True, p=weight)[0]

        title = f"{picked_side.capitalize()}!"
        description = staticemoji + f" `[{picked_side}]`"
        color = discord.Color.blue()

        if betAmount != 1:
            spell = "credits"
        else:
            spell = "credit"

        footer = f"{ctx.author.display_name} bet {betAmount} {spell} and selected {side}"

        if picked_side == side:
            author = f"{ctx.author.display_name}, you win {betAmount} {spell}"
            win(ctx, betAmount)
        else:
            author = f"{ctx.author.display_name}, you lose {betAmount} {spell}"
            lose(ctx, betAmount)

        loadingEmbed = discord.Embed(title="Coinflip",
                                     description=emoji,
                                     color=color)
        loadingEmbed.set_author(name=f"{ctx.author.display_name} flipped a coin", icon_url=ctx.author.avatar_url)
        loadingEmbed.set_footer(text=footer)
        message = await ctx.channel.send(embed=loadingEmbed)
        await asyncio.sleep(3.0)

        coinEmbed = discord.Embed(title=title,
                                  description=description,
                                  color=color)
        coinEmbed.set_author(name=author, icon_url=ctx.author.avatar_url)
        coinEmbed.set_footer(text=footer)

        try:
            await message.edit(embed=coinEmbed)
        except discord.NotFound:
            notFound = discord.Embed(title="Game Canceled",
                                     description="The original coinflip message was deleted",
                                     color=discord.Color.dark_red())
            await ctx.channel.send(embed=notFound, delete_after=10)
            with open('db/balance.json', 'r') as f:
                file = json.load(f)

                with open('db/gamestats.json', 'r') as g:
                    stats = json.load(g)

                    if picked_side == side:
                        file["Balance"][str(ctx.author.id)] -= betAmount
                        stats["Coinflip"][str(ctx.author.id)]["win"] -= 1
                    else:
                        file["Balance"][str(ctx.author.id)] += betAmount
                        stats["Coinflip"][str(ctx.author.id)]["lose"] -= 1

                with open('db/gamestats.json', 'w') as g:
                    json.dump(stats, g, indent=4)
            with open('db/balance.json', 'w') as f:
                json.dump(file, f, indent=4)

            gcmds.ratio(ctx.author, 'db/gamestats.json', 'Coinflip')
            return

        if betAmount > 1000 and picked_side == side:
            await message.pin()

        gcmds.incrCounter(ctx, 'coinflip')


def setup(client):
    client.add_cog(Coinflip(client))
