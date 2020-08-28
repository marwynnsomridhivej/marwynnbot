import discord
from discord.ext import commands
from globalcommands import GlobalCMDS as gcmds
import asyncio
from num2words import num2words
import re
import json
import os

timeout = 30
channel_tag_rx = re.compile(r'<#[0-9]{18}>')
channel_id_rx = re.compile(r'[0-9]{18}')


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
            if str(member.guild.id) in file:
                guild = member.guild
                channel_to_send = await self.client.fetch_channel(file[str(guild.id)]["channel_id"])
                embed_title = file[str(guild.id)]['title']
                edv = str(file[str(guild.id)]['description'])
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
                return await channel_to_send.send(embed=welcome_embed)

    async def get_welcome_help(self, ctx) -> discord.Message:
        title = "Welcomer Help Menu"
        description = f"{ctx.author.mention}, the welcomer is used to greet new members of your server when they join. " \
        f"The base command is `{gcmds.prefix(gcmds, ctx)}welcome [option]`. Here are the valid options for `[option]`\n\n"
        create = f"**Usage:** `{gcmds.prefix(gcmds, ctx)}welcome create`\n" \
        "**Returns:** An interactive setup panel that will create a working welcomer in your server\n" \
        "**Aliases:** `make` `start` `-c`\n" \
        "**Special Cases:** You will be unable to use this command if you already have a welcomer set up. If you try to " \
        "Use this command when you already have a welcomer set up, it will automatically redirect you to the interactive" \
        " edit panel"

        embed = discord.Embed(title=title,
                              description=description,
                              color=discord.Color.blue())
        embed.add_field(name="Create",
                        value=create,
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

    async def create_welcomer(self, ctx, channel_id: int, title: str = None, description: str = None) -> bool:
        init = {
            str(ctx.guild.id): {
                "channel_id": channel_id,
                "title": title,
                "description": description
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
                    "description": description
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
    
    async def has_reminder(self, ctx) -> bool:
        if not os.path.exists('welcomers.json'):
            return False
        
        with open('welcomers.json', 'r') as f:
            file = json.load(f)
            f.close()
        
        if file[str(ctx.guild.id)]:
            return True
        
        return False

    @commands.group()
    async def welcome(self, ctx):
        await gcmds.invkDelete(gcmds, ctx)

        if not ctx.invoked_subcommand:
            return await self.get_welcome_help(ctx)

    @welcome.command(aliases=['make', 'start', '-c'])
    @commands.has_permissions(manage_guild=True)
    async def create(self, ctx):
        if await self.has_reminder(ctx):
            await ctx.invoke(self.edit)
            return
        
        def from_user(message: discord.Message) -> bool:
            if message.author.id == ctx.author.id:
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
        cmd_title = "welcome setup"
        await asyncio.sleep(5.0)

        description = f"{ctx.author.mention}, please tag or enter the ID of the channel that you would like " \
        "the welcomer to send messages in"

        # User provides the channel that the welcome embed will be sent in
        while True:
            try:
                edit_success = await self.edit_panel(ctx, panel, title=None, description=description)
                if not edit_success:
                    return await gcmds.panel_deleted(gcmds, ctx, cmd_title)
                result = await commands.AutoShardedBot.wait_for(self.client, "message", check=from_user, timeout=timeout)
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
            result = await commands.AutoShardedBot.wait_for(self.client, "message", check=from_user, timeout=timeout)
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
            result = await commands.AutoShardedBot.wait_for(self.client, "message", check=from_user, timeout=timeout)
        except asyncio.TimeoutError:
            return await gcmds.timeout(gcmds, ctx, cmd_title, timeout)
        if result.content == "cancel":
            return await gcmds.cancelled(gcmds, ctx, cmd_title)
        elif result.content == "skip":
            embed_description = None
        else:
            embed_description = result.content
        await result.delete()

        succeeded = await self.create_welcomer(ctx, channel_id, embed_title, embed_description)
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
        return
    
    @welcome.command(aliases=['-rm', 'trash', 'cancel'])
    async def delete(self, ctx):
        return


def setup(client):
    client.add_cog(Welcome(client))
