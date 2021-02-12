import asyncio
import logging
import os
import pickle
from datetime import datetime
from typing import Dict

import aiohttp
from lavalink import Client, NodeManager, PlayerManager

from .mbplayer import MBPlayer


class MBClient(Client):
    def __init__(self, user_id: int, player: MBPlayer = MBPlayer, regions: dict = None, connect_back: bool = False):
        if not isinstance(user_id, int):
            raise TypeError('user_id must be an int (got {}). If the type is None, '
                            'ensure your bot has fired "on_ready" before instantiating '
                            'the Lavalink client. Alternatively, you can hardcode your user ID.'
                            .format(user_id))

        self._user_id = str(user_id)
        self.node_manager = NodeManager(self, regions)
        self.player_manager = PlayerManager(self, player)
        self._connect_back = connect_back
        self._logger = logging.getLogger('lavalink')

        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=None)
        )

    async def __get_tracks(self, query: str, guild_id: int, cache: dict, loop) -> Dict:
        current_timestamp = int(datetime.now().timestamp())
        res = await self.get_tracks(query, node=None)
        res_present = res and res.get("tracks")
        if res_present and res.get("loadType") != "PLAYLIST_LOADED":
            res["tracks"] = [res["tracks"][0]]
        data = {
            "data": res if res_present else None,
            "timestamp": current_timestamp,
            "cached_in": guild_id,
            "expire_at": -1 if res_present else current_timestamp + 86400
        }
        cache[query] = data
        export = {
            "query": query,
            "data": data,
        }
        try:
            _, writer = await asyncio.open_connection(
                host=os.getenv("MBC_CON_HOST"),
                port=int(os.getenv("MBC_CON_PORT")),
                loop=loop,
            )
            writer.write(pickle.dumps(export))
            await writer.drain()
            writer.close()
        except Exception:
            pass
        return data

    @staticmethod
    def _handle_task_result(task: asyncio.Task):
        try:
            task.result()
        except Exception:
            pass

    async def efficient_cache_rebuild(self, guild_id: int, future: asyncio.Future):
        loop = asyncio.get_running_loop()
        from .mbplayer import _cache as cache
        for query in cache:
            task = loop.create_task(self.__get_tracks(query, guild_id, cache, loop))
            task.add_done_callback(self._handle_task_result)
        future.set_result(True)
