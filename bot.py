import asyncio
import json
import os
import sys
import random
import traceback
import discord
import logging
from discord.ext import commands, tasks
from discord.ext.commands import CommandInvokeError
import yaml
from globalcommands import GlobalCMDS as gcmds

DISABLED_COGS = ["Blackjack", 'Coinflip', 'Oldmaid', 'Slots', 'Uno', 'Reactions', 'Moderation', 'Music', 'Utility']
DISABLED_COMMANDS = []


async def get_prefix(client, message):
    if isinstance(message.channel, discord.DMChannel) or isinstance(message.channel, discord.GroupChannel):
        extras = ('mb ', 'mB ', 'Mb ', 'MB ', 'm!', 'm! ')
        return commands.when_mentioned_or(*extras)(client, message)
    else:
        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)
            extras = (
                f'{prefixes[str(message.guild.id)]}', f'{prefixes[str(message.guild.id)]} ', 'mb ', 'mB ', 'Mb ', 'MB ',
                'm!')
            return commands.when_mentioned_or(*extras)(client, message)


client = commands.AutoShardedBot(command_prefix=get_prefix, help_command=None, shard_count=1)

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


@tasks.loop(seconds=120)
async def status():
    activity1 = discord.Activity(name=f"m!h for help!", type=discord.ActivityType.listening)
    activity2 = discord.Activity(name=f"{len(client.users)} users!", type=discord.ActivityType.watching)
    activity3 = discord.Activity(name=f"{len(client.guilds)} servers!", type=discord.ActivityType.watching)
    activity4 = discord.Activity(name=f"Under development [WIP]", type=discord.ActivityType.playing)
    activity5 = discord.Activity(name=f"MS Arranges#3060 for source code info", type=discord.ActivityType.watching)
    activity6 = discord.Activity(name=f"{len(client.commands)} commands", type=discord.ActivityType.listening)
    activityList = [activity1, activity2, activity3, activity4, activity5, activity6]
    activity = random.choice(activityList)
    await client.change_presence(status=discord.Status.online, activity=activity)


@client.event
async def on_ready():
    print('Successfully logged in as {0.user}'.format(client))
    await status.start()


@client.check
async def check_blacklist(ctx):
    if not os.path.exists('blacklist.json'):
        with open('blacklist.json', 'w') as f:
            json.dump({'Users': {}}, f, indent=4)
    with open('blacklist.json', 'r') as f:
        blacklist = json.load(f)
        try:
            blacklist["Users"]
            blacklist["Guilds"]
        except KeyError:
            blacklist["Users"] = {}
            blacklist["Guilds"] = {}
        try:
            if blacklist["Users"][str(ctx.author.id)]:
                blacklisted = discord.Embed(title="You Are Blacklisted",
                                            description=f"{ctx.author.mention}, you are blacklisted from using this bot. "
                                                        f"Please contact `MS Arranges#3060` if you believe this is a "
                                                        f"mistake",
                                            color=discord.Color.dark_red())
                await ctx.channel.send(embed=blacklisted, delete_after=10)
                return False
            elif blacklist["Guilds"][str(ctx.guild.id)]:
                blacklisted = discord.Embed(title="Guild is Blacklisted",
                                            description=f"{ctx.guild.name} is blacklisted from using this bot. "
                                                        f"Please contact `MS Arranges#3060` if you believe this is a "
                                                        f"mistake",
                                            color=discord.Color.dark_red())
                await ctx.channel.send(embed=blacklisted, delete_after=10)
                return False
            else:
                return True
        except KeyError:
            return True


@client.check
async def disable_dm_exec(ctx):
    if ctx.cog.qualified_name in DISABLED_COGS or ctx.command.name in DISABLED_COMMANDS:
        disabled = discord.Embed(title="Command Disabled in Non Server Channels",
                                 description=f"{ctx.author.mention}, `m!{ctx.invoked_with}` can only be accessed "
                                             f"in a server",
                                 color=discord.Color.dark_red())
        await ctx.channel.send(embed=disabled)
        return False
    else:
        return True


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CheckFailure):
        pass
    else:
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


