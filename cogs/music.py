import discord
import json
from discord.ext import commands
from discord.ext.commands import has_permissions, BotMissingPermissions


class Music(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "music" has been loaded')

    def incrCounter(self, cmdName):
        with open('counters.json', 'r') as f:
            values = json.load(f)
            values[str(cmdName)] += 1
        with open('counters.json', 'w') as f:
            json.dump(values, f, indent=4)

    @commands.command()
    async def join(self, ctx):
        await ctx.message.delete()
        self.incrCounter('join')
        channel = ctx.author.voice.channel
        await channel.connect()
        joinEmbed = discord.Embed(title='Join Success!',
                                  description=f'Successfully joined the voice channel `{channel}`',
                                  color=discord.Color.blue())
        await ctx.channel.send(embed=joinEmbed)
        self.incrCounter('join')

    @join.error
    async def join_error(self, ctx, error):
        if isinstance(error, BotMissingPermissions):
            joinError = discord.Embed(title='Error - Insufficient Permissions',
                                      description='I cannot join this voice channel.',
                                      color=discord.Color.dark_red())
            await ctx.channel.send(embed=joinError)
        else:
            with open('prefixes.json', 'r') as f:
                sp = json.load(f)
                serverPrefix = sp[str(ctx.guild.id)]
            joinError = discord.Embed(title='Error - User Not in a Voice Channel',
                                      description=f"{ctx.author.mention}, you're currently not in any voice channel! "
                                                  f"Join a voice channel and then do `{serverPrefix}join`!",
                                      color=discord.Color.dark_red())
            await ctx.channel.send(embed=joinError)

    @commands.command()
    async def leave(self, ctx):
        await ctx.message.delete()
        self.incrCounter('leave')
        channel = ctx.voice_client.channel
        await ctx.voice_client.disconnect()
        leaveEmbed = discord.Embed(title='Leave Success!',
                                   description=f'Successfully left the voice channel `{channel}`',
                                   color=discord.Color.blue())
        await ctx.channel.send(embed=leaveEmbed)
        self.incrCounter('leave')

    @leave.error
    async def leave_error(self, ctx, error):
        with open('prefixes.json', 'r') as f:
            sp = json.load(f)
            serverPrefix = sp[str(ctx.guild.id)]
        leaveError = discord.Embed(title="Error - Not in a Voice Channel",
                                   description=f"{ctx.author.mention}, I'm not currently connected to a voice channel.",
                                   color=discord.Color.dark_red())
        leaveError.add_field(name='Special Case: Connected Through Restart',
                             value=f"If it shows that I am connected to a voice channel, that means the owner "
                                   f"restarted the bot while it was still connected. Join the voice channel, "
                                   f"do `{serverPrefix}join`, then do `{serverPrefix}leave`.")
        await ctx.channel.send(embed=leaveError)


def setup(client):
    client.add_cog(Music(client))
