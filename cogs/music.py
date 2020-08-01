import shutil
import discord
import json
import os
import youtube_dl
import asyncio
from discord.ext import commands
from discord.ext.commands import has_permissions, BotMissingPermissions
from discord.utils import get

import globalcommands
from globalcommands import GlobalCMDS as gcmds


class Music(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "music" has been loaded')

    @commands.command()
    async def join(self, ctx):
        await ctx.message.delete()
        channel = ctx.author.voice.channel
        await channel.connect()
        joinEmbed = discord.Embed(title='Join Success!',
                                  description=f'Successfully joined the voice channel `{channel}`',
                                  color=discord.Color.blue())
        await ctx.channel.send(embed=joinEmbed)
        gcmds.incrCounter(gcmds, ctx, 'join')

    @join.error
    async def join_error(self, ctx, error):
        if isinstance(error, BotMissingPermissions):
            joinError = discord.Embed(title='Error - Insufficient Permissions',
                                      description='I cannot join this voice channel.',
                                      color=discord.Color.dark_red())
            await ctx.channel.send(embed=joinError)
        else:
            with open('prefixes.json', 'r') as f:
                sp = json.load(f)
                serverPrefix = sp[str(ctx.guild.id)]
            joinError = discord.Embed(title='Error - User Not in a Voice Channel',
                                      description=f"{ctx.author.mention}, you're currently not in any voice channel! "
                                                  f"Join a voice channel and then do `{serverPrefix}join`!",
                                      color=discord.Color.dark_red())
            await ctx.channel.send(embed=joinError)

    @commands.command()
    async def leave(self, ctx):
        await ctx.message.delete()
        channel = ctx.voice_client.channel
        await ctx.voice_client.disconnect()
        leaveEmbed = discord.Embed(title='Leave Success!',
                                   description=f'Successfully left the voice channel `{channel}`',
                                   color=discord.Color.blue())
        await ctx.channel.send(embed=leaveEmbed)
        gcmds.incrCounter(gcmds, ctx, 'leave')

    @leave.error
    async def leave_error(self, ctx, error):
        with open('prefixes.json', 'r') as f:
            sp = json.load(f)
            serverPrefix = sp[str(ctx.guild.id)]
        leaveError = discord.Embed(title="Error - Not in a Voice Channel",
                                   description=f"{ctx.author.mention}, I'm not currently connected to a voice channel.",
                                   color=discord.Color.dark_red())
        leaveError.add_field(name='Special Case: Connected Through Restart',
                             value=f"If it shows that I am connected to a voice channel, that means the owner "
                                   f"restarted the bot while it was still connected. Join the voice channel, "
                                   f"do `{serverPrefix}join`, then do `{serverPrefix}leave`.")
        await ctx.channel.send(embed=leaveError)

    @commands.command()
    async def play(self, ctx, url):

        async def check_queue():
            global voice
            voice = get(discord.Client.voice_clients, guild=ctx.guild)
            queue_infile = os.path.isdir("./queue")
            if queue_infile is True:
                dir = os.path.abspath(os.path.realpath("./queue"))
                length = len(os.listdir(dir))
                still_queued = length - 1
                try:
                    first_file = os.listdir(dir)[0]
                except:
                    none = discord.Embed(title="No Songs in Queue",
                                         description=f"Add more with `{gcmds.prefix(gcmds, ctx)}play [url]`",
                                         color=discord.Color.dark_red())
                    await ctx.channel.send(embed=none, delete_after=10)
                main_location = os.path.dirname(os.path.realpath(__file__))
                song_path = os.path.abspath(os.path.realpath("./queue") + "\\" + first_file)
                if length != 0:
                    playNext = discord.Embed(title="Song Done",
                                             description=f"Playing next song in queue\n\nSongs in queue: {still_queued}",
                                             color=discord.Color.blue())
                    song_there = os.path.isfile("song.mp3")
                    await ctx.channel.send(embed=playNext, delete_after=10)
                    if song_there:
                        os.remove("song.mp3")
                    shutil.move(song_path, main_location)
                    for file in os.listdir("./"):
                        if file.endswith(".mp3"):
                            os.rename(file, "song.mp3")

                    voice.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: check_queue())
                    voice.source = discord.PCMVolumeTransformer(voice.source)
                    voice.source.volume = 0.07
                else:
                    self.queues.clear()
                    return
            else:
                self.queues.clear()
                none = discord.Embed(title="Queue Finished",
                                     description=f"Add more with `{gcmds.prefix(gcmds, ctx)}play [url]`",
                                     color=discord.Color.dark_red())
                await ctx.channel.send(embed=none, delete_after=10)

            song_there = os.path.isfile("song.mp3")
            try:
                if song_there:
                    os.remove("song.mp3")
                    self.queues.clear()
                    print("Removed old song file")
            except PermissionError:
                print("Song file is being played")
                error = discord.Embed(title="PermissionError",
                                      description="Cannot delete song file because it is being played",
                                      color=discord.Color.dark_red())
                await ctx.channel.send(embed=error, delete_after=5)
                return

            queue_infile = os.path.isdir("./queue")
            try:
                queue_folder = "./queue"
                if queue_infile is True:
                    print("Removed old queue folder")
                    shutil.rmtree(queue_folder)
            except:
                print("No old queue folder")

            ready = discord.Embed(title="Preparing...",
                                  color=discord.Color.blue())
            await ctx.channel.send(embed=ready, delete_after=3)

            voice = get(discord.Client.voice_clients, guild=ctx.guild)

            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                print("Downloading audio now\n")
                ydl.download([url])

            for file in os.listdir("./"):
                if file.endswith(".mp3"):
                    name = file
                    print(f"Renamed File: {file}\n")
                    os.rename(file, "song.mp3")

            voice.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: check_queue())
            voice.source = discord.PCMVolumeTransformer(voice.source)
            voice.source.volume = 0.07

            nname = name.rsplit("-", 2)
            playing = discord.Embed(title=f"Now Playing: {nname[0]}",
                                    color=discord.Color.blue())
            await ctx.channel.send(embed=playing, delete_after=10)
            print("Playing\n")

    @commands.command()
    async def pause(self, ctx):

        voice = get(discord.Client.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            print("Music Paused")
            voice.pause()
            paused = discord.Embed(title="Song Paused",
                                   color=discord.Color.blue())
            await ctx.channel.send(embed=paused, delete_after=10)
        else:
            print("Music not playing")
            paused = discord.Embed(title="No Music Playing",
                                   color=discord.Color.dark_red())
            await ctx.channel.send(embed=paused, delete_after=5)

    @commands.command()
    async def resume(self, ctx):

        voice.get(discord.Client.voice_clients, guild=ctx.guild)

        if voice and voice.is_paused():
            print("Music resumed")
            voice.resume()
            resumed = discord.Embed(title="Song Resumed",
                                    color=discord.Color.blue())
            await ctx.channel.send(embed=resumed, delete_after=10)
        else:
            print("Music is not paused")
            resumed = discord.Embed(title="Song not Paused",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=resumed, delete_after=5)

    @commands.command()
    async def skip(self, ctx):

        voice = get(discord.Client.voice_clients, guild=ctx.guilds)

        self.queues.clear()

        if voice and voice.is_playing():
            print("Music skipped")
            voice.stop()
            skipped = discord.Embed(title="Song Skipped",
                                    color=discord.Color.blue())
            await ctx.channel.send(embed=skipped, delete_after=10)
        else:
            print("No music playing, cannot skip")
            skipped = discord.Embed(title="No Music Playing",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=skipped, delete_after=10)

    queues = {}
    
    @commands.command()
    async def queue(self, ctx, url):
        queue_infile = os.path.isdir("./queue")
        if queue_infile is False:
            os.mkdir("queue")
        dir = os.path.abspath(os.path.realpath("queue"))
        q_num = len(os.listdir(dir))
        q_num += 1
        add_queue = True
        while add_queue:
            if q_num is self.queues:
                q_num += 1
            else:
                add_queue = False
                self.queues[q_num] = q_num
        queue_path = os.path.abspath(os.path.realpath("queue") + f"song{q_num}.%(ext)s")

        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'outtmpl': queue_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print("Downloading audio now\n")
            ydl.download([url])
        adding = discord.Embed(title=f"Adding song {str(q_num)} to the queue",
                               color=discord.Color.blue())
        await ctx.channel.send(embed=adding, delete_after=10)
        print("Song added to the queue")


def setup(client):
    client.add_cog(Music(client))
