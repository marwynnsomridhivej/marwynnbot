import re

import discord
from discord.ext import commands
from utils import GlobalCMDS

gcmds = GlobalCMDS()
token_rx = re.compile(r'[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}')


class Token(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot) -> None:
        global gcmds
        self.bot = bot
        gcmds = GlobalCMDS(self.bot)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.bot.wait_until_ready()
        tokens = token_rx.findall(message.content)
        if tokens and message.guild:
            if await self._allow_checks(message.guild):
                await gcmds.smart_delete(message)
                if gcmds.env_check('GITHUB_TOKEN'):
                    url = await gcmds.create_gist('\n'.join(tokens), description="Discord token detected, posted for "
                                                  f"invalidation. Server: {message.guild.name}")
                    embed = discord.Embed(title="Token Found",
                                          description=f"{message.author.mention}, a Discord token was found in your message. It has"
                                          f" been sent to [Github]({url}) to be invalidated",
                                          color=discord.Color.dark_red())
                    await message.channel.send(embed=embed)
        return

    async def _allow_checks(self, guild: discord.Guild) -> bool:
        async with self.bot.db.acquire() as con:
            allowed = await con.fetchval(f"SELECT token FROM guild WHERE guild_id={guild.id}")
        return allowed or False

    @commands.command(aliases=['token'],
                      desc="Toggles token checking in messages",
                      usage="tokentoggle",
                      uperms=["Manage Server"],
                      note="This is disabled on all servers by default, requires an initial toggle to enable")
    @commands.has_permissions(manage_guild=True)
    async def tokentoggle(self, ctx):
        async with self.bot.db.acquire() as con:
            enabled = await con.fetchval(f"UPDATE guild SET token=NOT token WHERE guild_id={ctx.guild.id} RETURNING token")
        embed = discord.Embed(title="Token Check Toggled",
                              description=f"Token checking was {'enabled' if enabled else 'disabled'}",
                              color=discord.Color.blue())
        return await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Token(bot))
