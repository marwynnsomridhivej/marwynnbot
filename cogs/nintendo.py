import re
import discord
from discord.ext import commands
from utils import globalcommands, customerrors


gcmds = globalcommands.GlobalCMDS()
FC_REGEX = re.compile(r"SW-[\d]{4}-[\d]{4}-[\d]{4}")


class Nintendo(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        global gcmds
        self.bot = bot
        self.bot.loop.create_task(self.init_nintendo())
        gcmds = globalcommands.GlobalCMDS(self.bot)

    async def init_nintendo(self):
        await self.bot.wait_until_ready()
        async with self.bot.db.acquire() as con:
            await con.execute("CREATE TABLE IF NOT EXISTS nintendo(user_id bigint PRIMARY KEY, "
                              "friend_code text, games text[])")
        return

    async def send_nintendo_help(self, ctx):
        pfx = f"{await gcmds.prefix(ctx)}nintendo"
        description = (f"MarwynnBot's various Nintendo features allows users to register their Nintendo Switch friend "
                       "code and any games they play. Connect with other people and make some new friends! MarwynnBot "
                       "respects your privacy and will allow you to register and unregister your information at "
                       "any time")
        register = (f"**Usage:** `{pfx} register`",
                    "**Returns:** An embed that confirms you have successfully registered your information",
                    "**Aliases:** `reg`")
        friend_code = (f"**Usage:** `{pfx} friendcode [switch_friendcode]`")


def setup(bot):
    bot.add_cog(Nintendo(bot))
