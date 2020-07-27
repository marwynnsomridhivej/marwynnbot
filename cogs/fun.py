import pprint
import random
import requests
import typing
import yaml
import os
import re
import discord
import json
from discord.ext import commands
from discord.ext.commands import CommandInvokeError

import globalcommands
from globalcommands import GlobalCMDS as gcmds


class Fun(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "fun" has been loaded')

    async def imageSend(self, ctx, path):
        await ctx.message.delete()
        path = path
        files = os.listdir(path)
        name = random.choice(files)
        d = f'{path}/{name}'

        if "toad" in path:
            title = "Toad ❤️❤️❤️❤️❤️❤️"
            color = discord.Color.red()
            url = f"attachment://toad_{name}"
            gcmds.incrCounter(gcmds, 'toad')
        if "isabelle" in path:
            title = "Isabelle"
            color = discord.Color.blue()
            url = f"attachment://isabelle_{name}"
            gcmds.incrCounter(gcmds, 'isabelle')
        if "peppa" in path:
            title = "Peppa"
            color = discord.Color.blue()
            url = f"attachment://peppa_{name}"
            gcmds.incrCounter(gcmds, 'peppa')

        with open(d, 'rb') as f:
            picture = discord.File(f, d)
            pictureEmbed = discord.Embed(title=title,
                                         color=color)
            pictureEmbed.set_image(url=url)
            pictureEmbed.set_footer(text=f'Filename: {name}')
        await ctx.channel.send(file=picture,
                               embed=pictureEmbed)

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
    async def gifSearch(self, ctx, limit: typing.Optional[int] = None, *, query=None):
        await ctx.message.delete()
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
            if limit:
                query = str(limit)
                lmt = 50
                bool = True
            else:
                title = "No Search Term Specified"
                description = f"{ctx.author.mention}, you must specify at least one search term. "\
                              f"`Do {gcmds.prefix(gcmds, ctx)}help gifsearch` for command info"
                color = discord.Color.dark_red()
                bool = False

        if bool:
            query = str(query)
            if limit and limit < 50:
                lmt = limit
            else:
                lmt = 50
            r = requests.get("https://api.tenor.com/v1/random?q=%s&key=%s&limit=%s" % (query, api_key, lmt))
            if r.status_code == 200 or r.status_code == 202:
                results = json.loads(r.content)
                title = f"{query.capitalize()} GIF"
                description = "From *Tenor*"
                color = discord.Color.blue()
                getURL = []
                for i in range(len(results['results'])):
                    getURL.append(results['results'][i]['media'][0]['gif']['url'])
                url = random.choice(getURL)
                gcmds.incrCounter(gcmds, 'gifSearch')
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
        if bool:
            if url:
                embed.set_image(url=url)

        await ctx.channel.send(embed=embed)
        gcmds.incrCounter(gcmds, 'gifSearch')

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

    @commands.command(aliases=['isabellepic', 'isabelleemote', 'belle', 'bellepic', 'belleemote'])
    async def isabelle(self, ctx):
        path = "./isabelle"
        await self.imageSend(ctx, path)

    @commands.command(aliases=['peppapic', 'ppic', 'ppig'])
    async def peppa(self, ctx):
        path = "./peppa"
        await self.imageSend(ctx, path)

    @commands.command()
    async def say(self, ctx, *, args):
        await ctx.message.delete()
        sayEmbed = discord.Embed(description=args,
                                 color=discord.Color.blue())
        await ctx.channel.send(embed=sayEmbed)
        gcmds.incrCounter(gcmds, 'say')

    @commands.command(aliases=['toadpic', 'toademote'])
    async def toad(self, ctx):
        path = "./toad"
        await self.imageSend(ctx, path)


def setup(client):
    client.add_cog(Fun(client))
