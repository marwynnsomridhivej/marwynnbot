import asyncio
from asyncio import transports
import pickle


class MBCacheServerProtocol(asyncio.Protocol):
    def connection_made(self, transport: transports.BaseTransport) -> None:
        peername = transport.get_extra_info("peername", "Unknown")
        print(f"Connection established from {peername}")
        self.transport = transport

    def data_received(self, data: bytes) -> None:
        from .mbplayer import _cache
        unpickled: dict = pickle.loads(data)
        query = unpickled["query"]
        data = unpickled["data"]
        if not query in _cache:
            _cache[query] = data
        self.transport.close()


class MBCacheClientProtocol(asyncio.Protocol):
    def __init__(self, data, on_con_lost: asyncio.Future) -> None:
        self._data = data
        self.on_con_lost = on_con_lost

    def connection_made(self, transport: transports.WriteTransport) -> None:
        data = pickle.dumps(self._data)
        transport.write(data)
        print(f"Sending data {self._data}")

    def data_received(self, data: bytes) -> None:
        return

    def connection_lost(self, exc) -> None:
        print("Disconnected from server")
        self.on_con_lost.set_result(True)