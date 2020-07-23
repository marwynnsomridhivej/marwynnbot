import discord
import json
import os
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions, BotMissingPermissions


class Utility(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "utility" has been loaded')

    @commands.command(aliases=['p', 'checkprefix', 'prefixes'])
    async def prefix(self, ctx):
        await ctx.message.delete()
        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)

        serverPrefix = prefixes[str(ctx.guild.id)]
        prefixEmbed = discord.Embed(title='Prefixes',
                                    color=discord.Color.blue())
        prefixEmbed.add_field(name="Current Server Prefix",
                              value=f"The current server prefix is: `{serverPrefix}`",
                              inline=False)
        prefixEmbed.add_field(name="Global Prefixes",
                              value=f"{self.client.user.mention} or `mb `",
                              inline=False)
        await ctx.channel.send(embed=prefixEmbed)

    @commands.command(aliases=['sp', 'setprefix'])
    @commands.has_permissions(manage_guild=True)
    async def setPrefix(self, ctx, prefix):
        await ctx.message.delete()
        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)
            prefixes[str(ctx.guild.id)] = prefix
            with open('prefixes.json', 'w') as f:
                json.dump(prefixes, f, indent=4)
        with ctx.channel.typing():
            await ctx.message.delete()
            await ctx.send('Server prefix set to: ' + prefix)

    @setPrefix.error
    async def setPrefix_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            setPrefixError = discord.Embed(title="Error - Insufficient User Permissions",
                                           description=f"{ctx.author.mention}, you need the `Manage Server` "
                                                       f"permission to change the server prefix!",
                                           color=discord.Color.dark_red())
            await ctx.channel.send(embed=setPrefixError)


def setup(client):
    client.add_cog(Utility(client))
