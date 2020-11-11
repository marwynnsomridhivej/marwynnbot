import discord
from discord.ext import commands


TOPGG_URL = "https://top.gg/bot/623317451811061763/vote"
DBL = "https://discordbotlist.com/bots/marwynnbot/upvote"
DXTR = "https://discordextremelist.xyz/en-US/bots/623317451811061763"
DLABS = "https://bots.discordlabs.org/bot/623317451811061763?vote"


class Voting(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @commands.command(desc="Returns the link to vote for MarwynnBot",
                      usage="vote")
    async def vote(self, ctx):
        description = (f"{ctx.author.mention}, please vote for MarwynnBot "
                       "and show your support by voting on these bot listings:\n",
                       f"1. {TOPGG_URL}",
                       f"2. {DBL}",
                       f"3. {DXTR}",
                       f"4. {DLABS}")
        embed = discord.Embed(title="Vote for MarwynnBot!",
                              description="\n> ".join(description),
                              color=discord.Color.blue())
        embed.set_footer(
            text=("As of right now, there are no rewards set up yet. They will "
                  "be added soon. Thank you for your continued support!")
        )
        return await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Voting(bot))
