from datetime import datetime
from typing import Union, Optional

import discord
from discord.ext import commands

from utils import customerrors, premium
from utils.enums import LogLevel
from utils.enums import ChannelEmoji as CE


class LogDispatcher():
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__()
        self.bot = bot
        self.min_level = LogLevel.BASIC

    async def check_logging_enabled(self, guild, min_level):
        async with self.bot.db.acquire() as con:
            log_channel = await con.fetchval(f"SELECT log_channel FROM guild WHERE guild_id={guild.id}")
            log_level = await con.fetchval(f"SELECT log_level FROM guild WHERE guild_id={guild.id}")

        if not log_channel or log_channel == "DISABLED":
            raise customerrors.LoggingNotEnabled()
        elif log_level < min_level.value:
            raise customerrors.LoggingLevelInsufficient
        else:
            return self.bot.get_channel(log_channel)

    async def dispatch_embed(self, channel: discord.TextChannel, embed: discord.Embed):
        embed.set_footer(text="{:%m/%d/%Y %H:%M:%S}".format(datetime.now()))
        return await channel.send(embed=embed)


class GuildGenericEventDispatcher(LogDispatcher):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(bot)
        self.min_level = LogLevel.GUILD

    async def guild_update(self, guild: discord.Guild, diff: list):
        if not diff:
            return
        log_channel = await self.check_logging_enabled(guild, self.min_level)
        embed = discord.Embed(title="Server Updated", color=discord.Color.blue())
        description = [f"{item.type.replace('_', ' ').title()}\n> Server {item.type.replace('_', ' ')} changed "
                       f"from `{item.before}` ⟶ `{item.after}`\n" for item in diff if diff]
        embed.description = "\n".join(description)
        return await self.dispatch_embed(log_channel, embed)

    async def guild_integrations_update(self, guild: discord.Guild):
        log_channel = await self.check_logging_enabled(guild, self.min_level)
        embed = discord.Embed(title="Server Integrations Updated",
                              description=f"The integrations for {guild.name} were updated",
                              color=discord.Color.blue())
        return await self.dispatch_embed(log_channel, embed)


class GuildChannelEventDispatcher(GuildGenericEventDispatcher):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(bot)

    def get_channel_string(self, channel: discord.abc.GuildChannel, event_type: str = "none"):
        return f"Channel {CE[str(channel.type)]}{channel.mention if event_type != 'deleted' and str(channel.type) == 'text' else channel.name}"

    async def guild_channel_attr_update(self, channel: discord.abc.GuildChannel, diff: list):
        if not diff:
            return
        log_channel = await self.check_logging_enabled(channel.guild, self.min_level)
        embed = discord.Embed(title="Channel Updated", color=discord.Color.blue())
        description = [f"{item.type.replace('_', ' ').title()}\n> Channel {item.type.replace('_', ' ')} changed "
                       f"from `{item.before}` ⟶ `{item.after}`\n" for item in diff if diff]
        embed.description = f"{self.get_channel_string(channel)}\n\n" + "\n".join(description)
        return await self.dispatch_embed(log_channel, embed)

    async def guild_channels_update(self, channel: discord.abc.GuildChannel, event_type: str):
        log_channel = await self.check_logging_enabled(channel.guild, self.min_level)
        embed = discord.Embed(title=f"Channel {event_type.title()}",
                              description=f"{self.get_channel_string(channel, event_type)} was {event_type.lower()}",
                              color=discord.Color.blue() if event_type == "created" else discord.Color.dark_red())
        return await self.dispatch_embed(log_channel, embed)

    async def channel_pins_update(self, channel: discord.abc.GuildChannel):
        log_channel = await self.check_logging_enabled(channel.guild, self.min_level)
        pins = await channel.pins()
        last_pin = f"[Click Here]({pins[0].jump_url})" if pins else "`no pins`"
        embed = discord.Embed(title=f"Channel Pins Updated",
                              description=f"The pins for {channel.mention} were updated\n\n**Most Recent Pin:** {last_pin}",
                              color=discord.Color.blue())
        return await self.dispatch_embed(log_channel, embed)

    async def channel_webhooks_update(self, channel: discord.abc.GuildChannel):
        log_channel = await self.check_logging_enabled(channel.guild, self.min_level)
        embed = discord.Embed(title=f"Channel Webhooks Updated",
                              description=f"The webhooks in {channel.mention} were updated",
                              color=discord.Color.blue())
        return await self.dispatch_embed(log_channel, embed)


