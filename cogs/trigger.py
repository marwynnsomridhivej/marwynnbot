import asyncio
from typing import List, NamedTuple, Union

import discord
from discord import guild
from discord.embeds import EmptyEmbed
from discord.ext import commands
from discord.ext.commands.bot import AutoShardedBot
from utils import (EntryData, FieldPaginator, GlobalCMDS, SubcommandHelp,
                   extract_attr)

CONF_REACTIONS = ["✅", "🛑"]
PROHIB_NAMES = [
    "marwynn",
    "somridhivej",
    "mb",
    "marwynnbot",
    "all",
]


class TriggerEntry(NamedTuple):
    author_id: int = None
    guild_id: int = None
    key: str = None
    response: str = None
    case_sensitive: bool = None
    active: bool = True


class Trigger(commands.Cog):
    def __init__(self, bot: AutoShardedBot) -> None:
        self.bot = bot
        self.gcmds = GlobalCMDS(self.bot)
        self.bot.loop.create_task(self.init_triggers())
        self.key_cache = {}

    async def init_triggers(self):
        await self.bot.wait_until_ready()
        async with self.bot.db.acquire() as con:
            await con.execute("CREATE TABLE IF NOT EXISTS triggers(author_id BIGINT, guild_id BIGINT, key TEXT, response TEXT, case_sensitive BOOLEAN DEFAULT FALSE, active BOOLEAN DEFAULT TRUE)")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> discord.Message:
        await self.bot.wait_until_ready()
        if not message.author.bot and message.guild:
            channel = message.channel
            perms = channel.permissions_for(message.guild.me)
            pfx = await self.gcmds.prefix(None, guild_id=message.guild.id)
            if not message.guild.id in self.key_cache:
                async with self.bot.db.acquire() as con:
                    key_response_data = await con.fetch(f"SELECT * FROM triggers WHERE guild_id={message.guild.id}")
                self.key_cache[message.guild.id] = [
                    TriggerEntry(
                        author_id=entry["author_id"],
                        guild_id=entry["guild_id"],
                        key=entry["key"],
                        response=entry["response"],
                        case_sensitive=entry["case_sensitive"],
                        active=entry["active"],
                    ) for entry in key_response_data
                ] if key_response_data else []
            if message.content.startswith(pfx) or message.content.lower().startswith("mb"):
                return
            if perms.send_messages and self.key_cache[message.guild.id]:
                reg = message.content
                lowered = message.content.lower()
                for entry in [_ for _ in self.key_cache[message.guild.id] if _.active]:
                    if (entry.case_sensitive and entry.key in reg) or (entry.key.lower() in lowered):
                        return await message.channel.send(content=entry.response)

    async def get_triggers(self, guild_id: int, key: str = None) -> Union[List[TriggerEntry], TriggerEntry, None]:
        async with self.bot.db.acquire() as con:
            entries = await con.fetch(f"SELECT * FROM triggers WHERE guild_id={guild_id}{f' AND key=$key${key}$key$' if key else ''} ORDER BY KEY ASC")
        if not entries:
            return None
        elif key is not None:
            entries = entries[0]
            return TriggerEntry(
                author_id=entries["author_id"],
                guild_id=entries["guild_id"],
                key=entries["key"],
                response=entries["response"],
                case_sensitive=entries["case_sensitive"],
                active=entries["active"],
            )
        return [
            TriggerEntry(
                author_id=entry["author_id"],
                guild_id=entry["guild_id"],
                key=entry["key"],
                response=entry["response"],
                case_sensitive=entry["case_sensitive"],
                active=entry["active"]
            ) for entry in entries
        ]

    async def create_trigger(self, author_id: int, guild_id: int, key: str, response: str, case: str) -> discord.Embed:
        embed = discord.Embed(title="Create Trigger ", color=discord.Color.blue())
        exists = await self.get_triggers(guild_id, key=key)
        if exists is not None:
            embed.title += "Failed"
            embed.description = f"<@{author_id}>, the trigger `{key}` already exists"
            embed.color = discord.Color.dark_red()
        else:
            async with self.bot.db.acquire() as con:
                await con.execute(
                    f"INSERT INTO triggers(author_id, guild_id, key, response, case_sensitive) VALUES ({author_id}, {guild_id}, $key${key}$key$, $resp${response}$resp$, {case})"
                )
            if not guild_id in self.key_cache:
                self.key_cache[guild_id] = []
            self.key_cache[guild_id].append(
                TriggerEntry(
                    key=key,
                    response=response,
                    case_sensitive=case.lower() == "true",
                    active=True,
                )
            )
            embed.title += "Successful"
            embed.description = f"<@{author_id}>, the trigger `{key}` was created!"
        return embed

    async def edit_trigger(self, guild_id: int, key: str, response: str, case: str) -> discord.Embed:
        async with self.bot.db.acquire() as con:
            await con.execute(f"UPDATE triggers SET response=$resp${response}$resp$, case_sensitive={case} WHERE guild_id={guild_id} AND key=$key${key}$key$")
        existing: TriggerEntry = extract_attr(self.key_cache[guild_id], mode="all", key=key)
        self.key_cache[guild_id].remove(existing)
        self.key_cache[guild_id].append(
            TriggerEntry(
                author_id=existing.author_id,
                guild_id=existing.guild_id,
                key=existing.key,
                response=response,
                case_sensitive=case.lower() == "true",
                active=existing.active,
            )
        )
        return discord.Embed(
            title="Successfully Edited Trigger",
            description=f", the trigger `{key}` has been edited",
            color=discord.Color.blue()
        )

    async def delete_trigger(self, guild_id: int, key: str) -> discord.Embed:
        async with self.bot.db.acquire() as con:
            await con.execute(f"DELETE FROM triggers WHERE guild_id={guild_id} AND key=$key${key}$key$")
        existing: TriggerEntry = extract_attr(self.key_cache[guild_id], mode="all", key=key)
        self.key_cache[guild_id].remove(existing)
        return discord.Embed(
            title="Trigger Deleted",
            description=f", the trigger `{key}` has successfully been deleted",
            color=discord.Color.blue()
        )

    async def toggle_active_state(self, guild_id, key: str, active: bool) -> discord.Embed:
        op = "active" if active else "inactive"
        async with self.bot.db.acquire() as con:
            entries = await con.execute(f"UPDATE triggers SET active={'TRUE' if active else 'FALSE'} WHERE guild_id={guild_id}{f' AND key=$key${key}$key$' if key else ''} RETURNING *")
        if key is None:
            self.key_cache[guild_id] = [
                TriggerEntry(
                    author_id=entry["author_id"],
                    guild_id=entry["guild_id"],
                    key=entry["key"],
                    response=entry["response"],
                    case_sensitive=entry["case_sensitive"],
                    active=entry["active"],
                ) for entry in entries
            ] if entries else []
        else:
            existing: TriggerEntry = extract_attr(self.key_cache[guild_id], mode="all", key=key)
            self.key_cache[guild_id].remove(existing)
            self.key_cache[guild_id].append(
                TriggerEntry(
                    author_id=existing.author_id,
                    guild_id=existing.guild_id,
                    key=existing.key,
                    response=existing.response,
                    active=active,
                )
            )
        return discord.Embed(
            title=f"Triger {op.title()}",
            description=f", the trigger `{key}` is now {op}",
            color=discord.Color.blue()
        )

    async def purge_triggers(self, guild_id: int) -> discord.Embed:
        async with self.bot.db.acquire() as con:
            deleted_amount = await con.fetchval(f"WITH deleted as (DELETE FROM triggers WHERE guild_id={guild_id} RETURNING *) SELECT COUNT(*) FROM deleted")
        return discord.Embed(
            title="Purged All Triggers",
            description=f"**{deleted_amount}** trigger{'s were' if deleted_amount != 1 else 'was'} purged",
            color=discord.Color.blue()
        )

    @commands.group(invoke_without_command=True,
                    aliases=["trg", "trigger"],
                    desc="Shows the help for the trigger cog",
                    usage="trigger",)
    async def triggers(self, ctx):
        pfx = f"{await self.gcmds.prefix(ctx)}triggers"
        return await SubcommandHelp(
            pfx,
            title="Triggers Help",
            description=(
                "MarwynnBot features a simple, highly customisable automatic reply trigger system which allows MarwynnBot to "
                "respond to certain words and phrases with a set response. Triggers are only active on the **server** they were created on. "
                "This means that a trigger created in server A will not be a valid trigger in server B IF server B does not already have a "
                "trigger set for that particular word or phrase. Triggers will not activate in the context of a command invocation. "
                "Server administrators are able to fully control trigger operations, regardless if they are the creator of any trigger in their server. "
                f"The base command is `{pfx}`. Here are all valid subcommands"
            ),
            show_entry_count=True,
        ).add_entry(
            name="Help",
            data=EntryData(
                usage="help",
                returns="This embed",
                aliases=["h"],
                note="The help panel will be returned on invalid subcommands or no subcommand specified as well",
            )
        ).add_entry(
            name="List",
            data=EntryData(
                usage="list (trigger)",
                returns="An embed listing the amount of triggers set in the current server",
                aliases=["ls"],
                note="If `(trigger)` is specified, it will return detailed information for that trigger if it exists in the current server"
            )
        ).add_entry(
            name="Create",
            data=EntryData(
                usage="create [word | phrase]",
                returns="An interactive panel that will guide you through creating a trigger",
                aliases=["c", "make"],
                note=("All created triggers are active on a server scope, meaning that a trigger created in channel A will be active in all other channels as well. "
                      "The only `[word | phrase]` you may not create a trigger from is any case variant of the word \"all\""),
            )
        ).add_entry(
            name="Edit",
            data=EntryData(
                usage="edit [trigger]",
                returns="An interactive panel that will guide you through editing a trigger",
                aliases=["e", "modify"],
                note="You may only edit triggers you have created",
            )
        ).add_entry(
            name="Delete",
            data=EntryData(
                usage="delete [trigger]",
                returns="A confirmation panel that once confirmed, will delete the specified trigger",
                aliases=["del", "remove"],
                note="You may only delete triggers you have created",
            )
        ).add_entry(
            name="Activate",
            data=EntryData(
                usage="activate [trigger]",
                returns="A confirmation message that details trigger activation status",
                aliases=["ac", "enable"],
                note="`[trigger]` may be \"all\" to activate all triggers. Created triggers are active by default",
            )
        ).add_entry(
            name="Deactivate",
            data=EntryData(
                usage="deacticate [trigger]",
                returns="A confirmation message that details trigger activation status",
                aliases=["deac", "disable"],
                note="`[trigger]` may be \"all\" to deactivate all triggers. Created triggers are active by default",
            )
        ).add_entry(
            name="Purge",
            data=EntryData(
                usage="purge (@mention)",
                returns="A confirmation panel that once confirmed, will delete the specified trigger for the mentioned user, if specified, or all triggers created in the current server",
                aliases=["p"],
            )
        ).show_help(ctx)

    @triggers.command(name="list",
                      aliases=["ls"],)
    async def trigger_list(self, ctx, *, key: str = None):
        embed = discord.Embed(
            title="Triggers",
            description=f"{ctx.author.mention}, ",
            color=discord.Color.blue()
        ).set_thumbnail(
            url=ctx.guild.icon_url or ctx.guild.me.avatar_url
        )
        entries = await self.get_triggers(ctx.guild.id, key=key)
        if not entries:
            embed.title = "No Triggers Found"
            embed.description += "no triggers have been created for this server" if key is None else f"I could not find a trigger with the key `{key}`"
            embed.color = discord.Color.dark_red()
        elif isinstance(entries, TriggerEntry):
            embed.title = f"Trigger: {entries.key}"
            embed.description = EmptyEmbed
            author: discord.User = self.bot.get_user(entries.author_id)
            embed.set_author(
                name=f"Trigger by: {author.display_name}",
                icon_url=author.avatar_url,
            ).add_field(
                name="Case Sensitive",
                value="True" if entries.case_sensitive else "False",
                inline=True,
            ).add_field(
                name="Active",
                value="Yes" if entries.active else "No",
                inline=True,
            ).add_field(
                name="Response",
                value=f"```{entries.response}```",
                inline=False,
            ).set_footer(
                text="Triggers are specific to the current server, and may not be accessed outside of this server"
            )
        else:
            amount = len(entries)
            active_triggers = len([entry for entry in entries if entry.active])
            description = "\n".join([
                f"**Registered Triggers:** {amount}",
                f"**Active Triggers:** {active_triggers}",
                f"**Deactivated Triggers:** {amount - active_triggers}",
            ])
            embed.description = EmptyEmbed
            pag_entries = [(
                entry.key,
                "\n".join([
                    f"Author: <@{entry.author_id}>",
                    f"Trigger: `{entry.key}`",
                    f"Response: `{entry.response}`",
                    f"Case Sensitive: `{'True' if entry.case_sensitive else 'False'}`",
                    f"Active: `{'Yes' if entry.active else 'No'}`",
                ]),
                True,
            ) for entry in entries]
            return await FieldPaginator(
                ctx,
                entries=pag_entries,
                per_page=10,
                show_entry_count=True,
                embed=embed,
                description=description,
            ).paginate()
        return await ctx.channel.send(embed=embed)

    @triggers.command(name="create",
                      aliases=["c", "make"],)
    async def trigger_create(self, ctx, *, key):
        if key.lower() in PROHIB_NAMES:
            return await ctx.channel.send(
                embed=discord.Embed(
                    title="Trigger Restricted",
                    description=f"{ctx.author.mention}, you can't create a trigger with that name",
                    color=discord.Color.dark_red(),
                )
            )
        embed = discord.Embed(
            title="Create Trigger",
            description=f"{ctx.author.mention}, what would you like the bot to respond with if it finds the trigger `{key}` in a message?",
            color=discord.Color.blue()
        ).set_footer(
            text='Enter "cancel" to cancel at any time'
        )
        await ctx.channel.send(embed=embed)
        try:
            message = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=300)
        except asyncio.TimeoutError:
            return await self.gcmds.timeout(ctx, "Create Trigger", 300)
        else:
            if message.content == "cancel":
                return await self.gcmds.cancelled(ctx, "Create Trigger")
            response = message.content

        embed: discord.Embed = embed.copy()
        embed.description = f"{ctx.author.mention}, should this  be case sensitive?"
        panel_msg = await ctx.channel.send(embed=embed)
        for reaction in CONF_REACTIONS:
            await panel_msg.add_reaction(reaction)
        try:
            reaction, _ = await self.bot.wait_for("reaction_add", check=lambda r, u: u.id == ctx.author.id and r.message == panel_msg and r.emoji in CONF_REACTIONS, timeout=60)
        except asyncio.TimeotuError:
            return await self.gcmds.timeout(ctx, "Create Trigger", 60)
        case_sensitive = "TRUE" if reaction.emoji == CONF_REACTIONS[0] else "FALSE"

        return await ctx.channel.send(
            embed=await self.create_trigger(
                ctx.author.id,
                ctx.guild.id,
                key,
                response,
                case_sensitive,
            )
        )

    @triggers.command(name="edit",
                      aliases=["e", "modify"],)
    async def trigger_edit(self, ctx, *, key: str):
        embed = discord.Embed(color=discord.Color.dark_red())
        exists = await self.get_triggers(ctx.guild.id, key=key)
        if exists is None:
            embed.title = "No Trigger Exists"
            embed.description = f"{ctx.author.mention}, no trigger `{key}` exists"
        elif not exists.author_id == ctx.author.id:
            embed.title = "Cannot Edit Trigger"
            embed.description = f"{ctx.author.mention}, you do not own this trigger"
        else:
            embed = discord.Embed(
                title="Edit Trigger",
                description=f"{ctx.author.mention}, please enter what you would like the response to be for the trigger `{key}`",
                color=discord.Color.blue()
            ).set_footer(
                text="Enter \"cancel\" to cancel at any time"
            )
            await ctx.channel.send(embed=embed)
            try:
                message = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=300)
            except asyncio.TimeoutError:
                return await self.gcmds.timeout(ctx, "Edit Trigger")
            if message.content == "cancel":
                return await self.gcmds.cancelled(ctx, "Edit Trigger")
            response = message.content

            embed: discord.Embed = embed.copy()
            embed.description = f"{ctx.author.mention}, should this trigger be case sensitive?"
            panel_msg = await ctx.channel.send(embed=embed)
            for reaction in CONF_REACTIONS:
                await panel_msg.add_reaction(reaction)
            try:
                reaction, _ = await self.bot.wait_for("reaction_add", check=lambda r, u: u.id == ctx.author.id and r.message == panel_msg and r.emoji in CONF_REACTIONS, timeout=60)
            except asyncio.TimeotuError:
                return await self.gcmds.timeout(ctx, "Create Trigger", 60)
            case_sensitive = "TRUE" if reaction.emoji == CONF_REACTIONS[0] else "FALSE"

            embed = await self.edit_trigger(ctx.guild.id, key, response, case_sensitive)
            embed.description = ctx.author.mention + embed.description
        return await ctx.channel.send(embed=embed)

    @triggers.command(name="delete",
                      aliases=["del", "remove"],)
    async def trigger_delete(self, ctx, *, key: str):
        embed = discord.Embed(title="Delete Trigger", color=discord.Color.dark_red())
        perms: discord.Permissions = ctx.channel.permissions_for(ctx.author)
        exists = await self.get_triggers(ctx.guild.id, key=key)
        if exists is None:
            embed.title += "Failed"
            embed.description = f"{ctx.author.mention}, there is no trigger `{key}`"
        elif not perms.manage_guild and not exists.author_id == ctx.author.id:
            embed.title += "Failed"
            embed.description = f"{ctx.author.mention}, only the owner of this trigger may delete it"
        else:
            embed = discord.Embed(
                title="Confirm Delete Trigger",
                description=f"{ctx.author.mention}, this action is destructive and irreversible. React with {CONF_REACTIONS[0]} to proceed or {CONF_REACTIONS[1]} to cancel",
                color=discord.Color.blue()
            )
            panel_msg = await ctx.channel.send(embed=embed)
            for reaction in CONF_REACTIONS:
                await panel_msg.add_reaction(reaction)
            try:
                reaction, _ = await self.bot.wait_for("reaction_add", check=lambda r, u: u.id == ctx.author.id and r.message == panel_msg and r.emoji in CONF_REACTIONS, timeout=60)
            except asyncio.TimeoutError:
                return await self.gcmds.timeout(ctx, "Delete Trigger", 60)
            if reaction.emoji == CONF_REACTIONS[1]:
                return await self.gcmds.cancelled(ctx, "Delete Trigger")

            embed = await self.delete_trigger(ctx.guild.id, key)
            embed.description = ctx.author.mention + embed.description
        return await ctx.channel.send(embed=embed)

    @triggers.command(name="activate",
                      aliases=["ac", "enable"],)
    async def trigger_activate(self, ctx, *, key: str):
        embed = discord.Embed(
            title="Trigger Activated",
            description=f"{ctx.author.mention}, the trigger `{key}` is now active",
            color=discord.Color.dark_red(),
        )
        perms: discord.Permissions = ctx.channel.permissions_for(ctx.author)
        exists = await self.get_triggers(ctx.guild.id, key=key)
        if exists is None:
            embed.title = "No Trigger Exists"
            embed.description = f"{ctx.author.mention}, I couldn't find the trigger `{key}`"
        elif not perms.manage_guild and exists.author_id != ctx.author.id:
            embed.title = "Invalid Permissions"
            embed.description = f"{ctx.author.mention}, you must own this trigger to activate it"
        else:
            embed = await self.toggle_active_state(ctx.guild.id, key if key != "all" else None, True)
            embed.description = ctx.author.mention + embed.description
        return await ctx.channel.send(embed=embed)

    @triggers.command(name="deactivate",
                      aliases=["deac", "disable"])
    async def trigger_deactivate(self, ctx, *, key: str):
        embed = discord.Embed(
            title="Trigger Deactivated",
            description=f"{ctx.author.mention}, the trigger `{key}` is now not active",
            color=discord.Color.dark_red(),
        )
        perms: discord.Permissions = ctx.channel.permissions_for(ctx.author)
        exists = await self.get_triggers(ctx.guild.id, key=key)
        if exists is None:
            embed.title = "No Trigger Exists"
            embed.description = f"{ctx.author.mention}, I couldn't find the trigger `{key}`"
        elif not perms.manage_guild and exists.author_id != ctx.author.id:
            embed.title = "Invalid Permissions"
            embed.description = f"{ctx.author.mention}, you must own this trigger to deactivate it"
        else:
            embed = await self.toggle_active_state(ctx.guild.id, key if key != "all" else None, False)
            embed.description = ctx.author.mention + embed.description
        return await ctx.channel.send(embed=embed)

    @triggers.command(name="purge",
                      aliases=["p"],)
    @commands.has_permissions(manage_guild=True)
    async def trigger_purge(self, ctx):
        embed = discord.Embed(
            title="Purge Triggers",
            description=f"{ctx.author.mention}, this action is destructive and irreversible. To proceed, react with {CONF_REACTIONS[0]} or with {CONF_REACTIONS[1]} to cancel",
            color=discord.Color.blue()
        )
        panel_msg = await ctx.channel.send(embed=embed)
        for reaction in CONF_REACTIONS:
            await panel_msg.add_reaction(reaction)
        try:
            reaction, _ = await self.bot.wait_for("reaction_add", check=lambda r, u: u.id == ctx.author.id and r.message == panel_msg and r.emoji in CONF_REACTIONS, timeout=60)
        except asyncio.TimeoutError:
            return await self.gcmds.timeout(ctx, "Purge Triggers", 60)
        if reaction.emoji == CONF_REACTIONS[0]:
            return await ctx.channel.send(embed=await self.purge_triggers(ctx.guild.id))
        return await self.gcmds.cancelled(ctx, "Purge Triggers")


def setup(bot):
    bot.add_cog(Trigger(bot))
