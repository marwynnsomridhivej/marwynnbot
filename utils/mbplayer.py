from collections import deque
from typing import Deque, Union

import discord
from lavalink.events import TrackStartEvent
from lavalink.models import AudioTrack, DefaultPlayer


class MBPlayer(DefaultPlayer):
    def __init__(self, guild_id, node):
        super(MBPlayer, self).__init__(guild_id, node)
        self.queue: Deque[AudioTrack] = deque()
        self.session_queue: Deque[AudioTrack] = []
        self.current: AudioTrack = None
        self.voice_channel_id: int
        self.text_channel: discord.TextChannel
        self.votes: dict = {
            "pause": [],
            "unpause": [],
            "rewind": [],
            "fastforward": [],
            "stop": [],
        }
        self._rewind = False
        self._index = 1
        self._loop = 0

    def close_session(self) -> None:
        self.queue.clear()
        self.session_queue.clear()
        self.votes = {
            "pause": [],
            "unpause": [],
            "rewind": [],
            "fastforward": [],
            "stop": [],
        }
        self._rewind = False
        self._index = 1
        self._loop = 0

    def enable_rewind(self) -> Union[discord.Embed, None]:
        if self._index >= len(self.session_queue):
            return discord.Embed(
                title="Cannot Rewind",
                description=f"There are no tracks to rewind to",
                color=discord.Color.dark_red()
            )
        self._rewind = True
        return None

    def set_loop_times(self, times: str) -> discord.Embed:
        try:
            self._loop = int(times)
            description_fragment = f"loop {self._loop} time{'s' if self._loop != 1 else ''}" if self._loop != 0 else "not loop and play the next queued track once the current track finishes"
        except ValueError:
            self._loop = -1 if times.lower() == "forever" else 0
            description_fragment = "loop forever"
        return discord.Embed(
            title="Track Loop Status",
            description=f"The current track will {description_fragment}",
            color=discord.Color.blue()
        ).set_footer(
            text="To loop forever, do `m!loop forever`\nTo stop looping, do `m!loop stop`"
        )

    @property
    def loop_status(self) -> str:
        return f"loop {self._loop} time{'s' if self._loop != 1 else ''}" if self._loop >= 1 else "loop forever" if self._loop == -1 else "not loop"

    async def play(self) -> AudioTrack:
        self._last_update = 0
        self._last_position = 0
        self.position_timestamp = 0
        self.paused = False

        if not self._rewind:
            if self._loop == 0:
                track = self.queue.popleft()
                self.session_queue.appendleft(track)
            else:
                track = self.current
                self._loop -= 0 if self._loop == -1 else 1
            self._index = 1
        else:
            self._rewind = False
            # State of self.current has not been incremented to previous track
            # Therefore append current track to queue because we will need to play
            # The current song after the rewind has finished
            self.queue.append(self.current)
            # Set track equal to index (starts at 1), because index 0 is the currently playing one
            # self._index >= 1 will pick previously played tracks in the reverse order they were
            # played
            track = self.session_queue[self._index]
            self._index += 1

        self.current = track
        await self.node._send(op="play", guildId=self.guild_id, track=track.track)
        await self.node._dispatch_event(TrackStartEvent(self, self.current))
        return self.current
