import discord
from discord.ext import commands, tasks
from globalcommands import GlobalCMDS
import json
import os
import asyncio
import re
from datetime import datetime


gcmds = GlobalCMDS()
disboard_bot_id = 302050872383242240
channel_tag_rx = re.compile(r'<#[0-9]{18}>')
channel_id_rx = re.compile(r'[0-9]{18}')
timeout = 60


class Disboard(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.check_unsent_reminder.start()
    
    def cog_unload(self):
        self.check_unsent_reminder.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild and message.author.id == disboard_bot_id and os.path.exists('db/disboard.json'):
            message = message
            disboard_embed = message.embeds[0]
            if "bump done" in disboard_embed.description.lower():
                current_timestamp = datetime.now().timestamp()
                time_to_send = 7200 + int(current_timestamp)
                sleep_time = time_to_send - current_timestamp
                with open('db/disboard.json', 'r') as f:
                    file = json.load(f)
                    f.close()
                try:
                    channel = await self.client.fetch_channel(file[str(message.guild.id)]['channel_id'])
                except KeyError:
                    return
                title = "Disboard Bump Available!"
                message_content = file[str(message.guild.id)]['message_content']
                if not message_content:
                    description = "The bump cooldown has expired! You can now bump your server using `!d bump`"
                else:
                    description = message_content
                file[str(message.guild.id)].update({"time": time_to_send})
                with open('db/disboard.json', 'w') as g:
                    json.dump(file, g, indent=4)
                    g.close()
                self.client.loop.create_task(self.send_bump_reminder(channel, title, description, sleep_time))

    @tasks.loop(seconds=1, count=1)
    async def check_unsent_reminder(self):
        await self.client.wait_until_ready()
        if not os.path.exists('db/disboard.json'):
            return
        
        with open('db/disboard.json', 'r') as f:
            file = json.load(f)
            f.close()
        for guild in file:
            try:
                sleep_time = file[str(guild)]['time'] - int(datetime.now().timestamp())
                if sleep_time <= 0:
                    del file[str(guild)]['time']
                    continue
            except KeyError:
                continue
            title = "Disboard Bump Available!"
            if not file[str(guild)]['message_content']:
                description = "The bump cooldown has expired! You can now bump your server using `!d bump`"
            else:
                description = file[str(guild)]['message_content']
            channel = await self.client.fetch_channel(file[str(guild)]['channel_id'])
            self.client.loop.create_task(self.send_bump_reminder(channel, title, description, sleep_time))

    async def send_bump_reminder(self, channel, title, description, sleep_time) -> discord.Message:
        await asyncio.sleep(sleep_time)
        embed = discord.Embed(title=title,
                              description=description,
                              color=discord.Color.blue())
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass
        
        with open('db/disboard.json', 'r') as f:
            file = json.load(f)
            f.close()
        try:
            del file[str(channel.guild.id)]['time']
            with open('db/disboard.json', 'w') as g:
                json.dump(file, g, indent=4)
                g.close()
        except KeyError:
            pass

    async def get_disboard_help(self, ctx) -> discord.Message:
        title = "Disboard Commands"
        description = (f"{ctx.author.mention}, this is MarwynnBot's Disboard integration. MarwynnBot's many functions "
                       f"are listed here below. The base command is {gcmds.prefix(ctx)}disboard [option]. "
                       "Here are all the valid options for the `[option]` argument")
        create = (f"**Usage:** `{gcmds.prefix(ctx)}disboard create`\n"
                  "**Returns:** An interactive setup panel that will make your disboard bump reminder\n"
                  "**Aliases:** `-c` `make` `start`\n"
                  "**Special Cases:** You must have the `Disboard` bot in this server, otherwise, the command will fail")
        edit = (f"**Usage:** `{gcmds.prefix(ctx)}disboard edit`\n"
                "**Returns:** An interactive setup panel that will edit your current disboard bump reminder\n"
                "**Aliases:** `-e` `adjust`\n"
                "**Special Cases:** You must satisfy the special case for `create` and currently have a working bump "
                "reminder set")
        delete = (f"**Usage:** `{gcmds.prefix(ctx)}disboard delete`\n"
                  "**Returns:** A confirmation panel that will delete your current disboard bump reminder\n"
                  "**Aliases:** `-rm` `trash` `cancel`\n"
                  "**Special Cases:** You must satisfy the special case for `edit`")
        invite = (f"**Usage:** `{gcmds.prefix(ctx)}disboard invite`\n"
                  "**Returns:** An interactive panel that details how to get the `Disboard` bot into your own server")
        kick = (f"**Usage:** `{gcmds.prefix(ctx)}disboard kick`\n"
                "**Returns:** An embed that confirms if `Disboard` bot was successfully kicked from the server\n"
                "**Aliases:** `leave`\n"
                "**Special Cases:** You must satisfy the special case for `create`\nIt is recommended that you kick "
                "the `Disboard` bot this way because it will automatically delete any set bump reminders as well")
        name_value = [("Create", create), ("Edit", edit), ("Delete", delete), ("Invite", invite), ("Kick", kick)]
        embed = discord.Embed(title=title,
                              description=description,
                              color=discord.Color.blue())
        for name, value in name_value:
            embed.add_field(name=name,
                            value=value,
                            inline=False)
        return await ctx.channel.send(embed=embed)

    async def disboard_joined(self, ctx) -> bool:
        if not ctx.guild.get_member(disboard_bot_id):
            return False
        else:
            return True

    async def no_disboard(self, ctx) -> discord.Message:
        embed = discord.Embed(title="No Disboard Bot",
                              description=f"{ctx.author.mention}, you must register this server to `Disboard` before "
                              "you can use this command",
                              color=discord.Color.dark_red())
        return await ctx.channel.send(embed=embed, delete_after=10)

    async def check_bump_reminder(self, ctx) -> bool:
        if not os.path.exists("db/disboard.json"):
            return False

        with open('db/disboard.json', 'r') as f:
            file = json.load(f)
            f.close()

        try:
            if file[str(ctx.guild.id)]:
                return True
            else:
                return False
        except KeyError:
            return False

    async def has_bump_reminder(self, ctx) -> discord.Message:
        embed = discord.Embed(title="Bump Message Already Set",
                              description=f"{ctx.author.mention}, there is already a bump reminder set",
                              color=discord.Color.dark_red())
        return await ctx.channel.send(embed=embed, delete_after=10)

    async def set_bump_reminder(self, ctx, channel_id: int, message_content: str = None) -> bool:
        if not await self.disboard_joined(ctx):
            return False

        if not await self.client.fetch_channel(channel_id):
            return False

        init = {
            str(ctx.guild.id): {
                "channel_id": channel_id,
                "message_content": message_content
            }
        }

        gcmds.json_load('db/disboard.json', init)
        with open('db/disboard.json', 'r') as f:
            file = json.load(f)
            f.close()

        file[str(ctx.guild.id)] = {
            "channel_id": channel_id,
            "message_content": message_content
        }

        with open('db/disboard.json', 'w') as g:
            json.dump(file, g, indent=4)

        return True

    async def check_panel_exists(self, panel: discord.Message) -> bool:
        try:
            if panel.id:
                return True
            else:
                return False
        except (discord.NotFound, discord.Forbidden):
            return False

    async def edit_panel(self, ctx, panel: discord.Message, title: str = None, description: str = None,
                         color: discord.Color = discord.Color.blue()) -> discord.Message:
        if not await self.check_panel_exists(panel):
            return None

        orig_message = await ctx.channel.fetch_message(panel.id)
        orig_embed = orig_message.embeds[0]
        if title:
            title = title
        else:
            title = orig_embed.title

        if description:
            description = description
        else:
            description = orig_embed.description

        embed = discord.Embed(title=title,
                              description=description,
                              color=color)
        await orig_message.edit(embed=embed)
        return True

    @commands.group()
    @commands.has_permissions(manage_guild=True)
    async def disboard(self, ctx):
        await gcmds.invkDelete(ctx)
        if not ctx.invoked_subcommand:
            return await self.get_disboard_help(ctx)

    @disboard.command()
    async def create(self, ctx):
        if not await self.disboard_joined(ctx):
            return await self.no_disboard(ctx)

        if await self.check_bump_reminder(ctx):
            return await self.has_bump_reminder(ctx)

        def from_user(message: discord.Message) -> bool:
            if message.author.id == ctx.author.id and message.channel.id == ctx.channel.id:
                return True
            else:
                return False

        or_default = "or type \"skip\" to use the default value"

        panel_embed = discord.Embed(title="Disboard Bump Reminder Setup",
                                    description=f"{ctx.author.mention}, this interactive setup panel will guide you "
                                    "through creating a fully functional `Disboard` bump reminder",
                                    color=discord.Color.blue())
        panel_embed.set_footer(text='Type "cancel" to cancel at any time')
        panel = await ctx.channel.send(embed=panel_embed)

        await asyncio.sleep(5.0)

        cmd_name = "disboard bump reminder create"
        description = f"{ctx.author.mention}, tag or type the ID of the channel that you would like the bump reminder" \
            " to be sent in"

        # Get channel tag from user
        while True:
            try:
                if not await self.edit_panel(ctx, panel, None, description):
                    return await gcmds.panel_deleted(gcmds, ctx, cmd_name)
                result = await self.client.wait_for("message", check=from_user, timeout=timeout)
            except asyncio.TimeoutError:
                return await gcmds.timeout(self, ctx, cmd_name, timeout)
            if re.match(channel_tag_rx, result.content):
                channel_id = result.content[2:20]
                break
            elif re.match(channel_id_rx, result.content):
                channel_id = result.content
                break
            elif result.content == "cancel":
                return await gcmds.cancelled(ctx, cmd_name)
            else:
                continue
        await result.delete()

        description = f"{ctx.author.mention}, type what you would like the description of the reminder embed " \
            f"to be, {or_default}"
        
        try:
            if not await self.edit_panel(ctx, panel, None, description):
                return await gcmds.panel_deleted(gcmds, ctx, cmd_name)
            result = await self.client.wait_for("message", check=from_user, timeout=timeout)
        except asyncio.TimeoutError:
            return await gcmds.timeout(self, ctx, cmd_name, timeout)
        if result.content == "cancel":
            return await gcmds.cancelled(ctx, cmd_name)
        elif result.content == "skip":
            message_content = None
        else:
            message_content = result.content
        await result.delete()
        
        succeeded = await self.set_bump_reminder(ctx, channel_id, message_content)
        if succeeded:
            embed = discord.Embed(title="Successfully Created Disboard Bump Reminder",
                                  description=f"{ctx.author.mention}, as long as the `Disboard` bot is registering "
                                  f"bumps in <#{channel_id}>, this reminder should work",
                                  color=discord.Color.blue())
        else:
            embed = discord.Embed(title="Disboard Bump Reminder Creation Failed",
                                  description=f"{ctx.author.mention}, an error occurred during reminder creation",
                                  color=discord.Color.dark_red())
        try:
            return await panel.edit(embed=embed)
        except (discord.NotFound, discord.Forbidden):
            return await ctx.channel.send(embed=embed)

    @disboard.command()
    async def invite(self, ctx):
        title = "Disboard Bot Invite"
        description = (f"{ctx.author.mention}, here are the steps to get the `Disboard` bot onto any servers you have"
                       " permissions to add it to")
        login = ("You must connect your Discord account on https://disboard.org/. This will allow you to "
                 "register your server on `Disboard`")
        add_server = ("Add the server you would like `Disboard` to track. During the authentication process, the "
                      "`Disboard` bot should automatically be invited to join your server")
        from_url = ("Alternatively, you can manually add the bot by clicking on the *\"Add Bot\"* button on the "
                    "`Disboard` dashboard. You will be able to see the URL that will invite the bot. I assume "
                    "that if you choose to go this route and keep the URL, you know which parts of the URL need to "
                    "be kept and which parts can be removed")
        name_value = [("Login to Disboard", login), ("Add Your Server", add_server), ("Link from URL", from_url)]
        embed = discord.Embed(title=title,
                              description=description,
                              color=discord.Color.blue())
        for name, value in name_value:
            embed.add_field(name=name,
                            value=value,
                            inline=False)
        return await ctx.channel.send(embed=embed)


def setup(client):
    client.add_cog(Disboard(client))
