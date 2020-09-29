import asyncio
import json
import os
import random
import re
import typing

import aiohttp
import discord
import requests
from discord.ext import commands
from discord.ext.commands import CommandInvokeError
from utils import globalcommands

gcmds = globalcommands.GlobalCMDS()


class Fun(commands.Cog):

    def __init__(self, bot):
        global gcmds
        self.bot = bot
        gcmds = globalcommands.GlobalCMDS(self.bot)

    async def imageSend(self, ctx, path, url=None, toSend=None):
        path = path
        sleepTime = 1.0

        if "imgur" in path:
            local = False
            title = f"{path[5:].capitalize()} from Imgur"
            url = url
            color = discord.Color.blue()
            cmdName = "imgurSearch"
        elif "tenor" in path:
            local = False
            title = f"{path[5:].capitalize()} from Tenor"
            url = url
            color = discord.Color.blue()
            cmdName = "gifSearch"
        elif path == "cat":
            local = False
            title = "Cat"
            url = url
            color = discord.Color.blue()
            cmdName = "randomCat"
        elif path == "dog":
            local = False
            title = "Dog"
            url = url
            color = discord.Color.blue()
            cmdName = "randomDog"
        else:
            local = True
            files = os.listdir(path)
            if toSend is not None:
                counter = 0
                name = []
                d = []
                while counter < toSend:
                    name.append(random.choice(files))
                    counter += 1
            else:
                name = random.choice(files)
                d = f'{path}/{name}'

            if path == "./toad":
                title = "Toad️ ️❤️❤️❤️❤️❤️❤️"
                color = discord.Color.red()
                if toSend is not None:
                    url = []
                    for fn in name:
                        url.append(f"attachment://toad_{fn}")
                else:
                    url = f"attachment://toad_{name}"
                cmdName = "toad"
            if path == "./isabelle":
                title = "Isabelle"
                color = discord.Color.blue()
                if toSend is not None:
                    url = []
                    for fn in name:
                        url.append(f"attachment://isabelle_{fn}")
                else:
                    url = f"attachment://isabelle_{name}"
                cmdName = "isabelle"
            if path == "./peppa":
                title = "Peppa"
                color = discord.Color.blue()
                if toSend is not None:
                    url = []
                    for fn in name:
                        url.append(f"attachment://peppa_{fn}")
                else:
                    url = f"attachment://peppa_{name}"
                cmdName = "peppa"

            if (toSend is not None) and local:
                count = 0
                for filename in name:
                    d = f'{path}/{filename}'
                    with open(d, 'rb') as f:
                        picture = discord.File(f, d)
                        multipleEmbed = discord.Embed(title=f"{title} [{count + 1}/{len(url)}]",
                                                      color=color)
                        multipleEmbed.set_image(url=url[count])
                        multipleEmbed.set_footer(text=f"Filename: {filename}")
                        await ctx.channel.send(file=picture, embed=multipleEmbed)
                        await asyncio.sleep(sleepTime)
                        count += 1
                return
            else:
                with open(d, 'rb') as f:
                    picture = discord.File(f, d)
        if (toSend is not None) and not local:
            count = 0
            for i in url:
                count += 1
                multipleEmbed = discord.Embed(title=f"{title} [{count}/{len(url)}]",
                                              color=color)
                multipleEmbed.set_image(url=i)
                await ctx.channel.send(embed=multipleEmbed)
                await asyncio.sleep(sleepTime)
            return
        else:
            pictureEmbed = discord.Embed(title=title,
                                         color=color)
            pictureEmbed.set_image(url=url)

        if local:
            pictureEmbed.set_footer(text=f'Filename: {name}')
            await ctx.channel.send(file=picture,
                                   embed=pictureEmbed)
        else:
            await ctx.channel.send(embed=pictureEmbed)

    @commands.command(aliases=['dailyastro'])
    async def apod(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY") as returned:
                result = await returned.json()
        embed = discord.Embed(title=result['title'],
                              color=discord.Color.blue())
        embed.set_author(name=f"NASA Astronomy Photo of the Day {result['date'].replace('-', '/')}")
        embed.set_footer(text=result['explanation'])
        embed.set_image(url=result['hdurl'])
        return await ctx.channel.send(embed=embed)

    @commands.command(aliases=['dad', 'father'])
    async def dadjoke(self, ctx):
        async with aiohttp.ClientSession(headers={"Accept": "application/json"}) as session:
            async with session.get("https://icanhazdadjoke.com/") as returned:
                result = await returned.json()
        embed = discord.Embed(description=result['joke'],
                              color=discord.Color.blue())
        embed.set_author(name=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        return await ctx.channel.send(embed=embed)

    @commands.command(aliases=['8ball', '8b'])
    async def eightball(self, ctx, *, question):
        with open('responses', 'r') as f:
            responses = f.readlines()
        embed = discord.Embed(title='Magic 8 Ball 🎱', color=discord.colour.Color.blue())
        embed.set_thumbnail(url="https://www.horoscope.com/images-US/games/game-magic-8-ball-no-text.png")
        embed.add_field(name='Question', value=f"{ctx.message.author.mention}: " + question, inline=True)
        embed.add_field(name='Answer', value=f'{random.choice(responses)}', inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=['affirm'])
    async def encourage(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.affirmations.dev/") as returned:
                result = await returned.json()
        embed = discord.Embed(title="Affirmation",
                              description=f"{ctx.author.mention}\n```\n{result['affirmation']}\n```",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @commands.command()
    async def choose(self, ctx, *, choices):
        remQuestion = re.sub('[?]', '', str(choices))
        options = remQuestion.split(' or ')
        answer = random.choice(options)
        chooseEmbed = discord.Embed(title='Choose One',
                                    color=discord.Color.blue())
        chooseEmbed.add_field(name=f'{ctx.author} asked: {choices}',
                              value=answer)
        await ctx.channel.send(embed=chooseEmbed)

    @commands.command(aliases=['gifsearch', 'searchgif', 'searchgifs', 'gif', 'gifs'])
    async def gifSearch(self, ctx, toSend: typing.Optional[int] = None, *, query=None):
        api_key = gcmds.env_check("TENOR_API")
        if not api_key:
            title = "Missing API Key"
            description = "Insert your Tenor API Key in the `.env` file"
            color = discord.Color.red()
            embed = discord.Embed(title=title,
                                  description=description,
                                  color=color)
            return await ctx.channel.send(embed=embed)

        if query is None:
            if toSend:
                query = str(toSend)
                bool_check = True
            else:
                title = "No Search Term Specified"
                description = f"{ctx.author.mention}, you must specify at least one search term. " \
                              f"`Do {await gcmds.prefix(ctx)}help gifsearch` for command info"
                color = discord.Color.dark_red()
                bool_check = False
        else:
            bool_check = True

        if bool_check:
            query = str(query)
            r = requests.get("https://api.tenor.com/v1/random?q=%s&key=%s&limit=%s" % (query, api_key, 50))
            if r.status_code == 200 or r.status_code == 202:
                results = json.loads(r.content)
                getURL = []
                for i in range(len(results['results'])):
                    getURL.append(results['results'][i]['media'][0]['gif']['url'])
                if toSend is not None:
                    count = 0
                    url = []
                    while count < toSend:
                        url.append(random.choice(getURL))
                        count += 1
                else:
                    url = random.choice(getURL)
                path = f"tenor{str(query)}"
                return await self.imageSend(ctx, path, url=url, toSend=toSend)
            elif r.status_code == 429:
                title = "Error Code 429"
                description = "**HTTP ERROR:** Rate limit exceeded. Please try again in about 30 seconds"
                color = discord.Color.dark_red()
            elif 300 <= r.status_code < 400:
                title = f"Error Code {r.status_code}"
                description = "**HTTP ERROR:** Redirect"
                color = discord.Color.dark_red()
            elif r.status_code == 404:
                title = "Error Code 404"
                description = "**HTTP ERROR:** Not found - bad resource"
                color = discord.Color.dark_red()
            elif 500 <= r.status_code < 600:
                title = f"Error Code {r.status_code}"
                description = "**HTTP ERROR:** Unexpected server error"
                color = discord.Color.dark_red()

        embed = discord.Embed(title=title,
                              description=description,
                              color=color)

        await ctx.channel.send(embed=embed)

    @commands.command(aliases=['imgur', 'imgursearch'])
    async def imgurSearch(self, ctx, toSend: typing.Optional[int] = None, *, query):
        bot_id = gcmds.env_check("IMGUR_API")
        if not bot_id:
            title = "Missing Client ID"
            description = "Insert your Imgur Client ID in the `.env` file"
            color = discord.Color.red()
            embed = discord.Embed(title=title,
                                  description=description,
                                  color=color)
            return await ctx.channel.send(embed=embed)

        path = f"imgur{str(query)}"
        query = str(query)
        reqURL = f"https://api.imgur.com/3/gallery/search/?q_all={query}"
        headers = {'Authorization': f'Client-ID {bot_id}'}
        r = requests.request("GET", reqURL, headers=headers)
        results = json.loads(r.content)

        images = []
        data = int(len(results['data']))

        if r.status_code == 200:
            for i in range(data):
                if "false" != str(results['data'][i]['nsfw']):
                    try:
                        for j in range(len(results['data'][i]['images'])):
                            if ".mp4" not in str(results['data'][i]['images'][j]['link']):
                                images.append(str(results['data'][i]['images'][j]['link']))
                    except KeyError:
                        images.append(str(results['data'][i]['link']))
        if images is []:
            none = discord.Embed(title="No Images Found",
                                 description=f"{ctx.author.mention},there were no images that matched your query: `{query}`",
                                 color=discord.Color.dark_red())
            await ctx.channel.send(embed=none)
            return
        elif (toSend is not None) and (toSend != 0):
            url = []
            count = 0
            while count < toSend:
                url.append(random.choice(images))
                count += 1
        else:
            url = random.choice(images)

        await self.imageSend(ctx, path, url=url, toSend=toSend)

    @commands.command(aliases=['isabellepic', 'isabelleemote', 'belle', 'bellepic', 'belleemote'])
    async def isabelle(self, ctx, toSend: typing.Optional[int] = None):
        path = "./isabelle"
        await self.imageSend(ctx, path, toSend=toSend)

    @commands.command(aliases=['peppapic', 'ppic', 'ppig'])
    async def peppa(self, ctx, toSend: typing.Optional[int] = None):
        path = "./peppa"
        await self.imageSend(ctx, path, toSend=toSend)

    @commands.command(aliases=['randomcat', 'cat'])
    async def randomCat(self, ctx, toSend: typing.Optional[int] = None):
        api_key = gcmds.env_check("CAT_API")
        if not api_key:
            title = "Missing API Key"
            description = "Insert your TheCatAPI Key in the `.env` file"
            color = discord.Color.red()
            embed = discord.Embed(title=title,
                                  description=description,
                                  color=color)
            return await ctx.channel.send(embed=embed)

        headers = {"x-api-key": api_key}

        if toSend is None:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get("https://api.thecatapi.com/v1/images/search") as image:
                    response = await image.json()
                    search = response[0]
                    url = search['url']
        else:
            if toSend > 50:
                toSend = 50
            url = []
            for _ in range(toSend):
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get("https://api.thecatapi.com/v1/images/search") as image:
                        response = await image.json()
                        search = response[0]
                        url.append(search['url'])
        path = "cat"
        await self.imageSend(ctx, path, url=url, toSend=toSend)
        return

    @commands.command(aliases=['woof', 'dog', 'doggo', 'randomdog'])
    async def randomDog(self, ctx, toSend: typing.Optional[int] = None):
        if toSend is None:
            req_url = "https://dog.ceo/api/breeds/image/random"
        else:
            if toSend < 2:
                req_url = "https://dog.ceo/api/breeds/image/random"
            elif toSend > 50:
                toSend = 50
                req_url = f"https://dog.ceo/api/breeds/image/random/{toSend}"
            else:
                req_url = f"https://dog.ceo/api/breeds/image/random/{toSend}"

        async with aiohttp.ClientSession() as session:
            async with session.get(req_url) as image:
                response = await image.json()
                url = response["message"]
        path = "dog"
        await self.imageSend(ctx, path, url=url, toSend=toSend)
        return

    @commands.command()
    async def say(self, ctx, *, args):
        sayEmbed = discord.Embed(description=args,
                                 color=discord.Color.blue())
        await ctx.channel.send(embed=sayEmbed)

    @commands.command(aliases=['toadpic', 'toademote'])
    async def toad(self, ctx, toSend: typing.Optional[int] = None):
        path = "./toad"
        await self.imageSend(ctx, path, toSend=toSend)


def setup(bot):
    bot.add_cog(Fun(bot))
