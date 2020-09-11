import json
import os
import discord
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError
from utils import globalcommands

gcmds = globalcommands.GlobalCMDS()


class Owner(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=['l', 'ld'])
    @commands.is_owner()
    async def load(self, ctx, extension):

        try:
            self.client.load_extension(f'cogs.{extension}')
        except CommandInvokeError:
            title = "Cog Load Fail"
            description = f"Failed to load cog {extension}, it is already loaded"
            color = discord.Color.blue()
        else:
            print(f'Cog "{extension}" has been loaded')
            title = "Cog Load Success"
            description = f"Successfully loaded cog {extension}"
            color = discord.Color.blue()
        loadEmbed = discord.Embed(title=title,
                                  description=description,
                                  color=color)
        await ctx.channel.send(embed=loadEmbed, delete_after=5)

    @commands.command(aliases=['ul', 'uld'])
    @commands.is_owner()
    async def unload(self, ctx, extension):

        try:
            self.client.unload_extension(f'cogs.{extension}')
        except CommandInvokeError:
            title = "Cog Unoad Fail"
            description = f"Failed to unload cog {extension}, it is already unloaded"
            color = discord.Color.blue()
        else:
            print(f'Cog "{extension}" has been unloaded')
            title = "Cog Unload Success"
            description = f"Successfully unloaded cog {extension}"
            color = discord.Color.blue()
        unloadEmbed = discord.Embed(title=title,
                                    description=description,
                                    color=color)
        await ctx.channel.send(embed=unloadEmbed, delete_after=5)

    @commands.command(aliases=['r', 'rl'])
    @commands.is_owner()
    async def reload(self, ctx, *, extension=None):

        if extension is None:
            print("==========================")
            for filenameReload in os.listdir('./cogs'):
                if filenameReload.endswith('.py'):
                    self.client.reload_extension(f'cogs.{filenameReload[:-3]}')
                    print(f'Cog "{filenameReload[:-3].capitalize()}" has been reloaded')
            reloadEmbed = discord.Embed(title="Reload Success",
                                        description="Successfully reloaded all cogs",
                                        color=discord.Color.blue())
            await ctx.channel.send(embed=reloadEmbed, delete_after=5)
            print("==========================")
        else:
            print("==========================")
            self.client.reload_extension(f'cogs.{extension}')
            print(f'Cog "{extension}" has been reloaded')
            reloadEmbed = discord.Embed(title="Reload Success",
                                        description=f"Successfully reloaded cog `{extension}`",
                                        color=discord.Color.blue())
            await ctx.channel.send(embed=reloadEmbed, delete_after=5)
            print("==========================")

    @commands.command(aliases=['taskkill'])
    @commands.is_owner()
    async def shutdown(self, ctx):

        shutdownEmbed = discord.Embed(title="Bot Shutdown Successful",
                                      description="Bot is logging out",
                                      color=discord.Color.blue())
        await ctx.channel.send(embed=shutdownEmbed)
        await self.client.close()

    @commands.group(aliases=['balanceadmin', 'baladmin', 'balop'])
    @commands.is_owner()
    async def balanceAdmin(self, ctx):
        init = {'Balance': {}}
        gcmds.json_load('db/balance.json', init)

    @balanceAdmin.command()
    async def set(self, ctx, user: discord.Member, amount):
        try:
            user.id
        except AttributeError:
            invalid = discord.Embed(title="Invalid User",
                                    description=f"{ctx.author.mention}, please specify a valid user",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid)
            return

        try:
            amount = int(amount)
        except (TypeError, ValueError):
            invalid = discord.Embed(title="Invalid Amount",
                                    description=f"{ctx.author.mention}, please specify a valid credit amount",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid)
            return

        with open('db/balance.json', 'r') as f:
            file = json.load(f)
            try:
                file['Balance'][str(user.id)]
            except KeyError:
                file['Balance'][str(user.id)] = amount
            else:
                file['Balance'][str(user.id)] = amount
            balance = amount
            with open('db/balance.json', 'w') as g:
                json.dump(file, g, indent=4)

        if balance != 1:
            spell = "credits"
        else:
            spell = "credit"

        setEmbed = discord.Embed(title="Balance Set",
                                 description=f"The balance for {user.mention} is now set to ```{balance} {spell}```",
                                 color=discord.Color.blue())
        await ctx.channel.send(embed=setEmbed, delete_after=60)

    @balanceAdmin.command()
    async def give(self, ctx, user: discord.Member, amount):
        try:
            user.id
        except AttributeError:
            invalid = discord.Embed(title="Invalid User",
                                    description=f"{ctx.author.mention}, please specify a valid user",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid)
            return

        try:
            amount = int(amount)
        except (TypeError, ValueError):
            invalid = discord.Embed(title="Invalid Amount",
                                    description=f"{ctx.author.mention}, please specify a valid credit amount",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid)
            return

        with open('db/balance.json', 'r') as f:
            file = json.load(f)
            try:
                file['Balance'][str(user.id)]
            except KeyError:
                file['Balance'][str(user.id)] += amount
            else:
                file['Balance'][str(user.id)] += amount
            balance = file['Balance'][str(user.id)]
            with open('db/balance.json', 'w') as g:
                json.dump(file, g, indent=4)

        if balance != 1:
            spell = "credits"
        else:
            spell = "credit"

        if amount != 1:
            spell_amt = "credits"
        else:
            spell_amt = "credit"

        giveEmbed = discord.Embed(title="Balance Set",
                                  description=f"{user.mention} has been given `{amount} {spell_amt}`. \nTheir balance "
                                              f"is now ```{balance} {spell}```",
                                  color=discord.Color.blue())
        await ctx.channel.send(embed=giveEmbed, delete_after=60)

    @balanceAdmin.command()
    async def remove(self, ctx, user: discord.Member, amount):
        try:
            user.id
        except AttributeError:
            invalid = discord.Embed(title="Invalid User",
                                    description=f"{ctx.author.mention}, please specify a valid user",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid)
            return

        try:
            amount = int(amount)
        except (TypeError, ValueError):
            invalid = discord.Embed(title="Invalid Amount",
                                    description=f"{ctx.author.mention}, please specify a valid credit amount",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid)
            return

        with open('db/balance.json', 'r') as f:
            file = json.load(f)
            try:
                file['Balance'][str(user.id)]
            except KeyError:
                file['Balance'][str(user.id)] -= amount
            else:
                file['Balance'][str(user.id)] -= amount
            balance = file['Balance'][str(user.id)]
            with open('db/balance.json', 'w') as g:
                json.dump(file, g, indent=4)

        if balance != 1:
            spell = "credits"
        else:
            spell = "credit"

        if amount != 1:
            spell_amt = "credits"
        else:
            spell_amt = "credit"

        removeEmbed = discord.Embed(title="Balance Set",
                                    description=f"{user.mention} has had `{amount} {spell_amt}` removed. \nTheir "
                                                f"balance is now ```{balance} {spell}```",
                                    color=discord.Color.blue())
        await ctx.channel.send(embed=removeEmbed, delete_after=60)

    @commands.group(aliases=['blist'])
    @commands.is_owner()
    async def blacklist(self, ctx):
        return
    @blacklist.command(aliases=['member'])
    async def user(self, ctx, operation, user: discord.Member = None):

        if user is None:
            invalid = discord.Embed(title="Invalid User",
                                    description=f"{ctx.author.mention}, please specify a valid user",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid, delete_after=10)
            return

        try:
            user_id = user.id
            user_mention = commands.AutoShardedBot.get_user(self.client, int(user_id))
        except (TypeError, AttributeError):
            invalid = discord.Embed(title="Invalid User",
                                    description=f"{ctx.author.mention}, please specify a valid user",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid, delete_after=10)
            return
        if operation == "add":
            with open('db/blacklist.json', 'r') as f:
                blacklist = json.load(f)
                try:
                    blacklist["Users"]
                except KeyError:
                    blacklist["Users"] = {}
                blacklist["Users"][str(user_id)] = 0
                with open('db/blacklist.json', 'w') as g:
                    json.dump(blacklist, g, indent=4)

            b_add = discord.Embed(title="Blacklist Entry Added",
                                  description=f"{ctx.author.mention}, {user_mention.mention} has been added to the "
                                              f"blacklist",
                                  color=discord.Color.blue())
            await ctx.channel.send(embed=b_add)
        elif operation == "remove":
            with open('db/blacklist.json', 'r') as f:
                blacklist = json.load(f)
                del blacklist["Users"][str(user_id)]
                with open('db/blacklist.json', 'w') as g:
                    json.dump(blacklist, g, indent=4)

            b_remove = discord.Embed(title="Blacklist Entry Removed",
                                     description=f"{ctx.author.mention}, {user_mention.mention} has been removed from "
                                                 f"the blacklist",
                                     color=discord.Color.blue())
            await ctx.channel.send(embed=b_remove)
        else:
            invalid = discord.Embed(title="Invalid Operation",
                                    description=f"{ctx.author.mention}, `{operation}` is an invalid operation",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid, delete_after=10)

    @blacklist.command(aliases=['server'])
    async def guild(self, ctx, operation, server_id=None):

        if server_id is None:
            invalid = discord.Embed(title="Invalid Guild ID",
                                    description=f"{ctx.author.mention}, please provide a valid guild ID",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid)
            return

        try:
            guild = commands.AutoShardedBot.get_guild(self.client, int(server_id))
            guild_id = guild.id
        except (TypeError, AttributeError):
            invalid = discord.Embed(title="Invalid Guild ID",
                                    description=f"{ctx.author.mention}, please specify a valid guild ID",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid)
            return
        if operation == "add":
            with open('db/blacklist.json', 'r') as f:
                blacklist = json.load(f)
                try:
                    blacklist["Guild"]
                except KeyError:
                    blacklist["Guild"] = {}
                blacklist["Guild"][str(guild_id)] = 0
                with open('db/blacklist.json', 'w') as g:
                    json.dump(blacklist, g, indent=4)

            b_add = discord.Embed(title="Blacklist Entry Added",
                                  description=f"{ctx.author.mention}, {guild.name} `ID:{guild_id}` has been added "
                                              f"to the blacklist",
                                  color=discord.Color.blue())
            await ctx.channel.send(embed=b_add)
        elif operation == "remove":
            with open('db/blacklist.json', 'r') as f:
                blacklist = json.load(f)
                del blacklist["Guild"][str(guild_id)]
                with open('db/blacklist.json', 'w') as g:
                    json.dump(blacklist, g, indent=4)

            b_remove = discord.Embed(title="Blacklist Entry Removed",
                                     description=f"{ctx.author.mention}, {guild.name} `ID:{guild_id}` has been "
                                                 f"removed from the blacklist",
                                     color=discord.Color.blue())
            await ctx.channel.send(embed=b_remove)
        else:
            invalid = discord.Embed(title="Invalid Operation",
                                    description=f"{ctx.author.mention}, `{operation}` is an invalid operation",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid)

    @commands.command(aliases=['fleave'])
    @commands.is_owner()
    async def forceleave(self, ctx, guild_id=None):
        if guild_id is None:
            guild_id = ctx.guild.id
        await self.client.get_guild(guild_id).leave()
        leaveEmbed = discord.Embed(title="Successfully Left Server",
                                   description=f"Left guild id: {id}",
                                   color=discord.Color.blue())
        await ctx.author.send(embed=leaveEmbed)

    @commands.command(aliases=['dm', 'privatemessage'])
    @commands.is_owner()
    async def privateMessage(self, ctx, userID: int = None, *, message):

        if userID is None:
            no_id = discord.Embed(title="No User ID Specified",
                                  description=f"{ctx.author.mention}, you did not specify a user ID",
                                  color=discord.Color.dark_red())
            await ctx.channel.send(embed=no_id, delete_after=10)

        try:
            user = commands.AutoShardedBot.get_user(self.client, id=userID)
        except commands.BadArgument:
            bad_id = discord.Embed(title="Invalid User ID Specified",
                                   description=f"{ctx.author.mention}, please specify a valid user ID",
                                   color=discord.Color.dark_red())
            await ctx.channel.send(embed=bad_id, delete_after=10)

        dmEmbed = discord.Embed(title="MarwynnBot",
                                description=message,
                                color=discord.Color.blue())
        await user.send(embed=dmEmbed)
        await ctx.author.send(embed=dmEmbed)


def setup(client):
    client.add_cog(Owner(client))
