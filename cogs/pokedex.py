import math

import discord
from discord.ext import commands
import pokepy

from globalcommands import GlobalCMDS as gcmds

poke_client = pokepy.V2Client(cache='in_disk', cache_location="./pokepy_cache")


class Pokedex(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog {self.qualified_name} has been loaded')

    def truncate(self, number: float, decimal_places: int) -> float:
        stepper = 10.0 ** decimal_places
        return math.trunc(stepper * number) / stepper

    async def check_pokemon(self, name) -> pokepy.api.rv2.PokemonResource:
        try:
            return poke_client.get_pokemon(name)
        except Exception:
            return None

    async def get_dex_entry(self, name):
        value = await self.check_pokemon(name)
        if not value:
            return None

        pokemon_name = f"Name: `{value.name.capitalize()}`"
        type_list = [types.type.name.capitalize() for types in value.types]
        if not type_list:
            type = "Type: `Unknown`"
        else:
            type = "Type: `" + "` `".join(type_list) + "`"
        nat_dex_num = f"National Dex Number: `{value.id}`"
        ability_list = [(ability.ability.name.capitalize().replace("-", " "), ability.is_hidden) for ability in
                        value.abilities]
        abilities = "Abilities: "
        for ability_name, is_hidden in ability_list:
            if is_hidden:
                abilities += f"*`{ability_name} (hidden)`* "
            else:
                abilities += f"`{ability_name}` "
        base_xp = f"Base XP: `{value.base_experience}`"
        if value.height / 10 >= 1:
            height = f"Height: `{self.truncate((value.height / 10), 2)} m`"
        else:
            height = f"Height: `{self.truncate((value.height * 10), 3)} m`"
        items_list = [item.item.name.capitalize().replace("-", " ") for item in value.held_items]
        if not items_list:
            items = "Wild Held Items: `None`"
        else:
            items = "Wild Held Items: `" + "` `".join(items_list) + "`"
        weight = f"Weight: `{value.weight / 10} kg`"
        return pokemon_name, nat_dex_num, type, abilities, items, weight, height, base_xp

    async def get_dex_sprite(self, name):
        value = await self.check_pokemon(name)
        return value.sprites.front_default, value.sprites.front_shiny

    @commands.group(aliases=['dex'])
    async def pokedex(self, ctx):
        await gcmds.invkDelete(gcmds, ctx)

        if ctx.invoked_subcommand is None:
            panel = discord.Embed(title="Pokedex Commands",
                                  description=f"Access MarwynnBot's Pokédex using `{gcmds.prefix(gcmds, ctx)}pokedex "
                                              f"[option]`. Please note that in order to avoid discrepancies in "
                                              f"versions, I have not included many of the game specific data.\n Here "
                                              f"is a list of all available `pokedex` options",
                                  color=discord.Color.blue())
            panel.add_field(name="Pokémon",
                            value=f"Usage: `{gcmds.prefix(gcmds, ctx)}pokedex pokemon [name]`\n"
                                  f"Returns: Details about the specified Pokémon",
                            inline=False)
            panel.add_field(name="Move",
                            value=f"Usage: `{gcmds.prefix(gcmds, ctx)}pokedex move [name]`\n"
                                  f"Returns: Details about the move",
                            inline=False)
            panel.add_field(name="Ability",
                            value=f"Usage: `{gcmds.prefix(gcmds, ctx)}pokedex ability [name]`\n"
                                  f"Returns: Details about the specified ability",
                            inline=False)
            panel.add_field(name="Item",
                            value=f"Usage: `{gcmds.prefix(gcmds, ctx)} pokedex item [name]`\n"
                                  f"Returns: Details about the item",
                            inline=False)
            panel.add_field(name="Type",
                            value=f"Usage: `{gcmds.prefix(gcmds, ctx)}pokedex type [name]`\n"
                                  f"Returns: Details about that type")
            return await ctx.channel.send(embed=panel)

    @pokedex.command(aliases=['-p'])
    async def pokemon(self, ctx, *, pokemon_name: str):
        value = await self.get_dex_entry(pokemon_name)
        if value:
            embed = discord.Embed(title=pokemon_name.capitalize(),
                                  description=f"{ctx.author.mention}, here is {pokemon_name.capitalize()}'s "
                                              f"Pokédex entry\n\n",
                                  color=discord.Color.blue())
            embed.description += "\n".join(value)
            sprites = await self.get_dex_sprite(pokemon_name)
            if sprites[0]:
                embed.set_image(url=sprites[0])
            if sprites[1]:
                embed.set_thumbnail(url=sprites[1])
            return await ctx.channel.send(embed=embed)
        else:
            invalid = discord.Embed(title="Invalid Pokémon Name",
                                    description=f"{ctx.author.mention}, `{pokemon_name.capitalize()}` is not a valid "
                                                f"Pokémon",
                                    color=discord.Color.dark_red())
            return await ctx.channel.send(embed=invalid, delete_after=5)


def setup(client):
    client.add_cog(Pokedex(client))
