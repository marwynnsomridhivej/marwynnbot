from abc import ABC, abstractmethod
from datetime import datetime

import discord
from discord.ext import commands

from utils import customerrors, globalcommands, paginator, premium
from utils.enums import LogLevel
from utils.enums import ChannelEmoji as CE


class LogDispatcher(ABC):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__()
        self.bot = bot
        gcmds = globalcommands.GlobalCMDS(self.bot)

    @abstractmethod
    async def check_logging_enabled(self, guild):
        pass

    @abstractmethod
    async def dispatch_embed(self):
        pass


class GuildGenericEventDispatcher(LogDispatcher):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(bot)
        self.min_level = LogLevel.GUILD

    async def check_logging_enabled(self, guild, min_level):
        async with self.bot.db.acquire() as con:
            log_channel = await con.fetchval(f"SELECT log_channel FROM guild WHERE guild_id={guild.id}")
            log_level = await con.fetchval(f"SELECT log_level FROM guild WHERE guild_id={guild.id}")

        if not log_channel or log_channel == "DISABLED":
            raise customerrors.LoggingNotEnabled
        elif log_level < min_level.value:
            raise customerrors.LoggingLevelInsufficient
        else:
            return self.bot.get_channel(log_channel)

    async def dispatch_embed(self, channel: discord.TextChannel, embed: discord.Embed):
        embed.set_footer(text="{:%m/%d/%Y %H:%M:%S}".format(datetime.now()))
        return await channel.send(embed=embed)

    async def guild_update(self, guild: discord.Guild, diff: list):
        log_channel = await self.check_logging_enabled(guild, self.min_level)
        embed = discord.Embed(title="Server Updated", color=discord.Color.blue())
        description = [f"{item.type.replace('_', ' ').title()}\n> Server {item.type.replace('_', ' ')} changed "
                       f"from `{item.before}` ⟶ `{item.after}`\n" for item in diff if diff]
        embed.description = "\n".join(description)
        return await self.dispatch_embed(log_channel, embed) if diff else None


class GuildChannelEventDispatcher(GuildGenericEventDispatcher):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(bot)

    def get_channel_string(self, channel, event_type: str = "none"):
        return f"Channel {CE[str(channel.type)]}{channel.mention if event_type != 'deleted' and str(channel.type) == 'text' else channel.name}"

    async def guild_channel_attr_update(self, channel: discord.abc.GuildChannel, diff: list):
        log_channel = await self.check_logging_enabled(channel.guild, self.min_level)
        embed = discord.Embed(title="Channel Updated", color=discord.Color.blue())
        description = [f"{item.type.replace('_', ' ').title()}\n> Channel {item.type.replace('_', ' ')} changed "
                       f"from `{item.before}` ⟶ `{item.after}`\n" for item in diff if diff]
        embed.description = f"{self.get_channel_string(channel)}\n\n" + "\n".join(description)
        return await self.dispatch_embed(log_channel, embed) if diff else None

    async def guild_channels_update(self, channel: discord.abc.GuildChannel, event_type: str):
        log_channel = await self.check_logging_enabled(channel.guild, self.min_level)

        embed = discord.Embed(title=f"Channel {event_type.title()}",
                              description=f"{self.get_channel_string(channel, event_type)} was {event_type.lower()}",
                              color=discord.Color.blue() if event_type == "created" else discord.Color.dark_red())
        return await self.dispatch_embed(log_channel, embed)

    async def channel_pins_update(self, channel):
        return
