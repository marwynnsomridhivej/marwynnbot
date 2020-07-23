import json
import os
import discord
import logging
from discord.ext import commands
import sqlite3


# =================================================
# Removes Default Help Command (replaced with m!help below)
# =================================================

async def get_prefix(client, message):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)
        return commands.when_mentioned_or(f'{prefixes[str(message.guild.id)]}', 'mb ')(client, message)


client = commands.Bot(command_prefix=get_prefix, help_command=None)

# =================================================
# Logger
# =================================================

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# =================================================
# Bot Startup (Logs ready message to console, sets status, removes default help message)
# =================================================

@client.event
async def on_ready():
    print('Successfully logged in as {0.user}'.format(client))
    activity = discord.Game(name="Under Development", type=1)
    await client.change_presence(status=discord.Status.do_not_disturb, activity=activity)


@client.event
async def on_guild_join(guild):
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

# =================================================
# Loading Cogs
# =================================================

@client.command()
async def load(ctx, extension):
    await ctx.message.delete()
    client.load_extension(f'cogs.{extension}')
    print(f'Cog "{extension}" has been loaded')


@client.command()
async def unload(ctx, extension):
    await ctx.message.delete()
    client.unload_extension(f'cogs.{extension}')
    print(f'Cog "{extension}" has been unloaded')


for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')


@client.command()
async def reload(ctx, *, extension=None):
    await ctx.message.delete()
    if await client.is_owner(ctx.author):
        if extension is None:
            for filenameReload in os.listdir('./cogs'):
                if filenameReload.endswith('.py'):
                    client.reload_extension(f'cogs.{filenameReload[:-3]}')
                    print(f'Cog "{filenameReload}" has been reloaded')
            reloadEmbed = discord.Embed(title="Reload Success",
                                        description="Successfully reloaded all cogs",
                                        color=discord.Color.blue())
            await ctx.channel.send(embed=reloadEmbed, delete_after=5)
        else:
            client.reload_extension(f'cogs.{extension}')
            print(f'Cog "{extension}" has been reloaded')
            reloadEmbed = discord.Embed(title="Reload Success",
                                        description=f"Successfully reloaded cog `{extension}`",
                                        color=discord.Color.blue())
            await ctx.channel.send(embed=reloadEmbed, delete_after=5)
    else:
        reloadError = discord.Embed(title='Insufficient User Permissions',
                                    description='You need to be the bot owner to use this command',
                                    color=discord.Color.dark_red())
        await ctx.channel.send(embed=reloadError, delete_after=5)

# =================================================
# Client Initialisation and Logon
# =================================================

client.run('NjIzMzE3NDUxODExMDYxNzYz.XxT6OQ.uBal2OIHS9dWa7gP9rTGeGl_52U')
