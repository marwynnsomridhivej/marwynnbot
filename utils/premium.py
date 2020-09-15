import discord
from discord.ext import commands
from utils import customerrors, globalcommands


def is_premium(*args, **kwargs):

    async def predicate(ctx, *args, **kwargs):
        db = globalcommands.db
        if not db:
            raise customerrors.NoPostgreSQL()
        async with db.acquire() as con:
            if kwargs.get('req_guild', False):
                result = await con.fetch(f"SELECT guild_id FROM premium WHERE guild_id = {ctx.guild.id}")
                if not result:
                    raise customerrors.NotPremiumGuild(ctx.guild)
            else:
                result = await con.fetch(f"SELECT user_id FROM premium WHERE user_id = {ctx.author.id}")
                if not result:
                    raise customerrors.NotPremiumUser(ctx.author)
        return True

    return commands.check(predicate)