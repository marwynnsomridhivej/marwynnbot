import json
import logging
import math
import os
import random
import socket
import sys
import re
import discord
import asyncpg
import asyncio
from datetime import datetime
from discord.ext import commands, tasks
from dotenv import load_dotenv
from utils import customerrors, globalcommands


gcmds = globalcommands.GlobalCMDS()
DISABLED_COGS = ["Blackjack", 'Coinflip', 'Connectfour', 'Oldmaid', 'Slots', 'Uno',
                 'Reactions', 'Moderation', 'Music', 'Utility']
DISABLED_COMMANDS = []
token_rx = re.compile(r'[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}')
version = f"Running MarwynnBot {gcmds.version}"

if os.path.exists('discord.log'):
    os.remove('discord.log')

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


async def get_prefix(self: commands.AutoShardedBot, message):
    if not message.guild:
        extras = ('mb ', 'mB ', 'Mb ', 'MB ', 'm!', 'm! ')
    else:
        async with self.db.acquire() as con:
            prefix = await con.fetch(f"SELECT custom_prefix from PREFIX WHERE guild_id = {message.guild.id}")
        extras = (
            f'{prefix[0]}', 'mb ', 'mB ', 'Mb ', 'MB ',
            'm!')
    return commands.when_mentioned_or(*extras)(self, message)


async def run():
    credentials = {
        "user": os.getenv("PG_USER"),
        "password": os.getenv("PG_PASSWORD"),
        "database": os.getenv("PG_DATABASE"),
        "host": os.getenv("PG_HOST")
    }

    db = await asyncpg.create_pool(**credentials)
    await db.execute("CREATE TABLE IF NOT EXISTS prefix(guild_id bigint PRIMARY KEY, custom_prefix text)")
    await db.execute("CREATE TABLE IF NOT EXISTS global_counters(command text PRIMARY KEY, amount NUMERIC)")
    await db.execute("CREATE TABLE IF NOT EXISTS guild_counters(guild_id bigint PRIMARY KEY, command_amount jsonb)")

    description = "Marwynn's bot for Discord written in Python using the discord.py API wrapper"
    startup = discord.Activity(name="Starting Up...", type=discord.ActivityType.playing)
    bot = Bot(command_prefix=get_prefix, help_command=None, shard_count=1, description=description, db=db,
              fetch_offline_members=True, status=discord.Status.online, activity=startup)
    try:
        await bot.start(gcmds.env_check("TOKEN"))
    except KeyboardInterrupt:
        await db.close()
        await bot.close()


