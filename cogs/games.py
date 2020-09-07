import asyncio
import json
import discord
import typing
from discord.ext import commands
from globalcommands import GlobalCMDS

gcmds = GlobalCMDS()


class Games(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=['bal'])
    async def balance(self, ctx, member: commands.Greedy[discord.Member] = None):
        await gcmds.invkDelete(ctx)
        init = {'Balance': {}}
        gcmds.json_load('db/balance.json', init)
        with open('db/balance.json', 'r') as f:
            file = json.load(f)
            if member is None:
                try:
                    file['Balance'][str(ctx.author.id)]
                except KeyError:
                    file['Balance'][str(ctx.author.id)] = 1000
                    balance = 1000
                else:
                    balance = file['Balance'][str(ctx.author.id)]
            else:
                description = ""
                color = 0
                for user in member:
                    try:
                        file['Balance'][str(user.id)]
                    except KeyError:
                        file['Balance'][str(user.id)] = 1000
                        balance = 1000
                    else:
                        balance = file['Balance'][str(user.id)]
                        if balance != 1:
                            spelling = "credits"
                        elif balance == 1:
                            spelling = 'credit'
                        if balance == 0:
                            color += 1
                        description += f"{user.mention} has ```{balance} {spelling}```\n"
        with open('db/balance.json', 'w') as f:
            json.dump(file, f, indent=4)
            f.close()

        if member is None:
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
            balanceEmbed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/734962101432615006/738390147514499163"
                    "/chips.png")
            await ctx.channel.send(embed=balanceEmbed, delete_after=30)
            gcmds.incrCounter(ctx, 'balance')
        else:
            if color == len(member):
                color = discord.Color.dark_red()
            else:
                color = discord.Color.blue()
            balanceEmbed = discord.Embed(title="Balances",
                                         description=description,
                                         color=color)
            balanceEmbed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/734962101432615006/738390147514499163"
                    "/chips.png")
            await ctx.channel.send(embed=balanceEmbed, delete_after=30)
            gcmds.incrCounter(ctx, 'balance')

    @commands.command(aliases=['gamestats', 'stats'])
    async def gameStats(self, ctx, gameName: typing.Optional[str] = None,
                        member: commands.Greedy[discord.Member] = None):
        await gcmds.invkDelete(ctx)
        if gameName is not None:
            if "<@!" in gameName:
                userid = gameName[3:-1]
                if member is None:
                    member = [await commands.AutoShardedBot.fetch_user(self.client, user_id=int(userid))]
                else:
                    member.append(userid)
                gameName = None
            elif "<@" in gameName:
                userid = gameName[2:-1]
                if member is None:
                    member = [await commands.AutoShardedBot.fetch_user(self.client, user_id=int(userid))]
                else:
                    member.append(userid)
                gameName = None
        userlist = []
        if member is None:
            userlist.append(ctx.author)
        else:
            for user in member:
                userlist.append(user)

        for user in userlist:
            person_name = await commands.AutoShardedBot.fetch_user(self.client, user_id=user.id)
            with open('db/gamestats.json', 'r') as f:
                file = json.load(f)
                if gameName is not None:
                    try:
                        stats = file[str(gameName)][str(user.id)]
                        statsEmbed = discord.Embed(
                            title=f"{person_name.display_name}'s Stats for {str(gameName).capitalize()}",
                            color=discord.Color.blue())
                    except KeyError:
                        errorEmbed = discord.Embed(title="No Stats Available",
                                                   description=f"{ctx.author.mention}, you have no stats for this game",
                                                   color=discord.Color.dark_red())
                        await ctx.channel.send(embed=errorEmbed, delete_after=5)
                    else:
                        for item in stats:
                            value = file[str(gameName)][str(user.id)][item]
                            if item == "ratio":
                                continue
                            else:
                                if value == 1:
                                    spell = "time"
                                else:
                                    spell = "times"
                            statsEmbed.add_field(name=str(item).capitalize(),
                                                 value=f"**{value}** {spell}",
                                                 inline=False)
                        statsEmbed.add_field(name="Ratio",
                                             value=f"**{file[str(gameName)][str(user.id)]['ratio']}**",
                                             inline=False)

                        await ctx.channel.send(embed=statsEmbed)
                        gcmds.incrCounter(ctx, 'gameStats')
                else:
                    statsEmbed = discord.Embed(title=f"{person_name.display_name}'s Stats for All Games",
                                               color=discord.Color.blue())
                    for game in file:
                        try:
                            user_data = file[str(game)][str(user.id)]
                        except KeyError:
                            statsEmbed.add_field(name=f"{game}",
                                                 value="No Data Available")
                        else:
                            value = ""
                            for item in user_data:
                                if item == "ratio":
                                    continue
                                else:
                                    if file[str(game)][str(user.id)][str(item)] == 1:
                                        spell = "time"
                                    else:
                                        spell = "times"
                                value += f"**{str(item).capitalize()}:** `{str(file[str(game)][str(user.id)][str(item)])}` {spell}\n "
                            value += f"**Ratio**: `{str(file[str(game)][str(user.id)][str(item)])}`"
                            statsEmbed.add_field(name=game,
                                                 value=value)
                    await ctx.channel.send(embed=statsEmbed)
                    gcmds.incrCounter(ctx, 'gameStats')

    @commands.command()
    async def transfer(self, ctx, amount: int = None, member: commands.Greedy[discord.Member] = None):
        await gcmds.invkDelete(ctx)

        cmdExit = False
        if amount is None:
            errorEmbed = discord.Embed(title="No Amount Specified",
                                       description=f"{ctx.author.mention}, you must specify a credit amount to transfer",
                                       color=discord.Color.dark_red())
            await ctx.channel.send(embed=errorEmbed, delete_after=10)
            cmdExit = True
        if member is None:
            errorEmbed = discord.Embed(title="No User Specified",
                                       description=f"{ctx.author.mention}, you must specify user to transfer credit to",
                                       color=discord.Color.dark_red())
            await ctx.channel.send(embed=errorEmbed, delete_after=10)
            cmdExit = True
        if cmdExit:
            return

        memberString = ""
        userlist = [ctx.author.id]
        for members in member:
            memberString += f"{members.mention}, "
            userlist.append(members.id)

        init = {'Balance': {}}
        gcmds.json_load('db/balance.json', init)
        with open('db/balance.json', 'r') as f:
            file = json.load(f)
            for user in userlist:
                try:
                    file['Balance'][str(user)]
                except KeyError:
                    file['Balance'][str(user)] = 1000
                    f.close()
        with open('db/balance.json', 'w') as f:
            json.dump(file, f, indent=4)
            f.close()
        if (int(file['Balance'][str(ctx.author.id)])) < (amount * (int(len(userlist)) - 1)):
            if amount != 1:
                spell = "credits"
            else:
                spell = "credit"
            errorEmbed = discord.Embed(title="Insufficient Funds",
                                       description=f"{ctx.author.mention}, you cannot transfer more than you have\n"
                                                   f"*Attempted to transfer* "
                                                   f"```{(amount * (int(len(userlist)) - 1))} {spell}```, only have"
                                                   f"```{int(file['Balance'][str(ctx.author.id)])} {spell}```",
                                       color=discord.Color.dark_red())
            await ctx.channel.send(embed=errorEmbed, delete_after=10)
            return
        else:
            if amount != 1:
                spell = "credits"
            else:
                spell = "credit"
            confirmEmbed = discord.Embed(title="Credits Transfer",
                                         description=f"{ctx.author.mention}, are you sure you want to transfer\n"
                                                     f"```{amount} {spell}```\nto {memberString[:-2]}",
                                         color=discord.Color.blue())
            message = await ctx.channel.send(embed=confirmEmbed)
            await message.add_reaction('✅')
            await message.add_reaction('❌')

            def check(reaction, user):
                if ctx.author == user and str(reaction.emoji) == '✅':
                    return True
                elif ctx.author == user and str(reaction.emoji) == '❌':
                    return True
                else:
                    return False

            try:
                choice = await self.client.wait_for('reaction_add', timeout=60.0, check=check)
                for item in choice:
                    if str(item) == '✅':
                        choice = 'confirm'
                        break
                    if str(item) == '❌':
                        choice = 'cancel'
                        break
                if choice == 'confirm':
                    await message.clear_reactions()
                    description = "Successfully transferred:\n"
                    with open('db/balance.json', 'r') as f:
                        file = json.load(f)
                        for members in member:
                            file['Balance'][str(members.id)] += amount
                            file['Balance'][str(ctx.author.id)] -= amount
                            description += f"```{amount}``` ➡ {members.mention}\n"
                        with open('db/balance.json', 'w') as f:
                            json.dump(file, f, indent=4)
                    confirmEmbed = discord.Embed(title="Credits Transfer Successful",
                                                 description=description,
                                                 color=discord.Color.blue())
                    await message.edit(embed=confirmEmbed)
                    gcmds.incrCounter(ctx, 'transfer')
                    return
                if choice == 'cancel':
                    await message.clear_reactions()
                    confirmEmbed = discord.Embed(title="Credits Transfer Cancelled",
                                                 description=f"{ctx.author.mention} cancelled the transfer\n",
                                                 color=discord.Color.dark_red())
                    await message.edit(embed=confirmEmbed, delete_after=10)
                    return
            except asyncio.TimeoutError:
                await message.clear_reactions()
                canceled = discord.Embed(title="Confirmation Timeout",
                                         description=f"{ctx.author.mention}, transfer cancelled due to inactivity",
                                         color=discord.Color.dark_red())
                canceled.set_thumbnail(url='https://cdn.discordapp.com/attachments/734962101432615006'
                                           '/738083697726849034/nocap.jpg')
                canceled.set_footer(text=f"{ctx.author.name} did not provide a valid reaction within 60 seconds")
                await message.edit(embed=canceled, delete_after=10)
                return


def setup(client):
    client.add_cog(Games(client))
