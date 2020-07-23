import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions, BotMissingPermissions


class Moderation(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "moderation" has been loaded')

    @commands.command(aliases=['clear', 'clean', 'chatclear', 'cleanchat', 'clearchat', 'purge'])
    @commands.has_permissions(manage_messages=True)
    async def chatclean(self, ctx, amount=1, member: discord.Member = None):
        await ctx.message.delete()

        def from_user(message):
            return member is None or message.author == member

        deleted = await ctx.channel.purge(limit=amount, check=from_user)
        if amount == 1:
            dMessage = "Cleared 1 message."
        else:
            dMessage = "Cleared {} messages.".format(len(deleted))

        clearEmbed = discord.Embed(title="Cleared Chat",
                                   description=dMessage,
                                   color=discord.Color.blue())
        clearEmbed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/734962101432615006/734962158290468944/eraser.png")
        await ctx.channel.send(embed=clearEmbed, delete_after=5)

    @chatclean.error
    async def chatclean_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            clearError = discord.Embed(title="Insufficient User Permissions",
                                       description=f'{ctx.author.mention}, you need the \"Manage Messages\" '
                                                   f'permission to clear messages from chat.',
                                       color=discord.Color.dark_red())
            await ctx.channel.send(embed=clearError)

    @commands.command()
    @commands.bot_has_permissions(administrator=True)
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason='Unspecified'):
        await ctx.message.delete()
        perms = ctx.author.permissions_in(ctx.channel)
        if perms.kick_members:
            with ctx.channel.typing():
                await member.kick(reason=reason)
                kickEmbed = discord.Embed(title="Kicked User",
                                          description=f'{member.mention} has been kicked from the server!',
                                          color=discord.Color.blue())
                kickEmbed.set_thumbnail(url=member.avatar_url)
                kickEmbed.add_field(name='Reason:', value=reason, inline=False)
                await ctx.channel.send(embed=kickEmbed)
        else:
            kickError = discord.Embed(title='Error',
                                      description=f'{ctx.author.mention}, you are missing the required perms to kick '
                                                  f'users! Make sure you have the kick members permission!',
                                      color=discord.Color.dark_red())
            await ctx.channel.send(embed=kickError)

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            kickError = discord.Embed(title='Insufficient User Permissions',
                                      description=f'{ctx.author.mention}, you are missing the required perms to kick '
                                                  f'users! Make sure you have the kick members permission!',
                                      color=discord.Color.dark_red())
            await ctx.channel.send(embed=kickError)
        if isinstance(error, BotMissingPermissions):
            kickError = discord.Embed(title='Insufficient Bot Permissions',
                                      description="I require the \"Administrator\" permission to kick users! Please "
                                                  "check my permissions.",
                                      color=discord.Color.dark_red())
            await ctx.channel.send(embed=kickError)

    @commands.command()
    @commands.bot_has_permissions(administrator=True)
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason='Unspecified'):
        await ctx.message.delete()
        with ctx.channel.typing():
            await member.ban(reason=reason)
            banEmbed = discord.Embed(title="Banned User",
                                     description=f'{member.mention} has been banned from the server!',
                                     color=discord.Color.blue())
            banEmbed.set_thumbnail(url=member.avatar_url)
            banEmbed.add_field(name='Reason:', value=reason, inline=False)
            await ctx.channel.send(embed=banEmbed)

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            banError = discord.Embed(title='Insufficient User Permissions',
                                     description=f'{ctx.author.mention}, you are missing the required perms to ban '
                                                 f'users! Make sure you have the ban members permission!',
                                     color=discord.Color.dark_red())
            await ctx.channel.send(embed=banError)
        if isinstance(error, BotMissingPermissions):
            banError = discord.Embed(title='Insufficient Bot Permissions',
                                     description="I require the \"Administrator\" permission to ban users! Please "
                                                 "check my permissions.",
                                     color=discord.Color.dark_red())
            await ctx.channel.send(embed=banError)

    @commands.command()
    @commands.bot_has_permissions(administrator=True)
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, user=None):

        try:
            user = await commands.converter.UserConverter().convert(ctx, user)
        except:
            error = discord.Embed(title='Error',
                                  description='User could not be found!',
                                  color=discord.Color.dark_red())
            await ctx.channel.send(embed=error)
            return

        bans = tuple(ban_entry.user for ban_entry in await ctx.guild.bans())
        if user in bans:
            unban = discord.Embed(title='Unbanned',
                                  color=discord.Color.blue())
            unban.set_thumbnail(url=user.avatar_url)
            unban.add_field(name='User:',
                            value=user.mention)
            unban.add_field(name='Moderator:',
                            value=ctx.author.mention)
            await ctx.guild.unban(user, reason="Moderator: " + str(ctx.author))
            await ctx.channel.send(embed=unban)
        else:
            notBanned = discord.Embed(title="User Not Banned!",
                                      description='For now :)',
                                      color=discord.Color.blue())
            notBanned.set_thumbnail(url=user.avatar_url)
            notBanned.add_field(name='Moderator',
                                value=ctx.author.mention,
                                inline=False)
            await ctx.channel.send(embed=notBanned)

    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            unbanError = discord.Embed(title='Insufficient User Permissions',
                                       description=f'{ctx.author.mention}, you are missing the required perms to '
                                                   f'unban users! Make sure you have the ban members permission!',
                                       color=discord.Color.dark_red())
            await ctx.channel.send(embed=unbanError)
        if isinstance(error, BotMissingPermissions):
            unbanError = discord.Embed(title='Insufficient Bot Permissions',
                                       description="I require the \"Administrator\" permission to unban users! Please "
                                                   "check my permissions.",
                                       color=discord.Color.dark_red())
            await ctx.channel.send(embed=unbanError)


def setup(client):
    client.add_cog(Moderation(client))
