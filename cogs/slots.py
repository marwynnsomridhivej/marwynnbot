import asyncio
import discord
from discord.ext import commands
import numpy.random as np
import json
from utils import globalcommands

gcmds = globalcommands.GlobalCMDS()
emojis = [":apple:", ":green_apple:", ":pineapple:", ":cherries:", ":grapes:", ":strawberry:", ":lemon:", ":pear:",
          ":moneybag:", ":gem:", ":trophy:", ":violin:", ":musical_keyboard:", ":dragon:", ":free:", ":pirate_flag:"]
weights = [0.09375, 0.09375, 0.09375, 0.09375, 0.09375, 0.09375, 0.09375, 0.09375,
           0.015, 0.005, 0.03, 0.025, 0.025, 0.05, 0.05, 0.05]
fruits = [":apple:", ":green_apple:", ":pineapple:", ":cherries:", ":grapes:", ":strawberry:", ":lemon:", ":pear:"]
music = [":violin:", ":musical_keyboard:"]

global_jackpot = False


def rewards(slot_selection, bet):

    if ":pirate_flag:" in slot_selection:
        return 0

    if slot_selection[0] == ":free:" and slot_selection[1] == ":free:" and slot_selection[2] == ":free:":
        if bet * 3 > 300:
            return 300
        else:
            return bet * 3

    amounts = {}

    for emoji in slot_selection:
        try:
            amounts[str(emoji)] += 1
        except KeyError:
            amounts[str(emoji)] = 1

    index = 0

    try:
        while amounts[":free:"] != 0:
            if slot_selection[index] == ":free:":
                index += 1
                continue
            else:
                amounts[str(slot_selection[index])] += amounts[":free:"]
                amounts[":free:"] = 0
                break
    except KeyError:
        pass

    jackpot = False

    try:
        emoji_list = (list(amounts.keys()))
        occurences = (list(amounts.keys())[list(amounts.values()).index(3)])
        jackpot = True
    except ValueError:
        fruit_valid = True
        music_valid = True
        for emoji in emoji_list:
            if emoji in fruits or emoji == ":free:":
                pass
            else:
                fruit_valid = False
                break
        for emoji in emoji_list or emoji == ":free:":
            if emoji in music:
                pass
            else:
                music_valid = False
                break

        if fruit_valid or music_valid:
            if len(emoji_list) == 3:
                return bet
            if len(emoji_list) == 2:
                if bet * 2 > 200:
                    return 200
                else:
                    return bet * 2

    if jackpot:
        global_jackpot = True
        if occurences == ":moneybag:":
            if bet * 100 > 100000:
                return bet * 100
            else:
                return 100000
        elif occurences == ":gem:":
            if bet * 1000 < 1000000:
                return 10000000
            else:
                return bet * 1000
        elif occurences == ":trophy:":
            if bet * 10 < 10000:
                return 10000
            else:
                return bet * 10
        elif occurences in fruits:
            if bet * 5 < 500:
                return bet * 5
            else:
                return 500
        elif occurences in music:
            if bet * 10 < 5000:
                return 5000
            else:
                return bet * 10
        else:
            return bet * 2

    else:
        return 0


def win(ctx, reward, bot: commands.AutoShardedBot):
    load = False
    success = False
    op = (f"UPDATE balance SET amount = amount + {reward} WHERE user_id = {ctx.author.id}")
    bot.loop.create_task(gcmds.balance_db(op))
    init = {'Slots': {}}
    gcmds.json_load('db/gamestats.json', init)
    with open('db/gamestats.json', 'r') as f:
        file = json.load(f)
        while not load:
            try:
                file['Slots'][str(ctx.author.id)]['win']
            except KeyError:
                if not success:
                    try:
                        try:
                            file['Slots']
                        except KeyError:
                            file['Slots'] = {}
                        file['Slots'][str(ctx.author.id)]
                    except KeyError:
                        file['Slots'][str(ctx.author.id)] = {}
                        success = True
                file['Slots'][str(ctx.author.id)]['win'] = 0
            else:
                file['Slots'][str(ctx.author.id)]['win'] += 1
                load = True
        with open('db/gamestats.json', 'w') as f:
            json.dump(file, f, indent=4)
    gcmds.ratio(ctx.author, 'db/gamestats.json', 'Slots')


def lose(ctx, reward, bot: commands.AutoShardedBot):
    load = False
    success = False
    op = (f"UPDATE balance SET amount = amount - {reward} WHERE user_id = {ctx.author.id}")
    bot.loop.create_task(gcmds.balance_db(op))
    init = {'Slots': {}}
    gcmds.json_load('db/gamestats.json', init)
    with open('db/gamestats.json', 'r') as f:
        file = json.load(f)
        while not load:
            try:
                file['Slots'][str(ctx.author.id)]['lose']
            except KeyError:
                if not success:
                    try:
                        try:
                            file['Slots']
                        except KeyError:
                            file['Slots'] = {}
                        file['Slots'][str(ctx.author.id)]
                    except KeyError:
                        file['Slots'][str(ctx.author.id)] = {}
                        success = True
                file['Slots'][str(ctx.author.id)]['lose'] = 0
            else:
                file['Slots'][str(ctx.author.id)]['lose'] += 1
                load = True
        with open('db/gamestats.json', 'w') as f:
            json.dump(file, f, indent=4)
    gcmds.ratio(ctx.author, 'db/gamestats.json', 'Slots')


