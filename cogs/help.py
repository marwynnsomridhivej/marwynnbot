import random
import discord
import json
from discord.ext import commands


class Help(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "help" has been loaded')

    def prefix(self, commands, ctx):
        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)

        return prefixes[str(ctx.guild.id)]

    async def syntaxEmbed(self, ctx, commandName, syntaxMessage, exampleMessage=None, exampleOutput=None, aliases=None,
                          userPerms=None, botPerms=None, specialCases=None, thumbnailURL=None):
        embed = discord.Embed(title=f"{commandName} Help",
                              color=discord.Color.blue())
        embed.add_field(name="Command Syntax",
                        value=f'{syntaxMessage}')
        if exampleMessage is not None:
            embed.add_field(name="Example Usage",
                            value=exampleMessage,
                            inline=False)
        if exampleOutput is not None:
            embed.add_field(name="Output",
                            value=exampleOutput,
                            inline=False)
        if aliases is not None:
            embed.add_field(name="Aliases",
                            value=aliases,
                            inline=False)
        if userPerms is not None:
            embed.add_field(name="User Permissions Required",
                            value=userPerms,
                            inline=False)
        if botPerms is not None:
            embed.add_field(name="Bot Permissions Required",
                            value=botPerms,
                            inline=False)
        if specialCases is not None:
            embed.add_field(name="Special Cases",
                            value=specialCases,
                            inline=False)
        if thumbnailURL is not None:
            embed.set_thumbnail(url=thumbnailURL)
        await ctx.channel.send(embed=embed)

    @commands.group(aliases=['h'])
    async def help(self, ctx):
        await ctx.message.delete()
        if ctx.invoked_subcommand is None:
            helpEmbed = discord.Embed(title="MarwynnBot Help Menu",
                                      colour=discord.Colour(0x3498db),
                                      url="https://discord.gg/fYBTdUp",
                                      description="These are all the commands I currently support! Type"
                                                  f"`{self.prefix(self, ctx)}help [command]` to get help on that "
                                                  "specific command")
            helpEmbed.set_image(
                url="https://cdn.discordapp.com/avatars/623317451811061763/9bb63c734178694e8779aa102cb81062.png"
                    "?size=256")
            helpEmbed.set_thumbnail(
                url="https://cdn.discordapp.com/avatars/623317451811061763/9bb63c734178694e8779aa102cb81062.png"
                    "?size=128")
            helpEmbed.set_author(name="MarwynnBot",
                                 url="https://discord.gg/fYBTdUp",
                                 icon_url="https://cdn.discordapp.com/avatars/623317451811061763"
                                          "/9bb63c734178694e8779aa102cb81062.png?size=128")
            helpEmbed.set_footer(text="MarwynnBot",
                                 icon_url="https://cdn.discordapp.com/avatars/623317451811061763"
                                          "/9bb63c734178694e8779aa102cb81062.png?size=128")
            helpEmbed.add_field(name="Help",
                                value="`help`")

            debugCmds = "`ping`"
            funCmds = "`8ball` `choose` `say` `toad`"
            gamesCmds = "`Under Development`"
            moderationCmds = "`chatclean` `mute` `unmute` `kick` `ban` `unban`"
            musicCmds = "`join` `leave`"
            utilityCmds = "`prefix` `setprefix`"

            helpEmbed.add_field(name="Debug",
                                value=debugCmds,
                                inline=False)
            helpEmbed.add_field(name="Fun",
                                value=funCmds,
                                inline=False)
            helpEmbed.add_field(name="Games",
                                value=gamesCmds,
                                inline=False)
            helpEmbed.add_field(name="Moderation",
                                value=moderationCmds,
                                inline=False)
            helpEmbed.add_field(name="Music",
                                value=musicCmds,
                                inline=False)
            helpEmbed.add_field(name="Utility",
                                value=utilityCmds,
                                inline=False)
            await ctx.send(embed=helpEmbed)

    # =================================================
    # Debug
    # =================================================

    @help.command()
    async def ping(self, ctx):
        commandName = 'Ping'
        syntaxMessage = f"`{self.prefix(self, ctx)}ping`"
        await self.syntaxEmbed(ctx, commandName=commandName, syntaxMessage=syntaxMessage)

    # =================================================
    # Fun
    # =================================================

    @help.command(aliases=['8b', '8ball'])
    async def _8ball(self, ctx):
        commandName = 'Magic 8 Ball'
        syntaxMessage = f"`{self.prefix(self, ctx)}8ball`"
        aliases = "`8b`"
        thumbnailURL = 'https://www.horoscope.com/images-US/games/game-magic-8-ball-no-text.png'
        await self.syntaxEmbed(ctx, commandName=commandName, syntaxMessage=syntaxMessage, aliases=aliases,
                               thumbnailURL=thumbnailURL)

    @help.command()
    async def choose(self, ctx):
        commandName = 'Choose'
        syntaxMessage = f"`{self.prefix(self, ctx)}choose [strings separated by " + "\"or\"" + " ]`"
        exampleMessage = f"`{self.prefix(self, ctx)}choose Chocolate or Vanilla or Strawberry or Sherbet or No ice " \
                         f"cream bc I hate it?` "
        choices = ['Chocolate', 'Vanilla', 'Strawberry', 'Sherbet', 'No ice cream because I hate it']
        exampleOutput = random.choice(choices)
        specialCases = "The word \"or\" cannot be a valid choice for the bot to pick from due to it being the splitter."
        await self.syntaxEmbed(ctx, commandName=commandName, syntaxMessage=syntaxMessage, exampleMessage=exampleMessage,
                               exampleOutput=exampleOutput, specialCases=specialCases)

    @help.command()
    async def say(self, ctx):
        commandName = 'Say'
        syntaxMessage = f"`{self.prefix(self, ctx)}say`"
        await self.syntaxEmbed(ctx, commandName=commandName, syntaxMessage=syntaxMessage)

    @help.command()
    async def toad(self, ctx):
        commandName = 'Toad'
        syntaxMessage = f"`{self.prefix(self, ctx)}toad`"
        await self.syntaxEmbed(ctx, commandName=commandName, syntaxMessage=syntaxMessage)

    # =================================================
    # Games
    # =================================================

    # =================================================
    # Moderation
    # =================================================

    @help.command(aliases=['clear', 'clean', 'chatclear', 'cleanchat', 'clearchat', 'purge'])
    async def chatclean(self, ctx):
        commandName = "ChatClean"
        syntaxMessage = f"`{self.prefix(self, ctx)}chatclean [amount] [optional user @mention]`"
        aliases = "`clear` `clean` `chatclear` `cleanchat` `clearchat` `purge`"
        userPerms = "`Manage Messages`"
        botPerms = f"`{userPerms}` or `Administrator`"
        specialCases = "When clearing chat indiscriminately, you can eliminate the `[amount]` argument and only 1 " \
                       "message will be cleared.\n\nWhen an `[optional user @mention]` is specified, the `[amount]` " \
                       "must also be specified."
        await self.syntaxEmbed(ctx, commandName=commandName, syntaxMessage=syntaxMessage, aliases=aliases,
                               userPerms=userPerms, botPerms=botPerms, specialCases=specialCases)

    @help.command(aliases=['silence', 'stfu', 'shut', 'shush', 'shh', 'shhh', 'shhhh', 'quiet'])
    async def mute(self, ctx):
        commandName = "Mute"
        syntaxMessage = f"`{self.prefix(self, ctx)}mute [user @mention] [optional reason]`"
        aliases = "`silence` `stfu` `shut` `shush` `shh` `shhh` `shhhh` `quiet`"
        userPerms = "`Manage Roles`"
        botPerms = "Administrator"
        await self.syntaxEmbed(ctx, commandName=commandName, syntaxMessage=syntaxMessage, aliases=aliases,
                               userPerms=userPerms, botPerms=botPerms)

    @help.command(aliases=['unsilence', 'unstfu', 'unshut', 'unshush', 'unshh', 'unshhh', 'unshhhh', 'unquiet'])
    async def unmute(self, ctx):
        commandName = "Unmute"
        syntaxMessage = f"`{self.prefix(self, ctx)}unmute [user @mention] [optional reason]`"
        aliases = "`unsilence` `unstfu` `unshut` `unshush` `unshh` `unshhh` `unshhhh` `unquiet`"
        userPerms = "`Manage Roles`"
        botPerms = "Administrator"
        await self.syntaxEmbed(ctx, commandName=commandName, syntaxMessage=syntaxMessage, aliases=aliases,
                               userPerms=userPerms, botPerms=botPerms)

    @help.command()
    async def kick(self, ctx):
        commandName = "Kick"
        syntaxMessage = f"`{self.prefix(self, ctx)}kick [user @mention] [optional reason]`"
        userPerms = "`Kick Members`"
        botPerms = f"`{userPerms}` or `Administrator`"
        await self.syntaxEmbed(ctx, commandName=commandName, syntaxMessage=syntaxMessage, userPerms=userPerms,
                               botPerms=botPerms)

    @help.command()
    async def ban(self, ctx):
        commandName = "Ban"
        syntaxMessage = f"`{self.prefix(self, ctx)}ban [user @mention] [optional reason]`"
        userPerms = "`Ban Members`"
        botPerms = f"`{userPerms}` or `Administrator`"
        await self.syntaxEmbed(ctx, commandName=commandName, syntaxMessage=syntaxMessage, userPerms=userPerms,
                               botPerms=botPerms)

    @help.command()
    async def unban(self, ctx):
        commandName = "Unban"
        syntaxMessage = f"`{self.prefix(self, ctx)}ban [user @mention or user + discriminator] [optional reason]`"
        userPerms = "`Unban Members`"
        botPerms = f"`{userPerms}` or `Administrator`"
        await self.syntaxEmbed(ctx, commandName=commandName, syntaxMessage=syntaxMessage, userPerms=userPerms,
                               botPerms=botPerms)

    # =================================================
    # Music
    # =================================================

    @help.command()
    async def join(self, ctx):
        commandName = "Join"
        syntaxMessage = f"`{self.prefix(self,ctx)}join`"
        userPerms = "`Connect to Voice Channel`"
        botPerms = userPerms
        specialCases = "You must currently be connected to a voice channel in order to use this command"
        await self.syntaxEmbed(ctx, commandName=commandName, syntaxMessage=syntaxMessage, userPerms=userPerms,
                               botPerms=botPerms, specialCases=specialCases)

    @help.command()
    async def leave(self, ctx):
        commandName = "Leave"
        syntaxMessage = f"`{self.prefix(self, ctx)}leave`"
        specialCases = "You must currently be connected to a voice channel in order to use this command"
        await self.syntaxEmbed(ctx, commandName=commandName, syntaxMessage=syntaxMessage, specialCases=specialCases)

    # =================================================
    # Utility
    # =================================================

    @help.command(aliases=['p','checkprefix', 'prefix'])
    async def _prefix(self, ctx):
        commandName = "Prefix"
        syntaxMessage = f"`{self.prefix(self, ctx)}prefix`"
        exampleMessage = f"`{self.prefix(self, ctx)}prefix`"
        exampleOutput = f"`This server's prefix is: {self.prefix(self, ctx)}`"
        await self.syntaxEmbed(ctx, commandName=commandName, syntaxMessage=syntaxMessage, exampleMessage=exampleMessage,
                               exampleOutput=exampleOutput)

    @help.command(aliases=['sp', 'setprefix'])
    async def setPrefix(self, ctx):
        commandName = "Set Prefix"
        syntaxMessage = f"`{self.prefix(self, ctx)}setprefix [serverprefix]`"
        exampleMessage = f"`{self.prefix(self, ctx)}setprefix !m`"
        exampleOutput = "`Server prefix set to: !m`"
        await self.syntaxEmbed(ctx, commandName=commandName, syntaxMessage=syntaxMessage, exampleMessage=exampleMessage,
                               exampleOutput=exampleOutput)

def setup(client):
    client.add_cog(Help(client))