class Bot(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        global gcmds
        super().__init__(
            command_prefix=kwargs['command_prefix'],
            help_command=kwargs["help_command"],
            shard_count=kwargs['shard_count'],
            description=kwargs["description"],
            fetch_offline_members=kwargs['fetch_offline_members'],
            status=kwargs['status'],
            activity=kwargs['activity']
        )
        self.uptime = int(datetime.now().timestamp())
        self.db = kwargs.pop("db")
        gcmds = globalcommands.GlobalCMDS(bot=self)
        func_checks = (self.check_blacklist, self.disable_dm_exec)
        func_listen = (self.on_message, self.on_command_error, self.on_guild_join, self.on_guild_remove)
        for func in func_checks:
            self.add_check(func)
        for func in func_listen:
            self.event(func)
        cogs = [filename[:-3] for filename in os.listdir('./cogs') if filename.endswith(".py")]
        for cog in sorted(cogs):
            self.load_extension(f'cogs.{cog}')
            print(f"Cog \"{cog}\" has been loaded")
        self.loop.create_task(self.init_counters())
        self.loop.create_task(self.all_loaded())

    async def init_counters(self):
        await self.wait_until_ready()
        async with self.db.acquire() as con:
            values = "('" + "', 0), ('".join(command.name for command in self.commands) + "', 0)"
            await con.execute(f"INSERT INTO global_counters(command, amount) VALUES {values} ON CONFLICT DO NOTHING")
        return

    async def on_command_completion(self, ctx):
        async with self.db.acquire() as con:
            await con.execute(f"UPDATE global_counters SET amount = amount + 1 WHERE command = '{ctx.command.name}'")
            old_dict = json.loads((await con.fetch(f"SELECT command_amount FROM guild_counters WHERE guild_id = {ctx.guild.id}"))[0]['command_amount'])
            old_val = old_dict[ctx.command.name]
            new_dict = "{" + f'"{ctx.command.name}": {old_val + 1}' + "}"
            op = (f"UPDATE guild_counters SET command_amount = command_amount::jsonb - '{ctx.command.name}' || '{new_dict}'"
                  f" WHERE command_amount->>'{ctx.command.name}' = '{old_val}' and guild_id = {ctx.guild.id}")
            await con.execute(op)

    @tasks.loop(seconds=120)
    async def status(self):
        await self.wait_until_ready()
        at = await self.get_aliases()
        activity1 = discord.Activity(name="m!h for help!", type=discord.ActivityType.listening)
        activity2 = discord.Activity(name=f"{len(self.users)} users!", type=discord.ActivityType.watching)
        activity3 = discord.Activity(name=f"{len(self.guilds)} servers!", type=discord.ActivityType.watching)
        activity4 = discord.Activity(name=f"MarwynnBot {gcmds.version}", type=discord.ActivityType.playing)
        activity5 = discord.Activity(name=f"{len(self.commands)} commands {at} aliases",
                                     type=discord.ActivityType.listening)
        activityList = [activity1, activity2, activity3, activity4, activity5]
        activity = random.choice(activityList)
        await self.change_presence(status=discord.Status.online, activity=activity)

    async def on_message(self, message):
        tokens = token_rx.findall(message.content)
        if tokens and message.guild:
            await gcmds.smart_delete(message)
            if gcmds.env_check('GITHUB_TOKEN'):
                url = await gcmds.create_gist('\n'.join(tokens), description="Discord token detected, posted for "
                                              f"invalidation. Server: {message.guild.name}")
            embed = discord.Embed(title="Token Found",
                                  description=f"{message.author.mention}, a Discord token was found in your message. It has"
                                  f" been sent to {url} to be invalidated",
                                  color=discord.Color.dark_red())
            await message.channel.send(embed=embed)

        await self.process_commands(message)

    async def check_blacklist(self, ctx):
        if not ctx.guild:
            return True

        async with self.db.acquire() as con:
            blist = await con.fetch(f"SELECT type FROM blacklist WHERE id = {ctx.author.id} OR id = {ctx.guild.id}")
        if blist:
            for item in blist:
                if 'user' == item['type']:
                    blacklisted = discord.Embed(title="You Are Blacklisted",
                                                description=f"{ctx.author.mention}, you are blacklisted from using this bot. "
                                                            f"Please contact `MS Arranges#3060` if you believe this is a mistake",
                                                color=discord.Color.dark_red())
                    await ctx.channel.send(embed=blacklisted, delete_after=10)
                if 'guild' == item['type']:
                    blacklisted = discord.Embed(title="Guild is Blacklisted",
                                                description=f"{ctx.guild.name} is blacklisted from using this bot. "
                                                            f"Please contact `MS Arranges#3060` if you believe this is a mistake",
                                                color=discord.Color.dark_red())
                    await ctx.channel.send(embed=blacklisted, delete_after=10)
                    await ctx.guild.leave()
                    return False

        return False if blist else True

    async def disable_dm_exec(self, ctx):
        if not ctx.guild and (ctx.cog.qualified_name in DISABLED_COGS or ctx.command.name in DISABLED_COMMANDS):
            disabled = discord.Embed(title="Command Disabled in Non Server Channels",
                                     description=f"{ctx.author.mention}, `m!{ctx.invoked_with}` can only be accessed "
                                     f"in a server",
                                     color=discord.Color.dark_red())
            await ctx.channel.send(embed=disabled)
            return False
        else:
            return True

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            req_arg = discord.Embed(title="Missing Required Argument",
                                    description=f"{ctx.author.mention}, `[{error.param.name}]` is a required argument",
                                    color=discord.Color.dark_red())
            return await ctx.channel.send(embed=req_arg, delete_after=10)
        elif isinstance(error, discord.ext.commands.MissingPermissions):
            missing = discord.Embed(title="Insufficient User Permissions",
                                    description=f"{ctx.author.mention}, to execute this command, you need "
                                                f"`{'` `'.join(error.missing_perms).replace('_', ' ').title()}`",
                                    color=discord.Color.dark_red())
            return await ctx.channel.send(embed=missing, delete_after=10)
        elif isinstance(error, discord.ext.commands.BotMissingPermissions):
            missing = discord.Embed(title="Insufficient Bot Permissions",
                                    description=f"{ctx.author.mention}, to execute this command, I need "
                                                f"`{'` `'.join(error.missing_perms).replace('_', ' ').title()}`",
                                    color=discord.Color.dark_red())
            return await ctx.channel.send(embed=missing, delete_after=10)
        elif isinstance(error, commands.NotOwner):
            not_owner = discord.Embed(title="Insufficient User Permissions",
                                      description=f"{ctx.author.mention}, only the bot owner is authorised to use this "
                                      f"command",
                                      color=discord.Color.dark_red())
            return await ctx.channel.send(embed=not_owner, delete_after=10)
        elif isinstance(error, commands.CommandNotFound):
            notFound = discord.Embed(title="Command Not Found",
                                     description=f"{ctx.author.mention}, `{ctx.message.content}` "
                                     f"does not exist\n\nDo `{await gcmds.prefix(ctx)}help` for help",
                                     color=discord.Color.dark_red())
            return await ctx.channel.send(embed=notFound, delete_after=10)
        elif isinstance(error, commands.CommandOnCooldown):
            cooldown_time_truncated = truncate(error.retry_after, 3)
            if cooldown_time_truncated < 1:
                spell = "milliseconds"
                cooldown_time_truncated *= 1000
            else:
                spell = "seconds"
            cooldown = discord.Embed(title="Command on Cooldown",
                                     description=f"{ctx.author.mention}, this command is still on cooldown for {cooldown_time_truncated} {spell}",
                                     color=discord.Color.dark_red())
            await ctx.channel.send(embed=cooldown, delete_after=math.ceil(error.retry_after))
        elif isinstance(error, customerrors.TagNotFound):
            embed = discord.Embed(title="Tag Not Found",
                                  description=f"{ctx.author.mention}, the tag `{error.tag}` does not exist in this server. "
                                  f"You can create it by doing `{await gcmds.prefix(ctx)}tag create {error.tag}`",
                                  color=discord.Color.dark_red())
            return await ctx.channel.send(embed=embed, delete_after=15)
        elif isinstance(error, customerrors.TagAlreadyExists):
            embed = discord.Embed(title="Tag Already Exists",
                                  description=f"{ctx.author.mention}, the tag `{error.tag}` already exists in this server",
                                  color=discord.Color.dark_red())
            return await ctx.channel.send(embed=embed, delete_after=15)
        elif isinstance(error, customerrors.UserNoTags):
            embed = discord.Embed(title="No Tags",
                                  description=f"{ctx.author.mention}, you do not own any tags in this server. Create one by"
                                  f" doing `{await gcmds.prefix(ctx)}tag create [tag_name]`",
                                  color=discord.Color.dark_red())
            return await ctx.channel.send(embed=embed, delete_after=15)
        elif isinstance(error, customerrors.NoSimilarTags):
            embed = discord.Embed(title="No Results",
                                  description=f"{ctx.author.mention}, there were no results for any tag named `{error.query}`",
                                  color=discord.Color.dark_red())
            return await ctx.channel.send(embed=embed, delete_after=15)
        elif isinstance(error, commands.CheckFailure):
            pass
        else:
            raise error

    async def on_guild_join(self, guild):
        async with self.db.acquire() as con:
            # Checks blacklist table
            result = await con.fetch(f"SELECT id FROM blacklist WHERE id = {guild.id}")
            if result:
                await guild.leave()
            else:
                await con.execute(f"INSERT INTO prefix (guild_id, custom_prefix) VALUES ('{guild.id}', 'm!')")

            # Adds initial entry for guild in guild_counters table
            op = [f'"{command.name}": 0' for command in self.commands]
            op_string = "'{" + ", ".join(op) + "}'"
            await con.execute(f"INSERT INTO guild_counters(guild_id, command_amount) VALUES({guild.id}, {op_string}) ON CONFLICT DO NOTHING")

    async def on_guild_remove(self, guild):
        async with self.db.acquire() as con:
            await con.execute(f"DELETE FROM prefix WHERE guild_id = {guild.id}")
            await con.execute(f"DELETE FROM guild_counters WHERE guild_id = {guild.id}")

    async def all_loaded(self):
        await self.wait_until_ready()
        globalcommands.start_time = int(datetime.now().timestamp())
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        users = len(self.users)
        guilds = len(self.guilds)
        ct = len(self.commands)
        at = await self.get_aliases()
        print(f'Successfully logged in as {self.user}\nIP: {ip}\nHost: {str(hostname)}\nServing '
              f'{users} users across {guilds} servers\nCommands: {ct}\nAliases: {at}\n{version}')
        self.status.start()

    async def get_aliases(self):
        at = 0
        for command in self.commands:
            if command.aliases:
                for alias in command.aliases:
                    at += 1
        return at

    @staticmethod
    def truncate(number: float, decimal_places: int):
        stepper = 10.0 ** decimal_places
        return math.trunc(stepper * number) / stepper


loop = asyncio.get_event_loop()
loop.run_until_complete(run())