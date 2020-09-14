import asyncio
import os
import re
from datetime import datetime

import discord
from discord.ext import commands, tasks

from utils import globalcommands

gcmds = globalcommands.GlobalCMDS()
disboard_bot_id = 302050872383242240
channel_tag_rx = re.compile(r'<#[0-9]{18}>')
channel_id_rx = re.compile(r'[0-9]{18}')
timeout = 60


class Disboard(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.tasks = []
        self.bot.loop.create_task(self.init_disboard())
        self.check_unsent_reminder.start()

    def cog_unload(self):
        for task in self.tasks:
            task.cancel()
        self.check_unsent_reminder.cancel()

    async def init_disboard(self):
        await self.bot.wait_until_ready()
        async with self.bot.db.acquire() as con:
            await con.execute("CREATE TABLE IF NOT EXISTS disboard(guild_id bigint PRIMARY KEY, channel_id bigint, message_content text, time NUMERIC)")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild and message.author.id == disboard_bot_id:
            async with self.bot.db.acquire() as con:
                result = (await con.fetch(f"SELECT channel_id, message_content, time from disboard WHERE guild_id = {message.guild.id}"))[0]
            if not result:
                return
            message = message
            disboard_embed = message.embeds[0]
            if "bump done" in disboard_embed.description.lower():
                current_timestamp = int(datetime.now().timestamp())
                time_to_send = 7200 + int(current_timestamp)
                sleep_time = time_to_send - current_timestamp

                channel = await self.bot.fetch_channel(result['channel_id'])
                title = "Disboard Bump Available!"
                message_content = result['message_content']
                if not message_content:
                    description = "The bump cooldown has expired! You can now bump your server using `!d bump`"
                else:
                    description = message_content
                async with self.bot.db.acquire() as con:
                    await con.execute(f"INSERT INTO disboard(time) VALUES({time_to_send}) WHERE guild_id = "
                                      f"{message.guild.id} ON CONFLICT DO UPDATE disboard SET time = {time_to_send} WHERE guild_id = {message.guild.id}")

                self.tasks.append(self.bot.loop.create_task(
                    self.send_bump_reminder(channel, title, description, sleep_time)))

    @tasks.loop(seconds=1, count=1)
    async def check_unsent_reminder(self):
        await self.bot.wait_until_ready()
        async with self.bot.db.acquire() as con:
            result = await con.fetch(f"SELECT * FROM disboard")
        if not result:
            return

        for record in result:
            if not record['time']:
                continue
            sleep_time = record['time'] - int(datetime.now().timestamp())
            if sleep_time < 0:
                async with self.bot.db.acquire() as con:
                    await con.execute(f"UPDATE disboard SET time = NULL WHERE guild_id = {record['guild_id']}")
                continue
            title = "Disboard Bump Available!"
            description = record['message_content'] if record['message_content'] else "The bump cooldown has expired! You can now bump your server using `!d bump`"
            channel = await self.bot.fetch_channel(record['channel_id'])
            self.tasks.append(self.bot.loop.create_task(
                self.send_bump_reminder(channel, title, description, sleep_time)))

    async def send_bump_reminder(self, channel, title, description, sleep_time) -> discord.Message:
        await asyncio.sleep(sleep_time)
        embed = discord.Embed(title=title,
                              description=description,
                              color=discord.Color.blue())
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

        async with self.bot.db.acquire() as con:
            await con.execute(f"UPDATE disboard SET time = NULL WHERE guild_id = {channel.guild.id}")

    async def get_disboard_help(self, ctx) -> discord.Message:
        title = "Disboard Commands"
        description = (f"{ctx.author.mention}, this is MarwynnBot's Disboard integration. MarwynnBot's many functions "
                       f"are listed here below. The base command is {await gcmds.prefix(ctx)}disboard [option]. "
                       "Here are all the valid options for the `[option]` argument")
        create = (f"**Usage:** `{await gcmds.prefix(ctx)}disboard create`\n"
                  "**Returns:** An interactive setup panel that will make your disboard bump reminder\n"
                  "**Aliases:** `-c` `make` `start`\n"
                  "**Special Cases:** You must have the `Disboard` bot in this server, otherwise, the command will fail")
        edit = (f"**Usage:** `{await gcmds.prefix(ctx)}disboard edit`\n"
                "**Returns:** An interactive setup panel that will edit your current disboard bump reminder\n"
                "**Aliases:** `-e` `adjust`\n"
                "**Special Cases:** You must satisfy the special case for `create` and currently have a working bump "
                "reminder set")
        delete = (f"**Usage:** `{await gcmds.prefix(ctx)}disboard delete`\n"
                  "**Returns:** A confirmation panel that will delete your current disboard bump reminder\n"
                  "**Aliases:** `-rm` `trash` `cancel`\n"
                  "**Special Cases:** You must satisfy the special case for `edit`")
        invite = (f"**Usage:** `{await gcmds.prefix(ctx)}disboard invite`\n"
                  "**Returns:** An interactive panel that details how to get the `Disboard` bot into your own server")
        kick = (f"**Usage:** `{await gcmds.prefix(ctx)}disboard kick`\n"
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
        async with self.bot.db.acquire() as con:
            result = await con.fetch(f"SELECT * from disboard WHERE guild_id = {ctx.guild.id}")
        return True if result else False

    async def has_bump_reminder(self, ctx) -> discord.Message:
        embed = discord.Embed(title="Bump Message Already Set",
                              description=f"{ctx.author.mention}, there is already a bump reminder set",
                              color=discord.Color.dark_red())
        return await ctx.channel.send(embed=embed, delete_after=10)

    async def set_bump_reminder(self, ctx, channel_id: int, message_content: str = None) -> bool:
        if not await self.disboard_joined(ctx) or not await self.bot.fetch_channel(channel_id):
            return False

        async with self.bot.db.acquire() as con:
            await con.execute(f"INSERT INTO disboard(guild_id, channel_id, message_content) VALUES({ctx.guild.id}, {channel_id}, {message_content}) ON CONFLICT DO NOTHING")
        return True

    async def edit_bump_reminder(self, ctx, channel_id, message_content) -> bool:
        if not channel_id and not message_content:
            return True

        update = []
        if channel_id:
            update.append(f"channel_id = {channel_id}")
        if message_content:
            update.append(f"message_content = '{message_content}'" if message_content != "default" else "message_content = NULL")

        try:
            async with self.bot.db.acquire() as con:
                await con.execute(f"UPDATE disboard SET {', '.join(update)} WHERE guild_id = {ctx.guild.id}")
        except Exception:
            return False
        else:
            return True

    async def delete_bump_reminder(self, ctx):
        async with self.bot.db.acquire() as con:
            await con.execute(f"DELETE FROM disboard WHERE guild_id = {ctx.guild.id}")

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
                result = await self.bot.wait_for("message", check=from_user, timeout=timeout)
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

        await gcmds.smart_delete(result)

        description = f"{ctx.author.mention}, type what you would like the description of the reminder embed " \
            f"to be, {or_default}"

        try:
            if not await self.edit_panel(ctx, panel, None, description):
                return await gcmds.panel_deleted(gcmds, ctx, cmd_name)
            result = await self.bot.wait_for("message", check=from_user, timeout=timeout)
        except asyncio.TimeoutError:
            return await gcmds.timeout(self, ctx, cmd_name, timeout)
        await gcmds.smart_delete(result)
        if result.content == "cancel":
            return await gcmds.cancelled(ctx, cmd_name)
        elif result.content == "skip":
            message_content = None
        else:
            message_content = result.content
        await gcmds.smart_delete(result)

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

    @disboard.command(aliases = ['-e', 'adjust'])
    async def edit(self, ctx):
        if not self.check_bump_reminder(ctx):
            await ctx.invoke(self.create)
        
        async with self.bot.db.acquire() as con:
            info = (await con.fetch(f"SELECT * FROM disboard WHERE guild_id = {ctx.guild.id}"))[0]

        skip = ', or enter *"skip"* to keep the current channel'
        panel_embed = discord.Embed(title="Edit Disboard Reminder",
                                    description=f"{ctx.author.mention}, please tag the new channel you would like the "
                                    f"bump reminder to fire in {skip}.\n\nThe current channel is <#{info['channel_id']}>",
                                    color=discord.Color.blue())
        panel = await ctx.channel.send(embed=panel)

        def from_user_rx(message: discord.Message):
            return message.content == "cancel" or (re.match(channel_tag_rx, message.content) and message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)

        def from_user(message: discord.Message):
            return message.content == "cancel" or (message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)

        try:
            result = await self.bot.wait_for("message", check=from_user_rx, timeout=30)
        except asyncio.TimeoutError:
            return await gcmds.timeout(ctx, "bump reminder edit", 30)
        if result.content == "cancel":
            return await gcmds.cancelled(ctx, "bump reminder edit")
        channel_id = result.content[2:20] if result.content != "skip" else None

        content = info['message_content'] if info['message_content'] else "The bump cooldown has expired! You can now bump your server using `!d bump`"
        skip = skip.replace("channel", "message content")
        description = (f"{ctx.author.mention}, please enter the new message content you would like the bump reminder to"
                       f" display, or enter *\"default\"* to use the default message {skip}\n\nThe current message content is {content}")
        if not await self.edit_panel(ctx, panel, title=None, description=description):
            return await gcmds.panel_deleted(ctx, "bump reminder edit")

        try:
            result = await self.bot.wait_for("message", check=from_user, timeout=120)
        except asyncio.TimeoutError:
            return await gcmds.timeout(ctx, "bump reminder edit", 120)
        if result.content == "cancel":
            return await gcmds.cancelled(ctx, "bump reminder edit")
        if result.content == "default":
            message_content = "default"
        else:
            message_content = result.content if result.content != "skip" else None

        succeeded = await self.edit_bump_reminder(ctx, channel_id, message_content)
        if succeeded:
            title = "Edit Bump Reminder Success"
            description = f"{ctx.author.mention}, your bump reminder was successfully edited"
            color = discord.Color.blue()
        else:
            title = "Edit Bump Reminder Failed"
            description = f"{ctx.author.mention}, your bump reminder could not be edited"
            color = discord.Color.dark_red()
        if not await self.edit_panel(ctx, panel, title=title, description=description, color=color):
                embed = discord.Embed(title=title, description=description, color=color)
                return await ctx.channel.send(embed=embed)

    @disboard.command(aliases = ['-rm', 'trash', 'cancel'])
    async def delete(self, ctx):
        if not self.check_bump_reminder(ctx):
            embed = discord.Embed(title="No Bump Reminder Set",
                                  description=f"{ctx.author.mention}, there is currently no bump reminder set for this server",
                                  color=discord.Color.dark_red())
            return await ctx.channel.send(embed=embed)

        panel_embed = discord.Embed(title="Confirmation",
                                    description=f"{ctx.author.mention}, react with ✅ to delete the bump reminder or ❌ to cancel",
                                    color=discord.Color.blue())
        panel = await ctx.channel.send(embed=panel_embed)

        def user_reacted(reaction: discord.Reaction, user: discord.User):
            return reaction.emoji in ["✅", "❌"] and reaction.message.id == panel.id and user.id == ctx.author.id

        try:
            result = await self.bot.wait_for("reaction_add", check=user_reacted, timeout=30)
        except asyncio.TimeoutError:
            return await gcmds.timeout(ctx, "delete bump reminder", 30)
        if result[0].emoji == "✅":
            await self.delete_bump_reminder(ctx)
            return await self.edit_panel(ctx, panel, "Bump Reminder Deleted", f"{ctx.author.mention}, the bump reminder has been deleted")
        else:
            return await self.edit_panel(ctx, panel, "Cancelled", f'{ctx.author.mention}, you cancelled the bump reminder delete request')

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


def setup(bot):
    bot.add_cog(Disboard(bot))
