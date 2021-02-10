import os
import re
from typing import List, Union

import discord
import lavalink
from discord.ext import commands
from utils import (EmbedPaginator, FieldPaginator, GlobalCMDS, context,
                   customerrors, premium)
from utils.musicutils import *

VALID_TS = re.compile(r"([\d]*:[\d]{1,2}:[\d]{1,2})|([\d]{1,2}:[\d]{1,2})|([\d]*)")
SCARED_IDS: List[int]
BYPASS_BIND = [
    "bind",
    "musiccacheexport",
    "musiccacheevict",
    "musiccacheclear",
    "musiccacherestore",
]


class Music(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot) -> None:
        self.bot = bot
        self.gcmds = GlobalCMDS(self.bot)
        self.bot.loop.create_task(self.init_music(bot))
        self.track_hook: function

    async def init_music(self, bot: commands.AutoShardedBot):
        global SCARED_IDS
        await self.bot.wait_until_ready()
        async with self.bot.db.acquire() as con:
            await con.execute("CREATE TABLE IF NOT EXISTS music(guild_id bigint PRIMARY KEY, channel_id bigint, panel_id bigint)")
            await con.execute("CREATE TABLE IF NOT EXISTS playlists(id SERIAL, user_id bigint, playlist_name text PRIMARY KEY, urls text[])")
        if not hasattr(bot, 'lavalink'):
            bot.lavalink = lavalink.Client(self.bot.user.id, player=MBPlayer)
            data = [self.gcmds.env_check(key) for key in [f"LAVALINK_{info}" for info in "IP PORT PASSWORD".split()]]
            if not all(data):
                raise ValueError("Make sure your server IP, port, and password are in the .env file")
            bot.lavalink.add_node(*data, 'na', 'default-node', name="lavalink", reconnect_attempts=-1)
            self.bot.add_listener(bot.lavalink.voice_update_handler, 'on_socket_response')
        self.bot.lavalink = bot.lavalink
        self.bot.lavalink.add_event_hook(self.track_hook)
        SCARED_IDS = [int(id) for id in os.getenv("SCARED_IDS").split(",")]

    def cog_unload(self) -> None:
        self.bot.lavalink._event_hooks.clear()

    async def cog_check(self, ctx):
        return True if ctx.command.name in BYPASS_BIND else await context.music_bind(ctx)

    async def connect_to(self, guild: Union[discord.Guild, int], channel: Union[discord.VoiceChannel, int, None], mute: bool = False, deafen: bool = True) -> None:
        if isinstance(guild, int):
            guild = self.bot.get_guild(guild)
        if isinstance(channel, int):
            channel = guild.get_channel(channel)
        if channel and any([member.id in SCARED_IDS for member in channel.members if member.bot]):
            raise customerrors.OtherMBConnectedError()
        await guild.change_voice_state(channel=channel, self_mute=mute, self_deaf=deafen)
        player = get_player(self.bot, None, guild=guild)
        player.voice_channel_id = channel.id if channel is not None else None

    @commands.command(aliases=["mc", "mci"],
                      desc="Get MarwynnBot's lavalink cache details",
                      usage="musiccacheinfo (query)",
                      note="If `(query)` is unspecified, it will display general cache details")
    async def musiccacheinfo(self, ctx, *, query: str = None):
        return await ctx.channel.send(embed=MBPlayer.get_cache_info(query=query))

    @commands.command(aliases=["mcexp"],
                      desc="Exports MarwynnBot's lavalink cache",
                      usage="musiccacheexport [format] (query)",
                      uperms=["Bot Owner Only"],
                      note="Supported formats are JSON and PICKLE")
    @commands.is_owner()
    async def musiccacheexport(self, ctx, format: str = None, *, query: str = None):
        if not format or not format.lower() in ["json", "pickle"]:
            embed = discord.Embed(title="Invalid Format",
                                  description=f"{ctx.author.mention}, please pick a either JSON or PICKLE as the export format",
                                  color=discord.Color.dark_red())
        else:
            embed = await MBPlayer.export_cache(query=query, format=format.lower())
        return await ctx.channel.send(embed=embed)

    @commands.command(aliases=["mcev"],
                      desc="Evict a query from MarwynnBot's lavalink cache",
                      usage="musiccacheevict [query]",
                      uperms=["Bot Owner Only"])
    @commands.is_owner()
    async def musiccacheevict(self, ctx, *, query: str):
        return await ctx.channel.send(embed=MBPlayer.evict_cache(query))

    @commands.command(aliases=["mcc"],
                      desc="Clears the music cache",
                      usage="musiccacheclear",
                      uperms=["Bot Owner Only"],
                      note="A backup of the current cache will be made in JSON format")
    @commands.is_owner()
    async def musiccacheclear(self, ctx):
        await MBPlayer.export_cache()
        return await ctx.channel.send(embed=MBPlayer.evict_cache("", clear_all=True))

    @commands.command(aliases=["mcr"],
                      desc="Restore an exported lavalink cache state",
                      usage="musiccacherestore [filename]",
                      uperms=["Bot Owner Only"],
                      note="Incluce the extension")
    @commands.is_owner()
    async def musiccacherestore(self, ctx, filename: str):
        return await ctx.channel.send(embed=await MBPlayer.restore_cache(filename))

    @commands.command(desc="Binds the music commands to a channel",
                      usage="bind (channel)",
                      uperms=["Manage Server"],
                      note="If `(channel)` is not specified, the current channel will be used")
    @commands.has_permissions(manage_guild=True)
    async def bind(self, ctx, channel: discord.TextChannel = None):
        if not channel:
            channel = ctx.channel
        if not isinstance(channel, discord.TextChannel):
            converter = commands.TextChannelConverter()
            channel = await converter.convert(ctx, channel)
        if not isinstance(channel, discord.TextChannel):
            embed = discord.Embed(title="Invalid Channel",
                                  description=f"{ctx.author.mention}, please specify a valid channel",
                                  color=discord.Color.dark_red())
        else:
            async with self.bot.db.acquire() as con:
                entry = await con.fetchval(f"SELECT guild_id FROM music WHERE guild_id={ctx.guild.id}")
                if not entry:
                    op = f"INSERT INTO music(guild_id, channel_id) VALUES ({ctx.guild.id}, {channel.id})"
                else:
                    op = f"UPDATE music SET channel_id={channel.id} WHERE guild_id={ctx.guild.id}"
                await con.execute(op)
            embed = discord.Embed(title="Music Channel Bound",
                                  description=f"The music channel was bound to {channel.mention}",
                                  color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @commands.command(desc="Makes MarwynnBot join the same voice channel you're in",
                      usage="join",
                      note="You may only use this when you are connected to a voice channel")
    @ensure_voice()
    async def join(self, ctx):
        player = get_player(self.bot, ctx)
        embed = discord.Embed(
            title=f"Successfully {'Joined' if not player.is_connected else 'Moved to'} Voice Channel",
            description=f"{ctx.author.mention}, I have {'joined' if not player.is_connected else 'moved to'} {ctx.author.voice.channel.name}",
            color=discord.Color.blue()
        ).set_thumbnail(
            url="https://vignette.wikia.nocookie.net/mario/images/0/04/Music_Toad.jpg/revision/latest/top-crop/width/500/height/500?cb=20180812231020"
        )
        await self.connect_to(ctx.guild, ctx.author.voice.channel)
        return await ctx.channel.send(embed=embed)

    @commands.command(desc="Makes MarwynnBot play a song or the current queue",
                      usage="play (query)",
                      note="If there are any songs in queue, `(query)` can be unspecified to start playing the first song in queue")
    @ensure_voice(should_connect=True)
    async def play(self, ctx, *, query: str = None):
        player = get_player(self.bot, ctx)
        if not query:
            if player.queue:
                if not player.is_playing:
                    return await player.play()
                else:
                    embed = discord.Embed(
                        title="No Query",
                        description=f"{ctx.author.mention}, you didn't specify a query. Please do so if you wish to queue a track. "
                        "If you wish to skip the current track, vote by executing `m!skip`",
                        color=discord.Color.dark_red()
                    )
                    return await ctx.channel.send(embed=embed)
            else:
                return await no_queue(ctx)

        return await play_or_queue_tracks(ctx, player, query)

    @commands.command(aliases=["q"],
                      desc="List the current queue or queue a song or playlist",
                      usage="queue (query)",
                      note="You must be in the same voice channel as MarwynnBot")
    @ensure_voice(should_connect=True)
    async def queue(self, ctx, *, query: str = None):
        player = get_player(self.bot, ctx)
        if query is not None:
            return await play_or_queue_tracks(ctx, player, query)

        embed = discord.Embed(description="**Queue:**\n", color=discord.Color.blue())
        if player.is_playing:
            embed.description = f"**Now Playing:** [{player.current.title}]({player.current.uri})\n\n" + \
                embed.description
        queue_length = len(player.queue)
        title_extra = f": {queue_length} Track{'s' if queue_length != 1 else ''}" if queue_length else ""
        embed.title = f"Current Queue{title_extra}"

        description = [
            f"[{track.title}]({track.uri}) - {track.author} - {track_duration(track.duration)}" for track in player.queue] if player.queue else ["Nothing queued"]
        embed.set_author(
            name=f"Queue Duration: {total_queue_duration(player.queue)}",
            icon_url=ctx.me.avatar_url
        )
        return await EmbedPaginator(
            ctx,
            entries=description,
            per_page=10,
            show_entry_count=True,
            embed=embed,
            description=embed.description
        ).paginate()

    @commands.command(aliases=["qc", "clearqueue", "cq"],
                      desc="Clears the current queue",
                      usage="clearqueue",
                      uperms=["Manage Server"])
    @commands.has_permissions(manage_guild=True)
    async def queueclear(self, ctx):
        player = get_player(self.bot, ctx)
        if not player.queue:
            embed = discord.Embed(title="Nothing in Queue",
                                  description=f"{ctx.author.mention}, the queue is already empty",
                                  color=discord.Color.blue())
        else:
            player.queue.clear()
            embed = discord.Embed(title="Queue Cleared",
                                  description=f"{ctx.author.mention}, I have cleared the queue",
                                  color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @commands.command(desc="Bypass the voting system to forcefully stop music playback and clear the queue",
                      usage="forcestop",
                      uperms=["Manage Server` or `Mute Members` or `Deafen Members` or `Move Members"])
    @check_perms(req_perms={
        "manage_guild": True,
        "mute_members": True,
        "deafen_members": True,
        "move_members": True,
    }, mode="any")
    async def forcestop(self, ctx):
        player = get_player(self.bot, ctx)
        embed = discord.Embed(title="Error",
                              color=discord.Color.dark_red())
        if not player.is_connected:
            embed.description = f"{ctx.author.mention}, I am not currently in a voice channel"
        elif not player.queue and not player.is_playing:
            embed.description = f"{ctx.author.mention}, I'm not playing anything and my queue is already empty"
        else:
            await player.stop()
            await player.close_session()
            embed.title = "Player Stopped"
            embed.description = f"{ctx.author.mention}, I have stopped the player and cleared the queue"
            embed.color = discord.Color.blue()
        return await ctx.channel.send(embed=embed)

    @commands.command(aliases=["fvl"],
                      desc="Makes MarwynnBot leave the voice channel it is connected to",
                      usage="forcevoiceleave",
                      uperms=["Manage Server` or `Mute Members` or `Deafen Members` or `Move Members"])
    @ensure_voice()
    @check_perms(req_perms={
        "manage_guild": True,
        "mute_members": True,
        "deafen_members": True,
        "move_members": True,
    }, mode="any")
    async def forcevoiceleave(self, ctx):
        player = get_player(self.bot, ctx)
        if player.is_playing:
            player.queue.appendleft(player.current)
            await player.stop()
        await self.connect_to(ctx.guild, None)
        embed = discord.Embed(
            title="Disconnected",
            description=f"{ctx.author.mention}, I have disconnected from the voice channel",
            color=discord.Color.blue()
        ).set_thumbnail(
            url="https://i.pinimg.com/originals/56/3d/72/563d72539bbd9fccfbb427cfefdee05a.png"
        ).set_footer(
            text=f"Requested by: {ctx.author.display_name}"
        )
        return await ctx.channel.send(embed=embed)

    @commands.command(desc="Adjusts the music player volume",
                      usage="volume (0 - 100)",
                      uperms=["Manage Server` or `Mute Members` or `Deafen Members` or `Move Members"],
                      note="Any volume adjustment will affect the relative volume for everyone currently connected in the voice channel")
    @ensure_voice()
    @check_perms(req_perms={
        "manage_guild": True,
        "mute_members": True,
        "deafen_members": True,
        "move_members": True,
    }, mode="any")
    async def volume(self, ctx, amount: int = None):
        player = get_player(self.bot, ctx)
        embed = discord.Embed(title="Current Player Volume",
                              color=discord.Color.blue())
        if amount is None:
            embed.description = f"Player volume is currently {player.volume}%"
        elif 0 <= amount <= 100:
            await player.set_volume(amount)
            embed.description = f"Player volume has been set to {player.volume}%"
        else:
            embed.title = "Invalid Volume Setting"
            embed.description = f"{ctx.author.mention}, the volume must be between 0 and 100"
            embed.color = discord.Color.dark_red()
        return await ctx.channel.send(embed=embed)

    @commands.command(aliases=['eq', 'equalizer'],
                      desc="Adjusts the music player's equaliser",
                      usage="""equaliser (band) (gain)

Examples:
Set band 1 to +1 gain:
m!equaliser 1, 1

Set bands 1, 2, 4, 6, and 9 to -0.1 gain
m!equaliser 1,2,4,6,9 -0.1

Set all bands to +0.69 gain
m!equaliser all 0.69

Set bands 10, 12, and 14 to -0.25, 0, and +0.25 gain respectively
m!equaliser 10,12,14 -0.25,0,0.25

Reset equaliser (two options, functionally equivalent):
m!equaliser reset
or
m!equaliser all 0
""",
                      uperms=["Manage Server` or `Mute Members` or `Deafen Members` or `Move Members"],
                      note="To adjust gain on specific bands, you must specify both `(band)` and `(gain)`. "
                      "`(band)` may be between 1 and 15 inclusive, comma separated integers between 1 and 15 inclusive, or \"all\" to modify all bands at once. "
                      "`(gain)` may be a decimal between -0.25 and 1.00 inclusive, comma separated decimals between -0.25 and 1.00 inclusive. "
                      "You can set multiple bands to one gain by specifying comma separated `(band)` values and only one `(gain)` value"
                      "Doing `m!equaliser reset` will reset the gain for all bands to default (0). "
                      "The amount of comma separated `(band)` and `(gain)` arguments must be the same, otherwise, an error message will be returned.\n\n"
                      "To view the equaliser bands, omit both the `(band)` and `(gain)` arguments. To view the gain for a specific band, "
                      "you must specify `(band)`, but not `(gain)`")
    @ensure_voice()
    @check_perms(req_perms={
        "manage_guild": True,
        "mute_members": True,
        "deafen_members": True,
        "move_members": True,
    }, mode="any")
    async def equaliser(self, ctx, band: str = None, gain: str = None):
        player = get_player(self.bot, ctx)
        op = "adjust"
        if band is None:
            band = gain = None
            op = "display"
        elif band.lower() == "reset":
            band = gain = None
            op = "reset"
        elif band.lower() == "all":
            if gain is None:
                raise customerrors.EQGainError(ctx, f"you must provide a valid gain value. To reset the equaliser, do `{await self.gcmds.prefix(ctx)}equaliser reset`")
            band = [num for num in range(15)]
            try:
                if not -0.25 <= float(gain) <= 1.00:
                    raise customerrors.EQGainError(ctx, f"{gain} is not between -0.25 and 1.00 inclusive")
                gain = [float(gain) for _ in range(15)]
            except ValueError as e:
                raise customerrors.EQGainError(ctx, f"{gain} is not a valid gain value")
        else:
            try:
                if not "," in band:
                    band = int(band) - 1
                    if not 0 <= band <= 14:
                        raise customerrors.EQBandError(ctx, f"{band} is not between 1 and 15 inclusive")
                else:
                    band = [int(b) - 1 for b in band.split(",")]
                    if not all([0 <= b <= 14 for b in band]):
                        raise customerrors.EQBandError(
                            ctx, f"all supplied band numbers must be between 1 and 15 inclusive"
                        )
            except ValueError as e:
                raise customerrors.EQBandError(ctx) from e
            finally:
                gain = check_gain(ctx, band, gain)
        embed = (await player.process_eq(band=band, gain=gain, op=op)).set_footer(
            text=f"Requested by: {ctx.author.display_name}\nChanges may not be applied immediately. Please wait around 2 - 10 seconds.",
            icon_url=ctx.author.avatar_url
        )
        return await ctx.channel.send(embed=embed)

    @commands.command(desc="Toggle your vote to pause the player",
                      usage="pause",
                      note="The player will pause once the vote threshold has been crossed.")
    @ensure_voice()
    async def pause(self, ctx):
        return await ctx.channel.send(embed=await process_votes(self, self.bot, ctx, "pause"))

    @commands.command(desc="Toggle your vote to unpause the player",
                      usage="unpause",
                      note="The player will unpause once the vote threshold has been crossed.")
    @ensure_voice()
    async def unpause(self, ctx):
        return await ctx.channel.send(embed=await process_votes(self, self.bot, ctx, "unpause"))

    @commands.command(desc="Toggle your vote to rewind to the previous track",
                      usage="rewind",
                      note="The player will rewind to the previous track once the vote threshold has been crossed.")
    @ensure_voice()
    async def rewind(self, ctx):
        return await ctx.channel.send(embed=await process_votes(self, self.bot, ctx, "rewind"))

    @commands.command(desc="Toggle your vote to skip to the next track",
                      usage="skip",
                      note="The player will skip to the next track once the vote threshold has been crossed.")
    @ensure_voice()
    async def skip(self, ctx):
        return await ctx.channel.send(embed=await process_votes(self, self.bot, ctx, "skip"))

    @commands.command(desc="Toggle your vote to stop the player",
                      usage="stop",
                      note="The player will stop once the vote threshold has been crossed.")
    @ensure_voice()
    async def stop(self, ctx):
        return await ctx.channel.send(embed=await process_votes(self, self.bot, ctx, "stop"))

    @commands.command(desc="Toggle your vote to make MarwynnBot leave the current voice channel",
                      usage="leave",
                      note="The player will leave once the vote threshold has been crossed, regardless of whether or not it is currently playing a track")
    @ensure_voice()
    async def leave(self, ctx):
        return await ctx.channel.send(embed=await process_votes(self, self.bot, ctx, "leave"))

    @commands.command(desc="Set the player's track loop status",
                      usage="loop (times)",
                      note="`(times)` can be a positive integer value, \"forever\" to loop indefinitely, or \"stop\" to stop looping")
    @ensure_voice()
    async def loop(self, ctx, *, amount: str = None):
        player = get_player(self.bot, ctx)
        if amount is None:
            embed = discord.Embed(
                title="Track Loop Status",
                description=f"{ctx.author.mention}, the current track is set to {player.loop_status}",
                color=discord.Color.blue()
            )
        else:
            embed = player.set_loop_times(amount).set_footer(
                text=f"Requested by: {ctx.author.display_name}",
                icon_url=ctx.author.avatar_url
            )
        return await ctx.channel.send(embed=embed)

    @commands.command(desc="Seek to a specific timestamp in the current track",
                      usage="seek ( (+ | -) hours:minutes:seconds|minutes:seconds|seconds)",
                      note="There is no need to zero pad values. Please separate intervals with a colon \":\" character. "
                      "0 hours may be omitted, but 0 minutes or seconds must be specified (no need for padding). "
                      "Specifying plus (+) or minus (-) will add or subtract time from the current timestamp "
                      "(i.e, `m!seek -60` to seek back 60 seconds)")
    @ensure_voice()
    async def seek(self, ctx, *, timestamp: str = None):
        if timestamp.lower() in ["shortcuts", "sc", "help", "h"]:
            embed = discord.Embed(
                title="Seek Shortcuts",
                description=f"{ctx.author.mention}, here are valid seek shortcut words that can be used as time arguments:\n\n" +
                "\n".join([
                    "`start`, `s` - seek to the start of the current track",
                    "`middle`, `m` - seek to the middle of the current track",
                    "`end`, `e` - seek to the end of the current track (analogous to `m!skip`)"
                ]),
                color=discord.Color.blue()
            )
            return await ctx.channel.send(embed=embed)
        player = get_player(self.bot, ctx)
        if timestamp.lower() in ["start", "s", "middle", "m", "end", "e"]:
            if player.current:
                timestamp = {
                    "start": "0",
                    "s": "0",
                    "middle": f"{player.current.duration // 2000}",
                    "m": f"{player.current.duration // 2000}",
                    "end": f"{player.current.duration // 1000}",
                    "e": f"{player.current.duration // 1000}",
                }.get(timestamp.lower(), timestamp)
        timestamp = timestamp.replace(" ", "")
        sign = timestamp[0] if timestamp[0] in "+-" else None
        if sign:
            timestamp = timestamp[1:]
        embed = discord.Embed(title="Seek ", description=f"{ctx.author.mention}, ")
        failed = True
        if player.current and player.current.is_seekable and VALID_TS.fullmatch(timestamp):
            try:
                milliseconds = int(timestamp) * 1000
            except ValueError:
                try:
                    tokens = [int(value) for value in timestamp.split(":", 2)]
                    if len(tokens) > 3:
                        raise ValueError("Invalid seek timestamp format")
                except ValueError:
                    embed.description += f"`{timestamp}` is an invalid timestamp format"
                    return await ctx.channel.send(embed=embed)

                if len(tokens) == 2:
                    milliseconds = (tokens[0] * 60 + tokens[1]) * 1000
                else:
                    milliseconds = (tokens[0] * 3600 + tokens[1] * 60 + tokens[2]) * 1000

            seek_timestamp = await player.seek(milliseconds, sign=sign)
            failed = not isinstance(seek_timestamp, int)
            embed.description += str(
                f"I have successfully seeked {'to' if not sign else 'back by' if sign == '-' else 'forward by'} {track_duration(milliseconds)}" if not failed
                else seek_timestamp
            )
        else:
            embed.description += str(
                "I cannot seek when I am not currently playing any track" if not player.is_playing
                else "this track doesn't support seeking" if not player.current.is_seekable
                else f"`{timestamp}` is an invalid timestamp format"
            )
        embed.title += "Failed" if failed else "Successful"
        embed.color = discord.Color.dark_red() if failed else discord.Color.blue()
        if not failed:
            embed.set_footer(
                text=f"Requested by: {ctx.author.display_name}",
                icon_url=ctx.author.avatar_url
            )
        return await ctx.channel.send(embed=embed)

    @commands.group(invoke_without_command=True,
                    aliases=["playlists", "pl"],
                    desc="Shows help for the playlist command and subcommands",
                    usage="playlist (subcommand)",)
    async def playlist(self, ctx):
        return await get_playlist_help(self, ctx)

    @playlist.command(name="help",
                      aliases=["h"])
    async def playlist_help(self, ctx):
        return await get_playlist_help(self, ctx)

    @playlist.command(name="list",
                      aliases=["ls"])
    async def playlist_list(self, ctx, *, identifier: str = None):
        embed = discord.Embed(title="Your Playlists 🎶" if not identifier else "Playlist Details 🎶",
                              color=discord.Color.blue())
        loading_msg: discord.Message = await ctx.channel.send(embed=discord.Embed(
            title="Loading Playlist Details...",
            color=discord.Color.blue()
        )) if identifier is not None else None
        playlists = await get_playlist(self, ctx, identifier=identifier, ret=f"all{'-info' if identifier is not None else ''}")
        if not playlists:
            embed.description = f"{ctx.author.mention}, you don't have any saved playlists"
            return await ctx.channel.send(embed=embed)

        if identifier:
            playlist = playlists[0]
            description = "\n".join([
                f"**ID:** {playlist.id}",
                f"**Name:** {playlist.name}",
                f"**Author:** <@{playlist.user_id}>",
                f"**Duration:** {total_queue_duration(playlist.tracks)}"
            ]) + "\n\n"
            entries = [
                f"[{track.title}]({track.uri}) - {track.author} - [{track_duration(track.duration)}]" if track else "No Data Available" for track in playlist.tracks
            ]
            pag = EmbedPaginator(
                ctx,
                entries=entries,
                per_page=10,
                show_entry_count=True,
                embed=embed,
                description=description,
                provided_message=loading_msg
            )
        else:
            template = "**{}:** *ID: {}* - {} Track{} 💽"
            entries = [
                (
                    playlist.name,
                    template.format(
                        index,
                        playlist.id,
                        len(playlist.urls),
                        's' if len(playlist.urls) != 1 else ''
                    ),
                    False
                ) for index, playlist in enumerate(playlists, 1)
            ]
            pag = FieldPaginator(ctx, entries=entries, embed=embed)
        await pag.paginate()

    @premium.is_premium()
    @playlist.command(name="queue",
                      aliases=["q"])
    @ensure_voice(should_connect=True)
    async def playlist_queue(self, ctx, *, identifier: str):
        playlist = await prep_play_queue_playlist(self, ctx, identifier)
        return await play_or_queue_playlist(self.bot, ctx, get_player(self.bot, ctx), playlist)

    @premium.is_premium()
    @playlist.command(name="play",
                      aliases=["p"])
    @ensure_voice(should_connect=True)
    async def playlist_play(self, ctx, *, identifier: str):
        playlist = await prep_play_queue_playlist(self, ctx, identifier)
        return await play_or_queue_playlist(self.bot, ctx, get_player(self.bot, ctx), playlist, play=True)

    @premium.is_premium()
    @playlist.command(name="save",
                      aliases=["s"])
    async def playlist_save(self, ctx, *, urls: str = None):
        player = get_player(self.bot, ctx)
        return await save_playlist(self, ctx, urls.split(",") if urls else [track.uri for track in player.queue])

    @premium.is_premium()
    @playlist.command(name="append",
                      aliases=["add", "a"])
    async def playlist_append(self, ctx, id: int, *, urls: str = None):
        player = get_player(self.bot, ctx)
        return await modify_playlist(self, ctx, id, urls=urls.split(",") if urls else [track.uri for track in player.queue], op_type="append")

    @premium.is_premium()
    @playlist.command(name="replace",
                      aliases=["repl", "rp"])
    async def playlist_replace(self, ctx, id: int, *, urls: str = None):
        player = get_player(self.bot, ctx)
        return await modify_playlist(self, ctx, id, urls=urls.split(",") if urls else [track.uri for track in player.queue], op_type="replace")

    @premium.is_premium()
    @playlist.command(name="rename",
                      aliases=["ren", "rn"])
    async def playlist_rename(self, ctx, id: int, *, new_name: str = None):
        return await modify_playlist(self, ctx, id, name=new_name, op_type="rename")

    @premium.is_premium()
    @playlist.command(name="delete",
                      aliases=["del", "d"])
    async def playlist_delete(self, ctx, *, identifier: str):
        return await delete_playlist(self, ctx, identifier)


def setup(bot: commands.AutoShardedBot):
    bot.add_cog(Music(bot))


Music.track_hook = track_hook
