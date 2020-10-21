from collections import namedtuple

import discord
from discord.ext import commands
from utils import (GlobalCMDS, SubcommandPaginator, confirm, customerrors,
                   handle, levels)

gcmds = GlobalCMDS()
lrl = namedtuple("RoleRewardListing", ['level', 'type', 'entries'])


class Leveling(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        global gcmds
        self.bot = bot
        gcmds = GlobalCMDS(self.bot)
        self.bot.loop.create_task(self.init_leveling())

    async def init_leveling(self):
        await self.bot.wait_until_ready()
        async with self.bot.db.acquire() as con:
            await con.execute("CREATE TABLE IF NOT EXISTS level_config(guild_id bigint PRIMARY KEY, "
                              "enabled boolean DEFAULT TRUE, route_channel_id bigint DEFAULT NULL, "
                              "freq smallint DEFAULT 1, per_min smallint DEFAULT 20, "
                              "server_notif boolean DEFAULT FALSE, global_notif boolean DEFAULT FALSE)")
            await con.execute("CREATE TABLE IF NOT EXISTS level_disabled(channel_id bigint PRIMARY KEY, "
                              "guild_id bigint, disabled boolean DEFAULT TRUE)")
            await con.execute("CREATE TABLE IF NOT EXISTS level_users(user_id bigint, guild_id bigint, "
                              "level smallint DEFAULT 0, xp NUMERIC, last_msg NUMERIC, enabled boolean DEFAULT TRUE)")
            await con.execute("CREATE TABLE IF NOT EXISTS level_global(user_id bigint, level smallint DEFAULT 0, "
                              "xp NUMERIC, last_msg NUMERIC, enabled boolean DEFAULT TRUE)")
            await con.execute("CREATE TABLE IF NOT EXISTS level_roles(role_id bigint PRIMARY KEY, guild_id bigint, "
                              "obtain_at smallint, type text DEFAULT 'add')")
            for guild in self.bot.guilds:
                await con.execute(f"INSERT INTO level_config(guild_id) VALUES({guild.id}) ON CONFLICT DO NOTHING")
        return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or message.guild.id == 336642139381301249:
            return
        await levels.calculate_level(self.bot, message)

    async def send_leveling_help(self, ctx) -> discord.Message:
        pfx = f"{await gcmds.prefix(ctx)}level"
        description = ("MarwynnBot offers a robust leveling feature that will allow server "
                       "owners to encourage overall engagement with the server. The base "
                       f"command is `{pfx}`. Here are all of MarwynnBot's leveling features")
        lhelp = (f"**Usage:** `{pfx} help`",
                 "**Returns:** This paginated help menu",
                 "**Aliases:** `h`")
        lenable = (f"**Usage:** `{pfx} enable (#channel)*va`",
                   "**Returns:** An embed that confirms that leveling has been enabled",
                   "**Aliases:** `on`",
                   "**Note:** If `(#channel)*va` is unspecified, it will apply the action "
                   "across all server channels")
        ldisable = (f"**Usage:** `{pfx} disable (#channel)*va`",
                    "**Returns:** An embed that confirms that leveling has been disabled",
                    "**Aliases:** `off`",
                    "**Note:** Leveling must be enabled in order for it to be disabled. "
                    "If `(#channel)*va` is unspecified, it will apply the action "
                    "across all server channels")
        lxpperminute = (f"**Usage:** `{pfx}xpperminute (value)`",
                        "**Returns:** A panel that will allow you to adjust the average XP per minute",
                        "**Aliases:** `xpm` `xppermin`",
                        "**Note:** `(value)` must be a positive integer value between 1 and 10000 (inclusive). "
                        "If `(value)` is not specified, it will display the current average XP per minute. "
                        "Adjusting the XP per minute only impacts your server")
        lfrequency = (f"**Usage:** `{pfx}frequency (value)`",
                      "**Returns:** A panel that will allow you to adjust the minumum XP cooldown duration",
                      "**Aliases:** `freq` `rate`",
                      "**Note:** `(value)` must be a positive integer value between 1 and 60 (inclusive). "
                      "`(value)` represents the cooldown (in minutes) for a server member to receive "
                      "XP after the last time they were given XP. If `(value)` is not specified, it will display "
                      "the server's current frequency in minutes. 1 minute is the minimum to discourage spam")
        lreroute = (f"**Usage:** `{pfx} reroute [#channel]`",
                    "**Returns:** An embed that confirms the level up messages will be redirected to this channel",
                    "**Aliases:** `redirect`")
        lunroute = (f"**Usage:** `{pfx} unroute`",
                    "**Returns:** An embed that confirms the level up messages will no longer be redirected",
                    "**Aliases:** `unredirect`")
        lnotify = (f"**Usage:** `{pfx} notify [mode] (status)`",
                   "**Returns:** An embed that confirms the level up notifications for the specified mode was "
                   "changed to the specified status",
                   "**Aliases:** `notif` `notifs`",
                   "**Note:** `[mode]` can be \"server\" *(\"s\")* or \"global\" *(\"g\")*, and `(status)` can be "
                   "\"true\" *(\"t\")* or \"false\" *(\"f\")*. If `(status)` is not specified or is not one of "
                   "the previously mentioned valid values, it will act as a toggle for `[mode]`")
        labout = (f"**Usage:** `{pfx} about`",
                  "**Returns:** An embed that contains a detailed description about MarwynnBot's leveling feature",
                  "**Aliases:** `info`")
        nv = [("Help", lhelp), ("Enable", lenable), ("Disable", ldisable),
              ("XP Per Minute", lxpperminute), ("Frequency", lfrequency), ("Reroute", lreroute),
              ("Unroute", lunroute), ("Notify", lnotify), ("About", labout)]
        embed = discord.Embed(title="Leveling Help", description=description, color=discord.Color.blue())
        pag = SubcommandPaginator(ctx, entries=[(name, value, False) for name, value in nv],
                                  per_page=3, show_entry_count=False, embed=embed)
        return await pag.paginate()

    async def send_leveling_about(self, ctx) -> discord.Message:
        custom_elements = ("- Enabling/Disabling XP gain in certain channels",
                           "- Enabling/Disabling XP gain for certain users",
                           "- Average XP gained per minute",
                           "- How often users can gain XP",
                           "- Directly modify levels and XP for any server member "
                           "*(does not impact global levels and XP)*",
                           "- Routing level up messages to a specific channel",
                           "- Role rewards upon level up",
                           "- Manner in which MarwynnBot adds/removes roles upon level up "
                           "*(eg. upon reaching level x, give user role y. "
                           "Upon reaching lvl n, remove role y, give role z)*")
        description = ("MarwynnBot offers a robust leveling feature that will allow server "
                       "owners to encourage overall engagement with the server. Here are some key elements "
                       "of the leveling system that you'll find to be very useful")
        flexibility = ("MarwynnBot's leveling system has a high degree of flexibility. "
                       "Here is everything server owners can customise per server:\n> " +
                       "\n> ".join(custom_elements))
        rewards = ("MarwynnBot's leveling feature has some built in incentives to encourage activity. "
                   "The leveling leaderboard is available per-server and globally, so MarwynnBot users "
                   "can check their server and global leveling progress and climb the leaderboard. "
                   "Upon reaching specific milestone levels, users will gain a special icon on "
                   "their user profile. Individual servers can also configure roles to reward "
                   "server members upon reaching a certain level, and there are multiple types "
                   "of role rewarding on top of that")
        nv = [("Flexibility", flexibility), ("Rewards", rewards)]
        embed = discord.Embed(title="About Leveling", description=description, color=discord.Color.blue())
        for name, value in nv:
            embed.add_field(name=name, value="> " + "\n> ".join(value), inline=False)
        return await ctx.channel.send(embed=embed)

    @levels.check_entry_exists(entry="enabled", db_name="level_config")
    async def show_current_xp_rate(self, ctx) -> discord.Message:
        async with self.bot.db.acquire() as con:
            xp_rate = await con.fetchval(f"SELECT per_min FROM level_config WHERE guild_id={ctx.guild.id}")
        embed = discord.Embed(title="XP Rate",
                              description=f"The average XP per minute is {xp_rate} XP per minute for this server",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @levels.check_entry_exists(entry="enabled", db_name="level_config")
    async def edit_current_xp_rate(self, ctx, value: int) -> discord.Message:
        async with self.bot.db.acquire() as con:
            await con.execute(f"UPDATE level_config SET per_min={value} WHERE guild_id={ctx.guild.id}")
        embed = discord.Embed(title="XP Rate",
                              description="The average XP per minute has been changed to "
                              f"{value} XP per minute for this server",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @levels.check_entry_exists(entry="enabled", db_name="level_config")
    async def show_current_freq(self, ctx) -> discord.Message:
        async with self.bot.db.acquire() as con:
            freq = await con.fetchval(f"SELECT freq FROM level_config WHERE guild_id={ctx.guild.id}")
        embed = discord.Embed(title="Leveling Frequency",
                              description=f"The frequency of XP gain is once every "
                              f"{freq} {'minutes' if freq != 1 else 'minute'}",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @levels.check_entry_exists(entry="enabled", db_name="level_config")
    async def edit_current_freq(self, ctx, value: int) -> discord.Message:
        async with self.bot.db.acquire() as con:
            await con.execute(f"UPDATE level_config SET freq={value} WHERE guild_id={ctx.guild.id}")
        embed = discord.Embed(title="Leveling Frequency",
                              description=f"The frequency of XP gain has been changed to once every "
                              f"{value} {'minutes' if value != 1 else 'minute'}",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @levels.check_entry_exists(entry="enabled", db_name="level_config")
    async def set_notify(self, ctx, mode: str, status: str) -> discord.Message:
        async with self.bot.db.acquire() as con:
            if status in ['f', 'false']:
                curr_status = await con.fetchval(f"UPDATE level_config SET {mode}_notif=FALSE "
                                                 f"WHERE guild_id={ctx.guild.id} RETURNING {mode}_notif")
            elif status in ['t', 'true']:
                curr_status = await con.fetchval(f"UPDATE level_config SET {mode}_notif=TRUE "
                                                 f"WHERE guild_id={ctx.guild.id} RETURNING {mode}_notif")
            else:
                curr_status = await con.fetchval(f"UPDATE level_config SET {mode}_notif=NOT {mode}_notif "
                                                 f"WHERE guild_id={ctx.guild.id} RETURNING {mode}_notif")
        embed = discord.Embed(title="Level Up Notifications Set",
                              description=f"{ctx.author.mention}, notifications for {mode} level ups have been "
                              f"turned {'on' if curr_status else 'off'}",
                              color=discord.Color.blue() if curr_status else discord.Color.dark_red())
        return await ctx.channel.send(embed=embed)

    async def send_levelroles_help(self, ctx):
        pfx = f"{await gcmds.prefix(ctx)}levelroles"
        description = ("Once you have configured MarwynnBot's leveling system, you can configure "
                       f"role rewards for when users level up. The base command is `{pfx}`. "
                       "Here are all the features for configuring role rewards")
        lgive = (f"**Usage:** `{pfx} give [level] [type] [@role]*va`",
                 "**Returns:** An embed that confirms those role rewards were successfully added",
                 "**Aliases:** `set`",
                 "**Note:** `[level]` should be an integer value between 1 and 100 inclusive, `[type]` can "
                 "be \"add\" *(\"a\")* or \"replace\" *(\"r\")* to specify if the previous roles obtained "
                 "should be kept or if the new roles will replace the old roles")
        lremove = (f"**Usage:** `{pfx} remove [level] (@role)*va`",
                   "**Returns:** A confirmation panel that once confirmed, will remove the selected roles "
                   "from the role rewards at the specified level",
                   "**Aliases:** `unset`",
                   "**Note:** If `(@role)*va` is not specified, it will remove all role rewards for "
                   "the specified level")
        lreset = (f"**Usage:** `{pfx} reset`",
                  "**Returns:** A confirmation panel that once confirmed, will remove ALL role rewards "
                  "for ALL levels",
                  "**Aliases:** `clear`",
                  "**Note:** This action cannot be undone, and will remove ALL role rewards for ALL levels")
        llist = (f"**Usage:** `{pfx} list (level)`",
                 "**Returns:** An embed that displays the role rewards for the specified level",
                 "**Aliases:** `show` `-ls`",
                 "**Note:** If `(level)` is not specified, it will display ALL the role rewards that are set")
        lchangelevel = (f"**Usage:** `{pfx} changelevel [level] [@role]`",
                        "**Returns:** A confirmation panel that once confirmed, will set the level "
                        "required to obtain `[@role]` as a role reward to the specified level",
                        "**Aliases:** `cl` `levelchange`",
                        "**Note:** `[level]` must be between 1 and 100. If no role rewards currently "
                        "exist for the specified level, it will automatically create one with the same "
                        "role rewarding behavior as its current level. If that role is the only role "
                        "for it's current level role reward, it will keep the role reward, just adjust "
                        "the level")
        lchangetype = (f"**Usage:** `{pfx} changetype [type] (level)`",
                       "**Returns:** A confirmation panel that once confirmed, will set the type of "
                       "the role rewarding behavior for the specified level",
                       "**Aliases:** `ct` `typechange`",
                       "**Note:** If `(level)` is unspecified, it will set all currently active role rewards "
                       "to the type specified by `[type]`. `[type]` can be \"add\" *(\"a\")* or "
                       "\"replace\" *(\"r\")* to specify if the previous roles obtained "
                       "should be kept or if the new roles will replace the old roles")
        nv = [("Give", lgive), ("Remove", lremove), ("Reset", lreset), ("List", llist),
              ("Change Level", lchangelevel), ("Change Type", lchangetype)]
        embed = discord.Embed(title="Role Rewards Help", description=description, color=discord.Color.blue())
        pag = SubcommandPaginator(ctx, entries=[(name, value, False) for name, value in nv],
                                  per_page=2, show_entry_count=True, embed=embed)
        return await pag.paginate()

    @levels.check_entry_exists(entry="enabled", db_name="level_config")
    @handle(Exception, to_raise=customerrors.LevelRolesExists())
    async def give_levelroles(self, ctx, level: int, level_type: str, roles: list) -> discord.Message:
        async with self.bot.db.acquire() as con:
            if isinstance(roles, discord.Role):
                roles = [roles]
            values = [f"({role.id}, {ctx.guild.id}, {level}, '{level_type}')" for role in roles]
            await con.execute(f"INSERT INTO level_roles(role_id, guild_id, obtain_at, type) VALUES"
                              f"{', '.join(values)}")
        embed = discord.Embed(title="Successfully Set Role Rewards",
                              description=f"{ctx.author.mention}, when users on your server reach "
                              f"level {level}, they will receive the following roles:\n" +
                              "\n".join([role.mention for role in roles]) + "\n"
                              "They will be added to previous role rewards they have received"
                              if level_type == "add" else
                              "They will be added, but previous role rewards will be removed",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @levels.check_entry_exists(entry="enabled", db_name="level_config")
    @handle(Exception, to_raise=customerrors.LevelError())
    async def remove_levelroles(self, ctx, level: int, roles: list) -> discord.Message:
        del_roles = []
        async with self.bot.db.acquire() as con:
            if not roles:
                del_roles = await con.fetch(f"DELETE FROM level_roles WHERE "
                                            f"obtain_at={level} AND guild_id={ctx.guild.id} "
                                            "RETURNING role_id")
            else:
                if isinstance(roles, discord.Role):
                    roles = [roles]
                del_roles = await con.fetch(f"DELETE FROM level_roles WHERE "
                                            f"role_id IN ({', '.join([str(role.id) for role in roles])}) AND "
                                            f"obtain_at={level} RETURNING role_id")
        if not del_roles:
            description = f"{ctx.author.mention}, no role rewards were removed for level {level}"
            color = discord.Color.dark_red()
        else:
            description = (
                f"{ctx.author.mention}, the following role rewards have been "
                f"removed from level {level}:\n" + "\n".join(
                    [f'{ctx.guild.get_role(int(entry["role_id"])).mention}' for entry in del_roles]
                )
            )
            color = discord.Color.blue()
        embed = discord.Embed(title="Successfully Removed Role Reward",
                              description=description,
                              color=color)
        return await ctx.channel.send(embed=embed)

    @levels.check_entry_exists(entry="enabled", db_name="level_config")
    @handle(Exception, to_raise=customerrors.LevelError())
    async def reset_levelroles(self, ctx) -> discord.Message:
        async with self.bot.db.acquire() as con:
            await con.execute(f"DELETE FROM level_roles WHERE guild_id={ctx.guild.id}")
        embed = discord.Embed(title="Level Roles Reset",
                              description=f"{ctx.author.mention}, all role rewards were removed",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @levels.check_entry_exists(entry="enabled", db_name="level_config")
    @handle(Exception, to_raise=customerrors.LevelError())
    async def list_levelroles(self, ctx, level: int = None) -> discord.Message:
        async with self.bot.db.acquire() as con:
            obtain_type = await con.fetch(f"SELECT DISTINCT(obtain_at), type FROM level_roles "
                                          f"WHERE {f'obtain_at={level} AND ' if level else ''}"
                                          f"guild_id={ctx.guild.id} ORDER BY obtain_at ASC")
            complete_lr = [
                lrl(entry['obtain_at'], entry['type'],
                    await con.fetch(f"SELECT role_id FROM level_roles WHERE "
                                    f"guild_id={ctx.guild.id} AND obtain_at={int(entry['obtain_at'])}"))
                for entry in obtain_type
            ]
        embed = discord.Embed(title=f"Role Rewards{f' for Level {level}' if level else ''}",
                              description=f"Role Rewards for {ctx.guild.name}"
                              f"{f' given at level {level}'if level else ''}",
                              color=discord.Color.blue())
        entries = [
            (f"Level {entry.level}",
             (f"**Role Reward Behavior:** `{entry.type}`", "**Roles Given:**\n> " +
              "\n> ".join(
                  [ctx.guild.get_role(int(record['role_id'])).mention for record in entry.entries])),
             False)
            for entry in complete_lr
        ]
        if not entries:
            embed.description = "No role rewards configured"
            embed.color = discord.Color.dark_red()
            return await ctx.channel.send(embed=embed)
        pag = SubcommandPaginator(ctx, entries=entries, per_page=1, show_entry_count=False, embed=embed)
        return await pag.paginate()

    @levels.check_entry_exists(entry="enabled", db_name="level_config")
    @handle(Exception, to_raise=customerrors.LevelError())
    async def change_lr_level(self, ctx, role: discord.Role, level: int) -> discord.Message:
        async with self.bot.db.acquire() as con:
            level_type = await con.fetchval(f"SELECT DISTINCT(type) FROM level_roles "
                                            f"WHERE obtain_at={level}") or "add"
            await con.execute(f"UPDATE level_roles SET obtain_at={level}, type=$tag${level_type}$tag$ "
                              f"WHERE role_id={role.id}")
        embed = discord.Embed(title="Role Level Changed",
                              description=f"{ctx.author.mention}, server members will now get {role.mention} "
                              f"when they reach level {level}",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @levels.check_entry_exists(entry="enabled", db_name="level_config")
    @handle(Exception, to_raise=customerrors.LevelError())
    async def change_lr_type(self, ctx, level_type: str, level: int = None):
        async with self.bot.db.acquire() as con:
            if not level:
                await con.execute(f"UPDATE level_roles SET type=$tag${level_type}$tag$ "
                                  f"WHERE guild_id={ctx.guild.id}")
                description = (f"{ctx.author.mention}, all the role rewards in this server "
                               f"were updated to type `{level_type}`")
            else:
                await con.execute(f"UPDATE level_roles SET type=$tag${level_type}$tag$ "
                                  f"WHERE guild_id={ctx.guild.id} AND obtain_at={level}")
                description = (f"{ctx.author.mention}, all the level {level} role rewards "
                               f"in this server were updated to type `{level_type}`")
        embed = discord.Embed(title="Role Reward Type Changed",
                              description=description,
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @commands.group(invoke_without_command=True,
                    aliases=['lvl', 'levels'],
                    desc="Displays the user's server level",
                    usage="level (subcommand)",
                    note="Do `m!level help` to view the help menu for level subcommands. "
                    "Do `m!levelroles` to view the help menu for levelroles subcommands")
    async def level(self, ctx, member: discord.Member = None):
        export, embed = await levels.gen_guild_profile(self.bot, member if member else ctx.author)
        return await ctx.channel.send(file=export, embed=embed)

    @level.command(aliases=['h', 'help'])
    async def level_help(self, ctx):
        return await self.send_leveling_help(ctx)

    @level.command(aliases=['on', 'enable'])
    @commands.has_permissions(manage_guild=True)
    async def level_enable(self, ctx, channels: commands.Greedy[discord.TextChannel] = None):
        if not channels:
            channels = ctx.guild.text_channels
        return

    @level.command(aliases=['off', 'disable'])
    @commands.has_permissions(manage_guild=True)
    async def level_disable(self, ctx, channels: commands.Greedy[discord.TextChannel] = None):
        if not channels:
            channels = ctx.guild.text_channels
        return

    @level.command(aliases=['xpm', 'xppermin', 'xpperminute'])
    @commands.cooldown(1.0, 60.0, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def level_xpperminute(self, ctx, value: int = None):
        if not value:
            return await self.show_current_xp_rate(ctx)
        else:
            return await self.edit_current_xp_rate(ctx, value)

    @level.command(aliases=['freq', 'rate', 'frequency'])
    @commands.cooldown(1.0, 60.0, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def level_frequency(self, ctx, value: int = None):
        if not value:
            return await self.show_current_freq(ctx)
        else:
            return await self.edit_current_freq(ctx, value)

    @levels.check_entry_exists(entry="enabled", db_name="level_config")
    @level.command(aliases=['redirect', 'reroute'])
    @commands.has_permissions(manage_guild=True)
    async def level_reroute(self, ctx, channel: discord.TextChannel):
        async with self.bot.db.acquire() as con:
            await con.execute(f"UPDATE level_config SET route_channel_id={channel.id} WHERE guild_id={ctx.guild.id}")
        embed = discord.Embed(title="Level Up Reroute",
                              description=f"The level up messages will now appear in {channel.mention}",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @levels.check_entry_exists(entry="enabled", db_name="level_config")
    @level.command(aliases=['unredirect', 'unroute'])
    @commands.has_permissions(manage_guild=True)
    async def level_unroute(self, ctx):
        async with self.bot.db.acquire() as con:
            await con.execute(f"UPDATE level_config SET route_channel_id=NULL WHERE guild_id={ctx.guild.id}")
        embed = discord.Embed(title="Level Up Reroute",
                              description="The level up messages will now appear in "
                              "the channel the user leveled up in",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @level.command(aliases=['notif', 'notifs', 'notify'])
    @commands.has_permissions(manage_guild=True)
    async def level_notify(self, ctx, mode: str, status: str = "toggle"):
        if mode.lower() in ['s', 'server']:
            mode = 'server'
        elif mode.lower() in ['g', 'global']:
            mode = 'global'
        else:
            raise customerrors.LevelInvalidNotifyMode(mode)
        return await self.set_notify(ctx, mode, status.lower())

    @level.command(aliases=['info', 'about'])
    async def level_about(self, ctx):
        return await self.send_leveling_about(ctx)

    @commands.group(invoke_without_command=True,
                    aliases=['lr', 'lvlrole', 'levelrole'],
                    desc="Displays the help command for levelroles",
                    usage="levelroles (subcommand)",
                    note="You must have leveling set up first. Do `m!level` to see all available "
                    "commands for configuring MarwynnBot's leveling system on your server")
    async def levelroles(self, ctx):
        return await self.send_levelroles_help(ctx)

    @levelroles.command(aliases=['set', 'give'])
    @commands.has_permissions(manage_guild=True)
    async def levelroles_give(self, ctx, level: int, level_type: str, roles: commands.Greedy[discord.Role]):
        if not 1 <= level <= 100:
            raise customerrors.LevelInvalidRange(level)
        if not level_type.lower() in ['add', 'a', 'replace', 'r']:
            raise customerrors.LevelInvalidType(level_type)

        if level_type.lower() == "a":
            level_type = "add"
        elif level_type.lower() == "r":
            level_type = "replace"
        else:
            level_type = level_type.lower()
        return await self.give_levelroles(ctx, level, level_type, roles)

    @levelroles.command(aliases=['unset', 'remove'])
    @commands.has_permissions(manage_guild=True)
    async def levelroles_remove(self, ctx, level: int, roles: commands.Greedy[discord.Role] = None):
        if not 1 <= level <= 100:
            raise customerrors.LevelInvalidRange(level)
        return await confirm(ctx, self.bot,
                             user=ctx.author,
                             success_func=self.remove_levelroles(ctx, level, roles),
                             op="levelroles remove")

    @levelroles.command(aliases=['clear', 'reset'])
    @commands.has_permissions(manage_guild=True)
    async def levelroles_reset(self, ctx):
        return await confirm(ctx, self.bot,
                             user=ctx.author,
                             success_func=self.reset_levelroles(ctx),
                             op="levelroles reset")

    @levelroles.command(aliases=['show', '-ls', 'list'])
    async def levelroles_list(self, ctx, level: int = None):
        if level and not 1 <= level <= 100:
            raise customerrors.LevelInvalidRange(level)
        return await self.list_levelroles(ctx, level)

    @levelroles.command(aliases=['cl', 'levelchange', 'changelevel'])
    @commands.has_permissions(manage_guild=True)
    async def levelroles_changelevel(self, ctx, role: discord.Role, level: int):
        if not 1 <= level <= 100:
            raise customerrors.LevelInvalidRange(level)
        return await confirm(ctx, self.bot,
                             user=ctx.author,
                             success_func=self.change_lr_level(ctx, role, level),
                             op="levelroles change level")

    @levelroles.command(aliases=['ct', 'typechange', 'changetype'])
    @commands.has_permissions(manage_guild=True)
    async def levelroles_changetype(self, ctx, level_type: str, level: int = None):
        if level and not 1 <= level <= 100:
            raise customerrors.LevelInvalidRange(level)

        if not level_type.lower() in ['a', 'add', 'r', 'replace']:
            raise customerrors.LevelInvalidType(level_type)

        if level_type.lower() == "a":
            level_type = "add"
        elif level_type.lower() == "r":
            level_type = "replace"
        else:
            level_type = level_type.lower()
        return await confirm(ctx, self.bot,
                             user=ctx.author,
                             success_func=self.change_lr_type(ctx, level_type, level=level),
                             op="levelroles change type")


def setup(bot):
    bot.add_cog(Leveling(bot))
