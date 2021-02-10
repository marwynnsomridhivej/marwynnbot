import logging

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
