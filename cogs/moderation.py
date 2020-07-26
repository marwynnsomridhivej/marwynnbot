import discord
import os
import random
import json
import typing
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions, BotMissingPermissions


class Moderation(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "moderation" has been loaded')

    def incrCounter(self, cmdName):
        with open('counters.json', 'r') as f:
            values = json.load(f)
            values[str(cmdName)] += 1
        with open('counters.json', 'w') as f:
            json.dump(values, f, indent=4)

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
        self.incrCounter('chatclean')

    @chatclean.error
    async def chatclean_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            clearError = discord.Embed(title="Insufficient User Permissions",
                                       description=f'{ctx.author.mention}, you need the \"Manage Messages\" '
                                                   f'permission to clear messages from chat.',
                                       color=discord.Color.dark_red())
            await ctx.channel.send(embed=clearError)

    @commands.command(aliases=['silence', 'stfu', 'shut', 'shush', 'shh', 'shhh', 'shhhh', 'quiet'])
    @commands.bot_has_permissions(administrator=True)
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, members: commands.Greedy[discord.Member], *, reason="Unspecified"):
        await ctx.message.delete()
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            role = await ctx.guild.create_role(name="Muted",
                                               reason="Use for mutes")
            for channel in ctx.guild.channels:
                await channel.set_permissions(role, send_messages=False)
        for member in members:
            if role in member.roles:
                mutedEmbed = discord.Embed(title=f"{member} Already Muted",
                                           description=f"{member} has already been muted",
                                           color=discord.Color.dark_red())
                await ctx.channel.send(embed=mutedEmbed)
            else:
                await member.add_roles(role)
                path = './muted'
                files = os.listdir(path)
                name = random.choice(files)
                d = f'{path}//{name}'
                with open(d, 'rb') as f:
                    picture = discord.File(f, d)
                    mutedEmbed = discord.Embed(title=f'Muted {member}️',
                                               description=f"**Reason:** {reason}",
                                               color=discord.Color.blue())
                    mutedEmbed.set_thumbnail(url=f"attachment://muted_{name}")
                    mutedEmbed.set_footer(text=f'{member} was muted by: {ctx.author}')
                await ctx.channel.send(file=picture, embed=mutedEmbed)
        self.incrCounter('mute')

    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            muteError = discord.Embed(title="Insufficient User Permissions",
                                      description=f"{ctx.author.mention}, you need the Manage Roles permission to use"
                                                  " this command",
                                      color=discord.Color.dark_red())
            await ctx.channel.send(embed=muteError)
        if isinstance(error, BotMissingPermissions):
            muteError = discord.Embed(title="Insufficient Bot Permissions",
                                      description="I need the Administrator permission to mute users",
                                      color=discord.Color.dark_red())
            await ctx.channel.send(embed=muteError)

    @commands.command(aliases=['unsilence', 'unstfu', 'unshut', 'unshush', 'unshh', 'unshhh', 'unshhhh', 'unquiet'])
    @commands.bot_has_permissions(administrator=True)
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, members: commands.Greedy[discord.Member], *, reason="Unspecified"):
        await ctx.message.delete()
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        for member in members:
            if not role:
                unmuteEmbed = discord.Embed(title="No Muted Role",
                                            description="There is no muted role on this server.",
                                            color=discord.Color.dark_red())
                await ctx.channel.send(embed=unmuteEmbed, delete_after=5)
            if not (role in member.roles):
                unmuteEmbed = discord.Embed(title=f"User {member} Not Muted",
                                            description="You cannot unmute an already unmuted user.",
                                            color=discord.Color.dark_red())
                await ctx.channel.send(embed=unmuteEmbed, delete_after=5)
            else:
                await member.remove_roles(role)
                unmuteEmbed = discord.Embed(title=f"Unmuted {member}",
                                            description=f"**Reason:** {reason}",
                                            color=discord.Color.blue())
                unmuteEmbed.set_footer(text=f'{member} was unmuted by: {ctx.author}')
                await ctx.channel.send(embed=unmuteEmbed)
                self.incrCounter('unmute')

    @unmute.error
    async def unmute_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            muteError = discord.Embed(title="Insufficient User Permissions",
                                      description=f"{ctx.author.mention}, you need the Manage Roles permission to use"
                                                  " this command",
                                      color=discord.Color.dark_red())
            await ctx.channel.send(embed=muteError)
        if isinstance(error, BotMissingPermissions):
            muteError = discord.Embed(title="Insufficient Bot Permissions",
                                      description="I need the Administrator permission to unmute users",
                                      color=discord.Color.dark_red())
            await ctx.channel.send(embed=muteError)

    @commands.command()
    @commands.bot_has_permissions(administrator=True)
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, members: commands.Greedy[discord.Member], *, reason='Unspecified'):
        await ctx.message.delete()
        for member in members:
            await member.kick(reason=reason)
            kickEmbed = discord.Embed(title="Kicked User",
                                      description=f'{member.mention} has been kicked from the server!',
                                      color=discord.Color.blue())
            kickEmbed.set_thumbnail(url=member.avatar_url)
            kickEmbed.add_field(name='Reason:',
                                value=reason,
                                inline=False)
            await ctx.channel.send(embed=kickEmbed)
            self.incrCounter('kick')

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
    async def ban(self, ctx, members: commands.Greedy[discord.Member], days: typing.Optional[int] = 0, *,
                  reason='Unspecified'):
        await ctx.message.delete()
        for member in members:
            await member.ban(delete_message_days=days, reason=reason)
            if days != 0:
                dMessage = f"{member.mention} has been banned from the server! \n\nDeleted {member.mention}'s " \
                           f"messages from the past {days} days "
            else:
                dMessage = f'{member.mention} has been banned from the server!'
            banEmbed = discord.Embed(title="Banned User",
                                     description=dMessage,
                                     color=discord.Color.blue())
            banEmbed.set_thumbnail(url=member.avatar_url)
            banEmbed.add_field(name='Reason:',
                               value=reason,
                               inline=False)
            await ctx.channel.send(embed=banEmbed)
            self.incrCounter('ban')

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
    async def unban(self, ctx, users: commands.Greedy[discord.User]):
        await ctx.message.delete()

        for user in users:
            try:
                user = await commands.converter.UserConverter().convert(ctx, user)

            except:
                error = discord.Embed(title='Error',
                                      description='User could not be found!',
                                      color=discord.Color.dark_red())
                await ctx.channel.send(embed=error, delete_after=5)

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
                self.incrCounter('unban')
            else:
                notBanned = discord.Embed(title="User Not Banned!",
                                          description='For now :)',
                                          color=discord.Color.blue())
                notBanned.set_thumbnail(url=user.avatar_url)
                notBanned.add_field(name='Moderator',
                                    value=ctx.author.mention,
                                    inline=False)
                await ctx.channel.send(embed=notBanned, delete_after=5)
                self.incrCounter('unban')

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

    @commands.command(aliases=['mod', 'mods', 'modsonline', 'mo'])
    async def modsOnline(self, ctx):
        await ctx.message.delete()
        modsList = []
        for member in ctx.guild.members:
            if member.status is not discord.Status.offline:
                if not member.bot:
                    for role in member.roles:
                        if "moderator" in role.name.casefold():
                            modsList += [member.mention]
        if modsList:
            title = "Moderators Online"
            description = ""
            color = discord.Color.blue()
            for mods in modsList:
                description = f"{description} {mods}"
        else:
            title = "No Moderators Online"
            description = "There are currently no users that are moderators on this server\n\n*No users have a role " \
                          "with the substring* `moderator` *(case insensitive) in it*"
            color = discord.Color.dark_red()

        modsEmbed = discord.Embed(title=title,
                                  description=description,
                                  color=color)
        await ctx.channel.send(embed=modsEmbed, delete_after=60)
        self.incrCounter('modsonline')


def setup(client):
    client.add_cog(Moderation(client))
