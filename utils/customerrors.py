import discord
from discord.ext import commands


class TagNotFound(commands.CommandError):
    """Error raised when user tries to invoke a tag that does not currently exist in the current guild

    Args:
        tag (str): name of the tag
    """
    def __init__(self, tag: str):
        self.tag = tag


class TagAlreadyExists(commands.CommandError):
    """Error raised when user tries to create a tag that already exists

    Args:
        tag (str): name of the tag
    """
    def __init__(self, tag: str):
        self.tag = tag


class NotTagOwner(commands.CommandError):
    """Error raised when the user tries to edit or delete a tag they do not own

    Args:
        tag (str): name of the tag
    """
    def __init__(self, tag: str):
        self.tag = tag


class UserNoTags(commands.CommandError):
    """Error raised when the user tries to list a tag but doesn't own any tags

    Args:
        member (discord.Member): the discord.Member instance
    """
    def __init__(self, member: discord.Member):
        self.member = member


class NoSimilarTags(commands.CommandError):
    """Error raised when the user searches a tag but no similar or exact results were returned

    Args:
        query (str): the query that the user searched for
    """
    def __init__(self, query: str):
        self.query = query


class CannotPaginate(commands.CommandError):
    """Error raised when the paginator cannot paginate

    Args:
        message (str): message that will be sent in traceback
    """
    def __init__(self, message):
        self.message = message
