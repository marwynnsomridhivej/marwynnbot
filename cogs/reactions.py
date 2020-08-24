import asyncio
import json
import re
import discord
from discord.ext import commands

from globalcommands import GlobalCMDS as gcmds

channel_tag_rx = re.compile(r'<#[0-9]{18}>')
channel_id_rx = re.compile(r'[0-9]{18}')
role_tag_rx = re.compile(r'<@&[0-9]{18}>')
hex_color_rx = re.compile(r'#[A-Fa-f0-9]{6}')

gcmds.json_load(gcmds, 'reactionroles.json', {})
with open('reactionroles.json', 'r') as rr:
    rr_json = json.load(rr)


class Reactions(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" has been loaded')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        member = payload.member
        reacted_emoji = payload.emoji
        message_id = payload.message_id
        guild_id = payload.guild_id
        event_type = payload.event_type
        channel_id = payload.channel_id
        channel = await self.client.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)
        reactions = message.reactions
        users = [(reaction.emoji, await reaction.users().flatten()) for reaction in reactions]
        guild = await commands.AutoShardedBot.fetch_guild(self.client, guild_id)
        if not member.bot and event_type == "REACTION_ADD":
            try:
                role_emoji = rr_json[str(guild_id)][str(message_id)]
                type_name = role_emoji['type']
                for item in role_emoji['details']:
                    role = guild.get_role(int(item['role_id']))
                    if str(reacted_emoji) == str(item['emoji']):
                        if type_name == "normal" or type_name == "single_normal":
                            if role not in member.roles:
                                await member.add_roles(role)
                        if type_name == "reverse":
                            if role in member.roles:
                                await member.remove_roles(role)
                    elif str(reacted_emoji) != str(item['emoji']) and type_name == "single_normal":
                        if role in member.roles:
                            await member.remove_roles(role)
                if type_name == "single_normal":
                    for emoji, user in users:
                        if str(emoji) != str(reacted_emoji):
                            for reacted in user:
                                if member.id == reacted.id:
                                    await message.remove_reaction(emoji, member)
            except (discord.Forbidden, discord.NotFound, KeyError):
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        member_id = payload.user_id
        reacted_emoji = payload.emoji
        message_id = payload.message_id
        guild_id = payload.guild_id
        event_type = payload.event_type
        guild = await commands.AutoShardedBot.fetch_guild(self.client, guild_id)
        member = await guild.fetch_member(member_id)
        if not member.bot and event_type == "REACTION_REMOVE":
            try:
                role_emoji = rr_json[str(guild_id)][str(message_id)]
                type_name = role_emoji['type']
                for item in role_emoji['details']:
                    role = guild.get_role(int(item['role_id']))
                    if str(reacted_emoji) == str(item['emoji']):
                        if type_name == "normal" or type_name == "single_normal":
                            if role in member.roles:
                                await member.remove_roles(role)
                        if type_name == "reverse":
                            if role not in member.roles:
                                await member.add_roles(role)
            except (discord.Forbidden, discord.NotFound, KeyError):
                pass

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

    async def send_rr_message(self, ctx, channel: discord.TextChannel, send_embed: discord.Embed, emoji_list: list,
                              role_emoji: list, type_name: str):
        rr_message = await channel.send(embed=send_embed)
        for emoji in emoji_list:
            await rr_message.add_reaction(emoji)
        init = {str(ctx.guild.id): {str(rr_message.id): {"type": type_name, "details": []}}}
        gcmds.json_load(gcmds, 'reactionroles.json', init)
        with open('reactionroles.json', 'r') as f:
            file = json.load(f)
            f.close()
        file.update({str(ctx.guild.id): {}})
        file.update({str(ctx.guild.id): {str(rr_message.id): {}}})
        file[str(ctx.guild.id)].update({str(rr_message.id): {"type": type_name, "details": []}})
        for role, emoji in role_emoji:
            file[str(ctx.guild.id)][str(rr_message.id)]['details'].append({"role_id": str(role), "emoji": str(emoji)})
        with open('reactionroles.json', 'w') as g:
            json.dump(file, g, indent=4)

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
        panel_embed.set_footer(text="Type \"cancel\" to cancel at any time")
        panel = await ctx.channel.send(embed=panel_embed)

        await asyncio.sleep(5.0)

        def from_user(message: discord.Message) -> bool:
            if message.author == ctx.author and message.channel == ctx.channel:
                return True
            else:
                return False

        def panel_react(reaction: discord.Reaction, user: discord.User) -> bool:
            if reaction.message.id == panel.id and ctx.author.id == user.id:
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
                result = await commands.AutoShardedBot.wait_for(self.client, "message", check=from_user,
                                                                timeout=timeout)
            except asyncio.TimeoutError:
                return await self.timeout(ctx, timeout, panel)
            if not re.match(channel_tag_rx, result.content):
                if re.match(channel_id_rx, result.content):
                    channel_id = result.content
                    await result.delete()
                    break
                else:
                    if result.content == "cancel":
                        return await self.user_cancelled(ctx, panel_message)
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
        else:
            if result.content == "cancel":
                return await self.user_cancelled(ctx, panel_message)

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
        else:
            if result.content == "cancel":
                return await self.user_cancelled(ctx, panel_message)

        description = result.content
        await result.delete()

        # User will input the embed color
        while True:
            try:
                panel_message = await self.check_panel(panel)
                if not panel_message:
                    return self.no_panel(ctx)
                await self.edit_panel(panel_embed, panel_message, title=None,
                                      description=f"{ctx.author.mention}, please enter the hex color of the embed "
                                                  f"that will be sent")
                result = await commands.AutoShardedBot.wait_for(self.client, "message", check=from_user,
                                                                timeout=timeout)
            except asyncio.TimeoutError:
                return await self.timeout(ctx, timeout, panel)
            if not re.match(hex_color_rx, result.content):
                if result.content == "cancel":
                    return await self.user_cancelled(ctx, panel_message)
                else:
                    continue
            break

        color = int(result.content[1:], 16)
        await result.delete()

        # User will input the emoji, then appropriate role by tag
        emoji_role_list = []
        emoji_list = []
        while True:
            while True:
                try:
                    panel_message = await self.check_panel(panel)
                    if not panel_message:
                        return self.no_panel(ctx)
                    await self.edit_panel(panel_embed, panel_message, title=None,
                                          description=f"{ctx.author.mention}, please tag the role you would like to be "
                                                      f"added into the reaction role or type *finish* to finish setup")
                    result = await commands.AutoShardedBot.wait_for(self.client, "message", check=from_user,
                                                                    timeout=timeout)
                except asyncio.TimeoutError:
                    return await self.timeout(ctx, timeout, panel)
                if not re.match(role_tag_rx, result.content):
                    if result.content == "cancel":
                        return await self.user_cancelled(ctx, panel_message)
                    elif result.content == "finish":
                        break
                    else:
                        continue
                else:
                    break
            if result.content == "finish":
                await result.delete()
                break

            role = result.content[3:21]
            await result.delete()

            while True:
                try:
                    panel_message = await self.check_panel(panel)
                    if not panel_message:
                        return self.no_panel(ctx)
                    await self.edit_panel(panel_embed, panel_message, title=None,
                                          description=f"{ctx.author.mention}, please react to this panel with the emoji"
                                                      f" you want the user to react with to get the role {role}")
                    result = await commands.AutoShardedBot.wait_for(self.client, "reaction_add", check=panel_react,
                                                                    timeout=timeout)
                except asyncio.TimeoutError:
                    return await self.timeout(ctx, timeout, panel)
                if result[0].emoji in emoji_list:
                    continue
                else:
                    break

            emoji = result[0].emoji
            emoji_list.append(emoji)
            await result[0].message.clear_reactions()

            emoji_role_list.append((role, emoji))

        # User will input number to dictate type of reaction role
        while True:
            try:
                panel_message = await self.check_panel(panel)
                if not panel_message:
                    return self.no_panel(ctx)
                await self.edit_panel(panel_embed, panel_message, title=None,
                                      description=f"{ctx.author.mention}, please enter the number that corresponds to the "
                                                  f"type of reaction role behavior you would like\n\n"
                                                  f"**1:** Normal *(react to add, unreact to remove, multiple at a time)*\n"
                                                  f"**2:** Reverse *(react to remove, unreact to add, multiple at a time)*\n"
                                                  f"**3:** Single Normal *(same as normal, except you can only have one "
                                                  f"role at a time)*\n\n"
                                                  f"*If I wanted to pick `Normal`, I would type \"1\" as the response")
                result = await commands.AutoShardedBot.wait_for(self.client, "message", check=from_user,
                                                                timeout=timeout)
            except asyncio.TimeoutError:
                return await self.timeout(ctx, timeout, panel)
            else:
                if result.content == "cancel":
                    return await self.user_cancelled(ctx, panel_message)
                if result.content == "1":
                    type_name = "normal"
                    break
                if result.content == "2":
                    type_name = "reverse"
                    break
                if result.content == "3":
                    type_name = "single_normal"
                    break
                continue

        type_name = type_name
        await result.delete()

        # Post reaction role panel in the channel
        rr_embed = discord.Embed(title=title,
                                 description=description,
                                 color=color)
        return await self.send_rr_message(ctx, channel, rr_embed, emoji_list, emoji_role_list, type_name)


def setup(client):
    client.add_cog(Reactions(client))
