import asyncio
import types
from collections import namedtuple
from datetime import datetime
from typing import Optional, Sequence, Union

import discord
from discord.ext import commands
from utils import customerrors, globalcommands, premium
from utils.enums import ConfirmReactions, LogLevel
from utils.logdispatcher import (GuildChannelEventDispatcher,
                                 GuildEmojiEventDispatcher,
                                 GuildGenericEventDispatcher,
                                 GuildInviteEventDispatcher,
                                 GuildMessageEventDispatcher,
                                 GuildRoleEventDispatcher,
                                 MemberGenericEventDispatcher)

gcmds = globalcommands.GlobalCMDS()
GuildDiff = namedtuple("GuildAttributeDiff", ['type', 'before', 'after'])
ChannelDiff = namedtuple("ChannelAttributeDiff", ['type', 'before', 'after'])
MemberDiff = namedtuple("MemberAttributeDiff", ['type', 'before', 'after'])
MemberRoleDiff = namedtuple("MemberRoleDiff", ['type', 'role'])
UserDiff = namedtuple("UserAttributeDiff", ['type', 'before', 'after'])


class Logging(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        global gcmds
        self.bot = bot
        gcmds = globalcommands.GlobalCMDS(self.bot)
        self.bot.loop.create_task(self.init_logging())
        self.guild_gen_event_dispatcher = GuildGenericEventDispatcher(self.bot)
        self.guild_channel_event_dispatcher = GuildChannelEventDispatcher(self.bot)
        self.guild_role_event_dispatcher = GuildRoleEventDispatcher(self.bot)
        self.guild_emoji_event_dispatcher = GuildEmojiEventDispatcher(self.bot)
        self.guild_invite_event_dispatcher = GuildInviteEventDispatcher(self.bot)
        self.guild_message_event_dispatcher = GuildMessageEventDispatcher(self.bot)
        self.member_gen_event_dispatcher = MemberGenericEventDispatcher(self.bot)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        await self.guild_gen_event_dispatcher.guild_command_completed(ctx)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        set_after = set([(attr, getattr(after, attr)) for attr in after.__slots__
                         if not attr.startswith("_")
                         and not type(getattr(after, attr)) == list])
        set_before = set([(attr, getattr(before, attr)) for attr in before.__slots__
                          if not attr.startswith("_")
                          and not type(getattr(before, attr)) == list])
        diff_list = [GuildDiff(attr, getattr(before, attr), value) for attr, value in set_after - set_before]
        await self.guild_gen_event_dispatcher.guild_update(after, diff_list)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        await self.guild_channel_event_dispatcher.guild_channels_update(channel, "created")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self.guild_channel_event_dispatcher.guild_channels_update(channel, "deleted")

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        set_after = set([(attr, getattr(after, attr)) for attr in after.__slots__
                         if not attr.startswith("_")
                         and not type(getattr(after, attr)) == list])
        set_before = set([(attr, getattr(before, attr)) for attr in before.__slots__
                          if not attr.startswith("_")
                          and not type(getattr(before, attr)) == list])
        diff_list = [ChannelDiff(attr, getattr(before, attr), value) for attr, value in set_after - set_before]
        await self.guild_channel_event_dispatcher.guild_channel_attr_update(after, diff_list)

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel: discord.abc.GuildChannel, last_pin: Optional[datetime]):
        await self.guild_channel_event_dispatcher.channel_pins_update(channel)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        await self.guild_role_event_dispatcher.guild_role_update(role, "created")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        await self.guild_role_event_dispatcher.guild_role_update(role, "deleted")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        set_after = set([(attr, getattr(after, attr)) for attr in after.__slots__
                         if not attr.startswith("_")
                         and not type(getattr(after, attr)) == list])
        set_before = set([(attr, getattr(before, attr)) for attr in before.__slots__
                          if not attr.startswith("_")
                          and not type(getattr(before, attr)) == list])
        diff_list = [ChannelDiff(attr, getattr(before, attr), value) for attr, value in set_after - set_before]
        await self.guild_role_event_dispatcher.guild_role_attr_update(after, diff_list)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before: Sequence[discord.Emoji], after: Sequence[discord.Emoji]):
        event_type = "added" if len(before) < len(after) else "removed"
        diff_list = set(after) ^ set(before)
        await self.guild_emoji_event_dispatcher.guild_emoji_update(guild, event_type, diff_list)

    @commands.Cog.listener()
    async def on_guild_integrations_update(self, guild: discord.Guild):
        await self.guild_gen_event_dispatcher.guild_integrations_update(guild)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.abc.GuildChannel):
        await self.guild_channel_event_dispatcher.channel_webhooks_update(channel)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.member_gen_event_dispatcher.member_membership_update(member, "joined")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.member_gen_event_dispatcher.member_membership_update(member, "left")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        set_after = set([(attr, getattr(after, attr)) for attr in after.__slots__
                         if not attr.startswith("_")
                         and not attr == "system"
                         and not type(getattr(after, attr)) == list])
        set_before = set([(attr, getattr(before, attr)) for attr in before.__slots__
                          if not attr.startswith("_")
                          and not attr == "system"
                          and not type(getattr(before, attr)) == list])
        diff_list = [MemberDiff(attr, getattr(before, attr), value) for attr, value in set_after - set_before]
        if not diff_list:
            role_set_after = set([role for role in after.roles])
            role_set_before = set([role for role in before.roles])
            role_type = "role_add" if len(role_set_after) > len(role_set_before) else "role_remove"
            diff_list = [MemberRoleDiff(role_type, value) for value in role_set_after ^ role_set_before]
            if not diff_list:
                return
        await self.member_gen_event_dispatcher.member_update(after, diff_list)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: Union[discord.User, discord.Member]):
        await self.member_gen_event_dispatcher.member_ban_update(guild, user, "banned")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        await self.member_gen_event_dispatcher.member_ban_update(guild, user, "unbanned")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        set_after = set([(attr, getattr(after, attr)) for attr in after.__slots__
                         if not attr.startswith("_")
                         and not type(getattr(after, attr)) == list])
        set_before = set([(attr, getattr(before, attr)) for attr in before.__slots__
                          if not attr.startswith("_")
                          and not type(getattr(before, attr)) == list])
        diff_list = [MemberDiff(attr, getattr(before, attr), value) for attr, value in set_after - set_before]
        print(diff_list)
        await self.member_gen_event_dispatcher.member_voice_state_update(member, diff_list)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        await self.guild_invite_event_dispatcher.guild_invite_update(invite, "created")

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        await self.guild_invite_event_dispatcher.guild_invite_update(invite, "deleted")

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        await self.guild_message_event_dispatcher.message_raw_edit(
            payload.message_id,
            payload.channel_id,
            payload.data
        )

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        await self.guild_message_event_dispatcher.message_raw_delete(
            payload.message_id,
            payload.channel_id
        )

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        await self.guild_message_event_dispatcher.message_raw_bulk_delete(
            payload.message_ids,
            payload.channel_id
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.guild_message_event_dispatcher.reaction_raw_update(
            payload.message_id,
            payload.emoji,
            payload.user_id,
            payload.channel_id,
            "reaction added"
        )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.guild_message_event_dispatcher.reaction_raw_update(
            payload.message_id,
            payload.emoji,
            payload.user_id,
            payload.channel_id,
            "reaction removed"
        )

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload: discord.RawReactionClearEvent):
        await self.guild_message_event_dispatcher.reaction_raw_clear(
            payload.message_id,
            payload.channel_id
        )

    @commands.Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload: discord.RawReactionClearEmojiEvent):
        await self.guild_message_event_dispatcher.reaction_raw_clear_emoji(
            payload.message_id,
            payload.channel_id,
            payload.emoji
        )

    async def init_logging(self):
        await self.bot.wait_until_ready()
        async with self.bot.db.acquire() as con:
            values = "(guild_id bigint PRIMARY KEY, log_level text DEFAULT 'basic', \"" + \
                '\" boolean DEFAULT FALSE, \"'.join(command.name.lower() for command in sorted(self.bot.commands,
                                                                                               key=lambda x: x.name)) + \
                "\" boolean DEFAULT FALSE)"
            await con.execute(f"CREATE TABLE IF NOT EXISTS logging{values}")
            for command in sorted(self.bot.commands, key=lambda x: x.name):
                await con.execute(f"ALTER TABLE logging ADD COLUMN IF NOT EXISTS \"{command.name.lower()}\" boolean DEFAULT FALSE ")
        return

    async def send_logging_help(self, ctx):
        pfx = f"{await gcmds.prefix(ctx)}logging"
        description = (f"{ctx.author.mention}, the base command is `{pfx}` *aliases=`lg` `log`*. Logging is a powerful "
                       "tool that will allow you to track multiple things at a time:\n",
                       "**1. Command Execution**",
                       "> With logging level `basic`, MarwynnBot can send a message in the specified logging channel "
                       "whenever a server member uses a command. Logging messages may vary depending on what command "
                       "was used. *For example, logging moderation commands may display the results of the moderation "
                       "action, or logging actions commands may display what action was done to which member*\n",
                       "**2. Server Modification Events**",
                       "> With logging level `server`, MarwynnBot will be able to do anything in logging level `basic`, "
                       "but with the ability to log changes that happen to the server, such as moving voice regions, "
                       "renaming channels, changing channel permissions, anything that happens in audit log, etc\n",
                       "**3. Member Modification Events**",
                       "> With logging level 'hidef`, MarwynnBot will be able to do anything in loggin g level `server`, "
                       "but with the ability to log changes that happen to members in your server. This includes things "
                       "like status changes, nickname updates, username changes, etc. This can fall under a breach of "
                       "privacy, so this logging will only be reserved for those that have been pre-approved to access "
                       "this feature\n",
                       "Here are all the subcommands")
        lset = (f"**Usage:** `{pfx} set [#channel]`",
                "**Returns:** An embed that confirms that you have successfully set the logging channel",
                "**Aliases:** `-s` `use`",
                "**Special Cases:** `[#channel]` should be a channel tag or channel ID")
        llist = (f"**Usage:** `{pfx} list`",
                 "**Returns:** An embed that displays the current logging channel and logging level, if set",
                 "**Aliases:** `-ls` `show` `display`",
                 "**Special Cases:** This will return an error message if no logging channel is set")
        ldisable = (f"**Usage:** `{pfx} disable`",
                    "**Returns:** A confirmation embed that once confirmed, will disable logging on this server",
                    "**Aliases:** `-rm` `delete` `reset` `clear` `remove`")
        llevel = (f"**Usage:** `{pfx} level [level]`",
                  "**Returns:** An embed that confirms the server's log level was changed",
                  "**Aliases:** `lvl` `levels`",
                  "**Special Cases:** This command can only be used if your server is a MarwynnBot Premium Server. "
                  "`[level]` must be either \"basic\", \"server\", or \"hidef\"")
        lblacklist = (f"**Usage:** `{pfx} blacklist (guild)`",
                      "**Returns:** An embed that confirms the blacklist has been set for `(guild)`",
                      "**Aliases:** `bl`",
                      "**Special Cases:** This is an owner only command. `(guild)` will default to the current server "
                      "if unspecified")
        nv = [("Set", lset), ("List", llist), ("Remove", ldisable), ("Level", llevel), ("Blacklist", lblacklist)]
        embed = discord.Embed(title="Logging Help", description="\n".join(description), color=discord.Color.blue())
        for name, value in nv:
            embed.add_field(name=name, value="> " + "\n> ".join(value), inline=False)
        return await ctx.channel.send(embed=embed)

    async def set_logging_channel(self, ctx, channel: discord.TextChannel) -> discord.Message:
        embed = discord.Embed()
        try:
            async with self.bot.db.acquire() as con:
                await con.execute(f"UPDATE guild SET log_channel={channel.id} WHERE guild_id={ctx.guild.id}")
                await con.execute(f"UPDATE guild SET log_level={LogLevel.BASIC.value} WHERE guild_id={ctx.guild.id} AND log_level=0")
            embed.title = "Logging Channel Set!"
            embed.description = f"{ctx.author.mention}, this server's logging channel was set to {channel.mention}"
            embed.color = discord.Color.blue()
        except Exception:
            embed.title = "Set Logging Channel Failed"
            embed.description = f"{ctx.author.mention}, I could not set this server's logging channel"
            embed.color = discord.Color.dark_red()
        return await ctx.channel.send(embed=embed)

    async def remove_logging(self, ctx):
        embed = discord.Embed()
        try:
            async with self.bot.db.acquire() as con:
                await con.execute(f"UPDATE guild SET log_channel=NULL WHERE guild_id={ctx.guild.id}")
            embed.title = "Logging Disabled"
            embed.description = f"{ctx.author.mention}, logging is now disabled on this server"
            embed.color = discord.Color.blue()
        except Exception:
            embed.title = "Disable Logging Failed"
            embed.description = f"{ctx.author.mention}, logging could not be disabled on this server"
            embed.color = discord.Color.dark_red()
        return await ctx.channel.send(embed=embed)

    async def check_logging_level_updatable(self, ctx, level):
        if not await premium.check_guild_premium(ctx.guild):
            raise customerrors.NotPremiumGuild(ctx.guild)
        return

    async def set_logging_level(self, ctx, level_int):
        embed = discord.Embed()
        try:
            async with self.bot.db.acquire() as con:
                await con.execute(f"UPDATE guild SET log_level={LogLevel(level_int).value} WHERE guild_id={ctx.guild.id}")
            embed.title = "Logging Level Successfully Updated"
            embed.description = f"{ctx.author.mention}, the server's logging level is now `{LogLevel(level_int).name.lower()}`"
            embed.color = discord.Color.blue()
        except Exception:
            embed.title = "Update Logging Level Failed"
            embed.description = f"{ctx.author.mention}, I couldn't update the logging level for this server"
            embed.color = discord.Color.dark_red()
        return await ctx.channel.send(embed=embed)

    @commands.group(invoke_without_command=True, aliases=['lg', 'log'])
    async def logging(self, ctx):
        return await self.send_logging_help(ctx)

    @logging.command(aliases=['-s', 'use', 'set'])
    @commands.has_permissions(manage_guild=True)
    async def logging_set(self, ctx, channel: discord.TextChannel):
        return await self.set_logging_channel(ctx, channel)

    @logging.command(aliases=['ls', 'show', 'display', 'list'])
    async def logging_list(self, ctx):
        async with self.bot.db.acquire() as con:
            log_channel = await con.fetchval(f"SELECT log_channel FROM guild WHERE guild_id={ctx.guild.id}")
            log_level = LogLevel(await con.fetchval(f"SELECT log_level FROM guild WHERE guild_id={ctx.guild.id}"))
        embed = discord.Embed(title="Logging Details",
                              description=f"**Logging Channel:** {f'<#{log_channel}>' if log_channel else '`None Set`'}\n"
                              f"**Logging Level:** `{log_level}`",
                              color=discord.Color.blue() if log_channel else discord.Color.dark_red())
        return await ctx.channel.send(embed=embed)

    @logging.command(aliases=['rm', 'delete', 'reset', 'clear', 'remove', 'disable'])
    @commands.has_permissions(manage_guild=True)
    async def logging_disable(self, ctx):
        reactions = [reaction.value for reaction in ConfirmReactions]

        def reacted(reaction: discord.Reaction, user: discord.User):
            return reaction.emoji in reactions and user.id == ctx.author.id and reaction.message.id == panel.id

        panel_embed = discord.Embed(title="Confirmation",
                                    description=f"{ctx.author.mention}, this server will not log events until it is reenabled. "
                                    f"React with {reactions[0]} to confirm or {reactions[1]} to cancel",
                                    color=discord.Color.blue())
        panel = await ctx.channel.send(embed=panel_embed)
        for reaction in reactions:
            try:
                await panel.add_reaction(reaction)
            except Exception:
                pass

        try:
            result = await self.bot.wait_for("reaction_add", check=reacted, timeout=30)
        except asyncio.TimeoutError:
            return await gcmds.timeout(ctx, "logging disable", 30)
        await gcmds.smart_delete(panel)
        if result == reactions[0]:
            return await self.remove_logging(ctx)
        else:
            return await gcmds.cancelled(ctx, "logging disable")

    @logging.command(aliases=['lvl', 'level', 'levels'])
    @commands.has_permissions(manage_guild=True)
    async def logging_level(self, ctx, level):
        print(level)
        try:
            if level.lower() == "server":
                level = "guild"
            level_int = LogLevel[level.upper()]
        except KeyError:
            raise customerrors.LoggingLevelInvalid(level)
        await self.check_logging_level_updatable(ctx, level_int)
        return await self.set_logging_level(ctx, level_int)

    @logging.command(aliases=['bl', 'blacklist'])
    async def logging_blacklist(self, ctx, guild: discord.Guild = None):
        if not guild:
            guild = ctx.guild
        async with self.bot.db.acquire() as con:
            await con.execute(f"UPDATE guild SET log_channel=$tag$DISABLED$tag$, log_level=-1 WHERE guild_id={guild.id}")
        embed = discord.Embed(title="Server Logging Blacklisted",
                              description=f"{ctx.author.mention}, the server {guild.name} can no longer utilise any "
                              "logging functionality",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Logging(bot))
