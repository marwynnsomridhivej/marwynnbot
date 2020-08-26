import asyncio
import json
import os
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta
from dateparser.search import search_dates
from globalcommands import GlobalCMDS as gcmds

timeout = 30
reactions = ["🔁", "✅", "🛑"]


class Reminders(commands.Cog):

    def __init__(self, client):
        self.client = client
        if not self.check_single.is_running():
            self.check_single.start()
            self.check_loop.start()

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
                        if reminder['time'] - datetime.now().timestamp() <= 15.0:
                            user_id = int(user)
                            sleep_time = reminder['time'] - \
                                datetime.now().timestamp()
                            if sleep_time <= 0:
                                sleep_time = 0
                            await asyncio.create_task(self.send_single(sleep_time, user_id, reminder['channel_id'],
                                                                       reminder['message_content'], int(
                                                                           guild), index,
                                                                       file))
                    index += 1

    async def send_single(self, sleep_time: float, user_id: int, channel_id: int, message_content: str, guild_id: int,
                          index: int, file: dict):
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

    @tasks.loop(seconds=1, count=1)
    async def check_loop(self):
        with open('reminders.json', 'r') as f:
            file = json.load(f)
            f.close()
        for guild in file:
            for user in file[str(guild)]:
                for reminder in file[str(guild)][str(user)]:
                    if reminder['type'] == "loop":
                        await asyncio.create_task(self.send_loop(reminder['time'], int(user), reminder['channel_id'],
                                                                 reminder['message_content'], int(guild)))

    async def send_loop(self, loop_interval: int, user_id: int, channel_id: int, message_content: str, guild_id: int):
        while True:
            await asyncio.sleep(1.0)
            if int(datetime.now().timestamp()) % int(loop_interval) == 0:
                try:
                    channel = await commands.AutoShardedBot.fetch_channel(self.client, channel_id)
                    user = await channel.guild.fetch_member(user_id)
                    embed = discord.Embed(title=f"Reminder for {user.display_name}",
                                          description=message_content,
                                          color=discord.Color.blue())
                    await channel.send(f"{user.mention}")
                    await channel.send(embed=embed)
                except (discord.Forbidden, discord.HTTPException, discord.InvalidData, discord.NotFound):
                    pass
            else:
                continue

    async def send_remind_help(self, ctx) -> discord.Message:
        embed = discord.Embed(title="Reminders Help",
                              description=f"To use reminder commands, just do `{gcmds.prefix(gcmds, ctx)}remind ["
                                          f"option]`. Here is a list of valid options",
                              color=discord.Color.blue())
        embed.add_field(name="Create",
                        value=f"Usage: `{gcmds.prefix(gcmds, ctx)}remind [message_with_time]`\n"
                              f"Returns: Your reminder message at the specified time\n"
                              f"Aliases: `reminder`\n"
                              f"Special Cases: You must specify a time within your message, whether it be exact or "
                              f"relative",
                        inline=False)
        embed.add_field(name="Edit",
                        value=f"Usage: `{gcmds.prefix(gcmds, ctx)}remind edit`\n"
                              f"Returns: An interactive reminder edit panel\n"
                              f"Aliases: `-e`\n"
                              f"Special Cases: You must have at least one reminder queued",
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

    async def not_valid_time(self, ctx) -> discord.Message:
        embed = discord.Embed(title="Invalid Time",
                              description=f"{ctx.author.mention}, you did not provide a valid time",
                              color=discord.Color.dark_red())
        return await ctx.channel.send(embed=embed, delete_after=10)

    async def create_reminder(self, user_id: int, channel_id: int, guild_id: int,
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
                continue
        with open('reminders.json', 'w') as g:
            json.dump(file, g, indent=4)

        await asyncio.create_task(self.send_loop(send_time, user_id, channel_id, message_content, guild_id))

    async def get_reminders(self, guild_id: int, user_id: int) -> str:
        if not os.path.exists('reminders.json'):
            return None

        with open('reminders.json', 'r') as f:
            file = json.load(f)
            f.close()

        index = 1
        string = ""
        user_info = file[str(guild_id)][str(user_id)]
        if len(user_info) == 0 or not user_info:
            return None
        for entry in user_info:
            if entry['type'] == "single":
                string += f"**{index}:** {entry['type']}, fires at {datetime.fromtimestamp(entry['time'])}, "
                f"{entry['message_content']}\n\n"
            elif entry['type'] == "loop":
                td = timedelta(seconds=entry['time'])
                time_formatted = ""
                days = divmod(86400, td.seconds)
                if days[0] != 0:
                    time_formatted += f"{days[0]} days, "
                rem_sec = days[1]
                hours = divmod(3600, rem_sec)
                if hours[0] != 0:
                    time_formatted += f"{hours[0]} hours, "
                rem_sec = hours[1]
                minutes = divmod(60, rem_sec)
                if minutes[0] != 0:
                    time_formatted += f"{minutes[0]} minutes, "
                seconds = rem_sec
                if seconds != 0:
                    time_formatted += f"{seconds} seconds"
                print(days, hours, minutes, seconds)
                string += f"**{index}:** {entry['type']}, fires every {time_formatted}, {entry['message_content']}\n\n"
            index += 1
        return string

    async def get_reminder_time(self, guild_id: int, user_id: int, index: int) -> str:
        with open('reminders.json', 'r') as f:
            file = json.load(f)
            f.close()

        if file[str(guild_id)][str(user_id)][index]['type'] == "single":
            return datetime.fromtimestamp(file[str(guild_id)][str(user_id)][index]['time']).strftime("%m/%d/%Y %H:%M:%S UTC")
        else:
            td = timedelta(seconds=file[str(guild_id)]
                           [str(user_id)][index]['time'])
            time_formatted = ""
            days = divmod(86400, td.seconds)
            if days[0] != 0:
                time_formatted += f"{days[0]} days, "
            rem_sec = days[1]
            hours = divmod(3600, rem_sec)
            if hours[0] != 0:
                time_formatted += f"{hours[0]} hours, "
            rem_sec = hours[1]
            minutes = divmod(60, rem_sec)
            if minutes[0] != 0:
                time_formatted += f"{minutes[0]} minutes, "
            seconds = rem_sec
            if seconds != 0:
                time_formatted += f"{seconds} seconds"
            return time_formatted

    async def no_reminders(self, ctx) -> discord.Message:
        embed = discord.Embed(title="No Reminders",
                              description=f"{ctx.author.mention}, you currently have no reminders scheduled",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed, delete_after=10)

    async def get_reminder_type(self, guild_id: int, user_id: int, index: int) -> str:
        with open('reminders.json', 'r') as f:
            file = json.load(f)
            f.close()
        
        print(file[str(guild_id)][str(user_id)][index])

        return file[str(guild_id)][str(user_id)][index]['type']

    async def get_reminder_content(self, guild_id: int, user_id: int, index: int) -> str:
        with open('reminders.json', 'r') as f:
            file = json.load(f)
            f.close()

        return file[str(guild_id)][str(user_id)][index]['message_content']

    async def edit_reminder(self, guild_id: int, user_id: int, index: int, time_to_send, edited_content):
        try:
            with open('reminders.json', 'r') as f:
                file = json.load(f)
                f.close()
            info = file[str(guild_id)][str(user_id)][index]
            if time_to_send:
                info['time'] = time_to_send
            if edited_content:
                info['message_content'] = edited_content
            with open('reminders.json', 'w') as g:
                json.dump(file, g, indent=4)
                g.close()
            return True
        except KeyError:
            return False

    @commands.group(aliases=['reminder'])
    async def remind(self, ctx, *, message_with_time: str = None):
        await gcmds.invkDelete(gcmds, ctx)
        if not message_with_time:
            return await self.send_remind_help(ctx)

        if message_with_time == "-e" or message_with_time == "edit":
            await ctx.invoke(self.edit)
            return

        current_time = datetime.now().timestamp()
        dates = search_dates(text=message_with_time, settings={
                             'PREFER_DATES_FROM': "future"})
        if not dates:
            return await self.not_valid_time(ctx)
        time_to_send = dates[0][1].timestamp()
        remind_message_rem_time = message_with_time.replace(
            f"{dates[0][0]}", "")
        if remind_message_rem_time.startswith(" "):
            remind_message = remind_message_rem_time[1:]
        else:
            remind_message = remind_message_rem_time

        panel_embed = discord.Embed(title="Reminder Setup Panel",
                                    description=f"{ctx.author.mention}, would you like this reminder to loop?\n\n"
                                                f"*React with* 🔁 *to loop,* ✅ *to have it send once, or* 🛑 "
                                                f"*to cancel",
                                    color=discord.Color.blue())
        panel = await ctx.channel.send(embed=panel_embed)
        for reaction in reactions:
            await panel.add_reaction(reaction)

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
            if str(dates[0][0]).startswith("in ") or str(dates[0][0]).startswith("at "):
                str_time = str(dates[0][0])
            else:
                str_time = "in " + str(dates[0][0])
            panel_new_title = "Reminder Successfully Created"
            panel_new_description = f"{ctx.author.mention}, your reminder has been created and will be dispatched to " \
                                    f"this channel {str_time}"
            finished = await self.edit_panel(panel_embed, panel, panel_new_title, panel_new_description)
            if not finished:
                return await self.cancelled(ctx, panel)
            await self.create_reminder(ctx.author.id, ctx.channel.id, ctx.guild.id, time_to_send,
                                       remind_message, remind_type)
        elif remind_type == "loop":
            str_time = "every" + \
                str(dates[0][0]).replace("in ", "").replace("at ", "")
            panel_new_title = "Reminder Successfully Created"
            panel_new_description = f"{ctx.author.mention}, your reminder has been created and will be dispatched to " \
                                    f"this channel {str_time}"
            finished = await self.edit_panel(panel_embed, panel, panel_new_title, panel_new_description)
            if not finished:
                return await self.cancelled(ctx, panel)
            loop_interval = time_to_send - current_time
            await self.create_reminder(ctx.author.id, ctx.channel.id, ctx.guild.id, loop_interval,
                                       remind_message, remind_type)

    @remind.command(aliases=['-e'])
    async def edit(self, ctx):
        reminders_list = await self.get_reminders(ctx.guild.id, ctx.author.id)
        if not reminders_list:
            return await self.no_reminders(ctx)
        panel_embed = discord.Embed(title="Edit Reminders",
                                    description=f"{ctx.author.mention}, please type the number of the reminder that "
                                    f"you would like to edit, or type *\"cancel\"* to cancel\n\n{reminders_list}",
                                    color=discord.Color.blue())
        panel = await ctx.channel.send(embed=panel_embed)

        def from_user(message: discord.Message) -> bool:
            if message.author.id == ctx.author.id:
                return True
            else:
                return False

        while True:
            try:
                if not await self.check_panel_exists(panel):
                    return await self.cancelled(ctx, panel)
                result = await commands.AutoShardedBot.wait_for(self.client, "message", check=from_user, timeout=timeout)
            except asyncio.TimeoutError:
                return await self.timeout(ctx)
            if result.content == "cancel":
                return await self.cancelled(ctx, panel)
            try:
                index = int(result.content) - 1
                break
            except (ValueError, TypeError):
                continue
        await result.delete()

        reminder_type = await self.get_reminder_type(ctx.guild.id, ctx.author.id, index)
        if reminder_type == "single":
            description = f"{ctx.author.mention}, please enter the time you would like this reminder to fire, type " \
                f"*\"skip\"* to keep the current time or type *\"cancel\"* to cancel\n\n" \
                f"Current Time: {await self.get_reminder_time(ctx.guild.id, ctx.author.id, index)}"
        elif reminder_type == "loop":
            description = f"{ctx.author.mention}, please enter the interval you would like this reminder to loop or" \
                f"type *\"cancel\"* to cancel\n\n" \
                f"Loops Every: {await self.get_reminder_time(ctx.guild.id, ctx.author.id, index)}"

        await self.edit_panel(panel_embed, panel, title=None, description=description)

        while True:
            try:
                if not await self.check_panel_exists(panel):
                    return await self.cancelled(ctx, panel)
                result = await commands.AutoShardedBot.wait_for(self.client, "message", check=from_user, timeout=timeout)
            except asyncio.TimeoutError:
                return await self.timeout(ctx)
            if result.content == "cancel":
                return await self.cancelled(ctx, panel)
            if result.content == "skip":
                time_to_send = None
                break

            current_time = datetime.now().timestamp()
            dates = search_dates(text=result.content, settings={
                                 'PREFER_DATES_FROM': "future"})
            if not dates:
                continue
            if reminder_type == "single":
                time_to_send = dates[0][1].timestamp()
            elif reminder_type == "loop":
                time_to_send = dates[0][1].timestamp() - current_time
            break
        await result.delete()

        description = f"{ctx.author.mention}, please type what you would like the reminder content to be if you would "\
            "like to change it, otherwise, type *\"skip\"* to keep the current content or type *\"cancel\"* to cancel" \
            f"\n\nCurrent Content: {await self.get_reminder_content(ctx.guild.id, ctx.author.id, index)}"
        await self.edit_panel(panel_embed, panel, title=None, description=description)

        while True:
            try:
                if not await self.check_panel_exists(panel):
                    return await self.cancelled(ctx, panel)
                result = await commands.AutoShardedBot.wait_for(self.client, "message", check=from_user, timeout=timeout)
            except asyncio.TimeoutError:
                return await self.timeout(ctx)
            if result.content == "cancel":
                return await self.cancelled(ctx, panel)
            elif result.content == "skip":
                edited_content = None
            else:
                edited_content = result.content
            break
        await result.delete()

        succeeded = await self.edit_reminder(ctx.guild.id, ctx.author.id, index, time_to_send, edited_content)
        if succeeded:
            await self.edit_panel(panel_embed, panel, title="Reminder Successfully Edited",
                                  description=f"{ctx.author.mention}, your reminder was successfully edited")
        else:
            await self.edit_panel(panel_embed, panel, title="Reminder Edit Failed",
                                  description=f"{ctx.author.menbtion}, your reminder could not be edited")
        return


def setup(client):
    client.add_cog(Reminders(client))
