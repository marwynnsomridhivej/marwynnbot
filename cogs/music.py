import discord
from discord.ext import commands
import asyncio
import youtube_dl
import math
import json
from globalcommands import GlobalCMDS as gcmds


async def audio_playing(ctx):
    client = ctx.guild.voice_client
    if client and client.channel and client.source:
        return True
    else:
        raise commands.CommandError("Not currently playing any audio")


async def in_voice_channel(ctx):
    voice = ctx.author.voice
    bot_voice = ctx.guild.voice_client
    if voice and bot_voice and voice.channel and bot_voice.channel and voice.channel == bot_voice.channel:
        return True
    else:
        raise commands.CommandError("You need to be in the channel to do that")


async def is_audio_requester(ctx):
    music = ctx.bot.get_cog("Music")
    state = music.get_state(ctx.guild)
    permissions = ctx.channel.permissions_for(ctx.author)
    if permissions.administrator or permissions.mute_members or permissions.move_members or state.is_requester(
            ctx.author):
        return True
    else:
        raise commands.CommandError("You need to be the song requester to do that")


def get_config(guild_id: int, key: str, value=None):
    init = {guild_id: {"max_volume": 100, "vote_skip": True, "vote_skip_ratio": 0.5}}
    gcmds.json_load(gcmds, 'music.json', init)
    with open('music.json', 'r') as f:
        file = json.load(f)

        try:
            file[guild_id]
        except KeyError:
            file[guild_id] = {}

        try:
            file[guild_id][key]
        except KeyError:
            file[guild_id]["max_volume"] = 100
            file[guild_id]["vote_skip"] = True
            file[guild_id]["vote_skip_ratio"] = 0.5

        if value:
            file[guild_id][key] = value

        with open('music.json', 'w') as g:
            json.dump(file, g, indent=4)

        if not value:
            return file[guild_id][key]


class GuildState:

    def __init__(self):
        self.volume = 1.0
        self.playlist = []
        self.skip_votes = set()
        self.now_playing = None

    def is_requester(self, user):
        return self.now_playing.requested_by == user

YTDL_OPTS = {
    "default_search": "ytsearch",
    "format": "bestaudio/best",
    "quiet": True,
    "extract_flat": "in_playlist"
}


class Video:
    """Class containing information about a particular video."""

    def __init__(self, url_or_search, requested_by):
        """Plays audio from (or searches for) a URL."""
        with youtube_dl.YoutubeDL(YTDL_OPTS) as ydl:
            video = self._get_info(url_or_search)
            video_format = video["formats"][0]
            self.stream_url = video_format["url"]
            self.video_url = video["webpage_url"]
            self.title = video["title"]
            self.uploader = video["uploader"] if "uploader" in video else ""
            self.thumbnail = video[
                "thumbnail"] if "thumbnail" in video else None
            self.requested_by = requested_by

    def _get_info(self, video_url):
        with youtube_dl.YoutubeDL(YTDL_OPTS) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video = None
            if "_type" in info and info["_type"] == "playlist":
                return self._get_info(
                    info["entries"][0]["url"])  # get info for first video
            else:
                video = info
            return video

    def get_embed(self):
        """Makes an embed out of this Video's information."""
        embed = discord.Embed(
            title=self.title, description=self.uploader, url=self.video_url)
        embed.set_footer(
            text=f"Requested by {self.requested_by.name}",
            icon_url=self.requested_by.avatar_url)
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        return embed


