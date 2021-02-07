import discord
import lavalink
from discord.ext import commands
from utils import (FieldPaginator, GlobalCMDS, context, customerrors,
                   premium)
from utils.musicutils import *


class Music(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot) -> None:
        self.bot = bot
        self.gcmds = GlobalCMDS(self.bot)
        self.bot.loop.create_task(self.init_music(bot))
        self.track_hook: function

    async def init_music(self, bot: commands.AutoShardedBot):
        await self.bot.wait_until_ready()
        if not hasattr(bot, 'lavalink'):
            bot.lavalink = lavalink.Client(self.bot.user.id)
            data = [self.gcmds.env_check(key) for key in [f"LAVALINK_{info}" for info in "IP PORT PASSWORD".split()]]
            if not all(data):
                raise ValueError("Make sure your server IP, port, and password are in the .env file")
            bot.lavalink.add_node(*data, 'na', 'default-node', name="lavalink")
            self.bot.add_listener(bot.lavalink.voice_update_handler, 'on_socket_response')
        self.bot.lavalink = bot.lavalink
        self.bot.lavalink.add_event_hook(self.track_hook)

        async with self.bot.db.acquire() as con:
            await con.execute("CREATE TABLE IF NOT EXISTS music(guild_id bigint PRIMARY KEY, channel_id bigint, panel_id bigint)")
            await con.execute("CREATE TABLE IF NOT EXISTS playlists(id SERIAL, user_id bigint, playlist_name text PRIMARY KEY, urls text[])")
        return

    def cog_unload(self) -> None:
        self.bot.lavalink._event_hooks.clear()

    async def cog_check(self, ctx):
        return True if ctx.command.name == "bind" else await context.music_bind(ctx)

    async def connect_to(self, player: MBPlayer, guild_id: int, channel_id: int, mute: bool = False, deafen: bool = True) -> None:
        await self.bot.ws.voice_state(guild_id, channel_id, self_mute=mute, self_deaf=deafen)
        player = get_player(self.bot, None, guild=self.bot.get_guild(guild_id))
        player.store("channel_id", channel_id)

    @commands.command(desc="Binds the music commands to a channel",
                      usage="bind (channel)",
                      uperms=["Manage Server"],
                      note="If `(channel)` is not specified, the current channel will be used")
    @commands.has_permissions(manage_guild=True)
    async def bind(self, ctx, channel: discord.TextChannel = None):
        if not channel:
            channel = ctx.channel
        async with self.bot.db.acquire() as con:
            await con.execute(f"INSERT INTO music(guild_id, channel_id)")
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
        await self.connect_to(ctx.guild.id, ctx.author.voice.channel.id)
        return await ctx.channel.send(embed=embed)

    @commands.command(desc="Makes MarwynnBot play a song or the current queue",
                      usage="play (query)",
                      note="If there are any songs in queue, `(query)` can be unspecified to start playing the first song in queue")
    @ensure_voice(should_connect=True)
    async def play(self, ctx, *, query: str = None):
        player = get_player(self.bot, ctx)
        if not query:
            if player.queue and not player.is_playing:
                return await player.play()
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

        embed = discord.Embed(color=discord.Color.blue())
        description = [
            f"**Now Playing:** [{player.current.title}](https://www.youtube.com/watch?=v{player.current.identifier})\n\n**Queue"
            ":**"
        ] if player.is_playing else []
        queue_length = len(player.queue)
        title_extra = f": {queue_length} Track{'s' if queue_length != 1 else ''}" if queue_length else ""
        embed.title = f"Current Queue{title_extra}"

        if not player.queue:
            description.append("Nothing queued")
        else:
            for index, item in enumerate(player.queue, 1):
                description.append(
                    f"**{index}**: [{item['title']}]https://www.youtube.com/watch?v={item['identifier']})")
        embed.description = "\n".join(description)
        return await ctx.channel.send(embed=embed)

    @commands.command(aliases=["cq"],
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
            player.close_session()
            embed.title = "Player Stopped"
            embed.description = f"{ctx.author.mention}, I have stopped the player and cleared the queue"
            embed.color = discord.Color.blue()
        return await ctx.channel.send(embed=embed)

    @commands.command(desc="Makes MarwynnBot leave the voice channel it is connected to",
                      usage="leave",
                      uperms=["Manage Server` or `Mute Members` or `Deafen Members` or `Move Members"])
    @ensure_voice()
    @check_perms(req_perms={
        "manage_guild": True,
        "mute_members": True,
        "deafen_members": True,
        "move_members": True,
    }, mode="any")
    async def leave(self, ctx):
        await self.connect_to(ctx.guild.id, None)
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

    @commands.command(desc="Toggle your vote to pause the player",
                      usage="pause",
                      note="The player will pause once the vote threshold has been crossed.")
    @ensure_voice()
    async def pause(self, ctx):
        return await ctx.channel.send(embed=await process_votes(self.bot, ctx, "pause"))

    @commands.command(desc="Toggle your vote to unpause the player",
                      usage="unpause",
                      note="The player will unpause once the vote threshold has been crossed.")
    @ensure_voice()
    async def unpause(self, ctx):
        return await ctx.channel.send(embed=await process_votes(self.bot, ctx, "unpause"))

    @commands.command(desc="Toggle your vote to rewind to the previous track",
                      usage="rewind",
                      note="The player will rewind to the previous track once the vote threshold has been crossed.")
    @ensure_voice()
    async def rewind(self, ctx):
        return await ctx.channel.send(embed=await process_votes(self.bot, ctx, "rewind"))

    @commands.command(desc="Toggle your vote to skip to the next track",
                      usage="skip",
                      note="The player will skip to the next track once the vote threshold has been crossed.")
    @ensure_voice()
    async def skip(self, ctx):
        return await ctx.channel.send(embed=await process_votes(self.bot, ctx, "skip"))

    @commands.command(desc="Toggle your vote to stop the player",
                      usage="stop",
                      note="The player will stop once the vote threshold has been crossed.")
    @ensure_voice()
    async def stop(self, ctx):
        return await ctx.channel.send(embed=await process_votes(self.bot, ctx, "stop"))

    @commands.command(desc="Set the player's track loop status",
                      usage="loop (times)",
                      note="`(times)` can be a positive integer value, \"forever\" to loop indefinitely, or \"stop\" to stop looping")
    @ensure_voice()
    async def loop(self, ctx, *, amount: str = None):
        player = get_player(self.bot, ctx)
        if amount is None:
            embed = discord.Embed(
                title="Track Loop Status",
                description=f"{ctx.author.mention}, the current track will {player.loop_status}",
                color=discord.Color.blue()
            )
        else:
            embed = player.set_loop_times(amount)
        return await ctx.channel.send(embed=embed)

    @commands.group(invoke_without_command=True,
                    aliases=["playlists", "pl"],
                    desc="Shows help for the playlist command and subcommands",
                    usage="playlist (subcommand)",)
    async def playlist(self, ctx):
        return await get_playlist_help(self, ctx)

    @playlist.command(name="list",
                      aliases=["ls"])
    async def playlist_list(self, ctx):
        embed = discord.Embed(title="Your Playlists", color=discord.Color.blue())
        playlists = await get_playlist(self, ctx)
        if not playlists:
            embed.description = f"{ctx.author.mention}, you don't have any saved playlists"
            return await ctx.channel.send(embed=embed)

        template = "**{}:** *[ID: {}]* {} Track{}"
        entries = [
            template.format(
                index,
                playlist.id,
                len(playlist.urls),
                's' if len(playlist.urls) != 1 else ''
            ) for index, playlist in enumerate(playlists, 1)
        ]
        pag = FieldPaginator(ctx, entries=entries, embed=embed)
        return await pag.paginate()

    @premium.is_premium
    @playlist.command(name="queue",
                      aliases=["q"])
    @ensure_voice(should_connect=True)
    async def playlist_queue(self, ctx, *, identifier: str):
        playlist = await prep_play_queue_playlist(self, ctx, identifier)
        return await play_or_queue_playlist(self.bot, ctx, get_player(self, ctx), playlist)

    @premium.is_premium
    @playlist.command(name="play",
                      aliases=["p"])
    @ensure_voice(should_connect=True)
    async def playlist_play(self, ctx, *, identifier: str):
        playlist = await prep_play_queue_playlist(self, ctx, identifier)
        return await play_or_queue_playlist(self.bot, ctx, get_player(self, ctx), playlist, play=True)

    @premium.is_premium
    @playlist.command(name="save",
                      aliases=["s"])
    async def playlist_save(self, ctx, *, urls: str = None):
        player = get_player(self.bot, ctx)
        return await save_playlist(self, ctx, urls.split() if urls else [track.uri for track in player.queue])

    @premium.is_premium
    @playlist.command(name="append",
                      aliases=["add", "a"])
    async def playlist_append(self, ctx, id: int, *, urls: str = None):
        player = get_player(self.bot, ctx)
        return await modify_playlist(self, ctx, id, urls=urls.split() if urls else [track.uri for track in player.queue], op_type="append")

    @premium.is_premium
    @playlist.command(name="replace",
                      aliases=["repl", "rp"])
    async def playlist_replace(self, ctx, id: int, *, urls: str = None):
        player = get_player(self.bot, ctx)
        return await modify_playlist(self, ctx, id, urls=urls.split() if urls else [track.uri for track in player.queue], op_type="replace")

    @premium.is_premium
    @playlist.command(name="rename",
                      aliases=["ren", "rn"])
    async def playlist_rename(self, ctx, *, identifier: str):
        return await delete_playlist(self, ctx, identifier)


def setup(bot: commands.AutoShardedBot):
    bot.add_cog(Music(bot))


Music.track_hook = track_hook