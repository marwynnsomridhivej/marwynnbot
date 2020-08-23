import discord
from discord.ext import commands
from globalcommands import GlobalCMDS as gcmds
from mcstatus import MinecraftServer


class Minecraft(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" has been loaded')

    @commands.group(aliases=['mc'])
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def minecraft(self, ctx):
        await gcmds.invkDelete(gcmds, ctx)
        if not ctx.invoked_subcommand:
            embed = discord.Embed(title="Minecraft Commands Help",
                                  description=f"Access MarwynnBot's Minecraft commands using "
                                              f"`{gcmds.prefix(gcmds, ctx)}minecraft [option]`. Here is a list of all "
                                              f"the available options",
                                  color=discord.Color.blue())
            embed.add_field(name="Ping",
                            value=f"Usage: `{gcmds.prefix(gcmds, ctx)}minecraft ping [serverIP]`\n"
                                  f"Returns: The ping of the specified minecraft server\n"
                                  f"Aliases: `-p`",
                            inline=False)
            embed.add_field(name="Details",
                            value=f"Usage: `{gcmds.prefix(gcmds, ctx)}minecraft details [serverIP]`\n"
                                  f"Returns: Details about the specified minecraft server\n"
                                  f"Aliases: `-d` `-q` `query`",
                            inline=False)
            embed.add_field(name="Special Cases",
                            value=f"Special Cases: The `[serverIP]` argument can be a domain name, IP address, "
                                  f"or IP address:port",
                            inline=False)
            await ctx.channel.send(embed=embed)

    @minecraft.command(aliases=['-p'])
    async def ping(self, ctx, host: str = None):
        if not host:
            return await ctx.invoke(self.minecraft)




def setup(client):
    client.add_cog(Minecraft(client))
