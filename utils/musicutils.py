import asyncio
import functools
import re
from math import ceil
from typing import List, NamedTuple, Tuple, Union

import discord
import lavalink
from asyncpg.exceptions import UniqueViolationError
from discord.errors import Forbidden, HTTPException, NotFound
from discord.ext.commands import AutoShardedBot, Context
from lavalink.models import AudioTrack

from utils.paginator import EmbedPaginator

from . import EntryData, SubcommandHelp
from .customerrors import EQGainError, EQGainMismatch
from .mbplayer import MBPlayer

__all__ = (
    "MBPlayer",
    "ensure_voice",
    "check_perms",
    "track_hook",
    "get_player",
    "no_queue",
    "total_queue_duration",
    "track_duration",
    "process_votes",
    "prep_play_queue_playlist",
    "play_or_queue_tracks",
    "play_or_queue_playlist",
    "get_playlist_help",
    "get_playlist",
    "save_playlist",
    "modify_playlist",
    "delete_playlist",
    "check_gain",
    "PLAYER_REACTIONS",
)

PLAYER_REACTIONS = ["⏪", "⏯", "⏩", "⏹"]
CONF_REACTIONS = ["✅", "🛑"]
CONF_MSG = "{}, react with ✅ to confirm, or 🛑 to cancel"
BLUE = discord.Color.blue()
RED = discord.Color.dark_red()
url_rx = re.compile(r'https?://(?:www\.)?.+')
opp_source = {
    "yt": "sc",
    "sc": "yt",
}


class Playlist(NamedTuple):
    name: str
    urls: List[str]
    user_id: int
    id: int
    tracks: List[AudioTrack] = None


class InvalidURL(Exception):
    def __init__(self, *args, url: str = None) -> None:
        super().__init__(*args)
        self.url = url


class InvalidName(Exception):
    def __init__(self, *args, name: str = None) -> None:
        super().__init__(*args)
        self.name = name


class NonexistentPlaylist(Exception):
    def __init__(self, *args, id: int = None, name: str = None) -> None:
        super().__init__(*args)
        self.err_msg = "{}, no playlist exists with "
        self.err_msg += "a name of {name}" if name else f"an id of {id}"


class NotPlaylistOwner(Exception):
    def __init__(self, *args, id: int = None) -> None:
        super().__init__(*args)
        self.id = id


class NoNameSpecified(Exception):
    pass


class SetupCancelled(Exception):
    def __init__(self, *args, setup: str = None) -> None:
        super(SetupCancelled, self).__init__(*args)
        self.setup = setup


def ensure_voice(should_connect: bool = False):
    def wrapper(func):
        @functools.wraps(func)
        async def actual_deco(self, *args, **kwargs):
            ctx: Context = args[0]
            player = get_player(self.bot, ctx)
            embed = None

            if not ctx.author.voice or not ctx.author.voice.channel:
                embed = discord.Embed(title="Not in Voice Channel",
                                      description=f"{ctx.author.mention}, please join a voice channel first!",
                                      color=RED)
            elif not player.is_connected:
                permissions = ctx.author.voice.channel.permissions_for(ctx.me)
                if not all([permissions.connect, permissions.speak]):
                    embed = discord.Embed(title="Insufficient Bot Permissions",
                                          description=f"{ctx.author.mention}, please make sure I have the `connect` and "
                                          "`speak` permissions for your current voice channel",
                                          color=RED)
                else:
                    player.voice_channel_id = ctx.author.voice.channel.id
                    player.text_channel = ctx.channel
                    if should_connect:
                        await self.connect_to(ctx.guild, ctx.author.voice.channel)
                    return await func(self, *args, **kwargs)
            elif ctx.command.name == "join":
                if not player.is_playing:
                    return await func(self, *args, **kwargs)
                embed = discord.Embed(title="Cannot Switch Voice Channels",
                                      description=f"{ctx.author.mention}, I cannot switch voice channels while I am playing music",
                                      color=RED)
            elif player.voice_channel_id is None or player.voice_channel_id != ctx.author.voice.channel.id:
                embed = discord.Embed(title="Different Voice Channels",
                                      description=f"{ctx.author.mention}, I'm already in a voice channel",
                                      color=RED)
            else:
                return await func(self, *args, **kwargs)
            return await ctx.channel.send(embed=embed)
        return actual_deco
    return wrapper


