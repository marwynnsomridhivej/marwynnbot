import asyncio
import json
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
from dateparser.search import search_dates
from globalcommands import GlobalCMDS as gcmds

timeout = 30
reactions = ["🔁", "✅", "🛑"]


class Reminders(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.check_single.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" has been loaded')

    @tasks.loop(seconds=15)
    async def check_single(self):
        with open('reminders.json', 'r') as f:
            file = json.load(f)
            f.close()
        for guild in file:
            for user in file[str(guild)]:
                index = 0
                for reminder in file[str(guild)][str(user)]:
                    if reminder['type'] == "single":
                        if int(reminder['time'] - datetime.utcnow().timestamp()) <= 15:
                            user_id = int(user)
                            sleep_time = int(reminder['time'] - datetime.utcnow().timestamp())
                            if sleep_time <= 0:
                                sleep_time = 0
                            await asyncio.create_task(self.send_single(sleep_time, user_id, reminder['channel_id'],
                                                                       reminder['message_content'], int(guild), index,
                                                                       file))
                    index += 1

    async def send_single(self, sleep_time: int, user_id: int, channel_id: int, message_content: str, guild_id: int,
                          index: int, file: dict):
        print("Task created")
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)
        try:
            channel = await commands.AutoShardedBot.fetch_channel(self.client, channel_id)
            user = await channel.guild.fetch_member(user_id)
            embed = discord.Embed(title=f"Reminder for {user.display_name}",
                                  description=message_content,
                                  color=discord.Color.blue())
            await channel.send(f"{user.mention}")
            await channel.send(embed=embed)
            del file[str(guild_id)][str(user_id)][index]
            with open('reminders.json', 'w') as f:
                json.dump(file, f, indent=4)
        except (discord.Forbidden, discord.HTTPException, discord.InvalidData, discord.NotFound):
            pass

    async def send_remind_help(self, ctx) -> discord.Message:
        embed = discord.Embed(title="Reminders Help",
                              description=f"To use reminder commands, just do `{gcmds.prefix(gcmds, ctx)}remind ["
                                          f"option]`. Here is a list of valid options",
                              color=discord.Color.blue())
        embed.add_field(name="Create",
                        value=f"Usage: `{gcmds.prefix(gcmds, ctx)}remind create [message]`\n"
                              f"Returns: Your reminder message at the specified time\n"
                              f"Aliases: `-c` `make` `set`\n"
                              f"Special Cases: You must specify a time within your message, whether it be exact or "
                              f"relative",
                        inline=False)
        return await ctx.channel.send(embed=embed)

    async def timeout(self, ctx) -> discord.Message:
        embed = discord.Embed(title="Reminder Setup Timed Out",
                              description=f"{ctx.author.mention}, your reminder setup timed out due to inactivity",
                              color=discord.Color.dark_red())
        return await ctx.channel.send(embed=embed, delete_after=10)

    async def check_panel_exists(self, panel: discord.Message) -> bool:
        try:
            if panel.id:
                return True
        except discord.NotFound:
            return False

    async def edit_panel(self, panel_embed: discord.Embed, panel: discord.Message,
                         title: str = None, description: str = None, ) -> bool:
        panel_exists = await self.check_panel_exists(panel)
        if not panel_exists:
            return False

        panel_embed = panel_embed

        if title:
            panel_embed.title = title
        if description:
            panel_embed.description = description

        await panel.edit(embed=panel_embed)
        return True

    async def no_panel(self, ctx) -> discord.Message:
        embed = discord.Embed(title="Reminder Setup Cancelled",
                              description=f"{ctx.author.mention}, the reminder setup panel was either deleted or could "
                                          f"not be found",
                              color=discord.Color.dark_red())
        return await ctx.channel.send(embed=embed, delete_after=10)

    async def cancelled(self, ctx, panel: discord.Message) -> discord.Message:
        embed = discord.Embed(title="Reminder Setup Cancelled",
                              description=f"{ctx.author.mention}, the reminder setup was cancelled",
                              color=discord.Color.blue())
        if await self.check_panel_exists(panel):
            return await panel.edit(embed=embed, delete_after=10)
        else:
            return await ctx.channel.send(embed=embed, delete_after=10)

    async def create_single_reminder(self, user_id: int, channel_id: int, guild_id: int,
                                     send_time: int, message_content: str, remind_type: str):
        init = {
            str(guild_id): {
                str(user_id): [
                    {
                        "type": remind_type,
                        "time": send_time,
                        "channel_id": channel_id,
                        "message_content": message_content
                    }
                ]
            }
        }

        info = {
            "type": remind_type,
            "time": send_time,
            "channel_id": channel_id,
            "message_content": message_content
        }

        gcmds.json_load(gcmds, 'reminders.json', init)
        with open('reminders.json', 'r') as f:
            file = json.load(f)
            f.close()
        while True:
            try:
                file[str(guild_id)][str(user_id)].append(info)
                break
            except KeyError:
                file.update({str(guild_id): {}})
                file[str(guild_id)].update({str(user_id): []})
        with open('reminders.json', 'w') as g:
            json.dump(file, g, indent=4)

    @commands.group()
    async def remind(self, ctx, *, message_with_time: str = None):
        await gcmds.invkDelete(gcmds, ctx)
        if not message_with_time:
            return await self.send_remind_help(ctx)

        dates = search_dates(text=message_with_time)
        time_to_send = dates[0][1].timestamp()
        remind_message_rem_time = message_with_time.replace(f"{dates[0][0]}", "")
        if remind_message_rem_time.startswith(" "):
            remind_message = remind_message_rem_time[1:]
        else:
            remind_message = remind_message_rem_time

        panel_embed = discord.Embed(title="Reminder Setup Panel",
                                    description=f"{ctx.author.mention}, would you like this reminder to loop?\n\n"
                                                f"*React with* 🔁 *to loop,* ✅ *to have it send once, or* 🛑 *to cancel",
                                    color=discord.Color.blue())
        panel = await ctx.channel.send(embed=panel_embed)
        for reaction in reactions:
            await panel.add_reaction(reaction)

        def from_user(message: discord.Message) -> bool:
            if message.author.id == ctx.author.id:
                return True
            else:
                return False

        def reacted_user(reaction: discord.Reaction, user: discord.User) -> bool:
            if reaction.message.id == panel.id and user.id == ctx.author.id and (reaction.emoji in reactions):
                return True
            else:
                return False

        try:
            result = await commands.AutoShardedBot.wait_for(self.client, "reaction_add", check=reacted_user,
                                                            timeout=timeout)
        except asyncio.TimeoutError:
            return await self.timeout(ctx)
        reaction = result[0].emoji
        await panel.clear_reactions()
        if reaction == "🛑":
            return await self.cancelled(ctx, panel)
        if reaction == "✅":
            remind_type = "single"
        elif reaction == "🔁":
            remind_type = "loop"

        if remind_type == "single":
            panel_new_title = "Reminder Successfully Created"
            panel_new_description = f"{ctx.author.mention}, your reminder has been created and will be dispatched to " \
                                    f"this channel in {dates[0][0]}"
            finished = await self.edit_panel(panel_embed, panel, panel_new_title, panel_new_description)
            if not finished:
                return await self.cancelled(ctx, panel)
            time_sent = (datetime.utcnow().timestamp() - time_to_send) + datetime.utcnow().timestamp()
            await self.create_single_reminder(ctx.author.id, ctx.channel.id, ctx.guild.id, time_sent,
                                              remind_message, remind_type)


def setup(client):
    client.add_cog(Reminders(client))