def jackpot(ctx, reward, bot: commands.AutoShardedBot):
    load = False
    success = False
    op = (f"UPDATE balance SET amount = amount + {reward} WHERE user_id = {ctx.author.id}")
    bot.loop.create_task(gcmds.balance_db(op))
    init = {'Slots': {}}
    gcmds.json_load('db/gamestats.json', init)
    with open('db/gamestats.json', 'r') as f:
        file = json.load(f)
        while not load:
            try:
                file['Slots'][str(ctx.author.id)]['jackpot'] += 1
                success = False
                load = True
            except KeyError:
                if not success:
                    try:
                        try:
                            file['Slots']
                        except KeyError:
                            file['Slots'] = {}
                            file['Slots'][str(ctx.author.id)]['jackpot'] = 0
                    except KeyError:
                        file['Slots'][str(ctx.author.id)] = {}
                        success = True
        with open('db/gamestats.json', 'w') as f:
            json.dump(file, f, indent=4)
    gcmds.ratio(ctx.author, 'db/gamestats.json', 'Slots')


class Slots(commands.Cog):

    def __init__(self, bot):
        global gcmds
        self.bot = bot
        gcmds = globalcommands.GlobalCMDS(self.bot)

    @commands.command(aliases=['slot'])
    async def slots(self, ctx, betAmount=None):
        

        if betAmount is None:
            betAmount = 1
        try:
            betAmount = int(betAmount)
        except (TypeError, ValueError):
            betAmount = ""

        if isinstance(betAmount, str):
            rates = discord.Embed(title="Slots Payout",
                                  description=f"The following are instances where the player can win when playing slots:",
                                  color=discord.Color.blue())
            rates.add_field(name="Matching 3 of the Same Icons",
                            value="Matching 3 of the same icons will yield the `jackpot` reward as follows (latter "
                                  "value applies if former is less than latter)"
                                  "\nFruit Jackpot: `5x bet` or `500 credits`"
                                  "\nMusic Jackpot: `10x bet` or `5000 credits`"
                                  "\nTrophy Jackpot: `10x bet` or `10000 credits`"
                                  "\nMoneybag Jackpot: `100x bet` or `100000 credits`"
                                  "\nDiamond Jackpot: `1000x bet` or `1000000 credits`",
                            inline=False)
            rates.add_field(name="Matching 3 Icons from the Same Category",
                            value="Matching 3 icons from the fruits or music category may yield a reward, "
                                  "however, it will not reward higher than `200 credits`",
                            inline=False)
            rates.add_field(name="Wildcards",
                            value=":free: - can substitute any category\n"
                                  ":pirate_flag: - will immediately cause you to lose your bet",
                            inline=False)
            await ctx.channel.send(embed=rates)
            return

        balance = await gcmds.get_balance(ctx.author)
        if not balance:
            await gcmds.balance_db(f"INSERT INTO balance(user_id, amount) VALUES ({ctx.author.id}, 1000)")
            balance = 1000
            initEmbed = discord.Embed(title="Initialised Credit Balance",
                                        description=f"{ctx.author.mention}, you have been credited `1000` credits "
                                                    f"to start!\n\nCheck your current"
                                                    f" balance using `{await gcmds.prefix(ctx)}balance`",
                                        color=discord.Color.blue())
            initEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/734962101432615006"
                                        "/738390147514499163/chips.png")
            await ctx.channel.send(embed=initEmbed, delete_after=10)

        if balance < betAmount:
            insuf = discord.Embed(title="Insufficient Credit Balance",
                                  description=f"{ctx.author.mention}, you have `{balance}` credits"
                                              f"\nYour bet of `{betAmount}` credits exceeds your current balance",
                                  color=discord.Color.dark_red())
            await ctx.channel.send(embed=insuf, delete_after=10)
            return

        slot_selection = np.choice(a=emojis, size=3, replace=True, p=weights)

        reward = rewards(slot_selection, betAmount)

        if betAmount != 1:
            spell = "credits"
        else:
            spell = "credit"

        if reward == 0:
            description = f"{ctx.author.display_name}, you lost {betAmount} {spell}"
            lose(ctx, betAmount, self.bot)
        else:
            if reward != 1:
                spell = "credits"
            else:
                spell = "credit"
            if global_jackpot:
                description = f"Jackpot! {ctx.author.display_name}, you won {reward} {spell}!"
                jackpot(ctx, reward, self.bot)
            else:
                description = f"{ctx.author.display_name}, you won {reward} {spell}!"
                win(ctx, reward, self.bot)

        slot_string = "========\n|" + "|".join(slot_selection) + "|\n========"

        spinning = "<a:slotspin:742369382122127422>"

        spinning_string = "========\n|" + f"{spinning}|" * 3 + "\n========"

        slotEmbed = discord.Embed(title="Slots",
                                  description=f"{spinning_string}",
                                  color=discord.Color.blue())
        slotEmbed.set_author(name=f"{ctx.author.display_name} spun the slot machine", icon_url=ctx.author.avatar_url)
        slotEmbed.set_footer(text=f"You bet {betAmount} {spell}")
        message = await ctx.channel.send(embed=slotEmbed)

        await asyncio.sleep(5.0)

        slotEmbed = discord.Embed(title="Slots",
                                  description=f"{slot_string}",
                                  color=discord.Color.blue())
        slotEmbed.set_author(name=description, icon_url=ctx.author.avatar_url)
        slotEmbed.set_footer(text=f"You bet {betAmount} {spell}")
        await message.edit(embed=slotEmbed)

        if reward >= 1000:
            await message.pin()

        gcmds.incrCounter(ctx, "slots")


def setup(bot):
    bot.add_cog(Slots(bot))
