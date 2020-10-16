import asyncio
import functools
from contextlib import suppress
from datetime import datetime

import discord
from discord.ext import commands, tasks
from utils import EmbedPaginator, GlobalCMDS, customerrors, premium

gcmds = GlobalCMDS()
_bot = None


def check_registered_amount(func):
    @functools.wraps(func)
    async def checker(*args, **kwargs):
        ctx = kwargs.get("ctx", None)
        channel = kwargs.get("channel", None)
        if not ctx or not channel:
            raise customerrors.ServerLinkException()
        async with _bot.db.acquire() as con:
            amount_registered = await con.fetch(f"SELECT * FROM serverlink WHERE guild_id={ctx.guild.id}")
        if len(amount_registered) + 1 > 1 and not await premium.check_guild_premium(ctx.guild):
            raise customerrors.ServerLinkChannelLimitExceeded(ctx.guild)
        return await func(*args, **kwargs)
    return checker


def check_channel_registered(func):
    @functools.wraps(func)
    async def checker(*args, **kwargs):
        channel = kwargs.get("channel", None)
        if not channel:
            raise customerrors.ServerLinkException()
        async with _bot.db.acquire() as con:
            channel_id = await con.fetchval(f"SELECT channel_id FROM serverlink WHERE channel_id={channel.id}")
        if not channel_id:
            raise customerrors.ServerLinkNotRegisteredChannel(channel)
        return await func(*args, **kwargs)
    return checker


def check_request_exists(func):
    @functools.wraps(func)
    async def checker(*args, **kwargs):
        ctx = kwargs.get("ctx", None)
        initiator_id = kwargs.get("other_channel_id", None)
        if not ctx or not initiator_id:
            raise customerrors.ServerLinkException()
        async with _bot.db.acquire() as con:
            request = await con.fetchval(f"SELECT request_time FROM serverlink_conn WHERE "
                                         f"(initiator_id={initiator_id} OR recipient_id={initiator_id}) AND "
                                         "pending=TRUE AND active=FALSE")
        if not request:
            raise customerrors.ServerLinkNoRequestFound(initiator_id)
        return await func(*args, **kwargs)
    return checker


def ensure_inactive(func):
    @functools.wraps(func)
    async def checker(*args, **kwargs):
        initiator_id = kwargs.get("initiator_id", None)
        recipient_id = kwargs.get("recipient_id", None)
        if not initiator_id or not recipient_id:
            raise customerrors.ServerLinkException()
        async with _bot.db.acquire() as con:
            init_active = await con.fetchval(f"SELECT active FROM serverlink WHERE channel_id={initiator_id}")
            recip_active = await con.fetchval(f"SELECT active FROM serverlink WHERE channel_id={recipient_id}")
        if init_active or recip_active:
            raise customerrors.ServerLinkChannelUnavailable()
        return await func(*args, **kwargs)
    return checker


