import asyncio
import discord
from discord.ext import commands
from utils import globalcommands, paginator, context


gcmds = globalcommands.GlobalCMDS()
reactions = ["✅", "🛑"]


class Redirects(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        global gcmds
        self.bot = bot
        gcmds = globalcommands.GlobalCMDS(self.bot)
        self.bot.loop.create_task(self.init_redirects())

    async def init_redirects(self):
        await self.bot.wait_until_ready()
        async with self.bot.db.acquire() as con:
            await con.execute("CREATE TABLE IF NOT EXISTS redirects(type text, command text, channel_id bigint, "
                              "guild_id bigint, author_id bigint)")

    async def get_redirect_help(self, ctx):
        rd = f"{await gcmds.prefix(ctx)}redirect"
        description = (f"{ctx.author.mention}, the base command for redirects is `{rd}`. This command is used to instruct "
                       "MarwynnBot to redirect the output of a command to a specific channel. Redirects will only work "
                       "for MarwynnBot since MarwynnBot cannot truly redirect other bots' outputs without causing some features "
                       "to break.\n\nHere are the available subcommands for redirect")
        rset = (f"**Usage:** `{rd} set [#channel] [command]*va`",
                "**Returns:** A confirmation embed that requires the user to confirm that they would like the output for "
                "these commands to be redirected to the specified channel",
                "**Aliases:** `-s` `apply`",
                "**Special Cases:** The `[command]*va` must be a list of commands separated by commas, or \"all\" "
                "to set redirects for all commands")
        rlist = (f"**Usage:** `{rd} list (#channel)`",
                 "**Returns:** A list of all the redirects this server implements that redirect to the specified channel",
                 "**Aliases:** `-ls` `show`",
                 "**Special Cases:** If `(#channel)` is not specified, it will show all the redirects that this server "
                 "implements for all commands with redirects")
        rremove = (f"**Usage:** `{rd} remove [command]*va`",
                   "**Returns:** A confirmation embed that requires the user to confirm they would like to remove the redirect "
                   "for the specified commands",
                   "**Aliases:** `-rm` `delete` `cancel`",
                   "**Special Cases:** The `[command]*va` must be a list of commands separated by commas, or \"all\" to "
                   "remove all redirects for all commands")
        important_note = ("An important thing to note is that when setting the redirect for all commands at once, it will "
                          "be assigned the type `all`, and when setting the redirect for specific commands or a list of commands, "
                          "it will be assigned the type `override`. Essentially this means that when you set the redirect "
                          "for a specific command, it will use that redirect, even if a global redirect was set. This is "
                          "useful for when you want to redirect MarwynnBot's output for all commmands to a specific channel "
                          "EXCEPT for a couple commands. This is achieved by assigning their redirects seperately as stated above. "
                          "Subcommand redirects are not supported, so the redirect will apply to all commands within the "
                          "command group if the base command is a group.")

        nv = [("Set", rset), ("List", rlist), ("Remove", rremove), ("Important Info", important_note)]

        embed = discord.Embed(title="Redirect Help", description=description, color=discord.Color.blue())
        for name, value in nv:
            embed.add_field(name=name, value="> " + "\n> ".join(value), inline=False)

        return await ctx.channel.send(embed=embed)

    @commands.group(invoke_without_command=True, aliases=['rd'])
    @commands.has_permissions(manage_guild=True)
    async def redirect(self, ctx):
        await self.get_redirect_help(ctx)

    @redirect.command(aliases=['-s', 'set', 'apply'])
    async def redirect_set(self, ctx, channel: discord.TextChannel, *, cmds: str):
        if cmds != "all":
            cmds = cmds.replace(" ", "").split(",")
            realcmds = [name.lower() for name in cmds if name in [command.name.lower() for command in self.bot.commands]]
            description = f"{ctx.author.mention}, the commands `{'` `'.join(realcmds)}` will be redirected to {channel.mention}."
        else:
            description = f"{ctx.author.mention}, all commands will be redirected to {channel.mention}."
            realcmds = None

        panel = await gcmds.confirmation(ctx, description)
        try:
            for reaction in reactions:
                await panel.add_reaction(reaction)
        except Exception:
            return await gcmds.cancelled(ctx, "set redirect")

        def reacted(reaction: discord.Reaction, user: discord.User):
            return reaction.emoji in reactions and user.id == ctx.author.id and reaction.message.id == panel.id

        try:
            result = await self.bot.wait_for("reaction_add", check=reacted, timeout=30)
        except asyncio.TimeoutError:
            return await gcmds.timeout(ctx, "set redirect", 30)
        if result[0].emoji == reactions[0]:
            async with self.bot.db.acquire() as con:
                if realcmds:
                    for name in realcmds:
                        result = await con.fetchval(f"SELECT type FROM redirects WHERE guild_id={ctx.guild.id} AND command={name}")
                    if not result:
                        values = '($tag$$tag$)'
                        await con.execute("INSERT INTO redirects(type, command, channel_id, guild_id, author_id) VALUES {values}")


def setup(bot):
    bot.add_cog(Redirects(bot))