class GuildRoleEventDispatcher(GuildGenericEventDispatcher):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(bot)

    async def guild_role_update(self, role: discord.Role, event_type: str):
        log_channel = await self.check_logging_enabled(role.guild, self.min_level)
        embed = discord.Embed(title=f"Role {event_type.title()}",
                              description=f"Created role {role.mention}" if event_type == "created" else f"Deleted role {role.name}",
                              color=role.color if event_type == "created" else discord.Color.dark_red())
        return await self.dispatch_embed(log_channel, embed)

    async def guild_role_attr_update(self, role: discord.Role, diff: list):
        if not diff:
            return
        log_channel = await self.check_logging_enabled(role.guild, self.min_level)
        embed = discord.Embed(title="Role Updated", color=role.color)
        description = [f"{item.type.replace('_', ' ').title()}\n> Role {item.type.replace('_', ' ')} changed "
                       f"from `{item.before}` ⟶ `{item.after}`\n" for item in diff if diff]
        embed.description = f"{role.mention}\n\n" + "\n".join(description)
        return await self.dispatch_embed(log_channel, embed)


class GuildEmojiEventDispatcher(GuildGenericEventDispatcher):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(bot)

    async def guild_emoji_update(self, guild, event_type: str, diff: list):
        log_channel = await self.check_logging_enabled(guild, self.min_level)
        embed = discord.Embed(title=f"Emojis {event_type.title()}", color=discord.Color.blue()
                              if event_type == "added" else discord.Color.dark_red())
        embed.description = "\n".join([f"> {str(emoji)} `<:{emoji.name}:{emoji.id}>`" for emoji in diff])
        return await self.dispatch_embed(log_channel, embed)


class GuildInviteEventDispatcher(GuildGenericEventDispatcher):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(bot)

    async def guild_invite_update(self, invite: discord.Invite, event_type: str):
        if not invite.guild:
            return
        return


class GuildMessageEventDispatcher(GuildGenericEventDispatcher):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(bot)

    async def message_raw_edit(self, message_id: int, channel: int, data: dict):
        return

    async def message_raw_delete(self, message_id: int, channel_id: int, guild_id: Optional[int]):
        return


class GuildReactionEventDispatcher(GuildGenericEventDispatcher):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(bot)

    async def reaction_raw_update(self, message_id: int, emoji: discord.PartialEmoji, user_id: int, channel_id: int, event_type: str):
        return

    async def reaction_raw_clear(self, message_id: int, channel_id: int):
        return

    async def reaction_raw_clear_emoji(self, message_id: int, channel_id: int, emoji: discord.PartialEmoji):
        return


class MemberGenericEventDispatcher(LogDispatcher):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(bot)
        self.min_level = LogLevel.GUILD

    async def check_logging_enabled(self, member: discord.Member, min_level: LogLevel):
        if not member.bot:
            return await super().check_logging_enabled(member.guild, min_level)
        else:
            raise customerrors.LoggingNotEnabled()

    async def update_parser(self, member, item: namedtuple) -> str:
        if item.type == "activities":
            return f"{item.type.replace('_', ' ').title()}\n> Changed from `{item.before.name}` ⟶ `{item.after.name}`"
        elif item.type == "premium_since":
            return f"{item.type.replace('_', ' ').title()}\n> Nitro Boosted this server"
        elif "status" in item.type:
            pass
        elif item.type == "voice":
            return f"{item.type.replace('_', ' ').title()}\n> {f'Connected to voice channel {item.after.channel.name}'}" \
                if item.after.channel else f"Disconnected from voice channel `{item.before.channel.name}`'"
        else:
            return f"{item.type.replace('_', ' ').title()}\n> Changed from `{item.before}` ⟶ `{item.after}`"

    async def member_membership_update(self, member: discord.Member, event_type: str):
        log_channel = await self.check_logging_enabled(member, self.min_level)
        embed = discord.Embed(title=f"Member {event_type.title()}",
                              description=f"{member.mention} has {event_type} {member.guild.name}",
                              color=discord.Color.blue() if event_type == "joined" else discord.Color.dark_red())
        return await self.dispatch_embed(log_channel, embed)

    async def member_update(self, member: discord.Member, diff: list):
        if not diff:
            return
        log_channel = await self.check_logging_enabled(member, self.min_level)
        description = [await self.update_parser(member, item) for item in diff]
        embed = discord.Embed(title="Member Updated",
                              description = f"{member.mention} changed\n" + "\n".join(description),
                              color=member.color)
        return await self.dispatch_embed(log_channel, embed)

    async def member_ban_update(self, guild: discord.Guild, member: Union[discord.User, discord.Member], event_type: str):
        return

    async def member_voice_state_update(self, member: discord.Member, diff: list):
        return


class UserGenericEventDispatcher(LogDispatcher):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(bot)
        self.min_level = LogLevel.HIDEF

    async def user_update(self, user: discord.User, diff: list):
        return


class MessageGenericEventDispatcher(LogDispatcher):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(bot)
        self.min_level = LogLevel.HIDEF