class ServerLink(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        global gcmds, _bot
        self.bot = bot
        _bot = self.bot
        gcmds = GlobalCMDS(self.bot)
        self.bot.loop.create_task(self.init_serverlink())

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        async with self.bot.db.acquire() as con:
            recip_info = await con.fetch(f"SELECT recip_message_id, recip_channel_id FROM serverlink_temp "
                                         f"WHERE message_id={payload.message_id}")
        if not recip_info:
            return
        with suppress(Exception):
            recip_info = recip_info[0]
            orig_channel = self.bot.get_channel(payload.channel_id)
            orig_message = await orig_channel.fetch_message(payload.message_id)
            recip_channel = self.bot.get_channel(int(recip_info['recip_channel_id']))
            recip_message = await recip_channel.fetch_message(int(recip_info['recip_message_id']))
            await recip_message.edit(content=f"**{orig_message.author}:**\n{orig_message.content}",
                                     tts=orig_message.tts,
                                     embed=orig_message.embeds[0] if orig_message.embeds else None,
                                     allowed_mentions=discord.AllowedMentions.none())
        return

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        async with self.bot.db.acquire() as con:
            recip_info = await con.fetch(f"DELETE FROM serverlink_temp WHERE message_id={payload.message_id} "
                                         "RETURNING recip_message_id, recip_channel_id")
        if not recip_info:
            return
        with suppress(Exception):
            recip_info = recip_info[0]
            recip_channel = self.bot.get_channel(int(recip_info['recip_channel_id']))
            recip_message = await recip_channel.fetch_message(int(recip_info['recip_message_id']))
            await recip_message.delete()
        return

    async def init_serverlink(self):
        await self.bot.wait_until_ready()
        async with self.bot.db.acquire() as con:
            await con.execute("CREATE TABLE IF NOT EXISTS serverlink(guild_id bigint, channel_id bigint PRIMARY KEY, "
                              "active boolean DEFAULT FALSE, public boolean DEFAULT FALSE)")
            await con.execute("CREATE TABLE IF NOT EXISTS serverlink_conn(initiator_id bigint, recipient_id bigint, "
                              "pending boolean DEFAULT TRUE, active boolean DEFAULT FALSE, request_time NUMERIC, "
                              "start_time NUMERIC, end_time NUMERIC)")
            await con.execute("CREATE TABLE IF NOT EXISTS serverlink_temp(message_id bigint, "
                              "recip_message_id bigint, recip_channel_id bigint)")

    async def send_serverlink_help(self, ctx):
        pfx = f"{await gcmds.prefix(ctx)}serverlink"
        description = f"The base command is `{pfx}`. Here are all the valid subcommands for ServerLink"
        sabout = (f"**Usage:** `{pfx} about`",
                  "**Returns:** Relevant information about what the ServerLink function does and how "
                  "MarwynnBot respects your privacy while offering a robust interserver chat service")
        sregister = (f"**Usage:** `{pfx} register [#channel]`",
                     "**Returns:** An embed that confirms the channel was successfully registered",
                     "**Aliases:** `set` `enable`",
                     "**Note:** An error message will appear if you try to register an already "
                     "registered channel")
        sunregister = (f"**Usage:** `{pfx} unregister [#channel]`",
                       "**Returns:** An embed that confirms the channel was successfully unregistered",
                       "**Aliases:** `unset` `disable`",
                       "**Note:** An error message will appear if you try to unregister an already "
                       "unregistered channel")
        spublic = (f"**Usage:** `{pfx} public [#channel]`",
                   "**Returns:** A confirmation embed that once confirmed, will allow MarwynnBot to display "
                   "your server on its public ServerLink listings",
                   "**Aliases:** `pub`")
        sunpublic = (f"**Usage:** `{pfx} unpublic [#channel]`",
                     "**Returns:** An embed that confirms that the specified ServerLink channel was "
                     "removed from public listing",
                     "**Aliases:** `unpub` `private`",
                     "**Note:** `[#channel]` must be a registered, public ServerLink channel, otherwise "
                     "an error message will be sent instead")
        slistings = (f"**Usage:** `{pfx} listings`",
                     "**Returns:** A paginated embed that lists all public ServerLink channels",
                     "**Aliases:** `global`",
                     "**Note:** In order to appear on the listings, you must make your registered channel "
                     f"public. See the above two subcommands for reference")
        slist = (f"**Usage:** `{pfx} list`",
                 "**Returns:** An embed that lists all currently registered ServerLink channels",
                 "**Aliases:** `-ls` `show`",
                 "**Note:** An error message will appear if you do not have any registered channels")
        srequest = (f"**Usage:** `{pfx} request [server]`",
                    "**Returns:** An embed that confirms your request was successfully sent",
                    "**Aliases:** `req`",
                    "**Note:** `[server]` can be the name or ID of a server that has registered a public "
                    "ServerLink channel. If no servers are found matching these criteria, an error message "
                    "will be sent instead")
        saccept = (f"**Usage:** `{pfx} accept [ID]`",
                   "**Returns:** Initiates a ServerLink session between your server and the requester's server",
                   "**Aliases:** `allow`",
                   "**Note:** `[ID]` is provided in the request message. If the request is more than an hour old, "
                   "it is automatically invalidated")
        sdeny = (f"**Usage:** `{pfx} deny [ID]`",
                 "**Returns:** An embed that confirms you have denied the request",
                 "**Aliases:** `reject`",
                 "**Note:** `[ID]` is provided in the request message. If the request is more than an hour old, "
                 "it is automatically invalidated")
        nv = [("Register", sregister), ("Unregister", sunregister), ("Public", spublic), ("Unpublic", sunpublic),
              ("List", slist), ("Request", srequest), ("Accept", saccept), ("Deny", sdeny)]
        embed = discord.Embed(title="ServerLink Help", description=description, color=discord.Color.blue())
        for name, value in nv:
            embed.add_field(name=name, value="> " + "\n> ".join(value), inline=False)
        return await ctx.channel.send(embed=embed)

    async def send_serverlink_about(self, ctx):
        description = ("ServerLink is a unique feature of MarwynnBot that allows you to communicate to another server "
                       "while staying in the current server. It achieves this functionality while still respecting your "
                       "privacy. Here is an overview of how this feature works")
        register = ("> **You must register a specific channel as the channel that MarwynnBot will use for ServerLink**. "
                    "If you don't explicitly specify which channel to use, you will not be able to use any feature of "
                    "ServerLink. Registration of a specific channel constitutes as enabling ServerLink communications "
                    "for your server")
        consent = ("> **Registration does not imply consent!** MarwynnBot will never assume that just because you "
                   "Registered a channel, you are happy to communicate with any and every server with ServerLink enabled!"
                   "In order to communicate with other servers, you will need to send a comms request or accept an "
                   "incoming comms request to initiate the connection. If your request is denied, there will be a 15 "
                   "minute cooldown before you will be able to send a new request to that same server. You will also "
                   "be able to block connections from specific servers. Once blocked, you will no longer receive "
                   "requests from that server, and that server will not be made aware that they have been blocked")
        premium = ("> **There are also some nice premium perks.** Premium servers will not be subject to the cooldown "
                   "and will be able to initiate multiple connections in different channels. Your server will need "
                   "to have a MarwynnBot Premium Server subscription in order to obtain these perks")
        abuse = ("> **There are abuse prevention mechanisms in place!** Each server is subject to a global request "
                 "ratelimit of 5 requests per hour. This include any and all requests sent FROM the server. You are able "
                 "to accept as many requests as you would like.")
        nv = [("Registration", register), ("Consent/Privacy", consent), ("Premium Perks", premium), ("Abuse", abuse)]
        embed = discord.Embed(title="About ServerLink", description=description, color=discord.Color.blue())
        for name, value in nv:
            embed.add_field(name=name, value=value, inline=False)
        return await ctx.channel.send(embed=embed)

    @check_registered_amount
    async def register_channel(self, ctx: commands.Context = None, channel: discord.TextChannel = None):
        try:
            async with self.bot.db.acquire() as con:
                await con.execute(f"INSERT INTO serverlink(guild_id, channel_id) VALUES ({ctx.guild.id}, {channel.id})")
            embed = discord.Embed(title="Successfully Registered ServerLink Channel",
                                  description=f"{ctx.author.mention}, the channel {channel.mention} will be used for "
                                  f"any ServerLink communications for {ctx.guild.name}",
                                  color=discord.Color.blue())
        except Exception:
            embed = discord.Embed(title="Channel Already Registered",
                                  description=f"{ctx.author.mention}, the channel {channel.mention} was already registered",
                                  color=discord.Color.dark_red())
        finally:
            return await ctx.channel.send(embed=embed)

    @check_channel_registered
    async def unregister_channel(self, ctx, channel: discord.TextChannel = None):
        try:
            async with self.bot.db.acquire() as con:
                check = await con.fetchval(f"DELETE FROM serverlink WHERE guild_id={ctx.guild.id} "
                                           f"AND channel_id={channel.id} RETURNING channel_id")
                await con.execute(f"DELETE FROM serverlink_conn WHERE recipient_id={channel.id}")
        except Exception:
            raise customerrors.ServerLinkException()
        if not check:
            raise customerrors.ServerLinkNotRegisteredChannel(channel)
        embed = discord.Embed(title="Channel Unregistered Successfully",
                              description=f"{ctx.author.mention}, the channel {channel.mention} "
                              "was successfully unregistered. All incoming requests to that channel "
                              "have been cancelled",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @check_channel_registered
    async def make_public(self, ctx, channel: discord.TextChannel = None):
        try:
            async with self.bot.db.acquire() as con:
                await con.execute("UPDATE serverlink SET public=TRUE WHERE "
                                  f"channel_id={channel.id} and public=FALSE")
        except Exception:
            raise customerrors.ServerLinkException()
        embed = discord.Embed(title="Channel Made Public",
                              description=f"{ctx.author.mention}, {channel.mention} is now public and "
                              "visible on MarwynnBot's public ServerLink listings",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @check_channel_registered
    async def make_unpublic(self, ctx, channel: discord.TextChannel = None):
        try:
            async with self.bot.db.acquire() as con:
                await con.execute("UPDATE serverlink SET public=FALSE WHERE "
                                  f"channel_id={channel.id} AND public=TRUE")
        except Exception:
            raise customerrors.ServerLinkException()
        embed = discord.Embed(title="Channel Made Not Public",
                              description=f"{ctx.author.mention}, {channel.mention} is no longer "
                              "public and will not be shown on MarwynnBot's public ServerLink listings",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    async def get_serverlink_channels(self, ctx):
        async with self.bot.db.acquire() as con:
            entries = await con.fetch(f"SELECT channel_id FROM serverlink WHERE guild_id={ctx.guild.id}")
        if not entries:
            raise customerrors.ServerLinkNoRegisteredChannels(ctx.guild)
        return entries

    async def get_public_channels(self):
        try:
            async with self.bot.db.acquire() as con:
                entries = await con.fetch(f"SELECT channel_id, guild_id FROM serverlink "
                                          "WHERE active=FALSE AND public=TRUE")
        except Exception:
            raise customerrors.ServerLinkException()
        else:
            entry_list = []
            for entry in entries:
                try:
                    guild = self.bot.get_guild(int(entry['guild_id']))
                    entry_list.append(f"{guild.name} ⟶ <#{entry['channel_id']}>")
                except Exception:
                    continue
            return entry_list

    async def dispatch_request(self, ctx, other_guild: discord.Guild, my_channel_id: int, other_channel_id: int):
        try:
            channel = await self.bot.fetch_channel(other_channel_id)
        except Exception:
            raise customerrors.ServerLinkNoAvailableChannels(other_guild)
        else:
            async with self.bot.db.acquire() as con:
                await con.execute(f"INSERT INTO serverlink_conn(initiator_id, recipient_id, request_time) "
                                  f"VALUES({my_channel_id}, {other_channel_id}, {int(datetime.now().timestamp())})")
            embed = discord.Embed(title=f"Incoming ServerLink Request ⟶ {ctx.guild.name}",
                                  description=f"{ctx.guild.name} sent a serverlink request. Accept it with "
                                  f"`{await gcmds.prefix(ctx)}serverlink accept {my_channel_id}`",
                                  color=discord.Color.blue())
            return await channel.send(embed=embed)

    async def create_serverlink_request(self, ctx, other_guild: discord.Guild):
        async with self.bot.db.acquire() as con:
            my_channel_id = await con.fetchval(f"SELECT channel_id FROM serverlink WHERE guild_id={ctx.guild.id} "
                                               "AND active=FALSE LIMIT 1")
            other_channel_id = await con.fetchval(f"SELECT channel_id FROM serverlink WHERE guild_id={other_guild.id} "
                                                  "AND public=TRUE AND active=FALSE LIMIT 1")
            if not other_channel_id:
                raise customerrors.ServerLinkNoAvailableChannels(other_guild)
        await self.dispatch_request(ctx, other_guild, my_channel_id, other_channel_id)
        embed = discord.Embed(title="Request Successfully Sent",
                              description=f"{ctx.author.mention}, the ServerLink request to {other_guild.name} "
                              "was successfully sent. Your request will expire in 1 day if not accepted",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @check_request_exists
    async def accept_request(self, ctx: commands.Context = None, other_channel_id: int = None):
        return await self.start_session(initiator_id=other_channel_id, recipient_id=ctx.channel.id)

    @check_request_exists
    async def deny_request(self, ctx: commands.Context = None, other_channel_id: int = None):
        try:
            async with self.bot.db.acquire() as con:
                await con.execute(f"DELETE FROM serverlink_conn WHERE initiator_id={other_channel_id} AND "
                                  f"recipient_id={ctx.channel.id} AND pending=TRUE")
        except Exception:
            raise customerrors.ServerLinkException()
        embed = discord.Embed(title="Request Denied",
                              description=f"{ctx.author.mention}, you denied the request",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    async def configure_session(self, initiator_id: int, recipient_id: int):
        async with self.bot.db.acquire() as con:
            await con.execute(f"UPDATE serverlink_conn SET pending=FALSE, active=TRUE, "
                              f"start_time={int(datetime.now().timestamp())} WHERE initiator_id={initiator_id} AND "
                              f"recipient_id={recipient_id} AND pending=TRUE AND active=FALSE")
            await con.execute(f"UPDATE serverlink SET active=TRUE WHERE channel_id={initiator_id} OR "
                              f"channel_id={recipient_id}")
        return self.bot.get_channel(initiator_id), self.bot.get_channel(recipient_id)

    @ensure_inactive
    async def start_session(self, initiator_id: int = None, recipient_id: int = None):
        try:
            init_channel, recip_channel = await self.configure_session(initiator_id, recipient_id)
        except Exception:
            raise customerrors.ServerLinkException()
        title = "ServerLink Session Started"
        description = "Your ServerLink session with {} has started. Messages in {} will be relayed to {} automatically"
        to_initiator = discord.Embed(title=title,
                                     description=description.format(
                                         recip_channel.guild.name, init_channel.mention, recip_channel.mention
                                     ),
                                     color=discord.Color.blue())
        to_recip = discord.Embed(title=title,
                                 description=description.format(
                                     init_channel.guild.name, recip_channel.mention, init_channel.mention
                                 ),
                                 color=discord.Color.blue())
        await init_channel.send(embed=to_initiator)
        await recip_channel.send(embed=to_recip)
        await self.session_handler(init_channel, recip_channel)

    async def is_connected(self, init_channel: discord.TextChannel, recip_channel: discord.TextChannel):
        async with _bot.db.acquire() as con:
            active_con = await con.fetch("SELECT * FROM serverlink_conn WHERE active=TRUE AND "
                                         f"initiator_id={init_channel.id} AND recipient_id={recip_channel.id}")
        return True if active_con else False

    async def session_handler(self, init_channel: discord.TextChannel, recip_channel: discord.TextChannel):
        def valid_sesh_message(message: discord.Message):
            return not message.author.bot and (message.channel.id == init_channel.id
                                               or message.channel.id == recip_channel.id)

        while True:
            try:
                message: discord.Message = await self.bot.wait_for("message", check=valid_sesh_message, timeout=120)
                if not await self.is_connected(init_channel, recip_channel):
                    return
            except asyncio.TimeoutError:
                return await self.terminate_session(init_channel, recip_channel)
            else:
                if message.channel.id == init_channel.id:
                    channel = recip_channel
                else:
                    channel = init_channel
            with suppress(Exception):
                entry = await channel.send(content=f"**{message.author}:**\n{message.content}",
                                           tts=message.tts,
                                           embed=message.embeds[0] if message.embeds else None,
                                           files=[await attachment.to_file() for attachment in message.attachments],
                                           allowed_mentions=discord.AllowedMentions.none())
                values = f"({message.id}, {entry.id}, {channel.id})"
                async with self.bot.db.acquire() as con:
                    await con.execute("INSERT INTO serverlink_temp(message_id, recip_message_id, recip_channel_id) "
                                      f"VALUES {values}")

    async def terminate_session(self, init_channel: discord.TextChannel, recip_channel: discord.TextChannel,
                                timed_out: bool = True):
        await init_channel.trigger_typing()
        await recip_channel.trigger_typing()
        await asyncio.sleep(2.0)
        async with self.bot.db.acquire() as con:
            await con.execute(f"UPDATE serverlink_conn SET active=FALSE, end_time={int(datetime.now().timestamp())} "
                              f"WHERE initiator_id={init_channel.id} AND "
                              f"recipient_id={recip_channel.id} AND active=TRUE")
            await con.execute(f"UPDATE serverlink SET active=FALSE WHERE "
                              f"channel_id={init_channel.id} OR channel_id={recip_channel.id}")
            await con.execute(f"DELETE FROM serverlink_temp WHERE "
                              f"recip_channel_id={init_channel.id} OR recip_channel_id={recip_channel.id}")
        if timed_out:
            embed = discord.Embed(title="ServerLink Session Terminated",
                                  description=f"The session timed out after 2 minutes of inactivity",
                                  color=discord.Color.dark_red())
            await init_channel.send(embed=embed)
            await recip_channel.send(embed=embed)
        return

    @commands.group(invoke_without_command=True,
                    aliases=['sl', 'link'],
                    desc="Displays the help command for serverlink",
                    usage="serverlink")
    async def serverlink(self, ctx):
        return await self.send_serverlink_help(ctx)

    @serverlink.command(aliases=['about'])
    async def serverlink_about(self, ctx):
        return await self.send_serverlink_about(ctx)

    @serverlink.command(aliases=['register', 'set', 'enable'])
    @commands.has_permissions(manage_guild=True)
    async def serverlink_register(self, ctx, channel: discord.TextChannel):
        return await self.register_channel(ctx=ctx, channel=channel)

    @serverlink.command(aliases=['unregister', 'unset', 'disable'])
    @commands.has_permissions(manage_guild=True)
    async def serverlink_unregister(self, ctx, channel: discord.TextChannel):
        return await self.unregister_channel(ctx, channel=channel)

    @serverlink.command(aliases=['pub', 'public'])
    @commands.has_permissions(manage_guild=True)
    async def serverlink_public(self, ctx, channel: discord.TextChannel):
        return await self.make_public(ctx, channel=channel)

    @serverlink.command(aliases=['unpub', 'private', 'unpublic'])
    @commands.has_permissions(manage_guild=True)
    async def serverlink_unpublic(self, ctx, channel: discord.TextChannel):
        return await self.make_unpublic(ctx, channel=channel)

    @serverlink.command(aliases=['listings', 'global'])
    async def serverlink_listings(self, ctx):
        entries = await self.get_public_channels()
        pag = EmbedPaginator(ctx, entries=entries, per_page=10, show_entry_count=True, show_index=False)
        pag.embed.title = "Public ServerLink Channels"
        return await pag.paginate()

    @serverlink.command(aliases=['-ls', 'list', 'show'])
    async def serverlink_list(self, ctx):
        entries = [f"<#{entry['channel_id']}>" for entry in await self.get_serverlink_channels(ctx)]
        pag = EmbedPaginator(ctx, entries=entries, per_page=20, show_entry_count=False)
        pag.embed.title = "Registered ServerLink Channels"
        return await pag.paginate()

    @serverlink.command(aliases=['request', 'req'])
    async def serverlink_request(self, ctx, *, guild_name: str):
        guild = discord.utils.get(self.bot.guilds, name=guild_name)
        if not guild:
            raise customerrors.ServerLinkInvalidGuild(guild_name)
        if guild.id == ctx.guild.id:
            raise customerrors.ServerLinkNoSelf()
        return await self.create_serverlink_request(ctx, guild)

    @serverlink.command(aliases=['allow', 'accept'])
    @commands.has_permissions(manage_guild=True)
    async def serverlink_accept(self, ctx, other_channel_id: int):
        channel = self.bot.get_channel(other_channel_id)
        if not channel.guild:
            raise customerrors.ServerLinkException()
        return await self.accept_request(ctx=ctx, other_channel_id=other_channel_id)

    @serverlink.command(aliases=['reject', 'deny'])
    @commands.has_permissions(manage_guild=True)
    async def serverlink_deny(self, ctx, other_channel_id: int):
        channel = self.bot.get_channel(other_channel_id)
        if not channel.guild:
            raise customerrors.ServerLinkException()
        return await self.deny_request(ctx=ctx, other_channel_id=other_channel_id)

    @serverlink.command(aliases=['dc', 'end', 'disconnect'])
    async def serverlink_disconnect(self, ctx):
        async with self.bot.db.acquire() as con:
            pot_channel = await con.fetch(f"SELECT initiator_id, recipient_id FROM serverlink_conn WHERE "
                                          f"initiator_id={ctx.channel.id} OR recipient_id={ctx.channel.id} AND "
                                          "pending=FALSE AND active=TRUE")
        if not pot_channel:
            raise customerrors.ServerLinkNoActiveSession(ctx)
        pot_channel = pot_channel[0]
        if int(pot_channel['initiator_id']) == ctx.channel.id:
            other_channel = self.bot.get_channel(int(pot_channel['recipient_id']))
            await self.terminate_session(ctx.channel, other_channel, timed_out=False)
        else:
            other_channel = self.bot.get_channel(int(pot_channel['initiator_id']))
            await self.terminate_session(other_channel, ctx.channel, timed_out=False)
        embed = discord.Embed(title="ServerLink Session Terminated",
                              description=f"The ServerLink session has been terminated",
                              color=discord.Color.dark_red())
        await ctx.channel.send(embed=embed)
        await other_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(ServerLink(bot))
