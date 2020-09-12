import discord
import json
import os
import asyncio
from datetime import datetime
from discord.ext import commands
from utils import globalcommands, customerrors, paginator, fuzzysearch


gcmds = globalcommands.GlobalCMDS()
PROHIB_NAMES = ("list", "search", "create", "edit", "delete", "tag", "tags", "make", "remove")
timeout = 600


class Tags(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

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
            raise customerrors.TagNotFound(name)

        with open('db/tags.json', 'r') as f:
            file = json.load(f)

        if not str(ctx.guild.id) in file or not name in file[str(ctx.guild.id)]:
            raise customerrors.TagNotFound(name)

        return True

    async def check_tag_owner(self, ctx, tag) -> bool:
        await self.check_tag(ctx, tag)
        with open('db/tags.json', 'r') as f:
            file = json.load(f)

        if not ctx.author.id == file[str(ctx.guild.id)][tag]['author_id']:
            raise customerrors.NotTagOwner(tag)

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
            raise customerrors.UserNoTags(ctx.author)

        with open('db/tags.json', 'r') as f:
            file = json.load(f)

        if not str(ctx.guild.id) in file:
            raise customerrors.UserNoTags(ctx.author)

        desc_list = [f"{tag}\nCreated at {datetime.fromtimestamp(int(file[str(ctx.guild.id)][tag]['created_at'])).strftime('%m/%d/%Y %H:%M:%S')}\n"
                     for tag in file[str(ctx.guild.id)] if file[str(ctx.guild.id)][tag]['author_id'] == ctx.author.id]
        if len(desc_list) != 0:
            return desc_list
        else:
            raise customerrors.UserNoTags(ctx.author)

    async def search_tags(self, ctx, keyword) -> list:
        if not os.path.exists('db/tags.json'):
            raise customerrors.NoSimilarTags(keyword)

        with open('db/tags.json', 'r') as f:
            file = json.load(f)

        if not str(ctx.guild.id) in file:
            raise customerrors.NoSimilarTags(keyword)

        pool = [item for item in file[str(ctx.guild.id)]]
        return await fuzzysearch.TagFuzzy(query=keyword, pool=pool, threshold=60).over_threshold()

    async def check_tag_name_taken(self, ctx, tag) -> bool:
        with open('db/tags.json', 'r') as f:
            file = json.load(f)
        return True if tag in file[str(ctx.guild.id)] else False

    @commands.group(invoke_without_command=True, aliases=['tags'])
    async def tag(self, ctx, *, tag: str = None):
        if not tag:
            return await self.tag_help(ctx)
        if await self.check_tag(ctx, tag):
            return await self.send_tag(ctx, tag)

    @tag.command()
    async def list(self, ctx):
        desc_list = await self.list_user_tags(ctx)
        pag = paginator.EmbedPaginator(ctx, entries=desc_list, per_page=10)
        pag.embed.title = "Your Tags"
        return await pag.paginate()

    @tag.command()
    async def search(self, ctx, *, keyword):
        result = await self.search_tags(ctx, keyword)
        if not result:
            raise customerrors.NoSimilarTags(keyword)

        embed = discord.Embed(title="Search Results",
                              description="```\n" + '\n```\n```\n'.join(result) + "\n```",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)

    @tag.command(aliases=['make'])
    async def create(self, ctx, *, tag):
        await self.check_tag(ctx, tag)
        embed = discord.Embed(title=f"Create Tag \"{tag}\"",
                              description=f"{ctx.author.mention}, within 2 minutes, please enter what you would like the tag to return\n\n"
                              f"ex. *If you enter \"test\", doing `{gcmds.prefix(ctx)}tag {tag}` will return \"test\"*",
                              color=discord.Color.blue())
        embed.set_footer(text="Enter \"cancel\" to cancel this setup")
        panel = await ctx.channel.send(embed=embed)

        def from_user(message: discord.Message) -> bool:
            return message.author.id == ctx.author.id and message.channel == ctx.channel

        try:
            result = await self.bot.wait_for("message", check=from_user, timeout=timeout)
        except asyncio.TimeoutError:
            return await gcmds.timeout(ctx, "tag creation", timeout)
        if result.content == "cancel":
            return gcmds.cancelled(ctx, "tag creation")
        await gcmds.smart_delete(result)

        return await self.create_tag(ctx, tag, result.content)

    @tag.command()
    async def edit(self, ctx, *, tag):
        await self.check_tag_owner(ctx, tag)

        async def from_user(message: discord.Message):
            return message.author.id == ctx.author.id and not await self.check_tag_name_taken(ctx, message.content)

        # User can edit tag name

    @tag.command(aliaes=['remove'])
    async def delete(self, ctx, *, tag):
        await self.check_tag_owner(ctx, tag)



def setup(bot):
    bot.add_cog(Tags(bot))
