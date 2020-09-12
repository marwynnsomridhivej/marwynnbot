from datetime import datetime
import praw
import yaml
import random
import discord
from discord.ext import commands
from utils import globalcommands

gcmds = globalcommands.GlobalCMDS()


class Reddit(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def get_id_secret(self, ctx):
        bot_id = gcmds.env_check("REDDIT_CLIENT_ID")
        bot_secret = gcmds.env_check("REDDIT_CLIENT_SECRET")
        user_agent = gcmds.env_check("USER_AGENT")
        if not bot_id or not bot_secret or not user_agent:
            title = "Missing Reddit Client ID or Client Secret or User Agent"
            description = "Insert your Reddit Client ID, Client Secret, and User Agent in the `.env` file"
            embed = discord.Embed(title=title,
                                  description=description,
                                  color=discord.Color.dark_red())
            return await ctx.channel.send(embed=embed, delete_after=10)
        return [bot_id, bot_secret, user_agent]

    async def embed_template(self, ctx):
        info = await self.get_id_secret(ctx)

        if not info:
            return

        reddit = praw.Reddit(bot_id=info[0],
                             bot_secret=info[1],
                             user_agent=info[2])
        picture_search = reddit.subreddit(ctx.command.name).hot()

        submissions = []

        for post in picture_search:
            if len(submissions) == 300:
                break
            elif (not post.stickied and not post.over_18) and not "https://v.redd.it/" in post.url:
                submissions.append(post)

        picture = random.choice(submissions)

        web_link = f"https://www.reddit.com/{picture.permalink}"
        url = picture.url
        author = picture.author
        author_url = f"https://www.reddit.com/user/{author}/"
        author_icon_url = picture.author.icon_img
        created_timestamp = datetime.fromtimestamp(picture.created_utc)
        real_timestamp = created_timestamp.strftime("%d/%m/%Y %H:%M:%S")
        num_comments = picture.num_comments
        upvotes = picture.score
        ratio = picture.upvote_ratio * 100
        sub_name = picture.subreddit_name_prefixed
        embed = discord.Embed(title=sub_name,
                              url=web_link,
                              color=discord.Color.blue())
        embed.set_author(name=author, url=author_url, icon_url=author_icon_url)
        embed.set_image(url=url)
        embed.set_footer(
            text=f"⬆️{upvotes}️ ({ratio}%)\n💬{num_comments}\n🕑{real_timestamp}\n"
                 f"Copyrights belong to their respective owners")
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=['reddithelp'])
    async def reddit(self, ctx, cmdName=None):
        

        CMDLIST = self.get_commands()
        del CMDLIST[0]
        CMDNAMES = [i.name for i in CMDLIST]
        description = f"Do `{gcmds.prefix(ctx)}reddit [cmdName]` to get the usage of that particular " \
                      f"command.\n\n**List of all {len(CMDLIST)} reddit commands:**\n\n `{'` `'.join(sorted(CMDNAMES))}` "
        if cmdName is None or cmdName == "reddit":
            helpEmbed = discord.Embed(title="Reddit Commands Help",
                                      description=description,
                                      color=discord.Color.blue())
        else:
            if cmdName in CMDNAMES:
                r_command = cmdName.capitalize()
                helpEmbed = discord.Embed(title=f"{r_command}",
                                          description=f"Returns a randomly selected image from the subreddit r/{cmdName}",
                                          color=discord.Color.blue())
                helpEmbed.add_field(name="Usage",
                                    value=f"`{gcmds.prefix(ctx)}{cmdName}`",
                                    inline=False)
                pot_alias = self.bot.get_command(name=cmdName)
                aliases = [g for g in pot_alias.aliases]
                if aliases:
                    value = "`" + "` `".join(sorted(aliases)) + "`"
                    helpEmbed.add_field(name="Aliases",
                                        value=value,
                                        inline=False)
            else:
                helpEmbed = discord.Embed(title="Command Not Found",
                                          description=f"{ctx.author.mention}, {cmdName} is not a valid reddit command",
                                          color=discord.Color.blue())
        await ctx.channel.send(embed=helpEmbed)

    @commands.command(aliases=['abj', 'meananimals'])
    async def animalsbeingjerks(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command(aliases=['anime'])
    async def awwnime(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command(aliases=['car', 'cars', 'carpics'])
    async def carporn(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command()
    async def cosplay(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command(aliases=['earth', 'earthpics'])
    async def earthporn(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command(aliases=['food', 'foodpics'])
    async def foodporn(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command(aliases=['animemes'])
    async def goodanimemes(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command(aliases=['history', 'historypics'])
    async def historyporn(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command(aliases=['pic', 'itap'])
    async def itookapicture(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command(aliases=['map', 'maps', 'mappics'])
    async def mapporn(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command(aliases=['interesting', 'mi'])
    async def mildlyinteresting(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command()
    async def pareidolia(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command(aliases=['ptiming'])
    async def perfecttiming(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command(aliases=['psbattle'])
    async def photoshopbattles(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command(aliases=['quotes'])
    async def quotesporn(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command(aliases=['room', 'rooms', 'roompics'])
    async def roomporn(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command()
    async def tumblr(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command()
    async def unexpected(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command(aliases=['wallpaper'])
    async def wallpapers(self, ctx):
        
        await self.embed_template(ctx)
        return

    @commands.command(aliases=['woah'])
    async def woahdude(self, ctx):
        
        await self.embed_template(ctx)
        return


def setup(bot):
    bot.add_cog(Reddit(bot))
