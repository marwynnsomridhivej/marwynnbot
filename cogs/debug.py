import asyncio
import datetime
import os
from datetime import datetime, timedelta

import discord
import dotenv
import psutil
from discord.ext import commands
from utils import GlobalCMDS

gcmds = GlobalCMDS()
updates_reaction = ['✅', '📝', '🛑']


class Debug(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def timeout(self, ctx, message: discord.Message) -> discord.Message:
        embed = discord.Embed(title="Report Update Cancelled",
                              description=f"{ctx.author.mention}, your report update request timed out",
                              color=discord.Color.dark_red())
        try:
            return await message.edit(embed=embed)
        except (discord.NotFound, discord.HTTPError, discord.Forbidden):
            return await ctx.author.send(embed=embed)

    async def cancel(self, ctx, message: discord.Message) -> discord.Message:
        embed = discord.Embed(title="Report Update Cancelled",
                              description=f"{ctx.author.mention}, your report update request was cancelled",
                              color=discord.Color.dark_red())
        try:
            return await message.edit(embed=embed)
        except (discord.NotFound, discord.HTTPError, discord.Forbidden):
            return await ctx.author.send(embed=embed)

    @commands.command(desc="Displays MarwynnBot's ping in milliseconds (ms)",
                      usage="ping")
    async def ping(self, ctx):
        ping = discord.Embed(title='Ping', color=discord.Color.blue())
        ping.set_thumbnail(url='https://cdn1.iconfinder.com/data/icons/travel-and-leisure-vol-1/512/16-512.png')
        ping.add_field(name="MarwynnBot", value=f'{round(self.bot.latency * 1000)}ms')
        await ctx.send(embed=ping)

    @commands.command(aliases=['mb', 'selfinfo', 'about', 'me'],
                      desc="Get info about me! Mostly for debug purposes though",
                      usage="marwynnbot")
    async def marwynnbot(self, ctx):
        async with self.bot.db.acquire() as con:
            command_amount = await con.fetchval("SELECT SUM (amount) FROM global_counters")
        current_process = psutil.Process(os.getpid())
        mem = psutil.virtual_memory()
        mem_used = current_process.memory_full_info().uss
        swap = psutil.swap_memory()
        swap_used = getattr(current_process.memory_full_info(), "swap", swap.used)
        disk = psutil.disk_usage("/")
        time_now = int(datetime.now().timestamp())
        complete_command_list = [command for cog in self.bot.cogs
                                 for command in self.bot.get_cog(cog).walk_commands()]
        td = timedelta(seconds=time_now - self.bot.uptime)
        description = (f"Hi there! I am a multipurpose Discord Bot made by <@{self.bot.owner_id}> "
                       "written in Python using the `discord.py` API wrapper. Here are some of my stats:")
        stats = (f"Servers Joined: {len(self.bot.guilds)}",
                 f"Users Served: {len(self.bot.users)}",
                 f"Commands: {len(self.bot.commands)}",
                 f"Commands Including Subcommands: {len(complete_command_list)}",
                 f"Aliases: {len([alias for command in self.bot.commands for alias in command.aliases if command.aliases])}",
                 f"Commands Processed: {command_amount}",
                 f"Uptime: {str(td)}")
        cpu_stats = "```{}```".format(
            "\n".join(
                    [f"Core {counter}: {round(freq, 2)}%"
                     for counter, freq in enumerate(psutil.cpu_percent(percpu=True))]
            )
        )
        memory_stats = "```{}```".format(
            "\n".join(
                [f"Total: {round((mem.total / 1000000), 2)} MB",
                 f"Available: {round((mem.available / 1000000), 2)} MB",
                 f"Used: {round((mem_used / 1000000), 2)} MB",
                 f"Percent: {round(100 * (mem_used / mem.total), 2)}%"]
            )
        )
        swap_stats = "```{}```".format(
            "\n".join(
                [f"Total: {round((swap.total / 1000000))} MB",
                 f"Free: {round((swap.free / 1000000), 2)} MB",
                 f"Used: {round((swap_used / 1000000), 2)} MB",
                 f"Percentage: {round(100 * (swap_used / swap.total), 2)}%"]
            )
        )
        disk_stats = "```{}```".format(
            "\n".join(
                [f"Total: {round((disk.total / 1000000000), 2)} GB",
                 f"Used: {round((disk.used / 1000000000), 2)} GB",
                 f"Free: {round((disk.free / 1000000000), 2)} GB",
                 f"Percentage: {round((100 * disk.used / disk.total), 2)}%"]
            )
        )
        nv = [
            ("Stats", "```{}```".format("\n".join(stats))),
            ("CPU Info", cpu_stats),
            ("Memory Info", memory_stats),
            ("Swap Info", swap_stats),
            ("Disk Info", disk_stats)
        ]
        embed = discord.Embed(title="Info About Me!", description=description, color=discord.Color.blue())
        for name, value in nv:
            embed.add_field(name=name, value=value, inline=False)
        return await ctx.channel.send(embed=embed)

    @commands.group(invoke_without_command=True,
                    aliases=['flag'],
                    desc="Displays the help command for all of report's subcommands",
                    usage="report")
    async def report(self, ctx):
        menu = discord.Embed(title="Report Options",
                             description=f"{ctx.author.mention}, here are the options for the report command:\n`["
                             f"bug]` - reports a bug\n`[update]` - owner only\n`[userAbuse]` - "
                             f"reports user from mention\n`[serverabuse] - reports server from ID`",
                             color=discord.Color.blue())
        await ctx.channel.send(embed=menu)

    @report.command(aliases=['issue'])
    async def bug(self, ctx, *, bug_message):
        try:
            marwynnbot_channel = commands.AutoShardedBot.get_channel(self.bot, 742899140320821367)
        except discord.NotFound:
            invalid = discord.Embed(title="Logging Channel Does Not Exist",
                                    description=f"{ctx.author.mention}, this feature is not available",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid)
            return
        else:
            timestamp = "Timestamp: {:%m/%d/%Y %H:%M:%S}".format(datetime.now())
            bug_string = str(bug_message)
            bugEmbed = discord.Embed(title=f"Bug Report by {ctx.author}",
                                     description=bug_string,
                                     color=discord.Color.blue())
            bugEmbed.set_footer(text=timestamp,
                                icon_url=ctx.author.avatar_url)
            message = await marwynnbot_channel.send(embed=bugEmbed)
            await message.publish()

    @report.command(aliases=['server', 'guild', 'serverabuse'])
    async def serverAbuse(self, ctx, *, abuse_message):
        return

    @report.command(aliases=['user', 'member', 'userabuse'])
    async def userAbuse(self, ctx, *, abuse_message):
        return

    @report.command(aliases=['fix', 'patch'])
    @commands.is_owner()
    async def update(self, ctx, *, update_message=None):
        updates_channel_id = gcmds.env_check("UPDATES_CHANNEL")
        if not updates_channel_id:
            no_channel = discord.Embed(title="No Updates Channel Specified",
                                       description=f"{ctx.author.mention}, you must specify the updates channel ID in"
                                                   f"the `.env` file",
                                       color=discord.Color.dark_red())
            return await ctx.channel.send(embed=no_channel)

        def confirm(reaction: discord.Reaction, user) -> bool:
            if reaction.emoji in updates_reaction and user.id == ctx.author.id:
                return True
            else:
                return False

        try:
            updates_channel = self.bot.get_channel(int(updates_channel_id))
        except discord.NotFound:
            invalid = discord.Embed(title="Logging Channel Does Not Exist",
                                    description=f"{ctx.author.mention}, this feature is not available",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=invalid)
            return

        timestamp = "Timestamp: {:%m/%d/%Y %H:%M:%S}".format(datetime.now())
        update_string = str(update_message)
        if update_string.splitlines()[0].startswith("**") and update_string.splitlines()[0].endswith("**"):
            title = update_string.splitlines()[0]
            description = update_string.replace(title, "")
        else:
            title = "Bot Update"
            description = update_string
        updateEmbed = discord.Embed(title=title,
                                    description=description,
                                    color=discord.Color.blue())
        updateEmbed.set_footer(text=timestamp,
                               icon_url=ctx.author.avatar_url)
        preview = await ctx.channel.send(embed=updateEmbed)

        panel_embed_start = discord.Embed(title="Confirmation",
                                          description=f"{ctx.author.mention}, react below for actions",
                                          color=discord.Color.blue())
        panel = await ctx.channel.send(embed=panel_embed_start)

        while True:
            if panel:
                await panel.edit(embed=panel_embed_start)
            else:
                panel = await ctx.channel.send(embed=panel_embed_start)

            # Adds reaction controls
            for reaction in updates_reaction:
                await panel.add_reaction(reaction)

            # User confirms send, requests edit, or cancels send
            while True:
                try:
                    response = await self.bot.wait_for("reaction_add", check=confirm, timeout=30)
                except asyncio.TimeoutError:
                    await panel.delete()
                    return await self.timeout(ctx, preview)
                else:
                    if response[0].emoji in updates_reaction:
                        await panel.clear_reactions()
                        break
                    else:
                        await panel.remove_reaction(response[0].emoji, ctx.author)
                        continue

            if response[0].emoji == "✅":
                message = await updates_channel.send(embed=updateEmbed)
                await message.publish()
                updateEmbed.set_footer(text="Successfully reported update to announcement channel",
                                       icon_url=ctx.author.avatar_url)
                return await preview.edit(embed=updateEmbed)
            elif response[0].emoji == '📝':
                def from_user(message: discord.Message) -> bool:
                    if message.author.id == ctx.author.id:
                        return True
                    else:
                        return False

                panel_embed = discord.Embed(title="Edit Title",
                                            description=f"{ctx.author.mention}, please enter what you would like the update "
                                            f"title to be or type *\"skip\"* to keep the current title",
                                            color=discord.Color.blue())
                panel_embed.set_footer(text="Type \"cancel\" to cancel at any time")
                await panel.edit(embed=panel_embed)

                # User edits title
                try:
                    response = await self.bot.wait_for("message", check=from_user, timeout=30)
                except asyncio.TimeoutError:
                    await gcmds.smart_delete(preview)
                    return await self.timeout(ctx, panel)
                if response.content == "cancel":
                    return await self.cancel(ctx, panel)
                if not response.content == "skip":
                    updateEmbed.title = response.content
                    await preview.edit(embed=updateEmbed)
                await gcmds.smart_delete(response)

                panel_embed.title = "Edit Description"
                panel_embed.description = f"{ctx.author.mention}, please enter what you would like the update description" \
                    f"to be or type *\"skip\" to keep the current description*"
                try:
                    await panel.edit(embed=panel_embed)
                except (discord.NotFound, discord.Forbidden, discord.HTTPError):
                    return await self.cancel(ctx, panel)

                # User edits description
                try:
                    response = await self.bot.wait_for("message", check=from_user, timeout=30)
                except asyncio.TimeoutError:
                    await gcmds.smart_delete(preview)
                    return await self.timeout(ctx, panel)
                if response.content == "cancel":
                    return await self.cancel(ctx, panel)
                if not response.content == "skip":
                    updateEmbed.description = response.content
                    await preview.edit(embed=updateEmbed)
                await gcmds.smart_delete(response)
            elif response[0].emoji == '🛑':
                await gcmds.smart_delete(panel)
                return await self.cancel(ctx, preview)

    @commands.command(desc="Displays what MarwynnBot shard is connected to your server",
                      usage="shard (flag)",
                      note="If `(flag)` is \"count\", it will display the total number of shards")
    async def shard(self, ctx, option=None):
        if option != 'count':
            shardDesc = f"This server is running on shard: {ctx.guild.shard_id}"
        else:
            shardDesc = f"**Shards:** {self.bot.shard_count}"
        shardEmbed = discord.Embed(title="Shard Info",
                                   description=shardDesc,
                                   color=discord.Color.blue())
        await ctx.channel.send(embed=shardEmbed)


def setup(bot):
    bot.add_cog(Debug(bot))