def check_perms(req_perms: dict, mode: str = "all"):
    def wrapper(func):
        @functools.wraps(func)
        async def actual_deco(self, *args, **kwargs):
            ctx: Context = args[0]
            perms = ctx.author.guild_permissions
            method = {
                "all": all,
                "any": any,
            }.get(mode, all)
            if not method(getattr(perms, key) == value for key, value in req_perms.items()):
                embed = discord.Embed(
                    title="Insufficient Permissions",
                    description=f"{ctx.author.mention}, you lack the required permissions to execute this command. Do `m!help {ctx.command.name}` to see the required permissions",
                    color=RED
                )
                return await ctx.channel.send(embed=embed)
            return await func(self, *args, **kwargs)
        return actual_deco
    return wrapper


async def track_hook(self, event: lavalink.events.Event):
    if isinstance(event, lavalink.events.QueueEndEvent):
        await self.connect_to(int(event.player.guild_id), None)
        text_channel: discord.TextChannel = event.player.text_channel
        embed = discord.Embed(title="Finished Playing",
                              description="I have finished playing all tracks in queue and will now disconnect",
                              color=BLUE)
        return await text_channel.send(embed=embed)
    elif isinstance(event, lavalink.events.NodeConnectedEvent):
        print(f'Connected to Lavalink Node "{event.node.name}"@{event.node.host}:{event.node.port}')
    elif isinstance(event, lavalink.events.NodeDisconnectedEvent):
        print(f'Disconnected from Node "{event.node.name}" with code {event.code}, reason: {event.reason}')
    elif isinstance(event, lavalink.events.TrackStartEvent):
        text_channel: discord.TextChannel = event.player.text_channel
        track: AudioTrack = event.track
        requester: discord.User = self.bot.get_user(track.requester)
        queue_length = len(event.player.queue)
        queue_rem = f"{queue_length} Track{'s' if queue_length != 1 else ''} - about {_get_queue_total_duration(event.player.queue)}" if queue_length > 0 else "nothing"
        loop_count = event.player.loop_count
        embed = discord.Embed(
            title=f"Now Playing:",
            description=f"[{track.title}]({track.uri}) - {track.author} - {_get_track_duration_timestamp(track.duration)}",
            color=BLUE
        ).set_footer(
            text="\n".join([
                f"Requested by: {requester.display_name}",
                f"Author: {track.author}",
                f"Current Queue: {queue_rem}",
            ]) + f"\nLooped {loop_count} time{'s' if loop_count != 1 else ''}" if loop_count >= 1 else '',
            icon_url=requester.avatar_url
        ).set_image(
            url=_get_track_thumbnail(track)
        )
        await text_channel.send(embed=embed)
    else:
        pass


def get_player(bot: AutoShardedBot, ctx: Context, guild: discord.Guild = None) -> MBPlayer:
    return bot.lavalink.player_manager.create(
        ctx.guild.id if ctx else guild.id,
        endpoint=str(ctx.guild.region if ctx else guild.region)
    )


async def no_queue(ctx: Context) -> discord.Message:
    embed = discord.Embed(title="Nothing in Queue",
                          description=f"{ctx.author.mention}, please add a song to the queue first",
                          color=RED)
    return await ctx.channel.send(embed=embed)


def _process_op_threshold(bot: AutoShardedBot, ctx: Context, op: str) -> Tuple[int, int, bool, str]:
    player = get_player(bot, ctx)
    voice_channel: discord.VoiceChannel = ctx.author.voice.channel
    members = [member for member in voice_channel.members if not member.bot]
    current_member_count = len(members)
    vote_op: List[int] = player.votes.get(op, [])
    if ctx.author.id in vote_op:
        vote_op.remove(ctx.author.id)
        action = "rescinded"
    else:
        vote_op.append(ctx.author.id)
        action = "placed"
    current = len(vote_op)
    if current_member_count <= 2:
        threshold = 1
    else:
        threshold = int(ceil(current_member_count / 2))
    allow_op = True if current >= threshold else False
    return current, threshold, allow_op, action


