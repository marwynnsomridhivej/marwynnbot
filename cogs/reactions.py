import asyncio

import discord
import json
from discord.ext import commands
from globalcommands import GlobalCMDS as gcmds


class Reactions(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" has been loaded')

    @commands.group(aliases=['rr'])
    @commands.bot_has_permissions(administrator=True)
    @commands.has_permissions(administrator=True)
    async def reactionrole(self, ctx):
        await gcmds.invkDelete(gcmds, ctx)
        return

    @reactionrole.command(aliases=['c', 'make'])
    async def create(self, ctx, *, fastArgs=None):

        def check(message, user):
            if ctx.author == user and message.author == ctx.author and message.channel == ctx.channel:
                return True
            else:
                return False

        if fastArgs is None:
            rrGuide = discord.Embed(title="Reaction Roles Setup Menu",
                                    description=f"{ctx.author.mention}, I will walk you through setup for reaction "
                                                f"roles. Within 30 seconds, type `continue` to proceed or `cancel` to "
                                                f"cancel",
                                    color=discord.Color.blue())
            setup_message = await ctx.channel.send(embed=rrGuide)

            while True:
                try:
                    response = commands.AutoShardedBot.wait_for(self.client, 'message', check=check, timeout=30)
                except asyncio.TimeoutError:
                    rrCancel = discord.Embed(title="Reaction Roles Setup Cancelled",
                                             description=f"{ctx.author.mention}, setup was cancelled due to inactivity",
                                             color=discord.Color.dark_red())
                    await setup_message.edit(embed=rrCancel, delete_after=10)
                    return
                else:
                    if response.content == "continue":
                        try:
                            await invalid_response.delete()
                        except UnboundLocalError:
                            pass
                        break
                    elif response.content == "cancel":
                        rrCancel = discord.Embed(title="Reaction Roles Setup Cancelled",
                                                 description=f"{ctx.author.mention}, you have cancelled setup",
                                                 color=discord.Color.dark_red())
                        await setup_message.edit(embed=rrCancel, delete_after=10)
                        return
                    else:
                        invalid = discord.Embed(title="Invalid Response",
                                                description=f"{ctx.author.mention}, please type `continue` to "
                                                            f"continue or `cancel` to cancel",
                                                color=discord.Color.dark_red())
                        invalid_response = await ctx.channel.send(embed=invalid, delete_after=10)

            rrGuide = discord.Embed(title="Reaction Roles Setup Menu",
                                    description=f"{ctx.author.mention}, type the channel ID or tag the channel where "
                                                f"the message should be sent in",
                                    color=discord.Color.blue())
            await setup_message.edit(embed=rrGuide)

            try:
                reponse = commands.AutoShardedBot.wait_for(self.client, 'message', check=check, timeout=30)
            except asyncio.TimeoutError:
                rrCancel = discord.Embed(title="Reaction Roles Setup Cancelled",
                                         description=f"{ctx.author.mention}, setup was cancelled due to inactivity",
                                         color=discord.Color.dark_red())
                await setup_message.edit(embed=rrCancel, delete_after=10)
                return
            else:
                if "<" in response or ">" in response:
                    channel_id = int(response[2:-1])
                else:
                    channel_id = int(response)
                channel = commands.AutoShardedBot.get_channel(self.client, id=channel_id)
                # TODO: Send Message to Channel ID HERE

            rrGuide = discord.Embed(title="Reaction Roles Setup Menu",
                                    description=f"{ctx.author.mention}, type the title of the embed you would like to "
                                                f"send",
                                    color=discord.Color.blue())
            await setup_message.edit(embed=rrGuide)

            try:
                response = commands.AutoShardedBot.wait_for(self.client, 'message', check=check, timeout=30)
            except asyncio.TimeoutError:
                rrCancel = discord.Embed(title="Reaction Roles Setup Cancelled",
                                         description=f"{ctx.author.mention}, setup was cancelled due to inactivity",
                                         color=discord.Color.dark_red())
                await setup_message.edit(embed=rrCancel, delete_after=10)
                return
            else:
                title = response
                # TODO: Use TITLE as the embed title

            rrGuide = discord.Embed(title="Reaction Roles Setup Menu",
                                    description=f"{ctx.author.mention}, type the message you would like to send",
                                    color=discord.Color.blue())
            await setup_message.edit(embed=rrGuide)

            try:
                response = commands.AutoShardedBot.wait_for(self.client, 'message', check=check, timeout=30)
            except asyncio.TimeoutError:
                rrCancel = discord.Embed(title="Reaction Roles Setup Cancelled",
                                         description=f"{ctx.author.mention}, setup was cancelled due to inactivity",
                                         color=discord.Color.dark_red())
                await setup_message.edit(embed=rrCancel, delete_after=10)
                return
            else:
                description = response
                # TODO: Use DESCRIPTION as the embed description

            rrGuide = discord.Embed(title="Reaction Roles Setup Menu",
                                    description=f"{ctx.author.mention}, type the RGB value of the color you want the "
                                                f"embed to be",
                                    color=discord.Color.blue())
            await setup_message.edit(embed=rrGuide)

            while True:
                try:
                    response = commands.AutoShardedBot.wait_for(self.client, 'message', check=check, timeout=30)
                except asyncio.TimeoutError:
                    rrCancel = discord.Embed(title="Reaction Roles Setup Cancelled",
                                             description=f"{ctx.author.mention}, setup was cancelled due to inactivity",
                                             color=discord.Color.dark_red())
                    await setup_message.edit(embed=rrCancel, delete_after=10)
                    return
                else:
                    RGB = response.split()
                    for item in RGB:
                        if int(item) < 0 or int(item) > 255:
                            invalid = discord.Embed(title="Invalid RGB Value",
                                                    description="Please enter a valid RGB value",
                                                    color=discord.Color.dark_red())
                            invalid_response = ctx.channel.send(embed=invalid)
                            continue
                    try:
                        await invalid_response.delete()
                    except (UnboundLocalError, discord.NotFound):
                        pass
                    color = discord.Color.from_rgb(int(RGB[0]), int(RGB[1]), int(RGB[2]))
                    break
                    # TODO: Use COLOR as the embed color

            rolelist = []

            rrGuide = discord.Embed(title="Reaction Roles Setup Menu",
                                    description=f"{ctx.author.mention}, ping the role you would like to add, "
                                                f"or type `done` to finish adding roles",
                                    color=discord.Color.blue())
            await setup_message.edit(embed=rrGuide)

            while True:
                try:
                    response = commands.AutoShardedBot.wait_for(self.client, 'message', check=check, timeout=30)
                except asyncio.TimeoutError:
                    rrCancel = discord.Embed(title="Reaction Roles Setup Cancelled",
                                             description=f"{ctx.author.mention}, setup was cancelled due to inactivity",
                                             color=discord.Color.dark_red())
                    await setup_message.edit(embed=rrCancel, delete_after=10)
                    return
                else:
                    if response[0:4] == "<@&":
                        rolelist.append(response)
                    else:
                        invalid = discord.Embed(title="Invalid Emoji",
                                                description="Please enter a valid emoji",
                                                color=discord.Color.dark_red())
                        invalid_response = ctx.channel.send(embed=invalid)
                        continue
                    try:
                        await invalid_response.delete()
                    except (UnboundLocalError, discord.NotFound):
                        pass

            emojilist = []

            rrGuide = discord.Embed(title="Reaction Roles Setup Menu",
                                    description=f"{ctx.author.mention}, ping the emoji you would like to add, "
                                                f"or type `done` to finish adding emojis",
                                    color=discord.Color.blue())
            await setup_message.edit(embed=rrGuide)

            while True:
                try:
                    response = commands.AutoShardedBot.wait_for(self.client, 'message', check=check, timeout=30)
                except asyncio.TimeoutError:
                    rrCancel = discord.Embed(title="Reaction Roles Setup Cancelled",
                                             description=f"{ctx.author.mention}, setup was cancelled due to inactivity",
                                             color=discord.Color.dark_red())
                    await setup_message.edit(embed=rrCancel, delete_after=10)
                    return
                else:
                    if response[0] == ":" or response[0] == "<" or response[-1] == ":" or response[-1] == ">":
                        emojilist.append(response)
                        rrGuide.set_footer(text=f"Added emoji {response}")
                        setup_message.edit(embed=rrGuide)
                    elif response.content == "finish":
                        break
                    else:
                        invalid = discord.Embed(title="Invalid Emoji",
                                                description="Please enter a valid emoji",
                                                color=discord.Color.dark_red())
                        invalid_response = ctx.channel.send(embed=invalid)
                        continue
                    try:
                        await invalid_response.delete()
                    except (UnboundLocalError, discord.NotFound):
                        pass

            rrGuide.set_footer(text=discord.Embed.Empty)


def setup(client):
    client.add_cog(Reactions(client))