class Music(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.states = {}

    def get_state(self, guild):
        if guild.id in self.states:
            return self.states[guild.id]
        else:
            self.states[guild.id] = GuildState()
            return self.states[guild.id]

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" has been loaded')

    @commands.command()
    async def join(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                not_in = discord.Embed(title="User Not in Voice Channel",
                                       description=f"{ctx.author.mention}, please join a voice channel to use this "
                                                   f"command",
                                       color=discord.Color.dark_red())
                await ctx.channel.send(embed=not_in, delete_after=10)

    @commands.command()
    async def leave(self, ctx):
        state = self.get_state(ctx.guild)
        if ctx.me.voice:
            state.playlist = []
            state.now_playing = None
            await ctx.me.voice.channel.disconnect()
        else:
            not_in = discord.Embed(title="Not Connected",
                                   description=f"{ctx.author.mention}, I am not connected to a voice channel",
                                   color=discord.Color.dark_red())
            await ctx.channel.send(embed=not_in, delete_after=10)

    @commands.command()
    async def pause(self, ctx):
        client = ctx.guild.voice_client
        self._pause_audio(client)

    def _pause_audio(self, client):
        if client.is_paused():
            client.resume()
        else:
            client.pause()

    @commands.command()
    async def volume(self, ctx, volume: int):
        state = self.get_state(ctx.guild)

        if volume < 0:
            volume = 0

        max_vol = get_config(ctx.guild.id, "max_volume")
        if max_vol > -1:
            if volume > max_vol:
                volume = max_vol

        client = ctx.guild.voice_client

        state.volume = float(volume) / 100
        client.source.volume = state.volume

    @commands.command()
    async def skip(self, ctx):
        state = self.get_state(ctx.guild)
        client = ctx.guild.voice_client
        permissions = ctx.channel.permissions_for(ctx.author)
        if permissions.administrator or permissions.move_members or permissions.mute_members or state.is_requester(
                ctx.author):
            client.stop()
        elif get_config(ctx.guild.id, "vote_skip"):
            channel = client.channel
            self._vote_skip(channel, ctx.author)
            users_in_channel = len([member for member in channel.members if not member.bot])
            required_votes = math.ceil(get_config(ctx.guild.id, "vote_skip_ratio") * users_in_channel)

            voteEmbed = discord.Embed(title=f"Skip Voted ({len(state.skip_votes) / required_votes})",
                                      description=f"{ctx.author.mention} voted to skip the current song",
                                      color=discord.Color.blue())
            await ctx.channel.send(embed=voteEmbed, delete_after=10)
        else:
            noSkip = discord.Embed(title="Cannot Skip",
                                   description="Skip voting is disabled",
                                   color=discord.Color.blue())
            await ctx.channel.send(embed=noSkip, delete_after=10)

    def _vote_skip(self, channel, member):
        state = self.get_state(channel.guild)
        state.skip_votes.add(member)
        users_in_channel = len([member for member in channel.members if not member.bot])

        if (float(len(state.skip_votes)) / users_in_channel) >= get_config(channel.guild.id, "vote_skip_ratio"):
            channel.guild.voice_client.stop()

    def _play_song(self, client, state, song):
        state.now_playing = song
        state.skip_votes = set()
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song.stream_url), volume=state.volume)

        def after_playing(err):
            if len(state.playlist) > 0:
                next_song = state.playlist.pop(0)
                self._play_song(client, state, next_song)
            else:
                asyncio.run_coroutine_threadsafe(client.disconnect(), self.client.loop)

        client.play(source, after=after_playing)

    @commands.command()
    @commands.check(audio_playing)
    async def nowplaying(self, ctx):
        state = self.get_state(ctx.guild)
        message = await ctx.channel.send("", embed=state.now_playing.get_embed())
        await self._add_reaction_controls(message)

    @commands.command()
    @commands.check(audio_playing)
    async def queue(self, ctx):
        state = self.get_state(ctx.guild)
        await ctx.channel.send(self._queue_embed(state.playlist))

    def _queue_embed(self, queue):
        if len(queue) > 0:
            queue_list = [f"{index + 1}. **{song.title}** (requested by *{song.requested_by.name}*" for (index, song)
                          in enumerate(queue)]
            title = "Songs in Queue"
            description = "\n".join(queue_list)
            color = discord.Color.blue()
        else:
            title = "No Songs in Queue"
            description = "Songs that are added will appear here"
            color = discord.Color.dark_red()

        queueEmbed = discord.Embed(title=title,
                                   description=description,
                                   color=color)
        return queueEmbed

    @commands.command()
    @commands.check(audio_playing)
    async def clearqueue(self, ctx):
        state = self.get_state(ctx.guild)
        state.playlist = []

    @commands.command()
    @commands.check(audio_playing)
    async def editqueue(self, ctx, song: int, new_index: int):
        state = self.get_state(ctx.guild)
        if 1 <= song <= len(state.playlist) and 1 <= new_index:
            song = state.playlist.pop(song - 1)
            state.playlist.insert(new_index - 1, song)
            await ctx.channel.send(self._queue_embed(state.playlist))
        else:
            invalid = discord.Embed(title="Invalid Index",
                                    description=f"{ctx.author.mention}, please use a valid index",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid, delete_after=10)

    @commands.command()
    async def play(self, ctx, *, url):
        client = ctx.guild.voice_client
        state = self.get_state(ctx.guild)

        if client and client.channel:
            try:
                video = Video(url, ctx.author)
            except youtube_dl.DownloadError as e:
                errorDL = discord.Embed(title="Cannot Download Video",
                                        description=f"{ctx.author.mention}, I cannot download the video from the "
                                                    f"url \n\n*{url}*",
                                        color=discord.Color.dark_red())
                await ctx.channel.send(embed=errorDL, delete_after=10)
                return
            state.playlist.append(video)
            message = await ctx.channel.send(embed=video.get_embed())
            await self._add_reaction_controls(message)
        else:
            if ctx.author.voice is not None and ctx.author.voice.channel is not None:
                channel = ctx.author.voice.channel
                try:
                    video = Video(url, ctx.author)
                except youtube_dl.DownloadError as e:
                    errorDL = discord.Embed(title="Cannot Download Video",
                                            description=f"{ctx.author.mention}, I cannot download the video from the "
                                                        f"url \n\n*{url}*",
                                            color=discord.Color.dark_red())
                    await ctx.channel.send(embed=errorDL, delete_after=10)
                    return
                client = await channel.connect()
                self._play_song(client, state, video)
                message = await ctx.channel.send(embed=video.get_embed())
                await self._add_reaction_controls(message)
            else:
                inVC = discord.Embed(title="Not Connected to Voice Channel",
                                     description=f"{ctx.author.mention}, you need to be in a voice channel to use "
                                                 f"this command",
                                     color=discord.Color.blue())
                await ctx.channel.send(embed=inVC, delete_after=10)

    async def on_reaction_add(self, reaction, user):
        message = reaction.message
        if user != self.client.user and message.author == self.client.user:
            await message.remove_reaction(reaction, user)
            if message.guild and message.guild.voice_client:
                user_in_channel = user.voice and user.voice.channel and user.voice.channel == message.guild.voice_client.channel
                permissions = message.channel.permissions_for(user)
                guild = message.guild
                state = self.get_state(guild)
                if permissions.administrator or (user_in_channel and state.is_requester(user)):
                    client = message.guild.voice_client
                    if reaction.emoji == "⏯":
                        self._pause_audio(client)
                    elif reaction.emoji == "⏭":
                        client.stop()
                    elif reaction.emoji == "⏮":
                        state.playlist.insert(0, state.now_playing)
                        client.stop()
                elif reaction.emoji == "⏭" and get_config(guild.id, "vote_skip") and user_in_channel and message.guild.voice_client and message.guild.voice_client.channel:
                    voice_channel = message.guild.voice_client.channel
                    self._vote_skip(voice_channel, user)
                    channel = message.channel
                    users_in_channel = len([member for member in voice_channel.members if not member.bot])
                    required_votes = math.ceil(get_config(guild.id, "vote_skip_ratio") * users_in_channel)
                    voteEmbed = discord.Embed(title=f"Skip Voted ({len(state.skip_votes) / required_votes})",
                                              description=f"{user.mention} voted to skip the current song",
                                              color=discord.Color.blue())
                    await channel.send(embed=voteEmbed, delete_after=10)

    async def _add_reaction_controls(self, message):
        CONTROLS = ["⏮", "⏯", "⏭"]
        for control in CONTROLS:
            await message.add_reaction(control)


def setup(client):
    client.add_cog(Music(client))