async def process_votes(self,
                        bot: AutoShardedBot,
                        ctx: Context,
                        op_name: str) -> discord.Embed:
    ALLOW_TEMPLATES = {
        "pause": "The player has been paused",
        "unpause": "The player has been unpaused",
        "rewind": "The player has rewound to the previous track",
        "skip": "The player has skipped to the next track",
        "stop": "The player has stopped and the queue has been cleared",
        "leave": "The player has stopped and I have left the current voice channel. The queue has not been cleared."
    }
    NOT_ALLOW_TEMPLATES = {
        "pause": "pause the player",
        "unpause": "unpause the player",
        "rewind": "rewind to the previous track",
        "skip": "skip to the next track",
        "stop": "stop the player and clear the queue",
        "leave": "make MarwynnBot leave the current voice channel without clearing the queue"
    }
    current, threshold, allow_op, action = _process_op_threshold(bot, ctx, op_name)
    embed = discord.Embed(title=f"Vote {op_name.title()}", color=BLUE)
    if allow_op:
        player = get_player(bot, ctx)
        embed.description = ALLOW_TEMPLATES.get(op_name)
        if op_name == "pause":
            await player.set_pause(True)
            embed.description += "\n\nDo `m!unpause` to vote to unpause the player"
        elif op_name == "unpause":
            await player.set_pause(False)
        elif op_name == "rewind":
            player.set_loop_times(0)
            temp_embed = player.enable_rewind()
            if temp_embed is None:
                await player.play()
            embed = embed if temp_embed is None else temp_embed
        elif op_name == "skip":
            player.set_loop_times(0)
            res = await player.play()
            if res is None:
                return discord.Embed(
                    title="Finished Playing",
                    description="I have finished playing all tracks in queue and will now disconnect",
                    color=BLUE
                )
        elif op_name == "stop":
            await player.stop()
            await player.close_session()
        elif op_name == "leave":
            if player.is_playing:
                player.queue.appendleft(player.current)
                await player.stop()
            await self.connect_to(ctx.guild, None)
            embed.set_thumbnail(
                url="https://i.pinimg.com/originals/56/3d/72/563d72539bbd9fccfbb427cfefdee05a.png"
            )
            return embed
    else:
        req = threshold - current
        embed.description = f"{ctx.author.mention}, you've {action} your vote to {NOT_ALLOW_TEMPLATES.get(op_name)}"
        embed.set_footer(
            text=f"Current Votes: {current}\nRequired Votes: {threshold}\nNeed {req} more vote{'s' if req != 1 else ''}"
        )
    return embed


def _get_track_duration_timestamp(milliseconds: int) -> str:
    hours, milliseconds = divmod(milliseconds, 3.6e6)
    minutes, milliseconds = divmod(milliseconds, 6e4)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return "{}:{}:{}".format(*[str(int(num)).zfill(2) for num in [hours, minutes, seconds]])


def _get_queue_total_duration(queue: List[AudioTrack]) -> str:
    return _get_track_duration_timestamp(sum(track.duration if track else 0 for track in queue))


total_queue_duration = _get_queue_total_duration
track_duration = _get_track_duration_timestamp


def _get_track_thumbnail(track: Union[AudioTrack, List[AudioTrack]]) -> str:
    track = track if isinstance(track, AudioTrack) else track[0] if track else None
    return f"http://img.youtube.com/vi/{track.identifier}/maxresdefault.jpg" if track else ""


def _process_identifier(identifier: str) -> Tuple[int, str, str]:
    try:
        id = int(identifier)
        name = None
        not_found = "an id of {id}"
    except ValueError:
        id = None
        name = identifier
        not_found = "a name of {name}"
    return id, name, not_found


def _handle_task_result(task: asyncio.Task) -> None:
    try:
        task.result()
    except Exception:
        pass


