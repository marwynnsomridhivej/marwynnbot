import discord
from discord.ext import commands
from globalcommands import GlobalCMDS as gcmds
import json

disboard_bot_id = 302050872383242240


class Disboard(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" has been loaded')

    async def get_disboard_help(self, ctx) -> discord.Message:
        title = "Disboard Commands"
        description = (f"{ctx.author.mention}, this is MarwynnBot's Disboard integration. MarwynnBot's many functions "
                       f"are listed here below. The base command is {gcmds.prefix(gcmds, ctx)}disboard [option]. "
                       "Here are all the valid options for the `[option]` argument")
        create = (f"**Usage:** `{gcmds.prefix(gcmds, ctx)}disboard set`\n"
                  "**Returns:** An interactive setup panel that will make your disboard bump reminder\n"
                  "**Aliases:** `-c` `make` `start`\n"
                  "**Special Cases:** You must have the `Disboard` bot in this server, otherwise, the command will fail")
        edit = (f"**Usage:** `{gcmds.prefix(gcmds, ctx)}disboard edit`\n"
                "**Returns:** An interactive setup panel that will edit your current disboard bump reminder\n"
                "**Aliases:** `-e` `adjust`\n"
                "**Special Cases:** You must satisfy the special case for `create` and currently have a working bump "
                "reminder set")
        delete = (f"**Usage:** `{gcmds.prefix(gcmds, ctx)}disboard delete`\n"
                  "**Returns:** A confirmation panel that will delete your current disboard bump reminder\n"
                  "**Aliases:** `-rm` `trash` `cancel`\n"
                  "**Special Cases:** You must satisfy the special case for `edit`")
        invite = (f"**Usage:** `{gcmds.prefix(gcmds, ctx)}disboard invite`\n"
                  "**Returns:** An interactive panel that details how to get the `Disboard` bot into your own server")
        kick = (f"**Usage:** `{gcmds.prefix(gcmds, ctx)}disboard kick`\n"
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

    async def set_bump_reminder(self, ctx, channel_id: int, message_content: str = None) -> bool:
        if not self.disboard_joined(ctx):
            return False
        
        if not ctx.guild.get_channel(channel_id):
            return False

        init = {
            str(ctx.guild.id): {
                "channel_id": channel_id,
                "message_content": message_content
                }
            }

        gcmds.json_load(gcmds, 'disboard.json', init)
        with open('disboard.json', 'r') as f:
            file = json.load(f)
            f.close()
        
        file[str(ctx.guild.id)] = {
            "channel_id": channel_id,
            "message_content": message_content
        }

        with open('disboard.json', 'w') as g:
            json.dump(file, g, indent=4)
        
        return True

    @commands.group()
    @commands.has_permissions(manage_guild=True)
    async def disboard(self, ctx):
        await gcmds.invkDelete(gcmds, ctx)
        if not ctx.invoked_subcommand:
            return await self.get_disboard_help(ctx)

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
