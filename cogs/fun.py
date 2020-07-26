import random
import os
import re
import discord
import json
from discord.ext import commands


class Fun(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "fun" has been loaded')

    def incrCounter(self, cmdName):
        with open('counters.json', 'r') as f:
            values = json.load(f)
            values[str(cmdName)] += 1
        with open('counters.json', 'w') as f:
            json.dump(values, f, indent=4)

    async def imageSend(self, ctx, path):
        await ctx.message.delete()
        path = path
        files = os.listdir(path)
        name = random.choice(files)
        d = f'{path}//{name}'

        if "toad" in path:
            title = "Toad ❤️❤️❤️❤️❤️❤️"
            color = discord.Color.red()
            url = f"attachment://toad_{name}"
            self.incrCounter('toad')
        if "isabelle" in path:
            title = "Isabelle"
            color = discord.Color.blue()
            url = f"attachment://isabelle_{name}"
            self.incrCounter('isabelle')

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
        self.incrCounter('8ball')

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
        self.incrCounter('choose')

    @commands.command(aliases=['isabellepic', 'isabelleemote', 'belle', 'bellepic', 'belleemote'])
    async def isabelle(self, ctx):
        path = "./isabelle"
        await self.imageSend(ctx, path)

    @commands.command()
    async def say(self, ctx, *, args):
        await ctx.message.delete()
        sayEmbed = discord.Embed(description=args,
                                 color=discord.Color.blue())
        await ctx.channel.send(embed=sayEmbed)
        self.incrCounter('say')

    @commands.command(aliases=['toadpic', 'toademote'])
    async def toad(self, ctx):
        path = "./toad"
        await self.imageSend(ctx, path)


def setup(client):
    client.add_cog(Fun(client))