async def play_or_queue_tracks(bot: AutoShardedBot,
                               ctx: Context,
                               player: MBPlayer,
                               query: str,
                               source: str = "yt",
                               send_embeds: bool = True):
    queue_embed = discord.Embed(
        title="Processing Request...",
        description="Depending on how many tracks your request returns, this may take a while. Please be patient...",
        color=BLUE
    ) if send_embeds else None
    queue_message = await ctx.channel.send(embed=queue_embed) if queue_embed else None

    counter = 0
    results = None
    while counter < 2 and not results:
        _query = query.strip("<>")
        if source.lower() not in ["yt", "sc"]:
            source = "yt"
        source = source.lower()
        if counter == 1:
            source = opp_source[source]
        if not url_rx.match(query):
            _query = f"{source}search:{query}"
        results = await player.get_tracks(_query)
        counter += 1
    if not results or not results.get("tracks"):
        embed = discord.Embed(title="Nothing Found",
                              description=f"{ctx.author.mention}, I couldn't find anything for {query}",
                              color=RED)
        return await ctx.channel.send(embed=embed)

    embed = discord.Embed(color=BLUE)
    queue = player.queue
    pag = None
    if results['loadType'] == "PLAYLIST_LOADED":
        tracks = [AudioTrack(data, ctx.author.id) for data in results.get("tracks")]
        tracklist = [
            f"[{track.title}]({track.uri}) - {track.author} - {_get_track_duration_timestamp(track.duration)}" for track in tracks
        ]
        for track in tracks:
            player.add(requester=ctx.author.id, track=track)
            task = bot.loop.create_task(player.get_tracks(track.uri))
            task.add_done_callback(_handle_task_result)

        embed.title = "Playlist Queued"
        embed.description = f'**[{results["playlistInfo"]["name"]}]({query})** - {len(tracks)} tracks\n\nDuration: {_get_track_duration_timestamp(sum(track.duration for track in tracks))}'
        embed.set_image(
            url=_get_track_thumbnail(tracks)
        ).set_footer(text=f"Requested by: {ctx.author.display_name}\nQueue Duration: {_get_queue_total_duration(queue)}")
        pag = EmbedPaginator(
            ctx,
            entries=tracklist,
            per_page=10,
            show_entry_count=False,
            embed=embed,
            description=embed.description,
            provided_message=queue_message
        )
    else:
        track = AudioTrack(results['tracks'][0], ctx.author.id)
        player.add(requester=ctx.author.id, track=track)
        embed.title = "Track Queued"
        embed.description = f"**1:** [{track.title}]({track.uri}) - {track.author} - {_get_track_duration_timestamp(track.duration)}"
        embed.set_image(
            url=_get_track_thumbnail(track)
        ).set_author(
            name=f"Author: {track.author}"
        ).set_footer(
            text=f"Requested by: {ctx.author.display_name}\nQueue Duration: {_get_queue_total_duration(queue)}",
            icon_url=ctx.author.avatar_url,
        )
    if send_embeds:
        if pag:
            await pag.paginate()
        else:
            await queue_message.edit(embed=embed)

    if ctx.command.name == "play" and not player.is_playing:
        await player.play()
    return


