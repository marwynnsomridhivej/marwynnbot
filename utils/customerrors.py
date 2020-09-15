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


class NoPremiumGuilds(commands.CommandError):
    """Error raised when there are no guilds that are MarwynnBot Premium guilds
    """
    def __init__(self):
        self.message = "There are no servers registered as MarwynnBot Premium servers"


class NoPremiumUsers(commands.CommandError):
    """Error raised when the current guild contains no MarwynnBot Premium users
    """
    def __init__(self):
        self.message = "This server does not have any MarwynnBot Premium members \:("


class NotPremiumGuild(commands.CommandError):
    """Error raised when the current guild is not a MarwynnBot Premium guild

    Args:
        guild (discord.Guild): the current guild
    """
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.id = self.guild.id
        self.name = self.guild.name


class NotPremiumUser(commands.CommandError):
    """Error raised when the current user is not a MarwynnBot Premium user

    Args:
        commands (discord.User): the current user
    """
    def __init__(self, user: discord.User):
        self.user = user
        self.id = self.user.id
        self.name = self.user.display_name