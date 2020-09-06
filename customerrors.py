from discord.ext import commands


class TagNotFound(commands.CommandError):

    def __init__(self, tag):
        self.tag = tag


class TagAlreadyExists(commands.CommandError):

    def __init__(self, tag):
        self.tag = tag