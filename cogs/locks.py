import discord
from discord.ext import commands
from utils import globalcommands, customerrors, paginator

gcmds = globalcommands.GlobalCMDS()


class Locks(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        global gcmds
        self.bot = bot
        gcmds = globalcommands.GlobalCMDS(self.bot)
        self.bot.loop.create_task(self.init_locks())

    async def init_locks(self):
        await self.bot.wait_until_ready()
        async with self.bot.db.acquire() as con:
            await con.execute("CREATE TABLE IF NOT EXISTS locks(channel_id bigint PRIMARY KEY, type text, guild_id bigint, author_id bigint)")

    async def locks_help(self, ctx):
        pfx = f"{await gcmds.prefix(ctx)}lock"
        description = (f"{ctx.author.mention}, the base command is `{pfx}`. Locks are designed to prevent MarwynnBot from "
                       "executing commands in channels where you don't want MarwynnBot commands to be run. This can be "
                       "useful if you are having trouble specifying permissions in your server/channel settings, or "
                       "if you have a designated bots channel where you want users to be able to invoke MarwynnBot from. "
                       "With MarwynnBot, you can lock specific channels or lock every channel but specific channels. "
                       "\n\nHere are all the subcommands")
        lset = (f"**Usage:** `{pfx} set [#channel]*va`",
                "**Returns:** A confirmation panel that will let the user confirm they would like to lock the specified channels",
                "**Alaises:** `-s`, `apply` `create`",
                "**Special Cases:** [#channel] must be channel tags. Multiple channels can be specified by separating the tags "
                "by commas. After confirmation, MarwynnBot will no longer respond to any commands invoked in those channels")
        llist = (f"**Usage:** `{pfx} list`",
                 "**Returns:** A list of all channels that are locked",
                 "**Aliases:** `-ls` `show`")
        lunlock = (f"**Usage:** `{pfx} unlock [#channel]*va`",
                   "**Returns:** A confirmation panel that will let the user confirm they would like to unlock the specified channels",
                   "**Aliases:** `ul` `-rm` `remove` `delete` `cancel`",
                   "**Special Cases:** [#channel] must be channel tags. Multiple channels can be specified by separating the tags "
                    "by commas. After confirmation, MarwynnBot will once again respond to any commands invoked in those channels",
                    f"**Note:** *this command can also be invoked with `{await gcmds.prefix(ctx)}unlock [#channel]\*va*")


def setup(bot):
    bot.add_cog(Locks(bot))