async def get_playlist_help(self, ctx: Context) -> discord.Message:
    pfx = f"{await self.gcmds.prefix(ctx)}playlist"
    title = "Playlist Commands"
    description = (f"{ctx.author.mention}, MarwynnBot's playlist feature allows for easy loading and saving of audio playlists "
                   f"for use with general music commands. The base command is `{pfx}`. Every subcommand, except for `list`, is "
                   "premium only (currently available to everyone). Any playlist modification/deletion subcommand may only be "
                   "successfully executed on playlists you have created. Here are all the valid subcommands")
    phelp = SubcommandHelp(pfx, title, description, show_entry_count=True)
    return await phelp.add_entry("Help", EntryData(
        usage="help",
        returns="This help message",
        aliases=["h"],
        note=f"This same help message will appear by doing just `{pfx}`"
    )).add_entry("List", EntryData(
        usage="list",
        returns="A paginated list of all your created playlists",
        aliases=["ls"],
    )).add_entry("Queue", EntryData(
        usage="queue [name|id]",
        returns="A message which details if the playlist queued successfully",
        aliases=["q"],
        note="Playlist names and IDs can be found by executing the `list` subcommand"
    )).add_entry("Play", EntryData(
        usage="play (name|id)",
        returns="A music control panel if one does not exist prior to command invocation",
        aliases=["p"],
        note="If `(name|id)` is unspecified, this command behaves like the regular play command"
    )).add_entry("Save", EntryData(
        usage="save (urls)",
        returns="An interactive panel which guides you through the playlist saving process",
        aliases=["s"],
        note=("Individual URLs should be separated by a whitespace if provided, otherwise, it will save the current "
              "queue, excluding the currently playing track")
    )).add_entry("Append", EntryData(
        usage="append [id] (urls)",
        returns="An interactive panel which guides you through appending songs to the specified playlist",
        aliases=["add", "a"],
        note=("`(urls)` should be a list of comma separated URLs, otherwise it will save the current queue, excluding "
              "the currently playing track. Appending WILL NOT overwrite any URLs currently saved. Instead, they will "
              "add them along to the URLs saved in your playlist already. If a URL already exists, it will not be added twice.")
    )).add_entry("Replace", EntryData(
        usage="replace [id] (urls)",
        returns="An interactive panel which guides you through replacing the songs in the specified playlist",
        aliases=["repl", "rp"],
        note=("`(urls)` should be a list of comma separated URLs, otherwise it will save the current queue, excluding "
              "the currently playing track. Replacing WILL overwrite any URLs currently saved. After replacement, your "
              "playlist will only contain the songs you have specified during the interactive replacement prompt.")
    )).add_entry("Rename", EntryData(
        usage="rename [id] [new_name]",
        returns="A confirmation panel which, once confirmed, will rename the specified playlist",
        aliases=["ren", "rn"],
        note="You will not be able to rename a playlist using a name that already exists (case sensitive)"
    )).add_entry("Delete", EntryData(
        usage="delete [name|id]",
        returns="A confirmation panel which, once confirmed, will delete the specified playlist",
        aliases=["del", "d"],
        note="This operation is destructive and cannot be undone"
    )).show_help(ctx)


async def prep_play_queue_playlist(self, ctx: Context, identifier: str) -> Playlist:
    id, name, not_found = _process_identifier(identifier)
    playlist = await get_playlist(self, ctx, id=id, name=name, ret="load")
    if not playlist:
        embed = discord.Embed(
            title="Playlist Not Found",
            description=f"{ctx.author.mention}, a playlist with {not_found} could not be found",
            color=RED
        )
        await ctx.channel.send(embed=embed)
    return playlist


def _urls_pg(urls: List[str]) -> str:
    return "'{" + ",".join(urls) + "}'"


async def _check_urls(bot: AutoShardedBot, ctx: Context, urls: List[str]) -> List[str]:
    ret = []
    if urls:
        player = get_player(bot, ctx)
        for url in urls:
            if not url_rx.match(url):
                raise InvalidURL(url=url)
            results = await player.get_tracks(url)
            if not results:
                continue
            elif results["loadType"] == "TRACK_LOADED":
                ret.append(AudioTrack(results['tracks'][0], ctx.author.id).uri)
            elif results["loadType"] == "PLAYLIST_LOADED":
                ret += [AudioTrack(data, ctx.author.id).uri for data in results.get("tracks")]
    return ret


async def _check_ownership(bot: AutoShardedBot, ctx: Context, id: int) -> None:
    async with bot.db.acquire() as con:
        user_id = await con.fetchval(f"SELECT user_id FROM playlists WHERE id={id}")
    if user_id is None:
        raise NonexistentPlaylist(id=id)
    elif int(user_id) != ctx.author.id:
        raise NotPlaylistOwner(id=id)
    else:
        pass
    return


async def _extract_playlist_urls(bot: AutoShardedBot, ctx: Context, urls: List[str]) -> List[AudioTrack]:
    player = get_player(bot, ctx)
    ret = []
    for url in urls:
        results = await player.get_tracks(url)
        if not results or not results["tracks"]:
            continue
        if not results["loadType"] == "PLAYLIST_LOADED":
            ret.append(AudioTrack(results["tracks"][0], ctx.author.id))
            continue
        ret += [AudioTrack(data, ctx.author.id) for data in results.get("tracks")]
    return ret


