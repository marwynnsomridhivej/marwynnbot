import discord
from discord.ext import commands
from utils import SubcommandPaginator, GlobalCMDS, SetupPanel


gcmds = GlobalCMDS()


class Polls(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        global gcmds
        self.bot = bot
        gcmds = GlobalCMDS(self.bot)
        self.bot.loop.create_task(self.init_polls())

    async def init_polls(self):
        await self.bot.wait_until_ready()
        async with self.bot.db.acquire() as con:
            await con.execute("CREATE TABLE IF NOT EXISTS polls(message_id bigint PRIMARY KEY, channel_id bigint, "
                              "author_id bigint, max_count smallint DEFAULT 1, poll_content text, created_at NUMERIC, "
                              "active boolean DEFAULT TRUE, end_time NUMERIC DEFAULT NULL)")
            await con.execute("CREATE TABLE IF NOT EXISTS polls_reaction(message_id bigint, emoji text, "
                              "amount NUMERIC DEFAULT 0)")
        return

    async def send_poll_help(self, ctx) -> discord.Message:
        pfx = f"{await gcmds.prefix(ctx)}poll"
        description = ("MarwynnBot has a highly customisable polling feature which allows "
                       "you to create and manage polls in servers you moderate/own. You can create "
                       "polls with up to 10 answer choices and customise the maximum answers users can "
                       f"choose at once. The base command is `{pfx}`. Here are all the polling commands")
        pcreate = (f"**Usage:** `{pfx} create`",
                   "**Returns:** An interactive setup panel that will guide you to creating a poll",
                   "**Aliases:** `set` `start`")
        pfinish = (f"**Usage:** `{pfx} finish [message_id]`",
                   "**Returns:** A confirmation embed which once confirmed, will mark the poll as finished "
                   "and display its results",
                   "**Aliases:** `complete` `done`",
                   "**Note:** The original poll message will be deleted, and a new message will be sent in that "
                   "same channel that will display the results of the poll. This action cannot be undone")
        pedit = (f"**Usage:** `{pfx} edit [message_id]`",
                 "**Returns:** An interactive setup panel that will guide you to editing an active poll",
                 "**Aliases:** `edit` `modify` `change`",
                 "**Note:** `[message_id]`must be the message ID of a poll that you have created. "
                 "You may not edit a poll created by another user, even if you are the server owner")
        plist = (f"**Usage:** `{pfx} list`",
                 "**Returns:** A paginated list of all active polls in the server",
                 "**Aliases:** `ls` `show`",
                 "**Note:** Only the active polls will be displayed. All finished or inactive polls "
                 "will not be displayed through this command")
        pmode = (f"**Usage:** `{pfx} mode [mode] (message_id)*va`",
                 "**Returns:** A confirmation embed which once confirmed, will edit the mode of the "
                 "specified polls to the mode specified",
                 "**Aliases:** `cm`",
                 "**Note:** You may only change the mode of the polls you own. "
                 "`[mode]` may be a number between 1 and 10 inclusive, which will designate the maximum "
                 "amount of options a member can choose at a time. "
                 f"If `(message_id)*va` is unspecified, it will change the mode of all the currently active "
                 "polls you own to the mode specified in `[mode]`")
        ptitle = (f"**Usage:** `{pfx} title [title] [message_id]`",
                  "**Returns:** A confirmation embed which once confirmed, will edit the title of the specified "
                  "poll to the title specified",
                  "**Aliases:** `ct`",
                  "**Note:** You may only change the title of the polls you own. "
                  "`[title]` must be at most 256 characters (including whitespace)")
        pdescription = (f"**Usage:** `{pfx} description [description] [message_id]`",
                        "**Returns:** A confirmation embed which once confirmed, will edit the description "
                        "of the specified poll to the description specified",
                        "**Aliases:** `cd` `content`",
                        "**Note:** You may only change the description of the polls you own. "
                        "`[description]` must be at most 2048 characters (including whitespace)")
        pchoices = (f"**Usage:** `{pfx} choices [message_id]`",
                    "**Returns:** An interactive setup panel that will guide you to editing the "
                    "choices of the specified poll",
                    "**Aliases:** `options` `cc`",
                    "**Note:** You may only change the choices of the polls you own. ")
        nv = [("Create", pcreate), ("Finish", pfinish), ("Edit", pedit),
              ("List", plist), ("Mode", pmode), ("Title", ptitle),
              ("Description", pdescription), ("Choices", pchoices)]
        embed = discord.Embed(title="Polls Help", description=description, color=discord.Color.blue())
        pag = SubcommandPaginator(ctx, entries=[(name, value, False) for name, value in nv],
                                  per_page=3, show_entry_count=False, embed=embed)
        return await pag.paginate()

    @commands.group(invoke_without_command=True,
                    aliases=['polls'],
                    desc="Displays the help command for polls",
                    usage="poll")
    async def poll(self, ctx):
        return await self.send_poll_help(ctx)

    @poll.command(aliases=['set', 'start', 'create'])
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def poll_create(self, ctx):
        embed = discord.Embed(title="Poll Setup",
                              description=f"{ctx.author.mention}, welcome to MarwynnBot's iteractive "
                              "setup panel! Follow all steps to create a working poll!",
                              color=discord.Color.blue())
        embed.set_footer(text='To cancel at any time during this setup, enter "cancel"')
        sp = SetupPanel(ctx, self.bot, timeout=30, name="create poll",
                        embed=embed, has_intro=True, cancellable=True)
        embed1 = embed.copy()
        embed1.description = (f"{ctx.author.mention}, please tag the channel you would like this poll to be "
                             "sent in")
        embed2 = embed.copy()
        embed2.description = (f"{ctx.author.mention}, input what you would like the poll description to be. "
                             "This is the message that will appear above the options you will provide later")
        sp.until_finish("chain", func_names=['channel', 'message'], embeds=[embed1, embed2], timeouts=[30, 300])
        print(await sp.start())


def setup(bot):
    bot.add_cog(Polls(bot))
