import json
import os
import discord
import aiohttp
import asyncio
from dotenv import load_dotenv
from datetime import datetime
from discord.ext import commands

load_dotenv()
env_write = ["TOKEN=YOUR_BOT_TOKEN",
             "OWNER_ID=YOUR_ID_HERE",
             "PG_USER=POSTGRES_USERNAME",
             "PG_PASSWORD=POSTGRES_PASSWORD",
             "PG_DATABASE=POSTGRES_DATABASE",
             "PG_HOST=POSTGRES_HOST"
             "UPDATES_CHANNEL=CHANNEL_ID_HERE",
             "LAVALINK_IP=IP_ADDR",
             "LAVALINK_PORT=PORT",
             "LAVALINK_PASSWORD=DEFAULT_STRING",
             "CAT_API=API_KEY_FROM_CAT_API",
             "IMGUR_API=API_KEY_FROM_IMGUR",
             "REDDIT_CLIENT_ID=CLIENT_ID_FROM_REDDIT_API",
             "REDDIT_CLIENT_SECRET=CLIENT_SECRET_FROM_REDDIT_API",
             "USER_AGENT=YOUR_USER_AGENT",
             "TENOR_API=API_KEY_FROM_TENOR",
             "GITHUB_TOKEN=PERSONAL_ACCESS_TOKEN"]
default_env = ["YOUR_BOT_TOKEN",
               "YOUR_ID_HERE",
               "POSTGRES_USERNAME",
               "POSTGRES_PASSWORD",
               "POSTGRES_DATABASE",
               "POSTGRES_HOST"
               "CHANNEL_ID_HERE",
               "IP_ADDR",
               "PORT",
               "DEFAULT_STRING",
               "API_KEY_FROM_CAT_API",
               "API_KEY_FROM_IMGUR",
               "CLIENT_ID_FROM_REDDIT_API",
               "CLIENT_SECRET_FROM_REDDIT_API",
               "YOUR_USER_AGENT",
               "API_KEY_FROM_TENOR",
               "PERSONAL_ACCESS_TOKEN"]


class GlobalCMDS:

    def __init__(self, bot: commands.AutoShardedBot = None):
        self.version = "v0.2.0-alpha.1"
        self.bot = bot
        if bot:
            self.db = self.bot.db

    def init_env(self):
        if not os.path.exists('.env'):
            with open('./.env', 'w') as f:
                f.write("\n".join(env_write))
                return False
        return True

    def env_check(self, key: str):
        if not self.init_env() or os.getenv(key) in default_env:
            return False
        return os.getenv(key)

    def file_check(self, filenamepath: str, init):
        if not os.path.exists(filenamepath):
            with open(filenamepath, 'w') as f:
                for string in init:
                    f.write(string)

    async def smart_delete(self, message: discord.Message):
        if message.guild and message.guild.me.guild_permissions.manage_messages:
            try:
                await message.delete()
            except Exception:
                pass

    async def timeout(self, ctx: commands.Context, title: str, timeout: int) -> discord.Message:
        embed = discord.Embed(title=f"{title.title()} Timed Out",
                              description=f"{ctx.author.mention}, your {title} timed out after {timeout} seconds"
                              " due to inactivity",
                              color=discord.Color.dark_red())
        return await ctx.channel.send(embed=embed, delete_after=10)

    async def cancelled(self, ctx: commands.Context, title: str) -> discord.Message:
        embed = discord.Embed(title=f"{title.title()} Cancelled",
                              description=f"{ctx.author.mention}, your {title} was cancelled",
                              color=discord.Color.dark_red())
        return await ctx.channel.send(embed=embed, delete_after=10)

    async def panel_deleted(self, ctx: commands.Context, title: str) -> discord.Message:
        embed = discord.Embed(title=f"{title.title()} Cancelled",
                              description=f"{ctx.author.mention}, your {title} was cancelled because the panel was "
                              "deleted or could not be found",
                              color=discord.Color.dark_red())
        return await ctx.channel.send(embed=embed, delete_after=10)

    def json_load(self, filenamepath: str, init: dict):
        if not os.path.exists(filenamepath):
            with open(filenamepath, 'w') as f:
                json.dump(init, f, indent=4)

    async def prefix(self, ctx):
        if not ctx.guild:
            return "m!"

        async with self.db.acquire() as con:
            prefix = await con.fetch(f"SELECT custom_prefix FROM guild WHERE guild_id = {ctx.guild.id}")
            return (prefix[0][0])

    async def blacklist_db(self, execute):
        async with self.db.acquire() as con:
            result = await con.execute(execute)

    async def balance_db(self, execute: str, ret_val: bool = False):
        async with self.db.acquire() as con:
            if ret_val:
                val = await con.fetch(execute)
                return val[0]['amount']
            else:
                await con.execute(execute)

    async def get_balance(self, member: discord.Member):
        async with self.db.acquire() as con:
            bal = await con.fetch(f"SELECT amount FROM balance WHERE user_id = {member.id}")
            return bal[0]['amount'] if bal else None

    def ratio(self, user: discord.User, filenamepath: str, gameName: str):
        with open(filenamepath, 'r') as f:
            file = json.load(f)
            try:
                wins = file[str(gameName)][str(user.id)]['win']
            except KeyError:
                file[str(gameName)][str(user.id)]['ratio'] = 0
            else:
                try:
                    losses = file[str(gameName)][str(user.id)]['lose']
                except KeyError:
                    file[str(gameName)][str(user.id)]['ratio'] = 1
                else:
                    file[str(gameName)][str(user.id)]['ratio'] = round((wins / losses), 3)
        with open(filenamepath, 'w') as f:
            json.dump(file, f, indent=4)

    async def github_request(self, method, url, *, params=None, data=None, headers=None):
        hdrs = {
            'Accept': 'application/vnd.github.inertia-preview+json',
            'User-Agent': 'MarwynnBot Discord Token Invalidator',
            'Authorization': f"token {self.env_check('GITHUB_TOKEN')}"
        }

        req_url = f"https://api.github.com/{url}"

        if isinstance(headers, dict):
            hdrs.update(headers)

        async with aiohttp.ClientSession() as session:
            async with session.request(method, req_url, params=params, json=data, headers=hdrs) as response:
                ratelimit_remaining = response.headers.get('X-Ratelimit-Remaining')
                js = await response.json()
                if response.status == 429 or ratelimit_remaining == '0':
                    sleep_time = discord.utils._parse_ratelimit_header(response)
                    await asyncio.sleep(sleep_time)
                    return await self.github_request(method, url, params=params, data=data, headers=headers)
                elif 300 > response.status >= 200:
                    return js
                else:
                    raise GithubError(js['message'])

    async def create_gist(self, content, *, description):
        headers = {
            'Accept': 'application/vnd.github.v3+json',
        }

        filename = 'tokens.txt'
        data = {
            'public': True,
            'files': {
                filename: {
                    'content': content
                }
            },
            'description': description
        }

        response = await self.github_request('POST', 'gists', data=data, headers=headers)
        return response['html_url']


class GithubError(commands.CommandError):
    pass
