import discord
from discord.ext import commands, tasks
from utils import customerrors, enums, globalcommands, paginator, premium

REACTIONS = [reaction.value for reaction in enums.ConfirmReactions]


class ServerLink(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.bot.loop.create_task(self.init_serverlink())

    async def init_serverlink(self):
        await self.bot.wait_until_ready()
        async with self.bot.db.acquire() as con:
            await con.execute("CREATE TABLE IF NOT EXISTS serverlink(guild_id bigint, channel_id bigint PRIMARY KEY, "
                              "active boolean DEFAULT FALSE)")
            await con.execute("CREATE TABLE IF NOT EXISTS serverlink_conn(initiator_id bigint, recipient_id bigint, "
                              "pending boolean DEFAULT TRUE, active boolean DEFAULT FALSE, start_time NUMERIC, "
                              "end_time NUMERIC)")

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
                   "incoming comms request to initiate the connection. If your request is not accepted or you deny a "
                   "request, there will be a 15 minute cooldown before you will be able to send a new request to that "
                   "same server. You will also be able to block connections from specific servers. Once blocked, you "
                   "will no longer receive requests from that server, and that server will not be made aware that "
                   "they have been blocked")
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

    async def check_registered_channels(self, ctx):
        async with self.bot.db.acquire() as con:
            amount_registered = await con.fetch(f"SELECT * FROM serverlink WHERER guild_id={ctx.guild.id}")
        if amount_registered > 1 and not premium.check_guild_premium(ctx.guild):
            raise customerrors.ServerLinkChannelLimitExceeded(ctx.guild)
        return

    async def register_channel(self, ctx, channel: discord.TextChannel):
        await self.check_registered_channels(ctx)
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

    async def get_serverlink_channels(self, ctx):
        async with self.bot.db.acquire() as con:
            entries = await con.fetch(f"SELECT channel_id FROM serverlink WHERE guild_id={ctx.guild.id}")
        if not entries:
            raise customerrors.ServerLinkNoRegisteredChannels(ctx.guild)
        return entries

    async def create_serverlink_request(self, ctx, other_guild: discord.Guild):
        async with self.bot.db.acquire() as con:
            self_status = await con.fetchval(f"SELECT channel_id")

    @commands.group(invoke_without_command=True,
                    aliases=['sl', 'link'],
                    desc="Displays the help command for serverlink",
                    usage="serverlink")
    async def serverlink(self, ctx):
        return await self.send_serverlink_about(ctx)

    @serverlink.command(aliases=['register', 'set', 'enable'])
    @commands.has_permissions(manage_guild=True)
    async def serverlink_register(self, ctx, channel: discord.TextChannel):
        return await self.register_channel(ctx, channel)

    @serverlink.command(aliases=['-ls', 'list', 'show'])
    async def serverlink_list(self, ctx):
        entries = [f"<#{entry['channel_id']}>" for entry in await self.get_serverlink_channels(ctx)]
        pag = paginator.EmbedPaginator(ctx, entries=entries, per_page=20, show_entry_count=False)
        pag.embed.title = "Registered ServerLink Channels"
        return await pag.paginate()

    @serverlink.command(aliases=['request', 'req'])
    async def serverlink_request(self, ctx, *, guild_name: str):
        guild = discord.utils.get(self.bot.guilds, name=guild_name)
        if not guild:
            raise customerrors.ServerLinkInvalidGuild(guild_name)
        return await self.create_serverlink_request(ctx, guild)


def setup(bot):
    bot.add_cog(ServerLink(bot))
