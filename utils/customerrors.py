from discord.ext import commands


class TagNotFound(commands.CommandError):
    """Error raised when user tries to invoke a tag that does not currently exist in the current guild

    Args:
        tag (str): name of the tag
    """
    def __init__(self, tag):
        self.tag = tag


class TagAlreadyExists(commands.CommandError):
    """Error raised when user tries to create a tag that already exists

    Args:
        tag (str): name of the tag
    """
    def __init__(self, tag):
        self.tag = tag


class UserNoTags(commands.CommandError):
    """Error raised when the user tries to list a tag but doesn't own any tags

    Args:
        member (discord.Member): the discord.Member instance
    """
    def __init__(self, member):
        self.member = member


class CannotPaginate(commands.CommandError):
    """Error raised when the paginator cannot paginate

    Args:
        message (str): message that will be sent in traceback
    """
    def __init__(self, message):
        self.message = message
