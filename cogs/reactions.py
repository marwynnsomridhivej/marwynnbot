import asyncio
import re
import discord
from discord.ext import commands
from globalcommands import GlobalCMDS as gcmds

channel_tag_rx = re.compile(r'<#[0-9]{18}>')
channel_id_rx = re.compile(r'[0-9]{18}')

class Reactions(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" has been loaded')

    async def check_panel(self, panel: discord.Message) -> discord.Message:
        try:
            return panel
        except discord.NotFound:
            return None

    async def edit_panel(self, panel_embed: discord.Embed, panel: discord.Message,
                         title: str = None, description: str = None) -> discord.Message:
        if title:
            panel_embed.title = title
        if description:
            panel_embed.description = description
        return await panel.edit(embed=panel_embed)

    async def no_panel(self, ctx) -> discord.Message:
        embed = discord.Embed(title="Reacton Roles Setup Cancelled",
                              description=f"{ctx.author.mention}, the reaction roles setup was cancelled because the "
                                          f"setup panel was deleted or could not be found",
                              color=discord.Color.dark_red())
        return await ctx.channel.send(embed=embed)

    async def user_cancelled(self, ctx, panel: discord.Message) -> discord.Message:
        embed = discord.Embed(title="Reaction Roles Setup Cancelled",
                              description=f"{ctx.author.mention}, you have cancelled reaction roles setup",
                              color=discord.Color.dark_red())
        panel_message = await self.check_panel(panel)
        if not panel_message:
            return await ctx.channel.send(embed=embed, delete_after=10)
        else:
            return await panel_message.edit(embed=embed, delete_after=10)

    async def timeout(self, ctx, timeout: int, panel: discord.Message) -> discord.Message:
        embed = discord.Embed(title="Reaction Roles Setup Cancelled",
                              description=f"{ctx.author.mention}, the reaction roles setup was canelled because you "
                                          f"did not provide a valid action within {timeout} seconds",
                              color=discord.Color.dark_red())
        panel_message = await self.check_panel(panel)
        if not panel_message:
            return await ctx.channel.send(embed=embed, delete_after=10)
        else:
            return await panel_message.edit(embed=embed, delete_after=10)

    @commands.group(aliases=['rr'])
    @commands.bot_has_permissions(manage_roles=True, add_reactions=True)
    @commands.has_permissions(manage_guild=True)
    async def reactionrole(self, ctx):
        await gcmds.invkDelete(gcmds, ctx)
        if not ctx.invoked_subcommand:
            embed = discord.Embed(title="ReactionRoles Help Menu",
                                  description=f"All reaction roles commands can be accessed using "
                                              f"`{gcmds.prefix(gcmds, ctx)}reactionrole [option]`. "
                                              f"Below is a list of all the valid options",
                                  color=discord.Color.blue())
            embed.add_field(name="Create",
                            value=f"Usage: `{gcmds.prefix(gcmds, ctx)}reactionrole create`"
                                  f"Returns: Interactive reaction roles setup panel"
                                  f"Aliases: `start` `make`")
            return await ctx.channel.send(embed=embed)

    @reactionrole.command(aliases=['start', 'make'])
    async def create(self, ctx):

        panel_embed = discord.Embed(title="Reaction Role Setup Menu",
                                    description=f"{ctx.author.mention}, welcome to MarwynnBot's reaction role setup "
                                                f"menu. Just follow the prompts and you will have a working reaction "
                                                f"roles panel!",
                                    color=discord.Color.blue())
        panel = await ctx.channel.send(embed=panel_embed)

        await asyncio.sleep(5.0)

        def from_user(message: discord.Message) -> bool:
            if message.author == ctx.author and message.channel == ctx.channel:
                return True
            else:
                return False

        timeout = 30

        # User will input the channel by tag
        while True:
            try:
                panel_message = await self.check_panel(panel)
                if not panel_message:
                    return self.no_panel(ctx)
                await self.edit_panel(panel_embed, panel_message, title=None,
                                      description=f"{ctx.author.mention}, please tag the channel you would like the "
                                                  f"embed to be sent in (or type its ID)")
                result = await commands.AutoShardedBot.wait_for(self.client, "message", check=from_user, timeout=timeout)
            except asyncio.TimeoutError:
                return await self.timeout(ctx, timeout, panel)
            if not re.match(channel_tag_rx, result.content):
                if re.match(channel_id_rx, result.content):
                    channel_id = result.content
                    await result.delete()
                    break
                else:
                    continue
            channel_id = result.content[2:20]
            await result.delete()
            break

        channel = await commands.AutoShardedBot.fetch_channel(self.client, channel_id)

        # User will input the embed title
        try:
            panel_message = await self.check_panel(panel)
            if not panel_message:
                return self.no_panel(ctx)
            await self.edit_panel(panel_embed, panel_message, title=None,
                                  description=f"{ctx.author.mention}, please enter the title of the embed that will "
                                              f"be sent")
            result = await commands.AutoShardedBot.wait_for(self.client, "message", check=from_user, timeout=timeout)
        except asyncio.TimeoutError:
            return await self.timeout(ctx, timeout, panel)

        title = result.content
        await result.delete()

        # User will input the embed description
        try:
            panel_message = await self.check_panel(panel)
            if not panel_message:
                return self.no_panel(ctx)
            await self.edit_panel(panel_embed, panel_message, title=None,
                                  description=f"{ctx.author.mention}, please enter the description of the embed that "
                                              f"will be sent")
            result = await commands.AutoShardedBot.wait_for(self.client, "message", check=from_user, timeout=timeout)
        except asyncio.TimeoutError:
            return await self.timeout(ctx, timeout, panel)

        description = result.content
        await result.delete()

        # User will input the emoji, then appropriate role by tag
        emoji_role_list = []
        return


def setup(client):
    client.add_cog(Reactions(client))
