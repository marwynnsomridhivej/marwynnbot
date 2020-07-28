import asyncio
import json
import os
import random
import re
import typing
import urllib.request

import discord
import requests
import yaml
from bs4 import BeautifulSoup
from discord.ext import commands
from discord.ext.commands import CommandInvokeError

from globalcommands import GlobalCMDS as gcmds


class Fun(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "fun" has been loaded')

    async def imageSend(self, ctx, path, url=None, toSend=None):
        await ctx.message.delete()
        path = path
        sleepTime = 1.2

        if "imgur" in path:
            local = False
            title = f"{path[5:].capitalize()} from Imgur"
            url = url
            color = discord.Color.blue()
            gcmds.incrCounter(gcmds, 'imgurSearch')
        elif "tenor" in path:
            local = False
            title = f"{path[5:].capitalize()} from Tenor"
            url = url
            color = discord.Color.blue()
            gcmds.incrCounter(gcmds, 'gifSearch')
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
                title = "Toad ❤️❤️❤️❤️❤️❤️"
                color = discord.Color.red()
                if toSend is not None:
                    url = []
                    for fn in name:
                        url.append(f"attachment://toad_{fn}")
                else:
                    url = f"attachment://toad_{name}"
                gcmds.incrCounter(gcmds, 'toad')
            if path == "./isabelle":
                title = "Isabelle"
                color = discord.Color.blue()
                if toSend is not None:
                    url = []
                    for fn in name:
                        url.append(f"attachment://isabelle_{fn}")
                else:
                    url = f"attachment://isabelle_{name}"
                gcmds.incrCounter(gcmds, 'isabelle')
            if path == "./peppa":
                title = "Peppa"
                color = discord.Color.blue()
                if toSend is not None:
                    url = []
                    for fn in name:
                        url.append(f"attachment://peppa_{fn}")
                else:
                    url = f"attachment://peppa_{name}"
                gcmds.incrCounter(gcmds, 'peppa')

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

    @commands.command(aliases=['8ball', '8b'])
    async def _8ball(self, ctx, *, question):
        await ctx.message.delete()
        file = open('responses', 'r')
        responses = file.readlines()
        embed = discord.Embed(title='Magic 8 Ball 🎱', color=discord.colour.Color.blue())
        embed.set_thumbnail(url="https://www.horoscope.com/images-US/games/game-magic-8-ball-no-text.png")
        embed.add_field(name='Question', value=f"{ctx.message.author.mention}: " + question, inline=True)
        embed.add_field(name='Answer', value=f'{random.choice(responses)}', inline=False)
        await ctx.send(embed=embed)
        gcmds.incrCounter(gcmds, '8ball')

    @commands.command()
    async def choose(self, ctx, *, choices):
        await ctx.message.delete()
        remQuestion = re.sub('[?]', '', str(choices))
        options = remQuestion.split(' or ')
        answer = random.choice(options)
        chooseEmbed = discord.Embed(title='Choose One',
                                    color=discord.Color.blue())
        chooseEmbed.add_field(name=f'{ctx.author} asked: {choices}',
                              value=answer)
        await ctx.channel.send(embed=chooseEmbed)
        gcmds.incrCounter(gcmds, 'choose')

    @commands.command(aliases=['gifsearch', 'searchgif', 'searchgifs', 'gif', 'gifs'])
    async def gifSearch(self, ctx, toSend: typing.Optional[int] = None, *, query=None):
        try:
            with open('./tenor_api.yaml', 'r') as f:
                stream = yaml.full_load(f)
                api_key = stream[str('api_key')]
        except FileNotFoundError:
            with open('tenor_api.yaml', 'w') as f:
                f.write('api_key: API_KEY_FROM_TENOR')
            title = "Created File"
            description = "The file `tenor_api.yaml` was created. Insert your Tenor API Key in the placeholder"
            color = discord.Color.red()

        if query is None:
            if toSend:
                query = str(toSend)
                bool = True
            else:
                title = "No Search Term Specified"
                description = f"{ctx.author.mention}, you must specify at least one search term. " \
                              f"`Do {gcmds.prefix(gcmds, ctx)}help gifsearch` for command info"
                color = discord.Color.dark_red()
                bool = False
        else:
            bool = True

        if bool:
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
                await self.imageSend(ctx, path, url=url, toSend=toSend)
                return
            elif r.status_code == 429:
                title = "Error Code 429"
                description = f"**HTTP ERROR:** Rate limit exceeded. Please try again in about 30 seconds"
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

        await ctx.message.delete()
        await ctx.channel.send(embed=embed)

    @gifSearch.error
    async def gifSearch_error(self, ctx, error):
        if isinstance(error, CommandInvokeError):
            title = "No Tenor API Key"
            description = "Please paste your Tenor API Key in the file `tenor_api.yaml` in the placeholder"
            color = discord.Color.red()
            errorEmbed = discord.Embed(title=title,
                                       description=description,
                                       color=color)
            await ctx.channel.send(embed=errorEmbed, delete_after=20)

    @commands.command(aliases=['imgur'])
    async def imgurSearch(self, ctx, toSend: typing.Optional[int] = None, *, query):
        try:
            with open('./imgur_api.yaml', 'r') as f:
                stream = yaml.full_load(f)
                clientID = stream[str('Client-ID')]
        except FileNotFoundError:
            with open('imgur_api.yaml', 'w') as f:
                f.write('Client-ID: CLIENT_ID_FROM_IMGUR')
            title = "Created File"
            description = "The file `imgur_api.yaml` was created. Insert your Imgur Client ID in the placeholder"
            color = discord.Color.red()
            errorEmbed = discord.Embed(title=title,
                                       description=description,
                                       color=color)
            await ctx.channel.send(embed=errorEmbed)
            return

        path = f"imgur{str(query)}"
        query = str(query)
        reqURL = f"https://api.imgur.com/3/gallery/search/?q_all={query}"
        headers = {'Authorization': f'Client-ID {clientID}'}
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

    @imgurSearch.error
    async def imgurSearch_error(self, ctx, error):
        if isinstance(error, CommandInvokeError):
            title = "No Imgur Client ID"
            description = "Please paste your Imgur Client ID in the file `imgur_api.yaml` in the placeholder"
            color = discord.Color.red()
            errorEmbed = discord.Embed(title=title,
                                       description=description,
                                       color=color)
            await ctx.channel.send(embed=errorEmbed, delete_after=20)

    @commands.command(aliases=['isabellepic', 'isabelleemote', 'belle', 'bellepic', 'belleemote'])
    async def isabelle(self, ctx, toSend: typing.Optional[int] = None):
        path = "./isabelle"
        await self.imageSend(ctx, path, toSend=toSend)

    @commands.command(aliases=['peppapic', 'ppic', 'ppig'])
    async def peppa(self, ctx, toSend: typing.Optional[int] = None):
        path = "./peppa"
        await self.imageSend(ctx, path, toSend=toSend)

    @commands.command()
    async def say(self, ctx, *, args):
        await ctx.message.delete()
        sayEmbed = discord.Embed(description=args,
                                 color=discord.Color.blue())
        await ctx.channel.send(embed=sayEmbed)
        gcmds.incrCounter(gcmds, 'say')

    @commands.command(aliases=['toadpic', 'toademote'])
    async def toad(self, ctx, toSend: typing.Optional[int] = None):
        path = "./toad"
        await self.imageSend(ctx, path, toSend=toSend)


def setup(client):
    client.add_cog(Fun(client))
