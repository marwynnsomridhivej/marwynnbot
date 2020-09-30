import random
from datetime import datetime

import discord
from discord.ext import commands
from utils import globalcommands

gcmds = globalcommands.GlobalCMDS()


class Help(commands.Cog):

    def __init__(self, bot):
        global gcmds
        self.bot = bot
        gcmds = globalcommands.GlobalCMDS(self.bot)

    async def syntaxEmbed(self, ctx, commandName, syntaxMessage, exampleUsage=None, exampleOutput=None,
                          userPerms=None, botPerms=None, specialCases=None, thumbnailURL="https://www.jing.fm/clipimg"
                                                                                         "/full/71-716621_transparent"
                                                                                         "-clip-art-open-book-frame"
                                                                                         "-line-art.png",
                          delete_after=None):
        embed = discord.Embed(title=f"{commandName} Help",
                              color=discord.Color.blue())
        embed.add_field(name="Command Syntax",
                        value=f'{syntaxMessage}')
        if exampleUsage:
            embed.add_field(name="Example Usage",
                            value=exampleUsage,
                            inline=False)
        if exampleOutput:
            embed.add_field(name="Output",
                            value=exampleOutput,
                            inline=False)
        cmdName = self.bot.get_command(ctx.command.qualified_name)
        aliases = cmdName.aliases
        if aliases:
            embed.add_field(name="Aliases",
                            value=f"`{'` `'.join(aliases)}`",
                            inline=False)
        if userPerms:
            embed.add_field(name="User Permissions Required",
                            value=userPerms,
                            inline=False)
        if botPerms:
            embed.add_field(name="Bot Permissions Required",
                            value=botPerms,
                            inline=False)
        if specialCases:
            embed.add_field(name="Special Cases",
                            value=specialCases,
                            inline=False)
        if thumbnailURL:
            embed.set_thumbnail(url=thumbnailURL)

        timestamp = f"Executed by {ctx.author.display_name} " + "at: {:%m/%d/%Y %H:%M:%S}".format(datetime.now())
        embed.set_footer(text=timestamp,
                         icon_url=ctx.author.avatar_url)

        await ctx.channel.send(embed=embed, delete_after=delete_after)

    @commands.group(invoke_without_subcommand=True, aliases=['h'])
    async def help(self, ctx):

        timestamp = f"Executed by {ctx.author.display_name} " + "at: {:%m/%d/%Y %H:%M:%S}".format(datetime.now())
        helpEmbed = discord.Embed(title="MarwynnBot Help Menu",
                                  color=discord.Color.blue(),
                                  url="https://discord.gg/fYBTdUp",
                                  description="These are all the commands I currently support! Type"
                                  f"\n```{await gcmds.prefix(ctx)}help [command]```\n to get help on "
                                  f"that specific command")
        helpEmbed.set_thumbnail(
            url="https://www.jing.fm/clipimg/full/71-716621_transparent-clip-art-open-book-frame-line-art.png")
        helpEmbed.set_author(name="MarwynnBot",
                             icon_url=ctx.me.avatar_url)
        helpEmbed.set_footer(text=timestamp,
                             icon_url=ctx.author.avatar_url)

        cogNames = [i for i in self.bot.cogs]
        gameNames = ['Blackjack', 'Coinflip', 'ConnectFour', 'Slots', 'UNO']
        for name in gameNames:
            cogNames.remove(name)
        cogs = [self.bot.get_cog(j) for j in cogNames]
        strings = {}
        for name in cogNames:
            cog_commands = self.bot.get_cog(name).get_commands()
            strings.update({name.lower(): [command.name.lower() for command in cog_commands]})

        actionCmds = f"`{await gcmds.prefix(ctx)}actions` *for a full list*"
        debugCmds = f"`{'` `'.join(strings['debug'])}`"
        funCmds = f"`{'` `'.join(strings['fun'])}`"
        gamesCmds = f"`{'` `'.join(strings['games'])}` `blackjack` `coinflip` `connectfour` " \
            f"`slots` `uno`"
        helpCmds = f"`{'` `'.join(strings['help'])}`"
        minecraftCmds = f"`{await gcmds.prefix(ctx)}minecraft` *for a full list*"
        moderationCmds = f"`{'` `'.join(strings['moderation'])}`"
        musicCmds = f"`{'` `'.join(strings['music'])}`"
        ownerCmds = f"`{'` `'.join(strings['owner'])}`"
        pokedexCmds = f"`{await gcmds.prefix(ctx)}pokedex` *for a full list*"
        roleCmds = f"`{'` `'.join(strings['roles'])}`"
        redditCmds = f"`{await gcmds.prefix(ctx)}reddit` *for a full list*"
        utilityCmds = f"`{'` `'.join(strings['utility'])}`"
        welcomeCmds = f"`{'` `'.join(strings['welcome'])}`"

        cmd_list = [("Help", helpCmds), ("Actions", actionCmds), ("Debug", debugCmds), ("Fun", funCmds), ("Games", gamesCmds),
                    ("Minecraft", minecraftCmds), ("Moderation", moderationCmds), ("Music", musicCmds), ("Pokedex", pokedexCmds),
                    ("Roles", roleCmds), ("Reddit", redditCmds), ("Utility", utilityCmds), ("Welcome", welcomeCmds),
                    ("Owner Only", ownerCmds)]

        for name, value in cmd_list:
            helpEmbed.add_field(name=name,
                                value=value,
                                inline=False)
        await ctx.send(embed=helpEmbed)

    # =================================================
    # Help
    # =================================================

    @help.command(aliases=['h', 'help'])
    async def _help(self, ctx):
        commandName = 'Command Specific'
        syntaxMessage = f"`{await gcmds.prefix(ctx)}help [commandName]`"
        exampleUsage = f"`{await gcmds.prefix(ctx)}help ping`"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               exampleUsage=exampleUsage)

    # =================================================
    # Debug
    # =================================================

    @help.command()
    async def ping(self, ctx):
        commandName = 'Ping'
        syntaxMessage = f"`{await gcmds.prefix(ctx)}ping`"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage)

    @help.command()
    async def shard(self, ctx):
        commandName = "Shard"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}shard [optional \"count\"]`"
        specialCases = "If the optional argument is \"count\", it will display the total number of shards"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command(aliases=['flag'])
    async def report(self, ctx):
        commandName = "Report",
        syntaxMesage = f"`{await gcmds.prefix(ctx)}report [thing] [message]`"
        specialCases = "**Valid Arguments**\n`[thing]`: `bug` `update`\n\nThe `[message]` argument must be present for" \
                       "the report message to be sent"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMesage,
                               specialCases=specialCases)

    # =================================================
    # Fun
    # =================================================

    @help.command(aliases=['8b', '8ball'])
    async def _8ball(self, ctx):
        commandName = 'Magic 8 Ball'
        syntaxMessage = f"`{await gcmds.prefix(ctx)}8ball [question]`"
        exampleUsage = f"`{await gcmds.prefix(ctx)}8ball Is this a good bot?`"
        thumbnailURL = 'https://www.horoscope.com/images-US/games/game-magic-8-ball-no-text.png'
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               exampleUsage=exampleUsage,
                               thumbnailURL=thumbnailURL)

    @help.command()
    async def choose(self, ctx):
        commandName = 'Choose'
        syntaxMessage = f"`{await gcmds.prefix(ctx)}choose [strings separated by " + "\"or\"" + " ]`"
        exampleUsage = f"`{await gcmds.prefix(ctx)}choose Chocolate or Vanilla or Strawberry or Sherbet or No ice " \
                       f"cream bc I hate it?` "
        choices = ['Chocolate', 'Vanilla', 'Strawberry', 'Sherbet', 'No ice cream because I hate it']
        exampleOutput = random.choice(choices)
        specialCases = "The word \"or\" cannot be a valid choice for the bot to pick from due to it being the splitter."
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               exampleUsage=exampleUsage,
                               exampleOutput=exampleOutput,
                               specialCases=specialCases)

    @help.command(aliases=['gifsearch', 'searchgif', 'searchgifs', 'gif', 'gifs'])
    async def gifSearch(self, ctx):
        commandName = 'GifSearch'
        syntaxMessage = f"`{await gcmds.prefix(ctx)}gifsearch [optional amount] [searchTerm]`"
        exampleUsage = f"`{await gcmds.prefix(ctx)}gifsearch excited`"
        specialCases = "If the `[optional amount]` argument is specified, Tenor will return that amount of gifs" \
                       "\n\nIf the `tenor_api.yaml` file is not present, it will be created and contents initialised " \
                       "as:\n```yaml\napi_key: API_KEY_FROM_TENOR\n```\nGet an API Key from Tenor and replace " \
                       "`API_KEY_FROM_TENOR` with it"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               exampleUsage=exampleUsage,
                               specialCases=specialCases)

    @help.command(aliases=['imgur', 'imgursearch'])
    async def imgurSearch(self, ctx):
        commandName = "ImgurSearch"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}imgursearch [optional amount] [searchTerm]`"
        exampleUsage = f"{await gcmds.prefix(ctx)}imgursearch Toad"
        specialCases = "If the `[optional amount]` argument is specified, Imgur will return that amount of images" \
                       "\n\nIf the `imgur_api.yaml` file is not present, it will be created and contents initialised " \
                       "as:\n```yaml\nClient-ID: CLIENT_ID_FROM_IMGUR\n```\nGet a bot ID from Imgur and replace " \
                       "`CLIENT_ID_FROM_IMGUR` with it"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               exampleUsage=exampleUsage,
                               specialCases=specialCases)

    @help.command(aliases=['isabellepic', 'isabelleemote', 'belle', 'bellepic', 'belleemote'])
    async def isabelle(self, ctx):
        commandName = "Isabelle"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}isabelle [optional amount]`"
        specialCases = "If the `[optional amount]` argument is specified, it will send that many images"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command(aliases=['peppapic', 'ppic', 'ppig'])
    async def peppa(self, ctx):
        commandName = "Peppa"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}peppa [optional amount]`"
        specialCases = "If the `[optional amount]` argument is specified, it will send that many images"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command(aliases=['randomcat', 'cat'])
    async def randomCat(self, ctx):
        commandName = "RandomDog"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}randomcat [optional amount]`"
        specialCases = "If specified, `[optional amount]` is limited to at most 50. Otherwise, defaults to 1"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command(aliases=['woof', 'dog', 'doggo', 'randomdog'])
    async def randomDog(self, ctx):
        commandName = "RandomDog"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}randomdog [optional amount]`"
        specialCases = "If specified, `[optional amount]` is limited to at most 50. Otherwise, defaults to 1"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command()
    async def say(self, ctx):
        commandName = 'Say'
        syntaxMessage = f"`{await gcmds.prefix(ctx)}say`"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage)

    @help.command(alises=['toadpic', 'toademote'])
    async def toad(self, ctx):
        commandName = 'Toad'
        syntaxMessage = f"`{await gcmds.prefix(ctx)}toad [optional amount]`"
        specialCases = "If the `[optional amount]` argument is specified, it will send that many images"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    # =================================================
    # Games
    # =================================================

    @help.command(aliases=['bal'])
    async def balance(self, ctx):
        commandName = "Balance"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}balance [optional members @mentions]`"
        specialCases = "If `[optional members @mentions]` is specified, it will display the balances for only those " \
                       "members. If unspecified, defaults to your own balance "
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command(aliases=['gamestats', 'gs'])
    async def gameStats(self, ctx):
        commandName = "GameStats"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}gamestats [optional user @mention] [optional gameName]`"
        specialCases = 'If the `[optional gameName]` argument is not specified, it will show your stats for all the ' \
                       'games you have played at least once before' \
                       "\n\nIf the `[optional user @mention]` argument is not specified, it will default to yourself"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command()
    async def transfer(self, ctx):
        commandName = "Transfer"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}transfer [amount] [user @mention or multiple @mentions]`"
        specialCases = "If the `[user @mention or multiple @mentions]` arg is more than one user, it will give `[" \
                       "amount]` to each user. You must have sufficient funds for sending to all users"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command(aliases=['bj', 'Blackjack'])
    async def blackjack(self, ctx):
        commandName = "Blackjack"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}blackjack [betAmount]`"
        specialCases = "If `[betAmount]` is not specified, it will automatically bet 1 credit" \
                       "\n\nIf you do not have enough credits for the `[betAmount]` you will be unable to play"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command(aliases=['cf'])
    async def coinflip(self, ctx):
        commandName = "Coinflip"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}coinflip [optional betAmount] [optional face]`"
        specialCases = "If not specified:\n- `[optional betAmout]` defaults to `1`\n- `[optional face]` defaults to " \
                       "`heads` "
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command(aliases=['connectfour', 'c4', 'conn', 'connect'])
    async def connectFour(self, ctx):
        commandName = "ConnectFour"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}connectfour [opponent @mention]`"
        specialCases = "You can win a random amount of credits (between 1 - 5), with a very small chance " \
                       "of getting a jackpot of `1000000` credits"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command(aliases=['slot'])
    async def slots(self, ctx):
        commandName = "Slots"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}slots [optional betAmount or keyword]`"
        specialCases = "`[betAmount]` defaults to `1 credit` if otherwise specified\n Access the payout menu by " \
                       "entering `payout`, `rates`, or any `non-integer value` as the `[keyword]` "
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command()
    async def uno(self, ctx):
        commandName = "Uno"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}uno [opponent(s) @mention(s)]`"
        specialCases = "You can mention up to `9` other opponents" \
                       "\n\nYou will receive a random amount of credits that scales according to the amount of turns " \
                       "it took to establish a winner\n\n" \
                       "Cancel the game by typing `cancel` when it is your turn and you can place a card"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    # =================================================
    # Minecraft
    # =================================================

    @help.command(aliases=['mc'])
    async def minecraft(self, ctx):
        commandName = "Minecraft"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}minecraft`"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage)

    # =================================================
    # Moderation
    # =================================================

    @help.command(aliases=['clear', 'clean', 'chatclear', 'cleanchat', 'clearchat', 'purge'])
    async def chatclean(self, ctx):
        commandName = "ChatClean"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}chatclean [amount] [optional user @mention]`"
        userPerms = "`Manage Messages`"
        botPerms = userPerms
        specialCases = "When clearing chat indiscriminately, you can eliminate the `[amount]` argument and only 1 " \
                       "message will be cleared.\n\nWhen an `[optional user @mention]` is specified, the `[amount]` " \
                       "must also be specified."
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms,
                               botPerms=botPerms,
                               specialCases=specialCases)

    @help.command(aliases=['silence', 'stfu', 'shut', 'shush', 'shh', 'shhh', 'shhhh', 'quiet'])
    async def mute(self, ctx):
        commandName = "Mute"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}mute [user @mentions] [optional reason]`"
        userPerms = "`Manage Roles`"
        botPerms = userPerms
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms,
                               botPerms=botPerms)

    @help.command(aliases=['unsilence', 'unstfu', 'unshut', 'unshush', 'unshh', 'unshhh', 'unshhhh', 'unquiet'])
    async def unmute(self, ctx):
        commandName = "Unmute"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}unmute [user @mentions] [optional reason]`"
        userPerms = "`Manage Roles`"
        botPerms = userPerms
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms,
                               botPerms=botPerms)

    @help.command()
    async def kick(self, ctx):
        commandName = "Kick"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}kick [user @mentions] [optional reason]`"
        userPerms = "`Kick Members`"
        botPerms = userPerms
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms,
                               botPerms=botPerms)

    @help.command()
    async def ban(self, ctx):
        commandName = "Ban"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}ban [user @mentions] [optional deleteMessageDays] [optional reason]`"
        userPerms = "`Ban Members`"
        botPerms = userPerms
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms,
                               botPerms=botPerms)

    @help.command()
    async def unban(self, ctx):
        commandName = "Unban"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}ban [user @mentions or users + discriminators] [optional reason]`"
        userPerms = "`Unban Members`"
        botPerms = userPerms
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms,
                               botPerms=botPerms)

    @help.command()
    async def warn(self, ctx):
        commandName = "Warn"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}warn [@mentions] [reason]`"
        userPerms = "`Ban Members`"
        botPerms = userPerms
        specialCases = ("- 1st Warn - Nothing"
                        "\n- 2nd Warn - Mute for 10 minutes"
                        "\n- 3rd Warn - Kicked from the server"
                        "\n- 4th Warn - Banned from the server")
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms,
                               botPerms=botPerms,
                               specialCases=specialCases)

    @help.command(aliases=['offenses'])
    async def offense(self, ctx):
        commandName = "Offense"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}offense [@mention]`"
        specialCases = ("This command searches for all warnings that you have given. If you haven't given that user any "
                        "warnings, offense will return nothing, even if that user has warnings from other moderators")
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command()
    async def expunge(self, ctx):
        commandName = "Expunge"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}expunge [@mention]`"
        userPerms = "`Ban Members`"
        botPerms = userPerms
        specialCases = ("Instructions on how to expunge warn records will be given on an interactive panel")
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms,
                               botPerms=botPerms,
                               specialCases=specialCases)

    @help.command(aliases=['mod', 'mods', 'modsonline', 'mo'])
    async def modsOnline(self, ctx):
        commandName = "ModsOnline"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}modsonline`"
        specialCases = "If the server does not have a moderator role with the substring `moderator` (case " \
                       "insensitive), it will not detect that the server has a moderator role" \
                       "\n\nIf the mods have their status set to `invisible`, this command will not register them as " \
                       "being online"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    # =================================================
    # Music
    # =================================================

    @help.command()
    async def join(self, ctx):
        commandName = "Join"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}join`"
        userPerms = "`Connect to Voice Channel`"
        botPerms = userPerms
        specialCases = "You must currently be connected to a voice channel in order to use this command"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms,
                               botPerms=botPerms,
                               specialCases=specialCases)

    @help.command()
    async def play(self, ctx):
        commandName = "Play"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}play [query or url]`"
        specialCases = "`[query or url]` currently only supports YouTube queries and links. You can play livestreams " \
                       "as well"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command()
    async def queue(self, ctx):
        commandName = "Queue"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}queue [query or url]`"
        specialCases = "`[query or url]` currently only supports YouTube queries and links. You can play livestreams " \
                       "as well"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command(aliases=['clearqueue', 'qc'])
    async def queueclear(self, ctx):
        commandName = "Queue"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}queueclear"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage)

    @help.command()
    async def stop(self, ctx):
        commandName = "Stop"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}stop`"
        userPerms = "`Bot Owner`"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms)

    @help.command()
    async def leave(self, ctx):
        commandName = "Leave"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}leave`"
        specialCases = "You must currently be connected to a voice channel in order to use this command"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command()
    async def volume(self, ctx):
        commandName = "Volume"
        syntaxMessage = f"{await gcmds.prefix(ctx)}volume [integer]"
        specialCases = "``[integer]` must be a valid integer between 1 - 100"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command(aliases=['playlists'])
    async def playlist(self, ctx):
        commandName = "Playlist"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}playlist [optional operation]`"
        specialCases = "If `[optional operation]` is unspecified, it displays your saved playlists\n\n" \
                       "Valid arguments for `[optional operation]`:\n" \
                       "`add [playlistID] [url]` - adds track to playlist *(under development)*\n" \
                       "`load [playlistName]` - loads a playlist to queue\n" \
                       "`save` - saves current queue as a new playlist *alias=edit*\n" \
                       "`remove` - deletes a playlist *(under development)* *aliase=delete*"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    # =================================================
    # Utility
    # =================================================

    @help.command(aliases=['counters', 'used', 'usedcount'])
    async def counter(self, ctx):
        commandName = "Counter"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}counter [commandName] [optional \"global\"]`"
        exampleUsage = f"{await gcmds.prefix(ctx)}counter help"
        specialCases = 'If the `[commandName]` is not specified, it will display the count for all executed commands' \
                       "\n\nIf the `[optional \"global\"]` argument is not specified, it defaults to per server count"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               exampleUsage=exampleUsage,
                               specialCases=specialCases)

    @help.command()
    async def invite(self, ctx):
        commandName = "Invite"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}invite`"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage)

    @help.command()
    async def request(self, ctx):
        commandName = "Request"
        syntaxMessage = f"{await gcmds.prefix(ctx)}request"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage)

    @help.command(aliases=['p', 'checkprefix', 'prefix', 'prefixes'])
    async def _prefix(self, ctx):
        commandName = "Prefix"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}prefix`"
        exampleUsage = f"`{await gcmds.prefix(ctx)}prefix`"
        exampleOutput = f"`This server's prefix is: {await gcmds.prefix(ctx)}`\n\n`The global prefixes are:" \
                        f"`{self.bot.user.mention} or `mb `"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               exampleUsage=exampleUsage,
                               exampleOutput=exampleOutput)

    @help.command(aliases=['sp', 'setprefix'])
    async def setPrefix(self, ctx):
        commandName = "Set Prefix"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}setprefix [serverprefix]`"
        exampleUsage = f"`{await gcmds.prefix(ctx)}setprefix !m`"
        exampleOutput = "`Server prefix set to: !m`"
        specialCases = f"To reset the server prefix to bot default, enter `reset` as the `[serverprefix]` argument"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               exampleUsage=exampleUsage,
                               exampleOutput=exampleOutput,
                               specialCases=specialCases)

    @help.command(aliases=['emotes', 'serveremotes', 'serveremote', 'serverEmote', 'emojis', 'emoji'])
    async def serverEmotes(self, ctx):
        commandName = "Server Emotes"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}serveremotes [optional query]`"
        specialCases = "If `[optional query]` is specified, it will search for emotes with that substring in its name " \
                       "*(case sensitive)*"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command(aliases=['ss', 'serverstats', 'serverstatistics'])
    async def serverStats(self, ctx):
        commandName = "Server Stats"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}serverstats [optional \"reset\"]`"
        userPerms = '`Manage Server`'
        botPerms = userPerms
        specialCases = "If the `reset` argument is present, it will delete the currently active server stats channels" \
                       " and category\n\nYou will not be able to create another server stats panel if one" \
                       " already exists"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms,
                               botPerms=botPerms,
                               specialCases=specialCases)

    @help.command(aliases=['tz'])
    async def timezone(self, ctx):
        commandName = "Timezone"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}timezone [GMT time]`"
        exampleUsage = f"`{await gcmds.prefix(ctx)}timezone GMT+4`"
        exampleOutput = f"{ctx.author.mention}'s nickname will be changed to: `{ctx.author.display_name} [GMT+4]`"
        userPerms = '`Change Nickname`'
        botPerms = "`Manage Nicknames`"
        specialCases = "If the `[GMT time]` argument is `reset` or `r`, the tag will be removed and your nickname " \
                       "will be reset to default"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               exampleUsage=exampleUsage,
                               exampleOutput=exampleOutput,
                               userPerms=userPerms,
                               botPerms=botPerms,
                               specialCases=specialCases)

    # =================================================
    # Roles
    # =================================================

    @help.command()
    async def reactionrole(self, ctx):
        commandName = "ReactionRole"
        syntaxMessage = ""
        specialCases = "*Currently under development*"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    # =================================================
    # Reddit
    # =================================================

    @help.command(aliases=['reddithelp'])
    async def reddit(self, ctx):
        commandName = "Reddit"
        syntaxMessage = f"{await gcmds.prefix(ctx)}reddit"
        specialCases = "This command will bring up the reddit help panel where all the reddit commands are documented." \
                       "Please note that the name of the commands corresponds to the name of the subreddit the images " \
                       "are being pulled from. I have provided aliases so that those who are uncomfortable with the " \
                       "names of some subreddits can use a non-suggestive name to invoke the command\n\n" \
                       "**All of the images pulled are SFW**"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    # =================================================
    # Pokedex
    # =================================================

    @help.command(aliases=['dex'])
    async def pokedex(self, ctx):
        commandName = "Pokedex"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}pokedex`"
        specialCases = "This command will bring up the pokedex help panel that will detail all pokedex commands" \
                       "documented. "
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    # =================================================
    # Welcomer
    # =================================================

    @help.command(aliases=['welcome'])
    async def welcomer(self, ctx):
        commandName = "Welcomer"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}welcomer`"
        specialCases = "This command will bring up the welcomer help panel that will detail all welcomer commands"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    @help.command()
    async def leaver(self, ctx):
        commandName = "Leaver"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}leaver`"
        specialCases = "This command will bring up the leaver help panel that will detail all leaver commands"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               specialCases=specialCases)

    # =================================================
    # Owner
    # =================================================

    @help.command(aliases=['blist'])
    async def blacklist(self, ctx):
        commandName = "Blacklist"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}blacklist [type] [operation] [ID]`"
        userPerms = "`Bot Owner`"
        specialCases = "Valid Options for Arguments:\n" \
                       "`[type]`: `user` or `guild` *alias for guild is \"server\"*" \
                       "`[operation]`: `add` or `remove`" \
                       "`[ID]`: \nUser --> `user @mention` or `user ID`\nGuild --> `guild ID`"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms,
                               specialCases=specialCases)

    @help.command(aliases=['l', 'ld'])
    async def load(self, ctx):
        commandName = "Load"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}load [extension]`"
        userPerms = "`Bot Owner`"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms)

    @help.command(aliases=['ul', 'uld'])
    async def unload(self, ctx):
        commandName = "Unload"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}unload [extension]`"
        userPerms = "`Bot Owner`"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms)

    @help.command(aliases=['r', 'rl'])
    async def reload(self, ctx):
        commandName = "Reload"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}reload [optional extension]`"
        userPerms = "`Bot Owner`"
        specialCases = "If `[optional extension]` is not specified, it will reload all currently loaded extensions"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms,
                               specialCases=specialCases)

    @help.command(aliases=['taskkill'])
    async def shutdown(self, ctx):
        commandName = "Shutdown"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}shutdown`"
        userPerms = "`Bot Owner`"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms)

    @help.command(aliases=['balanceadmin', 'baladmin', 'balop'])
    async def balanceAdmin(self, ctx):
        commandName = "BalanceAdmin"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}balanceadmin [operation] [user @mention] [credit amount]`"
        userPerms = "`Bot Owner`"
        specialCases = "Valid Options for Arguments:\n" \
                       "`[operation]`: `set` `give` `remove`\n" \
                       "`[user @mention]`: Any user mention\n" \
                       "`[credit amount]`: Any non-negative integer"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms,
                               specialCases=specialCases)

    @help.command(aliases=['fleave'])
    async def forceleave(self, ctx):
        commandName = "ForceLeave"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}forceleave [optional guild ID]`"
        userPerms = "`Bot Owner`"
        specialCases = "If `[optional guild id]` is not specified, the bot will use the current guild's ID"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms,
                               specialCases=specialCases)

    @help.command(aliases=['dm', 'privatemessage'])
    async def privateMessage(self, ctx):
        commandName = "PrivateMessage"
        syntaxMessage = f"`{await gcmds.prefix(ctx)}privatemessage [user ID] [message]`"
        userPerms = "`Bot Owner`"
        await self.syntaxEmbed(ctx,
                               commandName=commandName,
                               syntaxMessage=syntaxMessage,
                               userPerms=userPerms)


def setup(bot):
    bot.add_cog(Help(bot))