async def _confirm_modify(bot: AutoShardedBot,
                          ctx: Context,
                          id: int,
                          urls: List[str] = None,
                          name: str = None,
                          type: str = None) -> List[str]:
    if urls:
        urls = await _extract_playlist_urls(bot, ctx, urls)
    if not urls and type in ["append", "replace"]:
        raise InvalidURL(url="`[NO URL PROVIDED]`")
    urls_listed = '\n'.join(f'**{index}:** [{track.title}]({track.uri})' for index,
                            track in enumerate(urls, 1)) if urls else ""
    panel_description = (
        f"URLs:\n{urls_listed}" if urls and len(urls) < 10 else
        f"{len(urls)} URLs" if urls else
        f'Rename to: "{name}"' + f"\n\n{CONF_MSG.format(ctx.author.mention)}"
    )
    panel = discord.Embed(title=f"Confirm {type.title()}",
                          description=panel_description,
                          color=BLUE)
    panel_msg = await ctx.channel.send(embed=panel)
    try:
        for reaction in CONF_REACTIONS:
            await panel_msg.add_reaction(reaction)
    except (NotFound, Forbidden, HTTPException):
        pass

    try:
        reaction, user = await bot.wait_for(
            "reaction_add",
            check=lambda r, u: r.message.id == panel_msg.id and r.emoji in CONF_REACTIONS and u.id == ctx.author.id,
            timeout=120
        )
    except asyncio.TimeoutError as e:
        raise SetupCancelled(setup=f"playlist {type}") from e
    else:
        if reaction.emoji == CONF_REACTIONS[1]:
            raise SetupCancelled(setup=f"playlist {type}")
    finally:
        if urls:
            urls = [track.uri for track in urls]

    if not type == "rename":
        if type == "replace":
            return urls
        async with bot.db.acquire() as con:
            stored_urls: List[str] = await con.fetchval(f"SELECT urls FROM playlists WHERE id={id}")
        if type == "append":
            return stored_urls + urls if stored_urls else [] + urls


async def _save_playlist_get_name(bot: AutoShardedBot, ctx: Context, urls: List[str]) -> str:
    panel_description = f"{ctx.author.mention}, you will be saving {len(urls)} track{'s' if len(urls) != 1 else ''}. Please enter the name of your playlist"
    panel = discord.Embed(
        title="Save Playlist",
        description=panel_description,
        color=BLUE
    ).set_footer(text="Enter \"cancel\" to cancel setup")
    await ctx.channel.send(embed=panel)

    try:
        name = await bot.wait_for(
            "message",
            check=lambda m: m.channel == ctx.channel and m.author == ctx.author,
            timeout=120
        )
        name = name.content
    except asyncio.TimeoutError as e:
        raise SetupCancelled(setup="playlist save") from e
    else:
        if name.lower() == "cancel":
            raise SetupCancelled(setup="playlist save")

    try:
        int(name)
    except ValueError:
        if url_rx.match(name):
            raise InvalidName(name=name)
    else:
        raise InvalidName(name=name)

    return name


