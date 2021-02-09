from collections import deque
from typing import Deque, Dict, List, Union

import discord
from lavalink.events import QueueEndEvent, TrackStartEvent
from lavalink.models import AudioTrack, DefaultPlayer

BLUE = discord.Color.blue()
RED = discord.Color.dark_red()

_cache = {}


class MBPlayer(DefaultPlayer):
    def __init__(self, guild_id, node):
        super(MBPlayer, self).__init__(guild_id, node)
        self.queue: Deque[AudioTrack] = deque()
        self.session_queue: Deque[AudioTrack] = deque()
        self.current: AudioTrack = None
        self.voice_channel_id: int
        self.text_channel: discord.TextChannel
        self.votes: dict = {
            "pause": [],
            "unpause": [],
            "rewind": [],
            "skip": [],
            "stop": [],
            "leave": [],
        }
        self.loop_count = 0
        self._rewind = False
        self._index = 1
        self._loop = 0

    def reset_votes(self) -> None:
        self.votes: dict = {
            "pause": [],
            "unpause": [],
            "rewind": [],
            "skip": [],
            "stop": [],
            "leave": [],
        }

    async def close_session(self) -> None:
        self.queue.clear()
        self.session_queue.clear()
        self.reset_votes()
        await self.reset_equalizer()
        self.loop_count = 0
        self._rewind = False
        self._index = 1
        self._loop = 0

    def enable_rewind(self) -> Union[discord.Embed, None]:
        if self._index >= len(self.session_queue):
            return discord.Embed(
                title="Cannot Rewind",
                description=f"There are no tracks to rewind to",
                color=RED
            )
        self._rewind = True
        return None

    def set_loop_times(self, times: str) -> discord.Embed:
        try:
            times = int(times)
            if not 0 <= times:
                return discord.Embed(
                    title="Invalid Loop Number",
                    description=f"The loop number must be a positive integer, not {times}",
                    color=discord.Color.dark_red()
                )
            self._loop = times
            description_fragment = f"loop {self._loop} time{'s' if self._loop != 1 else ''}" if self._loop != 0 else "not loop and play the next queued track once the current track finishes"
        except ValueError:
            self._loop = -1 if times.lower() == "forever" else 0
            description_fragment = "loop forever" if self._loop == -1 else "not loop"
        return discord.Embed(
            title="Track Loop Status",
            description=f"The current track will **{description_fragment}**\n\nTo loop forever, do `m!loop forever`\nTo stop looping, do `m!loop stop`",
            color=BLUE
        )

    @property
    def loop_status(self) -> str:
        return f"loop {self._loop} time{'s' if self._loop != 1 else ''}" if self._loop >= 1 else "loop forever" if self._loop == -1 else "not loop"

    async def get_tracks(self, query: str) -> Dict:
        if not query in _cache:
            ret = await self.node.get_tracks(query)
            if ret and ret.get("tracks"):
                _cache[query] = ret
        return _cache.get(query, None)

    async def seek(self, millisecond_amount: int, sign: str = None) -> Union[int, str]:
        if sign == "+":
            position = self.position + millisecond_amount
        elif sign == "-":
            position = self.position - millisecond_amount
        else:
            position = millisecond_amount

        if not 0 <= position:
            position = 0
        if not position <= self.current.duration:
            position = self.current.duration

        await super().seek(position)
        return int(position)

    async def play(self) -> AudioTrack:
        self.reset_votes()
        self._last_update = 0
        self._last_position = 0
        self.position_timestamp = 0
        self.paused = False

        if not self._rewind:
            if self._loop == 0:
                self.loop_count = 0
                try:
                    # FIFO pop
                    track = self.queue.popleft()
                    self.session_queue.appendleft(track)
                except IndexError:
                    # If no track available to skip
                    await self.node._dispatch_event(QueueEndEvent(self))
                    self.current = None
                    await self.stop()
                    await self.close_session()
                    return None
            else:
                self.loop_count += 1
                track = self.current
                self._loop -= 0 if self._loop == -1 else 1
            self._index = 1
        else:
            self._rewind = False
            # State of self.current has not been incremented to previous track
            # Therefore append current track to queue because we will need to play
            # The current song after the rewind has finished
            self.queue.appendleft(self.current)
            # Set track equal to index (starts at 1), because index 0 is the currently playing one
            # self._index >= 1 will pick previously played tracks in the reverse order they were
            # played
            track = self.session_queue[self._index]
            self._index += 1

        self.current = track
        if not self.current.uri in _cache:
            _cache[self.current.uri] = self.current
        await self.node._send(op="play", guildId=self.guild_id, track=track.track)
        await self.node._dispatch_event(TrackStartEvent(self, self.current))
        return self.current

    async def process_eq(self, band: Union[List[int], int] = None, gain: Union[List[float], float] = None, op: str = None) -> discord.Embed:
        if op == "reset":
            await self.reset_equalizer()
            return discord.Embed(
                title="Equaliser Reset",
                description=f"All equaliser bands have been reset to the default gain (0)",
                color=BLUE
            )
        elif op == "adjust":
            if isinstance(band, int):
                band = [band]
            if isinstance(gain, float):
                gain = [gain]
            await self.set_gains(*[(b, g) for b, g in zip(band, gain)])
            adjusted = f"band{'s' if len(band) != 1 else ''} " + ", ".join([
                str(b + 1) for b in band
            ]) if len(band) < 15 else "all bands"
            return discord.Embed(
                title="Equaliser Settings Changed",
                description=f"Equaliser settings for {adjusted} have been changed",
                color=BLUE
            )
        elif op == "display":
            band_gain_render = "\n".join([
                f"Band {str(index).zfill(2)} [{gain:.2f}] {round(((gain + 0.25) / 1.25) * 30) * '|'}" for index, gain in enumerate(self.equalizer, 1)
            ])
            return discord.Embed(
                title="Current Equaliser Setting",
                description=f"```{band_gain_render}```",
                color=BLUE
            )
