import discord
from discord.ext import commands


class Stats:
    def __init__(self, client=None):
        self.client = client

    @property
    def client(self):
        return self.client

    @client.setter
    def client(self, client):
        if isinstance(client, commands.AutoShardedBot):
            self.client = client
        else:
            raise TypeError(f"The passed client is of type {type(client)}, requires type commands.AutoShardedBot")

    @client.deleter
    def client(self):
        del self.client