async def play_or_queue_playlist(bot: AutoShardedBot,
                                 ctx: Context,
                                 player: MBPlayer,
                                 playlist: Playlist,
                                 play: bool = False,
                                 send_embeds: bool = True,):
    queue_embed = discord.Embed(
        title="Processing Request...",
        description="Depending on how many tracks your request returns, this may take a while. Please be patient...",
        color=BLUE
    ) if send_embeds else None
    queue_message = await ctx.channel.send(embed=queue_embed) if queue_embed else None

    pag = None
    successful = []
    failed = []
    queue = player.queue
    for url in playlist.urls:
        results = await player.get_tracks(url)
        if not results:
            failed.append(url)
        else:
            track = AudioTrack(results['tracks'][0], ctx.author.id)
            queue.append(track)
            successful.append(track)

    embed = discord.Embed(title=f"{playlist.name} Queued", color=BLUE)
    if len(failed) == len(playlist.urls):
        embed.title = f"Unable to Queue {playlist.name}"
        embed.description = f"{ctx.author.mention}, none of the tracks in the playlist were able to be found"
        embed.color = RED
    else:
        user: discord.User = bot.get_user(playlist.user_id)
        entries = [f" [{track.title}]({track.uri}) - {track.author}" for track in successful]
        embed.set_image(
            url=_get_track_thumbnail(successful[0])
        ).set_author(
            name=f"Playlist by: {user.display_name}",
            icon_url=user.avatar_url
        ).set_footer(
            text=f"Requested by: {ctx.author.display_name}\nQueue Duration: {_get_queue_total_duration(queue)}",
            icon_url=ctx.author.avatar_url
        )
        pag = EmbedPaginator(ctx,
                             entries=entries,
                             per_page=10,
                             show_entry_count=False,
                             embed=embed,
                             description=embed.description,
                             provided_message=queue_message)
    if send_embeds:
        if pag:
            await pag.paginate()
        else:
            await queue_message.edit(embed=embed)

    if play and not player.is_playing:
        await player.play()
    return


async def _get_playlist_tracks_data(player: MBPlayer, entries: List) -> List[List[AudioTrack]]:
    ret = []
    for record in entries:
        intermediate = []
        for url in record["urls"]:
            results = await player.get_tracks(url)
            intermediate.append(AudioTrack(results["tracks"][0], record["user_id"]) if results else None)
        ret.append(intermediate)
    return ret


async def get_playlist(self,
                       ctx: Context,
                       id: int = None,
                       name: str = None,
                       identifier: str = None,
                       ret: str = "all") -> Union[Playlist, List[Playlist], List[str], None]:
    if identifier is not None:
        id, name, not_found = _process_identifier(identifier)
        if not id and not name:
            return None
    player = get_player(self.bot, ctx)
    async with self.bot.db.acquire() as con:
        op = f"SELECT * FROM playlists WHERE user_id={ctx.author.id}"
        op += f" AND id={id}" if id is not None else f" AND playlist_name=$pln${name}$pln$" if name is not None else ""
        entries = await con.fetch(op + " ORDER BY id ASC")
    if not entries:
        return None
    elif ret == "all":
        return [Playlist(record["playlist_name"], record["urls"], record["user_id"], record["id"]) for record in entries]
    elif ret == "all-info":
        track_data = await _get_playlist_tracks_data(player, entries)
        return [Playlist(record["playlist_name"], record["urls"], record["user_id"], record["id"], tracks=tracks) for record, tracks in zip(entries, track_data)]
    elif ret == "url":
        if len(entries) != 1:
            raise ValueError(f"Playlist Query has returned {len(entries)} entries, supposed to return just 1")
        return entries[0]["url"]
    elif ret == "load":
        if len(entries) != 1:
            raise ValueError(f"Playlist Query has returned {len(entries)} entries, supposed to return just 1")
        playlist = entries[0]
        return Playlist(playlist["playlist_name"], playlist["urls"], playlist["user_id"], playlist["user_id"])
    else:
        return None


async def save_playlist(self, ctx: Context, urls: List[str]) -> discord.Message:
    raised = True
    embed = discord.Embed(title="Playlist Saved", color=BLUE)
    try:
        urls = await _check_urls(self.bot, ctx, urls)
        name = await _save_playlist_get_name(self.bot, ctx, urls)
        async with self.bot.db.acquire() as con:
            values = "(" + f"{ctx.author.id}, $pln${name}$pln$, {_urls_pg(urls)}" + ")"
            await con.execute(f"INSERT INTO playlists(user_id, playlist_name, urls) VALUES {values}")
        embed.description = f"{ctx.author.mention}, your playlist, \"{name}\", was successfully saved"
    except UniqueViolationError as i:
        embed.description = f"{ctx.author.mention}, a playlist with the specified name already exists. Please pick another name"
    except InvalidURL as i:
        embed.description = f"{ctx.author.mention}, {i.url} is not a valid URL"
    except InvalidName as i:
        embed.description = f"{ctx.author.mention}, {i.name} cannot be used as a playlist name"
    except SetupCancelled as i:
        embed.description = f"{ctx.author.mention}, the {i.setup} was cancelled"
    else:
        raised = False

    if raised:
        embed.title = "Playlist Save Failed"
        embed.color = RED
    return await ctx.channel.send(embed=embed)


