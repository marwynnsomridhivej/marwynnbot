import discord
from discord.ext import commands
from globalcommands import GlobalCMDS as gcmds
import asyncio
import aiohttp
from num2words import num2words
import re
import mimetypes
import json
import os
import random

timeout = 30
channel_tag_rx = re.compile(r'<#[0-9]{18}>')
channel_id_rx = re.compile(r'[0-9]{18}')
api_key = gcmds.env_check(gcmds, "TENOR_API")


class Welcome(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" has been loaded')

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if os.path.exists('welcomers.json') and not member.bot:
            with open('welcomers.json', 'r') as f:
                file = json.load(f)
                f.close()
            member = member
            if str(member.guild.id) in file:
                guild = member.guild
                channel_to_send = await self.client.fetch_channel(file[str(guild.id)]["channel_id"])
                embed_title = file[str(guild.id)]['title']
                edv = str(file[str(guild.id)]['description'])
                media = file[str(guild.id)]['media']
                bot_count = 0
                for member in guild.members:
                    if member.bot:
                        bot_count += 1
                embed_description = ((((edv.replace("{server_name}", member.guild.name)
                                        ).replace("{user_name}", member.display_name)
                                       ).replace("{user_mention}", member.mention)
                                      ).replace("{member_count}", str(len(member.guild.members) - bot_count))
                                     ).replace("{member_count_ord}", num2words((len(member.guild.members) - bot_count),
                                                                               to="ordinal_num"))
                welcome_embed = discord.Embed(title=embed_title,
                                              description=embed_description,
                                              color=discord.Color.blue())
                welcome_embed.set_thumbnail(url=member.avatar_url)
                if isinstance(media, list):
                    image_url = random.choice(media)
                else:
                    query = "anime wave"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                                "https://api.tenor.com/v1/search?q=%s&key=%s&limit=%s" % (query, api_key, 6)) as image:
                            response = await image.json()
                            getURL = []
                            for i in range(len(response['results'])):
                                for j in range(len(response['results'][i]['media'])):
                                    getURL.append(response['results'][i]['media'][j]['gif']['url'])
                            image_url = random.choice(getURL)
                            await session.close()

                welcome_embed.set_image(url=image_url)
                return await channel_to_send.send(embed=welcome_embed)

    async def get_welcome_help(self, ctx) -> discord.Message:
        title = "Welcomer Help Menu"
        description = f"{ctx.author.mention}, the welcomer is used to greet new members of your server when they join. " \
            f"The base command is `{gcmds.prefix(gcmds, ctx)}welcome [option]` *alias=welcomer*. Here are the valid " \
            "options for `[option]`\n\n"
        create = f"**Usage:** `{gcmds.prefix(gcmds, ctx)}welcome create`\n" \
            "**Returns:** An interactive setup panel that will create a working welcomer in your server\n" \
            "**Aliases:** `make` `start` `-c`\n" \
            "**Special Cases:** You will be unable to use this command if you already have a welcomer set up. If you" \
            " try to use this command when you already have a welcomer set up, it will automatically redirect you to " \
            "the interactive edit panel"
        edit = f"**Usage:** `{gcmds.prefix(gcmds, ctx)}welcome edit`\n" \
            "**Returns:** An interactive setup panel that will edit your current welcomer\n" \
            "**Aliases:** `adjust` `modify` `-e`\n" \
            "**Special Cases:** You must have a welcomer currently set up in this server to use this command"
        delete = f"**Usage:** `{gcmds.prefix(gcmds, ctx)}welcome delete`\n" \
            "**Returns:** A confirmation panel that will delete your current welcomer if you choose to do so\n" \
            "**Aliases:** `trash` `cancel` `-rm`\n" \
            "**Special Cases:** You must have a welcomer currently set up in this server to use this command"
        fields = [("Create", create), ("Edit", edit), ("Delete", delete)]

        embed = discord.Embed(title=title,
                              description=description,
                              color=discord.Color.blue())
        for name, value in fields:
            embed.add_field(name=name,
                            value=value,
                            inline=False)
        return await ctx.channel.send(embed=embed)

    async def check_panel(self, panel: discord.Message) -> bool:
        try:
            if panel.id:
                return True
            else:
                return False
        except Exception:
            return False

    async def get_panel_embed(self, panel: discord.Message) -> discord.Message:
        try:
            if not await self.check_panel(panel):
                return False
            if panel.embeds:
                return panel.embeds[0]
            else:
                return False
        except Exception:
            return False

    async def edit_panel(self, ctx, panel: discord.Message, title: str = None,
                         description: str = None, color: discord.Color = None) -> bool:
        try:
            panel_embed = await self.get_panel_embed(panel)
            if not panel_embed:
                return False
            if not color:
                if title:
                    panel_embed.title = title
                if description:
                    panel_embed.description = description
            else:
                if title:
                    embed_title = title
                else:
                    embed_title = panel_embed.title
                if description:
                    embed_description = description
                else:
                    embed_description = panel_embed.description
                panel_embed = discord.Embed(title=embed_title,
                                            description=embed_description,
                                            color=color)
            await panel.edit(embed=panel_embed)
            return True
        except Exception:
            return False

    async def create_welcomer(self, ctx, channel_id: int, title: str = None, description: str = None,
                              media: list = None) -> bool:
        init = {
            str(ctx.guild.id): {
                "channel_id": channel_id,
                "title": title,
                "description": description,
                "media": media
            }
        }
        gcmds.json_load(gcmds, 'welcomers.json', init)
        with open('welcomers.json', 'r') as f:
            file = json.load(f)
            f.close()

        while True:
            try:
                if not title:
                    title = "New Member Joined!"
                if not description:
                    description = "Welcome to {server_name}! {user_mention} is our {member_count_ord} member!"
                file[str(ctx.guild.id)] = {
                    "channel_id": channel_id,
                    "title": title,
                    "description": description,
                    "media": media
                }
                break
            except KeyError:
                file[str(ctx.guild.id)] = {}
                continue
            except Exception:
                return False

        with open('welcomers.json', 'w') as g:
            json.dump(file, g, indent=4)
            g.close()
        return True

    async def has_welcomer(self, ctx) -> bool:
        if not os.path.exists('welcomers.json'):
            return False

        with open('welcomers.json', 'r') as f:
            file = json.load(f)
            f.close()

        try:
            if file[str(ctx.guild.id)]:
                return True
        except KeyError:
            return False

    async def get_welcomer(self, ctx) -> list:
        if not await self.has_welcomer(ctx):
            return None

        with open('welcomers.json', 'r') as f:
            file = json.load(f)
            f.close()

        info = file[str(ctx.guild.id)]
        return [info['channel_id'], info['title'], info['description'], info['media']]

    async def edit_welcomer(self, ctx, channel_id: int, title: str, description: str, media: list = None) -> bool:
        with open('welcomers.json', 'r') as f:
            file = json.load(f)
            f.close()

        try:
            file[str(ctx.guild.id)]['channel_id'] = channel_id
            file[str(ctx.guild.id)]['title'] = title
            file[str(ctx.guild.id)]['description'] = description
            if media:
                if "default" in media:
                    file[str(ctx.guild.id)]['media'] = None
                else:
                    file[str(ctx.guild.id)]['media'] = media
        except KeyError:
            return False

        with open('welcomers.json', 'w') as g:
            json.dump(file, g, indent=4)
        return True

    async def no_welcomer(self, ctx) -> discord.Message:
        embed = discord.Embed(title="No Welcomer Set",
                              description=f"{ctx.author.mention}, no welcomer is set to display for this server",
                              color=discord.Color.dark_red())
        return await ctx.channel.send(embed=embed, delete_after=10)

    async def delete_welcomer(self, ctx) -> bool:
        with open('welcomers.json', 'r') as f:
            file = json.load(f)
            f.close()

        try:
            del file[str(ctx.guild.id)]
            if len(file) == 0:
                file = {}
        except KeyError:
            return False

        with open('welcomers.json', 'w') as g:
            json.dump(file, g, indent=4)
        return True

    @commands.group(aliases=['welcomer'])
    async def welcome(self, ctx):
        await gcmds.invkDelete(gcmds, ctx)

        if not ctx.invoked_subcommand:
            return await self.get_welcome_help(ctx)

    @welcome.command(aliases=['make', 'start', '-c'])
    @commands.has_permissions(manage_guild=True)
    async def create(self, ctx):
        if await self.has_welcomer(ctx):
            await ctx.invoke(self.edit)
            return

        def from_user(message: discord.Message) -> bool:
            if message.author.id == ctx.author.id and message.channel.id == ctx.channel.id:
                return True
            else:
                return False

        panel_embed = discord.Embed(title="Welcomer Setup Panel",
                                    description=f"{ctx.author.mention}, this is the interactive welcomer setup panel. "
                                    "Follow all the prompts and you will have a fully functioning welcomer in no time!",
                                    color=discord.Color.blue())
        panel_embed.set_footer(text="Cancel anytime by entering \"cancel\"")
        panel = await ctx.channel.send(embed=panel_embed)

        or_default = "or type *\"skip\"* to use the default value"
        cmd_title = "welcomer setup"
        await asyncio.sleep(5.0)

        description = f"{ctx.author.mention}, please tag or enter the ID of the channel that you would like " \
            "the welcomer to send messages in"

        # User provides the channel that the welcome embed will be sent in
        while True:
            try:
                edit_success = await self.edit_panel(ctx, panel, title=None, description=description)
                if not edit_success:
                    return await gcmds.panel_deleted(gcmds, ctx, cmd_title)
                result = await self.client.wait_for("message", check=from_user, timeout=timeout)
            except asyncio.TimeoutError:
                return await gcmds.timeout(gcmds, ctx, cmd_title, timeout)
            if re.match(channel_tag_rx, result.content):
                channel_id = result.content[2:20]
                break
            elif re.match(channel_id_rx, result.content):
                channel_id = result.content
                break
            else:
                continue
        await result.delete()

        description = f"{ctx.author.mention}, please enter the title of the welcome embed, {or_default}\n\n" \
            "Default Value: New Member Joined!"

        # User provides welcome embed title
        try:
            edit_success = await self.edit_panel(ctx, panel, title=None, description=description)
            if not edit_success:
                return await gcmds.panel_deleted(gcmds, ctx, cmd_title)
            result = await self.client.wait_for("message", check=from_user, timeout=timeout)
        except asyncio.TimeoutError:
            return await gcmds.timeout(gcmds, ctx, cmd_title, timeout)
        if result.content == "cancel":
            return await gcmds.cancelled(gcmds, ctx, cmd_title)
        elif result.content == "skip":
            embed_title = None
        else:
            embed_title = result.content
        await result.delete()

        bot_count = 0
        for member in ctx.guild.members:
            if member.bot:
                bot_count += 1

        description = f"{ctx.author.mention}, please enter the description of the welcome embed, {or_default}\n\n" \
            "Default Value: Welcome to {server_name}! {user_mention} is our {member_count_ord} member!\n\n" \
            "Variables Supported:\n" \
            "`{server_name}` ⟶ Your server's name ⟶ " + f"{ctx.guild.name}\n" \
            "`{user_name}` ⟶ The name of the user that just joined ⟶ " + f"{ctx.author.display_name}\n" \
            "`{user_mention}` ⟶ The mention for the user that just joined ⟶ " + f"{ctx.author.mention}\n" \
            "`{member_count}` ⟶ The number of members in this server ⟶ " + f"{int(len(ctx.guild.members) - bot_count)}\n" \
            "`{member_count_ord}` ⟶ The ordinal number of members in this server ⟶ " \
            f"{num2words((len(ctx.guild.members) - bot_count), to='ordinal_num')}"

        # User provides welcome embed description
        try:
            edit_success = await self.edit_panel(ctx, panel, title=None, description=description)
            if not edit_success:
                return await gcmds.panel_deleted(gcmds, ctx, cmd_title)
            result = await self.client.wait_for("message", check=from_user, timeout=timeout)
        except asyncio.TimeoutError:
            return await gcmds.timeout(gcmds, ctx, cmd_title, timeout)
        if result.content == "cancel":
            return await gcmds.cancelled(gcmds, ctx, cmd_title)
        elif result.content == "skip":
            embed_description = None
        else:
            embed_description = result.content
        await result.delete()

        # User provides media links
        url_list = []
        while True:
            if not url_list:
                formatted_urls = ""
            else:
                formatted_urls = '\n==============\n'.join(url_list)
            description = f"{ctx.author.mention}, you can set custom images or gifs to be sent in the welcomer message " \
                f"when someone joins this server. Please enter a valid image URL *(.png, .jpg, .gif)*, {or_default}." \
                f" Enter *\"finish\"* to finish adding URLs\n\nCurrent URLs:\n {formatted_urls}"
            try:
                edit_success = await self.edit_panel(ctx, panel, title=None, description=description)
                if not edit_success:
                    return await gcmds.panel_deleted(gcmds, ctx, cmd_title)
                result = await self.client.wait_for("message", check=from_user, timeout=120)
            except asyncio.TimeoutError:
                return await gcmds.timeout(gcmds, ctx, cmd_title, 120)
            if result.content == "cancel":
                return await gcmds.cancelled(gcmds, ctx, cmd_title)
            elif result.content == "skip":
                url_list = None
                break
            elif result.content == "finish":
                break
            else:
                mimetype, encoding = mimetypes.guess_type(result.content)
                if mimetype and mimetype in ["image/gif", "image/jpeg", "image/jpg", "image/png"]:
                    url_list.append(result.content)
                await result.delete()
                continue

        succeeded = await self.create_welcomer(ctx, channel_id, embed_title, embed_description, url_list)
        if succeeded:
            title = "Successfully Created Welcomer"
            description = f"{ctx.author.mention}, your welcomer will be fired at <#{channel_id}> every time a new " \
                "member joins your server!"
            edit_success = await self.edit_panel(ctx, panel, title=title, description=description)
            if not edit_success:
                embed = discord.Embed(title=title,
                                      description=description,
                                      color=discord.Color.blue())
                return await ctx.channel.send(embed=embed)
        else:
            title = "Could Not Create Welcomer"
            description = f"{ctx.author.mention}, there was a problem creating your welcomer"
            edit_success = await self.edit_panel(ctx, panel, title=title, description=description,
                                                 color=discord.Color.dark_red())
            if not edit_success:
                embed = discord.Embed(title=title,
                                      description=description,
                                      color=discord.Color.dark_red())
                return await ctx.channel.send(embed=embed)

    @welcome.command(aliases=['adjust', 'modify', '-e'])
    @commands.has_permissions(manage_guild=True)
    async def edit(self, ctx):
        info = await self.get_welcomer(ctx)
        if not info:
            return await self.no_welcomer(ctx)

        cmd_title = "welcomer edit"
        or_default = "or type *\"skip\"* to use the currently set value"

        def from_user(message: discord.Message) -> bool:
            if message.author.id == ctx.author.id and message.channel.id == ctx.channel.id:
                return True
            else:
                return False
        
        if not info[3]:
            media = "Current Images: Default"
        else:
            media = "Current Images:\n" + '\n==============\n'.join(info[3])

        # Display the current welcomer
        temp_welcomer_embed = discord.Embed(title=info[1],
                                            description=info[2] + "\n\n" + media,
                                            color=discord.Color.blue())
        temp_welcomer = await ctx.channel.send(embed=temp_welcomer_embed)

        panel_embed = discord.Embed(title="Welcomer Edit Setup",
                                    description=f"{ctx.author.mention}, this welcomer edit panel will walk you through "
                                    "editing your current server welcome message",
                                    color=discord.Color.blue())
        panel_embed.set_footer(text="Type *\"cancel\"* to cancel at any time")
        panel = await ctx.channel.send(embed=panel_embed)

        await asyncio.sleep(5)

        description = "Please tag or enter the ID of the channel you would like MarwynnBot to send the welcomer" \
            f" message, {or_default}\n\nCurrent Channel: <#{info[0]}>"

        # Get channel ID from user
        while True:
            try:
                edit_success = await self.edit_panel(ctx, panel, title=None, description=description)
                if not edit_success:
                    return await gcmds.panel_deleted(gcmds, ctx, cmd_title)
                result = await self.client.wait_for("message", check=from_user, timeout=timeout)
            except asyncio.TimeoutError:
                return await gcmds.timeout(gcmds, ctx, cmd_title, timeout)
            if result.content == "cancel":
                try:
                    await temp_welcomer.delete()
                except Exception:
                    pass
                return await gcmds.cancelled(gcmds, ctx, cmd_title)
            elif result.content == "skip":
                new_channel_id = info[0]
                break
            elif re.match(result.content, channel_tag_rx):
                new_channel_id = result.content[2:20]
                break
            elif re.match(result.content, channel_id_rx):
                new_channel_id = result.content
                break
            else:
                continue
        await result.delete()

        description = f"{ctx.author.mention}, please enter the title of the welcomer you would like " \
            f"MarwynnBot to display, {or_default}\n\nCurrent Title: {info[1]}"

        # Get title from user
        try:
            edit_success = await self.edit_panel(ctx, panel, title=None, description=description)
            if not edit_success:
                return await gcmds.panel_deleted(gcmds, ctx, cmd_title)
            result = await self.client.wait_for("message", check=from_user, timeout=timeout)
        except asyncio.TimeoutError:
            return await gcmds.timeout(gcmds, ctx, cmd_title, timeout)
        await result.delete()
        if result.content == "cancel":
            try:
                await temp_welcomer.delete()
            except Exception:
                pass
            return await gcmds.cancelled(gcmds, ctx, cmd_title)
        elif result.content == "skip":
            new_title = info[1]
        else:
            new_title = result.content

        # Update temp_welcomer

        try:
            temp_welcomer_embed.title = new_title
            await temp_welcomer.edit(embed=temp_welcomer_embed)
        except (discord.NotFound, discord.HTTPException, discord.Forbidden):
            return await gcmds.cancelled(gcmds, ctx, cmd_title)

        # Edit panel description
        bot_count = 0
        for member in ctx.guild.members:
            if member.bot:
                bot_count += 1

        desc_variables = "Variables Supported:\n" \
            "`{server_name}` ⟶ Your server's name ⟶ " + f"{ctx.guild.name}\n" \
            "`{user_name}` ⟶ The name of the user that just joined ⟶ " + f"{ctx.author.display_name}\n" \
            "`{user_mention}` ⟶ The mention for the user that just joined ⟶ " + f"{ctx.author.mention}\n" \
            "`{member_count}` ⟶ The number of members in this server ⟶ " + f"{int(len(ctx.guild.members) - bot_count)}\n" \
            "`{member_count_ord}` ⟶ The ordinal number of members in this server ⟶ " \
            f"{num2words((len(ctx.guild.members) - bot_count), to='ordinal_num')}"

        description = "Please enter the description of the welcomer message you would like MarwynnBot to" \
            f" display, {or_default}\n\nCurrent Description: {info[2]}\n\n{desc_variables}"

        # Get desription from user
        try:
            edit_success = await self.edit_panel(ctx, panel, title=None, description=description)
            if not edit_success:
                return await gcmds.panel_deleted(gcmds, ctx, cmd_title)
            result = await self.client.wait_for("message", check=from_user, timeout=timeout)
        except asyncio.TimeoutError:
            return await gcmds.timeout(gcmds, ctx, cmd_title, timeout)
        await result.delete()
        if result.content == "cancel":
            try:
                await temp_welcomer.delete()
            except Exception:
                pass
            return await gcmds.cancelled(gcmds, ctx, cmd_title)
        elif result.content == "skip":
            new_description = info[2]
        else:
            new_description = result.content

        # User provides media links
        url_list = []
        while True:
            if not url_list:
                formatted_urls = ""
            else:
                formatted_urls = '\n==============\n'.join(url_list)
            description = f"{ctx.author.mention}, you can set custom images or gifs to be sent in the welcomer message " \
                f"when someone joins this server. Please enter a valid image URL *(.png, .jpg, .gif)*, *\"default\"* " \
                f"to use the default gifs, {or_default}." \
                f" Enter *\"finish\"* to finish adding URLs\n\nCurrent URLs:\n {formatted_urls}"
            try:
                edit_success = await self.edit_panel(ctx, panel, title=None, description=description)
                if not edit_success:
                    return await gcmds.panel_deleted(gcmds, ctx, cmd_title)
                result = await self.client.wait_for("message", check=from_user, timeout=120)
            except asyncio.TimeoutError:
                return await gcmds.timeout(gcmds, ctx, cmd_title, 120)
            await result.delete()
            if result.content == "cancel":
                try:
                    await temp_welcomer.delete()
                except Exception:
                    pass
                return await gcmds.cancelled(gcmds, ctx, cmd_title)
            elif result.content == "skip":
                url_list = None
                break
            elif result.content == "default":
                url_list = ['default']
                break
            elif result.content == "finish":
                break
            else:
                mimetype, encoding = mimetypes.guess_type(result.content)
                if mimetype and mimetype in ["image/gif", "image/jpeg", "image/jpg", "image/png"]:
                    url_list.append(result.content)
                continue

        succeeded = await self.edit_welcomer(ctx, new_channel_id, new_title, new_description, url_list)
        await temp_welcomer.delete()
        if succeeded:
            title = "Successfully Edited Welcomer"
            description = f"{ctx.author.mention}, your welcomer will be fired at <#{new_channel_id}> every time a new " \
                "member joins your server!"
            edit_success = await self.edit_panel(ctx, panel, title=title, description=description)
            if not edit_success:
                embed = discord.Embed(title=title,
                                      description=description,
                                      color=discord.Color.blue())
                return await ctx.channel.send(embed=embed)
        else:
            title = "Could Not Edit Welcomer"
            description = f"{ctx.author.mention}, there was a problem editing your welcomer"
            edit_success = await self.edit_panel(ctx, panel, title=title, description=description,
                                                 color=discord.Color.dark_red())
            if not edit_success:
                embed = discord.Embed(title=title,
                                      description=description,
                                      color=discord.Color.dark_red())
                return await ctx.channel.send(embed=embed)

    @welcome.command(aliases=['-rm', 'trash', 'cancel'])
    async def delete(self, ctx):
        info = await self.get_welcomer(ctx)
        if not info:
            return await self.no_welcomer(ctx)

        reactions = ["✅", "🛑"]
        cmd_title = "welcomer delete"

        panel_embed = discord.Embed(title="Confirm Welcomer Delete",
                                    description=f"{ctx.author.mention}, please react with ✅ to delete this server's "
                                    "welcomer message or react with 🛑 to cancel",
                                    color=discord.Color.blue())
        panel = await ctx.channel.send(embed=panel_embed)
        for reaction in reactions:
            await panel.add_reaction(reaction)

        def user_reacted(reaction: discord.Reaction, user: discord.User) -> bool:
            if reaction.emoji in reactions and user.id == ctx.author.id and \
                    reaction.message.id == panel.id and not user.bot:
                return True
            else:
                return False

        # Get confirmation from user
        while True:
            try:
                result = await self.client.wait_for("reaction_add", check=user_reacted, timeout=timeout)
            except asyncio.TimeoutError:
                return await gcmds.timeout(gcmds, ctx, cmd_title, timeout)
            if result[0].emoji in reactions:
                break
            else:
                continue
        await panel.clear_reactions()

        if result[0].emoji == "✅":
            succeeded = await self.delete_welcomer(ctx)
            if succeeded:
                title = "Successfully Deleted Welcomer"
                description = f"{ctx.author.mention}, your welcomer was successfully deleted"
                edit_success = await self.edit_panel(ctx, panel, title=title, description=description)
                if not edit_success:
                    embed = discord.Embed(title=title,
                                          description=description,
                                          color=discord.Color.blue())
                    return await ctx.channel.send(embed=embed)
        else:
            title = "Could Not Delete Welcomer"
            description = f"{ctx.author.mention}, there was a problem deleting your welcomer"
            edit_success = await self.edit_panel(ctx, panel, title=title, description=description,
                                                 color=discord.Color.dark_red())
            if not edit_success:
                embed = discord.Embed(title=title,
                                      description=description,
                                      color=discord.Color.dark_red())
                return await ctx.channel.send(embed=embed)


def setup(client):
    client.add_cog(Welcome(client))
