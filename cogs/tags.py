import discord
import json
import os
import asyncio
from datetime import datetime
from discord.ext import commands
from utils import globalcommands, customerrors, paginator


gcmds = globalcommands.GlobalCMDS()
PROHIB_NAMES = ("list", "search", "create", "edit", "delete", "tag", "tags", "make", "remove")
timeout = 600


class Tags(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def tag_help(self, ctx) -> discord.Message:
        timestamp = f"Executed by {ctx.author.display_name} " + "at: {:%m/%d/%Y %H:%M:%S}".format(datetime.now())
        pfx = gcmds.prefix(ctx)
        tag = (f"**Usage:** `{pfx}tag`\n"
               "**Returns:** This help menu\n"
               "**Aliases:** `tags`")
        list = (f"**Usage:** `{pfx}tag list`\n"
                "**Returns:** A list of all the tags you own, if any")
        search = (f"**Usage:** `{pfx}tag search`\n"
                  "**Returns:** A list of the top 20 tags that contain the query substring in the order of most used\n"
                  "**Special Cases:** If no tag is found, it will return an error message")
        create = (f"**Usage:** `{pfx}tag create (name)`\n"
                  "**Returns:** An interactive tag creation panel\n"
                  "**Aliases:** `make`\n"
                  "**Special Cases:** If the tag `name` already exists and you own it, you can choose to edit or delete it")
        edit = (f"**Usage:** `{pfx}tag edit (name)`\n"
                "**Returns:** An interactive tag edit panel\n"
                "**Special Cases:** If the tag does not exist, you will have the option to create it. You can only "
                "edit tags you own")
        delete = (f"**Usage:** `{pfx}tag delete`\n"
                  "**Returns:** A tag delete confirmation panel\n"
                  "**Aliases:** `remove`\n"
                  "**Special Cases:** The tag must exist and you must own the tag in order to delete it")
        cmds = [("Help", tag), ("List", list), ("Search", search),
                ("Create", create), ("Edit", edit), ("Delete", delete)]

        embed = discord.Embed(title="Tag Commands",
                              description=f"{ctx.author.mention}, tags are an easy way to create your own custom "
                              "command! Here are all the tag commands MarwynnBot supports",
                              color=discord.Color.blue())
        embed.set_footer(text=timestamp, icon_url=ctx.author.avatar_url)
        for name, value in cmds:
            embed.add_field(name=name,
                            value=value,
                            inline=False)
        return await ctx.channel.send(embed=embed)

    async def check_tag(self, ctx, name) -> bool:
        if not os.path.exists('db/tags.json') or not name:
            return False

        with open('db/tags.json', 'r') as f:
            file = json.load(f)

        if not str(ctx.guild.id) in file or not name in file[str(ctx.guild.id)]:
            return False

        return True

    async def create_tag(self, ctx, name, content) -> discord.Message:
        gcmds.json_load('db/tags.json', {})
        with open('db/tags.json', 'r') as f:
            file = json.load(f)
        if not str(ctx.guild.id) in file:
            file.update({str(ctx.guild.id): {}})
        file[str(ctx.guild.id)].update({
            name: {
                'author_id': ctx.author.id,
                'content': content,
                'created_at': int(datetime.now().timestamp())
            }
        })
        with open('db/tags.json', 'w') as g:
            json.dump(file, g, indent=4)

        embed = discord.Embed(title="Tag Created",
                              description=f"{ctx.author.mention}, your tag `{name}` was created and can be accessed "
                              f"using `{gcmds.prefix(ctx)}tag {name}`",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    async def send_tag(self, ctx, name: str) -> discord.Message:
        timestamp = "{:%m/%d/%Y %H:%M:%S}".format(datetime.now())
        with open('db/tags.json', 'r') as f:
            file = json.load(f)
        content = file[str(ctx.guild.id)][name]['content']
        embed = discord.Embed(description=content,
                              color=discord.Color.blue())
        embed.set_author(name=name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name} at {timestamp}")
        await ctx.channel.send(embed=embed)

    async def list_user_tags(self, ctx) -> list:
        if not os.path.exists('db/tags.json'):
            return None

        with open('db/tags.json', 'r') as f:
            file = json.load(f)

        if not str(ctx.guild.id) in file:
            return None

        desc_list = [f"{tag}\nCreated at {datetime.fromtimestamp(int(file[str(ctx.guild.id)][tag]['created_at'])).strftime('%m/%d/%Y %H:%M:%S')}\n"
                     for tag in file[str(ctx.guild.id)] if file[str(ctx.guild.id)][tag]['author_id'] == ctx.author.id]
        if len(desc_list) != 0:
            return desc_list
        else:
            raise customerrors.UserNoTags(ctx.author)

    async def search_tags(self, ctx) -> list:
        if not os.path.exists('db/tags.json'):
            return None

        with open('db/tags.json', 'r') as f:
            file = json.load(f)

        if not str(ctx.guild.id) in file:
            return None

    @commands.group(invoke_without_command=True, aliases=['tags'])
    async def tag(self, ctx, *, tag: str = None):
        if not tag:
            return await self.tag_help(ctx)
        if not await self.check_tag(ctx, tag):
            raise customerrors.TagNotFound(tag)
        return await self.send_tag(ctx, tag)

    @tag.command()
    async def list(self, ctx):
        desc_list = await self.list_user_tags(ctx)
        pag = paginator.EmbedPaginator(ctx, entries=desc_list, per_page=10)
        pag.embed.title = "Your Tags"
        return await pag.paginate()

    @tag.command()
    async def search(self, ctx, *, keyword):
        return

    @tag.command(aliases=['make'])
    async def create(self, ctx, *, tag):
        if await self.check_tag(ctx, tag):
            raise customerrors.TagAlreadyExists(tag)
        embed = discord.Embed(title=f"Create Tag \"{tag}\"",
                              description=f"{ctx.author.mention}, within 2 minutes, please enter what you would like the tag to return\n\n"
                              f"ex. *If you enter \"test\", doing `{gcmds.prefix(ctx)}tag {tag}` will return \"test\"*",
                              color=discord.Color.blue())
        embed.set_footer(text="Enter \"cancel\" to cancel this setup")
        panel = await ctx.channel.send(embed=embed)

        def from_user(message: discord.Message) -> bool:
            return message.author.id == ctx.author.id and message.channel == ctx.channel

        try:
            result = await self.client.wait_for("message", check=from_user, timeout=timeout)
        except asyncio.TimeoutError:
            return await gcmds.timeout(ctx, "tag creation", timeout)
        if result.content == "cancel":
            return gcmds.cancelled(ctx, "tag creation")
        await gcmds.smart_delete(result)

        return await self.create_tag(ctx, tag, result.content)

    @tag.command()
    async def edit(self, ctx, *, tag):
        return

    @tag.command(aliaes=['remove'])
    async def delete(self, ctx, *, tag):
        return


def setup(client):
    client.add_cog(Tags(client))
