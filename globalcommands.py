import json
import os
import discord
from discord.ext import commands

env_write = ["TOKEN=YOUR_BOT_TOKEN",
             "OWNER_ID=YOUR_ID_HERE",
             "UPDATES_CHANNEL=CHANNEL_ID_HERE",
             "LAVALINK_IP=IP_ADDR",
             "LAVALINK_PORT=PORT",
             "LAVALINK_PASSWORD=DEFAULT_STRING",
             "CAT_API=API_KEY_FROM_CAT_API",
             "IMGUR_API=API_KEY_FROM_IMGUR",
             "REDDIT_CLIENT_ID=CLIENT_ID_FROM_REDDIT_API",
             "REDDIT_CLIENT_SECRET=CLIENT_SECRET_FROM_REDDIT_API",
             "USER_AGENT=YOUR_USER_AGENT",
             "TENOR_API=API_KEY_FROM_TENOR"]
default_env = ["YOUR_BOT_TOKEN",
               "YOUR_ID_HERE",
               "CHANNEL_ID_HERE",
               "IP_ADDR",
               "PORT",
               "DEFAULT_STRING",
               "API_KEY_FROM_CAT_API",
               "API_KEY_FROM_IMGUR",
               "CLIENT_ID_FROM_REDDIT_API",
               "CLIENT_SECRET_FROM_REDDIT_API",
               "YOUR_USER_AGENT",
               "API_KEY_FROM_TENOR"]


class GlobalCMDS:

    def init_env(self):
        if not os.path.exists('.env'):
            with open('./.env', 'w') as f:
                f.write("\n".join(env_write))
                return False
        return True

    def env_check(self, key: str):
        if not self.init_env(self) or os.getenv(key) in default_env:
            return False
        return os.getenv(key)

    def file_check(self, filenamepath: str, init):
        if not os.path.exists(filenamepath):
            with open(filenamepath, 'w') as f:
                for string in init:
                    f.write(string)

    def incrCounter(self, ctx, cmdName: str):

        init = {'Server': {}, 'Global': {}}

        self.json_load(self, 'counters.json', init)
        with open('counters.json', 'r') as f:
            values = json.load(f)

            try:
                values['Global'][str(cmdName)]
            except KeyError:
                values['Global'][str(cmdName)] = 1
            else:
                values['Global'][str(cmdName)] += 1

            if not self.isGuild(self, ctx):
                pass
            else:
                try:
                    values['Server'][str(ctx.guild.id)]
                except KeyError:
                    values['Server'][str(ctx.guild.id)] = {}
                try:
                    values['Server'][str(ctx.guild.id)][str(cmdName)]
                except KeyError:
                    values['Server'][str(ctx.guild.id)][str(cmdName)] = 1
                else:
                    values['Server'][str(ctx.guild.id)][str(cmdName)] += 1

        with open('counters.json', 'w') as f:
            json.dump(values, f, indent=4)

    async def invkDelete(self, ctx):
        if isinstance(ctx.channel, discord.TextChannel) and ctx.guild.me.guild_permissions.manage_messages:
            await ctx.message.delete()

    async def msgDelete(self, message: discord.Message):
        if isinstance(message.channel, discord.TextChannel) and message.guild.me.guild_permissions.manage_messages:
            await message.delete()

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

    def isGuild(self, ctx):
        if ctx.guild:
            return True
        else:
            return False

    def json_load(self, filenamepath: str, init: dict):
        if not os.path.exists(filenamepath):
            with open(filenamepath, 'w') as f:
                json.dump(init, f, indent=4)

    def prefix(self, ctx):
        if not self.isGuild(self, ctx):
            return "m!"

        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)

        return prefixes[str(ctx.guild.id)]

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
