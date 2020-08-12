import json
import random
import discord
import yaml
import aiohttp
from discord.ext import commands
from globalcommands import GlobalCMDS as gcmds


class Actions(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "actions" has been loaded')

    async def embed_template(self, ctx, cmdName: str, cmdNameQuery: str, user: discord.Member = None):
        await gcmds.invkDelete(gcmds, ctx)
        try:
            with open('./tenor_api.yaml', 'r') as f:
                stream = yaml.full_load(f)
                api_key = stream[str('api_key')]
        except FileNotFoundError:
            with open('tenor_api.yaml', 'w') as f:
                f.write('api_key: API_KEY_FROM_TENOR')
            no_api = discord.Embed(title="Created File",
                                   description="The file `tenor_api.yaml` was created. Insert your Tenor API Key in "
                                               "the placeholder",
                                   color=discord.Color.dark_red())
            await ctx.channel.send(embed=no_api, delete_after=10)
        else:
            query = f"%23anime %23{cmdNameQuery}"
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        "https://api.tenor.com/v1/random?q=%s&key=%s&limit=%s" % (query, api_key, 10)) as image:
                    response = await image.json()
                    getURL = []
                    for i in range(len(response['results'])):
                        getURL.append(response['results'][i]['media'][0]['gif']['url'])
                    url = random.choice(getURL)
                    await session.close()

            if user is None or user == ctx.author:
                title = f"MarwynnBot {cmdName} {ctx.author.display_name}"
                user_specified = False
                user = None
            else:
                title = f"{ctx.author.display_name} {cmdName} {user.display_name}"
                user_specified = True
                user = user

            embed = discord.Embed(title=title,
                                  color=discord.Color.blue())
            embed.set_image(url=url)

            init = {f"{cmdNameQuery}": {'give': {}, 'receive': {}}}
            gcmds.json_load(gcmds, 'actionstats.json', init)
            with open('actionstats.json', 'r') as f:
                file = json.load(f)

                try:
                    file[str(cmdNameQuery)]
                except KeyError:
                    file[str(cmdNameQuery)] = {'give': {}, 'receive': {}}

                if user_specified:
                    try:
                        file[str(cmdNameQuery)]['give'][str(ctx.author.id)] += 1
                    except KeyError:
                        file[str(cmdNameQuery)]['give'][str(ctx.author.id)] = 1

                    try:
                        give_exec_count = file[str(cmdNameQuery)]['give'][str(user.id)]
                    except KeyError:
                        give_exec_count = 0

                    try:
                        file[str(cmdNameQuery)]['receive'][str(user.id)] += 1
                    except KeyError:
                        file[str(cmdNameQuery)]['receive'][str(user.id)] = 1
                    receive_exec_count = file[str(cmdNameQuery)]['receive'][str(user.id)]
                    with open('actionstats.json', 'w') as g:
                        json.dump(file, g, indent=4)
                    embed.set_footer(
                        text=f"{user.display_name} was {cmdName} {receive_exec_count} times, and {cmdName} others {give_exec_count} times")
                else:
                    try:
                        file[str(cmdNameQuery)]['give'][str(self.client.user.id)] += 1
                    except KeyError:
                        file[str(cmdNameQuery)]['give'][str(self.client.user.id)] = 1

                    try:
                        give_exec_count = file[str(cmdNameQuery)]['give'][str(ctx.author.id)]
                    except KeyError:
                        give_exec_count = 0

                    try:
                        file[str(cmdNameQuery)]['receive'][str(ctx.author.id)] += 1
                    except KeyError:
                        file[str(cmdNameQuery)]['receive'][str(ctx.author.id)] = 1
                    receive_exec_count = file[str(cmdNameQuery)]['receive'][str(ctx.author.id)]
                    with open('actionstats.json', 'w') as g:
                        json.dump(file, g, indent=4)
                    embed.set_footer(
                        text=f"{ctx.author.display_name} was {cmdName} {receive_exec_count} times, and {cmdName} others {give_exec_count} times")

        await ctx.channel.send(embed=embed)
        gcmds.incrCounter(gcmds, ctx, cmdNameQuery)

    @commands.command()
    async def bite(self, ctx, user: discord.Member = None):
        cmdName = "bit"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="bite",
                                  user=user)
        return

    @commands.command()
    async def blush(self, ctx, user: discord.Member = None):
        cmdName = "blushed"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="blush",
                                  user=user)
        return

    @commands.command()
    async def bonk(self, ctx, user: discord.Member = None):
        cmdName = "bonked"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="bonk",
                                  user=user)
        return

    @commands.command()
    async def boop(self, ctx, user: discord.Member = None):
        cmdName = "booped"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="boop",
                                  user=user)
        return

    @commands.command()
    async def bored(self, ctx, user: discord.Member = None):
        cmdName = "bored"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="bored",
                                  user=user)
        return

    @commands.command()
    async def chase(self, ctx, user: discord.Member = None):
        cmdName = "chased"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="chase",
                                  user=user)
        return

    @commands.command()
    async def cheer(self, ctx, user: discord.Member = None):
        cmdName = "cheered"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="cheer",
                                  user=user)
        return

    @commands.command()
    async def cringe(self, ctx, user: discord.Member = None):
        cmdName = "cringed"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="cringe",
                                  user=user)
        return

    @commands.command()
    async def cry(self, ctx, user: discord.Member = None):
        cmdName = "cried"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="cry",
                                  user=user)
        return

    @commands.command()
    async def cuddle(self, ctx, user: discord.Member = None):
        cmdName = "cuddled"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="cuddle",
                                  user=user)
        return

    @commands.command()
    async def cut(self, ctx, user: discord.Member = None):
        cmdName = "cut"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="cut",
                                  user=user)
        return

    @commands.command()
    async def dab(self, ctx, user: discord.Member = None):
        cmdName = "dabbed"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="dab",
                                  user=user)
        return

    @commands.command()
    async def dance(self, ctx, user: discord.Member = None):
        cmdName = "danced"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="dance",
                                  user=user)
        return

    @commands.command()
    async def destroy(self, ctx, user: discord.Member = None):
        cmdName = "destroyed"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="destroy",
                                  user=user)
        return

    @commands.command()
    async def die(self, ctx, user: discord.Member = None):
        cmdName = "died"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="die",
                                  user=user)
        return

    @commands.command()
    async def drown(self, ctx, user: discord.Member = None):
        cmdName = "drowned"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="drown",
                                  user=user)
        return

    @commands.command()
    async def eat(self, ctx, user: discord.Member = None):
        cmdName = "ate"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="eat",
                                  user=user)
        return

    @commands.command()
    async def facepalm(self, ctx, user: discord.Member = None):
        cmdName = "facepalmed"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="facepalm",
                                  user=user)
        return

    @commands.command()
    async def feed(self, ctx, user: discord.Member = None):
        cmdName = "fed"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="feed",
                                  user=user)
        return

    @commands.command()
    async def flip(self, ctx, user: discord.Member = None):
        cmdName = "flipped"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="flip",
                                  user=user)
        return

    @commands.command()
    async def flirt(self, ctx, user: discord.Member = None):
        cmdName = "flirted"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="flirt",
                                  user=user)
        return

    @commands.command()
    async def forget(self, ctx, user: discord.Member = None):
        cmdName = "forgot"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="forget",
                                  user=user)
        return

    @commands.command()
    async def forgive(self, ctx, user: discord.Member = None):
        cmdName = "forgave"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="forgive",
                                  user=user)
        return

    @commands.command()
    async def friend(self, ctx, user: discord.Member = None):
        cmdName = "friended"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="friend",
                                  user=user)
        return

    @commands.command()
    async def fry(self, ctx, user: discord.Member = None):
        cmdName = "fried"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="fry",
                                  user=user)
        return

    @commands.command()
    async def glomp(self, ctx, user: discord.Member = None):
        cmdName = "glomped"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="glomp",
                                  user=user)
        return

    @commands.command()
    async def handhold(self, ctx, user: discord.Member = None):
        cmdName = "held hands"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="handhold",
                                  user=user)
        return

    @commands.command()
    async def happy(self, ctx, user: discord.Member = None):
        cmdName = "happy"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="happy",
                                  user=user)
        return

    @commands.command()
    async def hate(self, ctx, user: discord.Member = None):
        cmdName = "hated"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="hate",
                                  user=user)
        return

    @commands.command()
    async def highfive(self, ctx, user: discord.Member = None):
        cmdName = "highfived"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="highfive",
                                  user=user)
        return

    @commands.command()
    async def hug(self, ctx, user: discord.Member = None):
        cmdName = "hugged"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="hug",
                                  user=user)
        return

    @commands.command()
    async def kill(self, ctx, user: discord.Member = None):
        cmdName = "killed"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="kill",
                                  user=user)
        return

    @commands.command()
    async def kiss(self, ctx, user: discord.Member = None):
        cmdName = "kissed"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="kiss",
                                  user=user)
        return

    @commands.command()
    async def laugh(self, ctx, user: discord.Member = None):
        cmdName = "laughed"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="laugh",
                                  user=user)
        return

    @commands.command()
    async def lick(self, ctx, user: discord.Member = None):
        cmdName = "licked"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="lick",
                                  user=user)
        return

    @commands.command()
    async def love(self, ctx, user: discord.Member = None):
        cmdName = "loved"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="love",
                                  user=user)
        return

    @commands.command()
    async def lurk(self, ctx, user: discord.Member = None):
        cmdName = "lurked"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="lurk",
                                  user=user)
        return

    @commands.command()
    async def marry(self, ctx, user: discord.Member = None):
        cmdName = "married"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="marry",
                                  user=user)
        return

    @commands.command()
    async def massacre(self, ctx, user: discord.Member = None):
        cmdName = "massacred"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="massacre",
                                  user=user)
        return

    @commands.command()
    async def miss(self, ctx, user: discord.Member = None):
        cmdName = "missed"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="miss",
                                  user=user)
        return

    @commands.command()
    async def nervous(self, ctx, user: discord.Member = None):
        cmdName = "nervous"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="nervous",
                                  user=user)
        return

    @commands.command()
    async def no(self, ctx, user: discord.Member = None):
        cmdName = "no"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="no",
                                  user=user)
        return

    @commands.command()
    async def nom(self, ctx, user: discord.Member = None):
        cmdName = "nommed"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="nom",
                                  user=user)
        return

    @commands.command()
    async def nuzzle(self, ctx, user: discord.Member = None):
        cmdName = "nuzzled"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="nuzzle",
                                  user=user)
        return

    @commands.command()
    async def panic(self, ctx, user: discord.Member = None):
        cmdName = "panicked"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="panic",
                                  user=user)
        return

    @commands.command(aliases=['paralyze'])
    async def paralyse(self, ctx, user: discord.Member = None):
        cmdName = "paralysed"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="paralyse",
                                  user=user)
        return

    @commands.command()
    async def pat(self, ctx, user: discord.Member = None):
        cmdName = "patted"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="pat",
                                  user=user)
        return

    @commands.command()
    async def peck(self, ctx, user: discord.Member = None):
        cmdName = "pecked"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="peck",
                                  user=user)
        return

    @commands.command()
    async def poke(self, ctx, user: discord.Member = None):
        cmdName = "poked"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="poke",
                                  user=user)
        return

    @commands.command()
    async def pout(self, ctx, user: discord.Member = None):
        cmdName = "pouted"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="pout",
                                  user=user)
        return

    @commands.command()
    async def punt(self, ctx, user: discord.Member = None):
        cmdName = "punted"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="punt",
                                  user=user)
        return

    @commands.command()
    async def run(self, ctx, user: discord.Member = None):
        cmdName = "ran"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="run",
                                  user=user)
        return

    @commands.command()
    async def race(self, ctx, user: discord.Member = None):
        cmdName = "raced"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="race",
                                  user=user)
        return

    @commands.command()
    async def ramble(self, ctx, user: discord.Member = None):
        cmdName = "rambled"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="ramble",
                                  user=user)
        return

    @commands.command()
    async def ransack(self, ctx, user: discord.Member = None):
        cmdName = "ransacked"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="ransack",
                                  user=user)
        return

    @commands.command(aliases=['realize'])
    async def realise(self, ctx, user: discord.Member = None):
        cmdName = "realised"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="realise",
                                  user=user)
        return

    @commands.command()
    async def rebel(self, ctx, user: discord.Member = None):
        cmdName = "rebelled"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="rebel",
                                  user=user)
        return

    @commands.command()
    async def reassure(self, ctx, user: discord.Member = None):
        cmdName = "reassured"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="reassure",
                                  user=user)
        return

    @commands.command()
    async def run(self, ctx, user: discord.Member = None):
        cmdName = "ran"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="run",
                                  user=user)
        return

    @commands.command()
    async def sad(self, ctx, user: discord.Member = None):
        cmdName = "saddened"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="sad",
                                  user=user)
        return

    @commands.command()
    async def shoot(self, ctx, user: discord.Member = None):
        cmdName = "shot"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="shoot",
                                  user=user)
        return

    @commands.command()
    async def shrug(self, ctx, user: discord.Member = None):
        cmdName = "shrugged"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="shrug",
                                  user=user)
        return

    @commands.command()
    async def sip(self, ctx, user: discord.Member = None):
        cmdName = "sipped"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="sip",
                                  user=user)
        return

    @commands.command()
    async def slap(self, ctx, user: discord.Member = None):
        cmdName = "slapped"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="slap",
                                  user=user)
        return

    @commands.command()
    async def sleep(self, ctx, user: discord.Member = None):
        cmdName = "sleep"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="sleep",
                                  user=user)
        return

    @commands.command()
    async def slice(self, ctx, user: discord.Member = None):
        cmdName = "sliced"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="slice",
                                  user=user)
        return

    @commands.command()
    async def smug(self, ctx, user: discord.Member = None):
        cmdName = "smug"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="smug",
                                  user=user)
        return

    @commands.command()
    async def stab(self, ctx, user: discord.Member = None):
        cmdName = "stabbed"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="stab",
                                  user=user)
        return

    @commands.command()
    async def stare(self, ctx, user: discord.Member = None):
        cmdName = "stared"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="stare",
                                  user=user)
        return

    @commands.command()
    async def tackle(self, ctx, user: discord.Member = None):
        cmdName = "taunted"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="taunt",
                                  user=user)
        return

    @commands.command()
    async def tame(self, ctx, user: discord.Member = None):
        cmdName = "tamed"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="tame",
                                  user=user)
        return

    @commands.command()
    async def tap(self, ctx, user: discord.Member = None):
        cmdName = "tapped"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="tap",
                                  user=user)
        return

    @commands.command()
    async def taste(self, ctx, user: discord.Member = None):
        cmdName = "tasted"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="taste",
                                  user=user)
        return

    @commands.command()
    async def talk(self, ctx, user: discord.Member = None):
        cmdName = "talked"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="talk",
                                  user=user)
        return

    @commands.command()
    async def taunt(self, ctx, user: discord.Member = None):
        cmdName = "taunted"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="taunt",
                                  user=user)
        return

    @commands.command()
    async def tease(self, ctx, user: discord.Member = None):
        cmdName = "teased"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="tease",
                                  user=user)
        return

    @commands.command()
    async def thank(self, ctx, user: discord.Member = None):
        cmdName = "thanked"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="thank",
                                  user=user)
        return

    @commands.command()
    async def think(self, ctx, user: discord.Member = None):
        cmdName = "think"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="think",
                                  user=user)
        return

    @commands.command()
    async def throw(self, ctx, user: discord.Member = None):
        cmdName = "threw"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="throw",
                                  user=user)
        return

    @commands.command()
    async def thumbsdown(self, ctx, user: discord.Member = None):
        cmdName = "thumbsdown"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="thumbsdown",
                                  user=user)
        return

    @commands.command()
    async def thumbsup(self, ctx, user: discord.Member = None):
        cmdName = "thumbsup"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="thumbsup",
                                  user=user)
        return

    @commands.command()
    async def tickle(self, ctx, user: discord.Member = None):
        cmdName = "tickled"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="tickle",
                                  user=user)
        return

    @commands.command()
    async def torment(self, ctx, user: discord.Member = None):
        cmdName = "tormented"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="torment",
                                  user=user)
        return

    @commands.command()
    async def touch(self, ctx, user: discord.Member = None):
        cmdName = "touched"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="touch",
                                  user=user)
        return

    @commands.command()
    async def trash(self, ctx, user: discord.Member = None):
        cmdName = "trashed"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="trash",
                                  user=user)
        return

    @commands.command(aliases=['triggered'])
    async def trigger(self, ctx, user: discord.Member = None):
        cmdName = "triggered"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="trigger",
                                  user=user)
        return

    @commands.command()
    async def understand(self, ctx, user: discord.Member = None):
        cmdName = "understood"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="understand",
                                  user=user)
        return

    @commands.command()
    async def upset(self, ctx, user: discord.Member = None):
        cmdName = "upset"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="upset",
                                  user=user)
        return

    @commands.command()
    async def wag(self, ctx, user: discord.Member = None):
        cmdName = "wagged"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="wag",
                                  user=user)
        return

    @commands.command()
    async def wait(self, ctx, user: discord.Member = None):
        cmdName = "waited"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="wait",
                                  user=user)
        return

    @commands.command()
    async def wakeup(self, ctx, user: discord.Member = None):
        cmdName = "woke up"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="wakeup",
                                  user=user)
        return

    @commands.command()
    async def wash(self, ctx, user: discord.Member = None):
        cmdName = "washed"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="wash",
                                  user=user)
        return

    @commands.command()
    async def wave(self, ctx, user: discord.Member = None):
        cmdName = "waved"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="wave",
                                  user=user)
        return

    @commands.command()
    async def whine(self, ctx, user: discord.Member = None):
        cmdName = "whined"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="whine",
                                  user=user)
        return

    @commands.command()
    async def whisper(self, ctx, user: discord.Member = None):
        cmdName = "whispered"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="whisper",
                                  user=user)
        return

    @commands.command()
    async def wink(self, ctx, user: discord.Member = None):
        cmdName = "winked"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="wink",
                                  user=user)
        return

    @commands.command()
    async def worship(self, ctx, user: discord.Member = None):
        cmdName = "worshipped"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="worship",
                                  user=user)
        return

    @commands.command()
    async def worry(self, ctx, user: discord.Member = None):
        cmdName = "worried"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="worry",
                                  user=user)
        return

    @commands.command()
    async def yes(self, ctx, user: discord.Member = None):
        cmdName = "yes"
        await self.embed_template(ctx,
                                  cmdName=cmdName,
                                  cmdNameQuery="yes",
                                  user=user)
        return


def setup(client):
    client.add_cog(Actions(client))
