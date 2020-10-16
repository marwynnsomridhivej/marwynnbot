import json
import os
from datetime import datetime, timedelta
from io import BytesIO

import discord
from discord.ext import commands, tasks
from utils import EmbedPaginator, GlobalCMDS

gcmds = GlobalCMDS()
invite_url = "https://discord.com/oauth2/authorize?client_id=623317451811061763&scope=bot&permissions=2146958583"


class Utility(commands.Cog):

    def __init__(self, bot: commands.AutoShardedBot):
        global gcmds
        self.bot = bot
        gcmds = GlobalCMDS(bot=self.bot)
        self.bot.loop.create_task(self.init_requests())

    async def init_requests(self):
        await self.bot.wait_until_ready()
        async with self.bot.db.acquire() as con:
            await con.execute("CREATE TABLE IF NOT EXISTS requests(message_id bigint PRIMARY KEY, user_id bigint, type text)")

    async def add_entry(self, ctx, message_id: int, type: str):
        async with self.bot.db.acquire() as con:
            await con.execute(f"INSERT INTO requests(message_id, user_id, type) VALUES ({message_id}, {ctx.author.id}, '{type}')")

    async def get_entry(self, message_id: int):
        async with self.bot.db.acquire() as con:
            result = await con.fetch(f"SELECT * FROM requests WHERE message_id = {message_id}")
        return result if result else None

    async def remove_entry(self, message_id: int):
        async with self.bot.db.acquire() as con:
            await con.execute(f"DELETE FROM requests WHERE message_id = {message_id}")

    @commands.command(aliases=['counters', 'used', 'usedcount'],
                      desc="Displays the used counter for commands",
                      usage="counter (command) (mode)",
                      note="Valid arguments for `(mode)` are \"server\" and \"global\". "
                      "If `(command)` is unspecified, it will show the counters for all commands. "
                      "If `(mode)` is unspecified, it will show the count for only commands executed in this server.")
    async def counter(self, ctx, name=None, mode='server'):
        if name == "server" or name == "global":
            mode = name
            name = None
        if not name:
            async with self.bot.db.acquire() as con:
                if mode == 'server':
                    result = await con.fetch(f"SELECT * FROM guild_counters WHERE guild_id={ctx.guild.id} "
                                             "ORDER BY command ASC")
                    title = f"Counters for {ctx.guild.name}"
                    entries = [
                        f"***{item['command']}:*** *used {item['amount']} "
                        f"{'times' if item['amount'] != 1 else 'time'}*"
                        for item in result]
                else:
                    result = await con.fetch(f"SELECT * from global_counters ORDER BY command ASC")
                    title = "Global Counters"
                    entries = [
                        f"***{record['command'].lower()}:*** *used {record['amount'] if record['amount'] else '0'} "
                        f"{'times' if record['amount'] != 1 else 'time'}*"
                        for record in result]
            pag = EmbedPaginator(ctx, entries=entries, per_page=20, show_entry_count=True)
            pag.embed.title = title
            return await pag.paginate()
        else:
            command = self.bot.get_command(name)
            async with self.bot.db.acquire() as con:
                if mode == "global":
                    amount = await con.fetchval(f"SELECT amount from global_counters WHERE "
                                                f"command=$tag${command.name.lower()}$tag$")
                    title = f"Global Counter for {command.name.title()}"
                else:
                    amount = await con.fetchval(f"SELECT amount FROM guild_counters WHERE "
                                                f"command=$tag${command.name.lower()}$tag$")
                    title = f"Server Counter for {command.name.title()}"
            description = (f"***{command.name}:*** *used {amount if amount else '0'} "
                           f"{'times' if amount != 1 else 'time'}*")
            embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
            return await ctx.channel.send(embed=embed)

    @commands.command(desc="Displays MarwynnBot's invite link",
                      usage="invite")
    async def invite(self, ctx):
        embed = discord.Embed(title="MarwynnBot's Invite Link",
                              description=f"{ctx.author.mention}, thank you for using MarwynnBot! Here is MarwynnBot's"
                              f" invite link that you can share:\n\n {invite_url}",
                              color=discord.Color.blue(),
                              url=invite_url)
        await ctx.channel.send(embed=embed)

    @commands.group(invoke_without_command=True,
                    desc="Displays the help command for request",
                    usage="request")
    async def request(self, ctx):
        menu = discord.Embed(title="Request Options",
                             description=f"{ctx.author.mention}, do `{await gcmds.prefix(ctx)}request feature` "
                             f"to submit a feature request with a 60 second cooldown",
                             color=discord.Color.blue())
        await ctx.channel.send(embed=menu)

    @request.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def feature(self, ctx, *, feature_message: str = None):
        if not feature_message:
            menu = discord.Embed(title="Request Options",
                                 description=f"{ctx.author.mention}, do `{await gcmds.prefix(ctx)}request feature` "
                                             f"to submit a feature request",
                                 color=discord.Color.dark_red())
            return await ctx.channel.send(embed=menu)

        timestamp = f"Executed at: " + "{:%m/%d/%Y %H:%M:%S}".format(datetime.now())

        feature_embed = discord.Embed(title="Feature Request",
                                      description=feature_message,
                                      color=discord.Color.blue())
        feature_embed.set_footer(text=timestamp)
        owner_id = gcmds.env_check("OWNER_ID")
        if not owner_id:
            no_api = discord.Embed(title="Missing Owner ID",
                                   description="This command is disabled",
                                   color=discord.Color.dark_red())
            return await ctx.channel.send(embed=no_api)
        owner = self.bot.get_user(int(owner_id))
        message = await owner.send(embed=feature_embed)
        feature_embed.set_footer(text=f"{timestamp}\nMessage ID: {message.id}")
        await message.edit(embed=feature_embed)
        if not feature_message.endswith(" --noreceipt"):
            feature_embed.set_author(name=f"Copy of your request", icon_url=ctx.author.avatar_url)
            await ctx.author.send(embed=feature_embed)
        self.add_entry(ctx, message.id, "feature")

    @request.command()
    @commands.is_owner()
    async def reply(self, ctx, message_id: int = None, *, reply_message: str = None):
        if not reply_message or not message_id:
            menu = discord.Embed(title="Request Options",
                                 description=f"{ctx.author.mention}, please write specify a valid message ID and a "
                                             f"reply message",
                                 color=discord.Color.dark_red())
            return await ctx.channel.send(embed=menu)
        user_id = self.get_entry(message_id)
        user = await self.bot.fetch_user(user_id)
        raw_reply = reply_message
        if reply_message == "spam":
            reply_message = f"{user.mention}, your request was either not related to a feature, or was categorised as " \
                            f"spam. Please review the content of your request carefully next time so that it isn't " \
                            f"marked as this. If you believe this was a mistake, please contact the bot owner: " \
                            f"{ctx.author.mention}"
        if reply_message == "no":
            reply_message = f"{user.mention}, unfortunately, your request could not be considered as of this time."
        thank = f"{user.mention}, thank you for submitting your feature request. Here is a message from" \
                f"{ctx.author.mention}, the bot owner:\n\n "
        timestamp = f"Replied at: " + "{:%m/%d/%Y %H:%M:%S}".format(datetime.now())
        reply_embed = discord.Embed(title=f"Reply From {ctx.author} To Your Request",
                                    description=thank + reply_message,
                                    color=discord.Color.blue())
        reply_embed.set_footer(text=timestamp)

        await user.send(embed=reply_embed)
        reply_embed.description = f"Message was successfully sent:\n\n{raw_reply}"
        await ctx.author.send(embed=reply_embed)
        self.remove_entry(message_id)

    @commands.command(aliases=['pfp'],
                      desc="Displays a member's profile picture",
                      usage="profilepic [@member]")
    async def profilepic(self, ctx, *, member: discord.Member):
        icon = member.avatar_url_as(static_format="png", size=4096)
        embed = discord.Embed(color=discord.Color.blue())
        embed.set_author(name=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        embed.set_image(url=icon)
        return await ctx.channel.send(embed=embed)

    @commands.command(aliases=['p', 'checkprefix', 'prefixes'],
                      desc="Displays the server's custom prefix",
                      usage="prefix")
    async def prefix(self, ctx):
        serverPrefix = await gcmds.prefix(ctx)
        prefixEmbed = discord.Embed(title='Prefixes',
                                    color=discord.Color.blue())
        prefixEmbed.add_field(name="Current Server Prefix",
                              value=f"The current server prefix is: `{serverPrefix}`",
                              inline=False)
        prefixEmbed.add_field(name="Global Prefixes",
                              value=f"{self.bot.user.mention} or `mb ` - *ignorecase*",
                              inline=False)
        await ctx.channel.send(embed=prefixEmbed)

    @commands.command(aliases=['sp', 'setprefix'],
                      desc="Sets the server's custom prefix",
                      usage="setprefix [prefix]",
                      uperms=["Manage Server"],
                      note="If `[prefix]` is \"reset\", then the custom prefix will be set to \"m!\"")
    @commands.has_permissions(manage_guild=True)
    async def setPrefix(self, ctx, prefix):
        async with self.db.acquire() as con:
            if prefix != 'reset':
                await con.execute(f"UPDATE guild SET custom_prefix=$tag${prefix}$tag$ WHERE guild_id={ctx.guild.id}")
                prefixEmbed = discord.Embed(title='Server Prefix Set',
                                            description=f"Server prefix is now set to `{prefix}` \n\n"
                                                        f"You will still be able to use {self.bot.user.mention} "
                                                        f"and `mb ` as prefixes",
                                            color=discord.Color.blue())
            else:
                await con.execute(f"UPDATE guild SET custom_prefix='m!' WHERE guild_id={ctx.guild.id}")
                prefixEmbed = discord.Embed(title='Server Prefix Set',
                                            description=f"Server prefix has been reset to `m!`",
                                            color=discord.Color.blue())
            await ctx.channel.send(embed=prefixEmbed)

    @ commands.command(aliases=['emotes', 'serveremotes', 'serveremote', 'serverEmote', 'emojis', 'emoji'],
                       desc="Queries emotes that belong to this server",
                       usage="serveremotes (query)",
                       note="If `(query)` is unspecified, it will display all the emojis that belong to this server")
    async def serverEmotes(self, ctx, *, search=None):
        description = [f"**{emoji.name}:** \\<:{emoji.name}:{emoji.id}>"
                       for emoji in ctx.guild.emojis] if not search else [f"**{emoji.name}:** \\<:{emoji.name}:{emoji.id}>"
                                                                          for emoji in ctx.guild.emojis
                                                                          if search in emoji.name]

        emojiEmbed = discord.Embed(title="Server Custom Emotes:",
                                   description="\n".join(sorted(description)),
                                   color=discord.Color.blue())
        await ctx.channel.send(embed=emojiEmbed)

    @commands.command(aliases=['info', 'si', 'serverinfo'],
                      desc="Displays the current server's information",
                      usage="serverinfo")
    async def serverInfo(self, ctx):
        description = ("**Basic Info**",
                       f"> Owner: {ctx.guild.owner.mention}",
                       f"> ID: `{ctx.guild.id}`",
                       f"> Created At: `{str(ctx.guild.created_at)[:-7]}`",
                       f"> Description: `{ctx.guild.description}`",
                       f"> Region: `{str(ctx.guild.region).replace('-', ' ')}`",
                       f"> AFK Timeout: `{int(ctx.guild.afk_timeout / 60)} "
                       f"{'minutes' if ctx.guild.afk_timeout / 60 > 1 else 'minute'}`",
                       f"> AFK Channel: `{ctx.guild.afk_channel}`",
                       "",
                       "**Stats:**",
                       f"> Members: `{len([member for member in ctx.guild.members if not member.bot])}`",
                       f"> Roles: `{len(ctx.guild.roles)}`",
                       f"> Emojis: `{len(ctx.guild.emojis)} / {ctx.guild.emoji_limit}`",
                       f"> Text Channels: `{len(ctx.guild.text_channels)}`",
                       f"> Voice Channels: `{len(ctx.guild.voice_channels)}`",
                       f"> Total Channels: `{len(ctx.guild.channels) - len(ctx.guild.categories)}`",
                       f"> Boosts: `{len(ctx.guild.premium_subscribers)}`",
                       f"> Filesize Limit: `{round(ctx.guild.filesize_limit / 1000000)} MB`",
                       f"> MarwynnBot Shard: `Shard {ctx.guild.shard_id}`",)
        embed = discord.Embed(title=ctx.guild.name, description="\n".join(description), color=discord.Color.blue())
        embed.set_image(url=ctx.guild.icon_url)
        return await ctx.channel.send(embed=embed)

    @commands.command(aliases=['tz'],
                      desc="Appends a timezone tag to yourself",
                      usage="timezone [timezone]",
                      uperms=["Change Nickname"],
                      bperms=["Manage Nicknames"],
                      note="`[timezone]` must be in GMT format. If `[timezone]` is \"reset\" or \"r\", "
                      "the tag will be removed")
    @commands.has_permissions(change_nickname=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def timezone(self, ctx, *, timezoneInput: str):
        name = timezoneInput.replace(" ", "")
        if name == 'reset' or name == 'r':
            await ctx.author.edit(nick=f"{ctx.author.name}")
            title = "Timezone Reset Success"
            description = f"{ctx.author.mention}'s timezone has been removed from their name"
            color = discord.Color.blue()
        elif name:
            if "GMT" in name:
                nick = f"{ctx.author.display_name} [{name}]"
                await ctx.author.edit(nick=nick)
                title = "Timezone Update Success"
                description = f"{ctx.author.mention}'s timezone has been added to their nickname"
                color = discord.Color.blue()

            else:
                title = "Invalid Timezone Format"
                description = "Please put your timezone in `GMT+` or `GMT-` format"
                color = discord.Color.dark_red()
        else:
            title = "Invalid Timezone Format"
            description = "Please put your timezone in `GMT+` or `GMT-` format"
            color = discord.Color.dark_red()
        gmt = discord.Embed(title=title,
                            description=description,
                            color=color)
        await ctx.channel.send(embed=gmt)

    @commands.command(desc="Displays MarwynnBot's uptime since the last restart",
                      usage="uptime")
    async def uptime(self, ctx):
        time_now = int(datetime.now().timestamp())
        td = timedelta(seconds=time_now - self.bot.uptime)
        embed = discord.Embed(title="Uptime",
                              description=f"MarwynnBot has been up and running for\n```\n{str(td)}\n```",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Utility(bot))