async def modify_playlist(self, ctx: Context, id: int, urls: List[str] = None, name: str = None, op_type: str = None) -> discord.Message:
    raised = True
    embed = discord.Embed(title=f"Playlist {op_type.title()}", color=BLUE)
    try:
        urls = await _check_urls(self.bot, ctx, urls)
        await _check_ownership(self.bot, ctx, id)
        if op_type == "rename" and name is None:
            raise NoNameSpecified()
        urls = await _confirm_modify(self.bot, ctx, id, urls=urls, name=name, type=op_type)
        async with self.bot.db.acquire() as con:
            op = f"urls={_urls_pg(urls)}" if op_type != "rename" else f"playlist_name=$pln${name}$pln$"
            await con.execute(f"UPDATE playlists set {op} WHERE id={id} and user_id={ctx.author.id}")
            success = "append" if op_type == "append" else "replacement" if op_type == "replace" else "rename" if op_type == "rename" else "[error]"
        embed.description = f"{ctx.author.mention}, the {success} was successful"
    except InvalidURL as i:
        embed.description = f"{ctx.author.mention}, {i.url} is not a valid URL"
    except NonexistentPlaylist as i:
        embed.description = i.err_msg.format(ctx.author.mention)
    except NotPlaylistOwner as i:
        embed.description = f"{ctx.author.mention}, you must own this playlist in order to modify it"
    except NoNameSpecified as i:
        embed.description = f"{ctx.author.mention}, you must specify a name to rename this playlist to"
    except SetupCancelled as i:
        embed.description = f"{ctx.author.mention}, the {i.setup} was cancelled"
    else:
        raised = False

    if raised:
        embed.title = f"Playlist {op_type.title()} Failed"
        embed.color = RED
    return await ctx.channel.send(embed=embed)


async def delete_playlist(self, ctx: Context, identifier: str) -> discord.Message:
    raised = True
    id, name, _ = _process_identifier(identifier)
    filter = f"playlist_name=$pln${name}$pln$" if name else f"id={id}"
    embed = discord.Embed(title="Playlist Deleted", color=BLUE)
    try:
        async with self.bot.db.acquire() as con:
            playlist_id = await con.fetchval(f"SELECT id from playlists WHERE {filter}")
            if not playlist_id:
                raise NonexistentPlaylist(id=id, name=name)
            await _check_ownership(self.bot, ctx, playlist_id)
            await con.execute(f"DELETE FROM playlists WHERE {filter} AND user_id={ctx.author.id}")
        identifier = f'"{name}"' if name is not None else f"[ID: {id}]"
        embed.description = f"{ctx.author.mention}, your playlist, {identifier}, was successfully deleted"
    except NonexistentPlaylist as i:
        embed.description = i.err_msg.format(ctx.author.mention)
    except NotPlaylistOwner as i:
        embed.description = f"{ctx.author.mention}, you must own this playlist in order to delete it"
    except SetupCancelled as i:
        embed.description = f"{ctx.author.mention}, the {i.setup} was cancelled"
    else:
        raised = False

    if raised:
        embed.title = "Playlist Delete Failed"
        embed.color = RED
    return await ctx.channel.send(embed=embed)


def check_gain(ctx: Context, band: List[int], gain: str) -> Union[List[float], float]:
    if gain is None:
        return [0.00 for _ in range(len(band))]
    else:
        try:
            if not "," in gain:
                if not -0.25 <= float(gain) <= 1.00:
                    raise EQGainError(ctx, f"{gain} is not between -0.25 and 1.00 inclusive")
                gain = float(gain) if type(band) == int else [float(gain) for _ in range(len(band))]
            else:
                gain = [float(val) for val in gain.split(",")]
                if len(gain) != len(band):
                    raise EQGainMismatch(ctx, len(band), len(gain))
        except ValueError as e:
            raise EQGainError(ctx) from e
    return gain