@client.event
async def on_guild_join(guild):
    if not os.path.exists('blacklist.json'):
        with open('blacklist.json', 'w') as f:
            json.dump({'Guilds': {}}, f, indent=4)
    with open('blacklist.json', 'r') as f:
        blacklist = json.load(f)
        try:
            blacklist["Guilds"]
        except KeyError:
            blacklist["Guilds"] = {}
        if guild.id in blacklist["Guilds"]:
            to_leave = client.get_guild(guild.id)
            await to_leave.leave()
    if not os.path.exists('prefixes.json'):
        with open('prefixes.json', 'w') as f:
            f.write('{\n\n}')
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)
    prefixes[str(guild.id)] = 'm!'

    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)


@client.event
async def on_guild_remove(guild):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    prefixes.pop(str(guild.id))

    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)


@client.command(aliases=['l', 'ld'])
async def load(ctx, extension):
    await gcmds.invkDelete(gcmds, ctx)
    if await client.is_owner(ctx.author):
        try:
            client.load_extension(f'cogs.{extension}')
        except CommandInvokeError:
            title = "Cog Load Fail"
            description = f"Failed to load cog {extension}, it is already loaded"
            color = discord.Color.blue()
        else:
            print(f'Cog "{extension}" has been loaded')
            title = "Cog Load Success"
            description = f"Successfully loaded cog {extension}"
            color = discord.Color.blue()
    else:
        title = 'Insufficient User Permissions'
        description = 'You need to be the bot owner to use this command'
        color = discord.Color.dark_red()

    loadEmbed = discord.Embed(title=title,
                              description=description,
                              color=color)
    await ctx.channel.send(embed=loadEmbed, delete_after=5)


@client.command(aliases=['ul', 'uld'])
async def unload(ctx, extension):
    await gcmds.invkDelete(gcmds, ctx)
    if await client.is_owner(ctx.author):
        try:
            client.unload_extension(f'cogs.{extension}')
        except CommandInvokeError:
            title = "Cog Unoad Fail"
            description = f"Failed to unload cog {extension}, it is already unloaded"
            color = discord.Color.blue()
        else:
            print(f'Cog "{extension}" has been unloaded')
            title = "Cog Unload Success"
            description = f"Successfully unloaded cog {extension}"
            color = discord.Color.blue()
    else:
        title = 'Insufficient User Permissions'
        description = 'You need to be the bot owner to use this command'
        color = discord.Color.dark_red()

    unloadEmbed = discord.Embed(title=title,
                                description=description,
                                color=color)
    await ctx.channel.send(embed=unloadEmbed, delete_after=5)


for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')


@client.command(aliases=['r', 'rl'])
async def reload(ctx, *, extension=None):
    await gcmds.invkDelete(gcmds, ctx)
    if await client.is_owner(ctx.author):
        if extension is None:
            print("==========================")
            for filenameReload in os.listdir('./cogs'):
                if filenameReload.endswith('.py'):
                    client.reload_extension(f'cogs.{filenameReload[:-3]}')
                    print(f'Cog "{filenameReload}" has been reloaded')
            reloadEmbed = discord.Embed(title="Reload Success",
                                        description="Successfully reloaded all cogs",
                                        color=discord.Color.blue())
            await ctx.channel.send(embed=reloadEmbed, delete_after=5)
            print("==========================")
        else:
            print("==========================")
            client.reload_extension(f'cogs.{extension}')
            print(f'Cog "{extension}" has been reloaded')
            reloadEmbed = discord.Embed(title="Reload Success",
                                        description=f"Successfully reloaded cog `{extension}`",
                                        color=discord.Color.blue())
            await ctx.channel.send(embed=reloadEmbed, delete_after=5)
            print("==========================")
    else:
        reloadError = discord.Embed(title='Insufficient User Permissions',
                                    description='You need to be the bot owner to use this command',
                                    color=discord.Color.dark_red())
        await ctx.channel.send(embed=reloadError, delete_after=5)


@client.command(aliases=['taskkill'])
async def shutdown(ctx):
    await gcmds.invkDelete(gcmds, ctx)
    if await client.is_owner(ctx.author):
        title = "Bot Shutdown Successful"
        description = "Bot is logging out"
        color = discord.Color.blue()
    else:
        title = "Insufficient User Permissions"
        description = "You need to be the bot owner to use this command"
        color = discord.Color.dark_red()
    shutdownEmbed = discord.Embed(title=title,
                                  description=description,
                                  color=color)
    await ctx.channel.send(embed=shutdownEmbed)
    await status.stop()
    await client.logout()


with open('./token.yaml', 'r') as f:
    stream = yaml.full_load(f)
    token = stream[str('token')]
client.run(token)
