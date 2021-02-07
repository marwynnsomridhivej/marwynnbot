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

from . import EntryData, SubcommandHelp
from .mbplayer import MBPlayer

__all__ = (
    "MBPlayer",
    "ensure_voice",
    "check_perms",
    "track_hook",
    "get_player",
    "no_queue",
    "process_votes",
    "prep_play_queue_playlist",
    "play_or_queue_tracks",
    "play_or_queue_playlist",
    "get_playlist_help",
    "get_playlist",
    "save_playlist",
    "modify_playlist",
    "delete_playlist",
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
        self.err_msg = "{}, no playlist exists with " + f"a name of {name}" if name else f"an id of {id}"


class NotPlaylistOwner(Exception):
    def __init__(self, *args, id: int = None) -> None:
        super().__init__(*args)
        self.id = id


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
                        await self.connect_to(ctx.guild.id, ctx.author.voice.channel.id)
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
        embed = discord.Embed(
            title=f"Now Playing:",
            description="\n".join([
                f"[{track.title}]({track.uri})",
                f"Duration: {_get_track_duration_timestamp(track.duration) if not track.stream else 'livestream'}"
            ]),
            color=BLUE
        ).set_footer(
            text="\n".join([
                f"Requested by: {requester.display_name}",
                f"Author: {track.author}",
                f"Current Queue: {queue_rem}",
            ]),
            icon_url=requester.avatar_url
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
    members = [member for member in voice_channel if not member.bot]
    current_member_count = len(members)
    vote_op: List[int] = player.votes.get(op)
    if ctx.author.id in vote_op:
        vote_op.remove(ctx.author.id)
        action = "rescinded"
    else:
        vote_op.append(ctx.author.id)
        action = "placed"
    current = len(vote_op)
    if current <= 2:
        threshold = 1
    else:
        threshold = int(ceil(current_member_count / 2))
    allow_op = True if current >= threshold else False
    return current, threshold, allow_op, action


async def process_votes(bot: AutoShardedBot,
                        ctx: Context,
                        op_name: str) -> discord.Embed:
    ALLOW_TEMPLATES = {
        "pause": "The player has been paused",
        "unpause": "The player has been unpaused",
        "rewind": "The player has rewound to the previous track",
        "skip": "The player has skipped to the next track",
        "stop": "The player has stopped and the queue has been cleared",
    }
    NOT_ALLOW_TEMPLATES = {
        "pause": "pause the player",
        "unpause": "unpause the player",
        "rewind": "rewind to the previous track",
        "skip": "skip to the next track",
        "stop": "stop the player and clear the queue",
    }
    current, threshold, allow_op, action = _process_op_threshold(bot, ctx, op_name)
    embed = discord.Embed(title=f"Vote {op_name.title()}", color=BLUE)
    if allow_op:
        player = get_player(bot, ctx)
        desc = ALLOW_TEMPLATES.get(op_name)
        embed.description = desc
        if op_name == "pause":
            await player.set_pause(True)
            embed.set_footer(text="Do `m!unpause` to vote to unpause the player")
        elif op_name == "unpause":
            await player.set_pause(False)
        elif op_name == "rewind":
            temp_embed = player.enable_rewind()
            embed = embed if temp_embed is None else temp_embed
        elif op_name == "skip":
            await player.play()
        elif op_name == "stop":
            await player.stop()
            player.close_session()
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
    return _get_track_duration_timestamp(sum(track for track in queue))


def _get_track_thumbnail(track: Union[AudioTrack, List[AudioTrack]]) -> str:
    track = track if isinstance(track, AudioTrack) else track[0]
    return f"http://img.youtube.com/vi/{track.identifier}/maxresdefault.jpg"


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


async def play_or_queue_tracks(ctx: Context,
                               player: MBPlayer,
                               query: str,
                               source: str = "yt",
                               send_embeds: bool = True):
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
        results = await player.node.get_tracks(_query)
        counter += 1
    if not results or not results.get("tracks"):
        embed = discord.Embed(title="Nothing Found",
                              description=f"{ctx.author.mention}, I couldn't find anything for {query}",
                              color=RED)
        return await ctx.channel.send(embed=embed)

    embed = discord.Embed(color=BLUE)
    queue = player.queue
    if results['loadType'] == "PLAYLIST_LOADED":
        tracks = (AudioTrack(data, ctx.author.id) for data in results.get("tracks"))
        tracklist = []
        for index, track in enumerate(tracks, 1):
            tracklist.append(f"**{index}:** [{track.title}]({track.uri})")
            player.add(requester=ctx.author.id, track=track)
            queue.append(track)

        embed.title = "Playlist Queued"
        embed.description = f'**[{results["playlistInfo"]["name"]}]({query})** - {len(tracks)} tracks:\n\n' + "\n".join(
            tracklist
        ) + f"\n\nDuration: {_get_track_duration_timestamp(sum(track.duration for track in tracks))}"
        embed.set_image(
            url=_get_track_thumbnail(tracks)
        ).set_footer(text=f"Requested by: {ctx.author.display_name}\n\nQueue Duration: {_get_queue_total_duration(queue)}")
    else:
        track = AudioTrack(results['tracks'][0], ctx.author.id)
        queue.append(track)
        embed.title = "Track Queued"
        embed.description = f'[{track.title}]({track.uri})\n\nDuration: {_get_track_duration_timestamp(track.duration)}'
        embed.set_image(
            url=_get_track_thumbnail(track)
        ).set_author(
            name=f"Author: {track.author}"
        ).set_footer(
            text=f"Requested by: {ctx.author.display_name}\n\nQueue Duration: {_get_queue_total_duration(queue)}",
            icon_url=ctx.author.avatar_url,
        )
    if send_embeds:
        await ctx.channel.send(embed=embed)

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
    return await phelp.add_entry("List", EntryData(
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


def _check_urls(urls: List[str]) -> None:
    for url in urls:
        if not url_rx.match(url):
            raise InvalidURL(url=url)
    return


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


async def _confirm_modify(bot: AutoShardedBot,
                          ctx: Context,
                          urls: List[str] = None,
                          name: str = None,
                          type: str = None) -> None:
    urls_listed = '\n'.join(f'**{index}:** {url}' for index, url in enumerate(urls, 1))
    panel_description = (f"URLs: {urls_listed}" if urls else f'Rename to: "{name}"' +
                         f"\n\n{CONF_MSG.format(ctx.author.mention)}")
    panel = discord.Embed(title=f"Confirm {type.title()}",
                          description=panel_description,
                          color=BLUE)
    panel_msg = await ctx.channel.send(embed=panel)
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


async def _save_playlist_get_name(bot: AutoShardedBot, ctx: Context, urls: List[str]) -> str:
    panel_description = ('\n'.join(f'**{index}:** {url}' for index, url in enumerate(urls, 1)) + "\n\n" +
                         f"{ctx.author.mention}, these are the URLs that will be saved into your playlist. Please enter the name of your playlist.")
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
                                 send_embeds: bool = True):
    successful = failed = []
    queue = player.queue
    for url in playlist.urls:
        results = player.node.get_tracks(url)
        if not results:
            failed.append(url)
            continue
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
        embed.description = "\n".join(
            f"**{index}:** [{track.title}]({track.uri}) - {track.author}"
            for index, track in enumerate(successful, 1)
        )
        if failed:
            embed.description += "\n\nThese songs could not be found:\n" + "\n".join(
                f"**{index}:** {url}" for index, url in enumerate(failed, 1)
            )
        embed.set_image(
            url=_get_track_thumbnail(successful[0])
        ).set_author(
            name=f"Playlist by: {user.display_name}",
            icon_url=user.avatar_url
        ).set_footer(
            text=f"Requested by: {ctx.author.display_name}\n\nQueue Duration: {_get_queue_total_duration(queue)}",
            icon_url=ctx.author.avatar_url
        )
    if send_embeds:
        await ctx.channel.send(embed=embed)

    if play and not player.is_playing:
        await player.play()
    return


async def get_playlist(self, ctx, id: int = None, name: str = None, ret: str = "all") -> Union[Playlist, List[Playlist], List[str], None]:
    async with self.bot.db.acquire() as con:
        op = (f"SELECT * FROM playlists WHERE user_id={ctx.author.id}" +
              f" AND id={id}" if id is not None else f" AND playlist_name=$pln${name}$pln$" if name is not None else "")
        entries = await con.fetch(str(op) + " ORDER BY id ASC")
    if not entries:
        return None
    elif ret == "all":
        return [Playlist(record["playlist_name"], record["urls"], record["user_id"], record["id"]) for record in entries]
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
        _check_urls(urls)
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
        _check_urls(urls)
        await _check_ownership(ctx, id)
        await _confirm_modify(self.bot, ctx, urls=urls, name=name, type=op_type)
        async with self.bot.db.acquire() as con:
            op = f"urls={_urls_pg(urls)}" if op_type != "rename" else f"name=$pln${name}$pln$"
            await con.execute(f"UPDATE playlists set {op} WHERE id={id} and user_id={ctx.author.id}")
        embed.description = f"{ctx.author.mention}, {len(urls)} the {op_type if op_type == 'append' else 'replacement'} was successful"
    except InvalidURL as i:
        embed.description = f"{ctx.author.mention}, {i.url} is not a valid URL"
    except NonexistentPlaylist as i:
        embed.description = i.err_msg.format(ctx.author.mention)
    except NotPlaylistOwner as i:
        embed.description = f"{ctx.author.mention}, you must own this playlist in order to modify it"
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
    name, id, _ = _process_identifier(identifier)
    filter = f"name=$pln${name}$pln$" if name else f"id={id}"
    embed = discord.Embed(title="Playlist Deleted", color=BLUE)
    try:
        async with self.bot.db.acquire() as con:
            playlist_id = await con.fetchval(f"SELECT id from playlists WHERE {filter}")
            if not playlist_id:
                raise NonexistentPlaylist(id=id, name=name)
            await _check_ownership(self.bot, ctx, playlist_id)
            await con.execute(f"DELETE FROM playlists WHERE {filter} AND user_id={ctx.author.id}")
        embed.description = f"{ctx.author.mention}, your playlist, \"{name}\", was successfully saved"
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
