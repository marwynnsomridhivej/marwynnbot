import math

import discord
from discord.ext import commands
import pokepy

from globalcommands import GlobalCMDS as gcmds

poke_client = pokepy.V2Client(cache='in_disk', cache_location="./pokepy_cache")
move_status_icon_urls = ["https://oyster.ignimgs.com/mediawiki/apis.ign.com/pokemon-switch/e/ef/Physical.png?width=325",
                         "https://oyster.ignimgs.com/mediawiki/apis.ign.com/pokemon-switch/2/24/Special.png?width=325",
                         "https://oyster.ignimgs.com/mediawiki/apis.ign.com/pokemon-switch/d/d0/Status.png?width=325"]


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

    async def check_move(self, name) -> pokepy.api.rv2.MoveResource:
        try:
            return poke_client.get_move(name)
        except Exception:
            return None

    async def get_move_entry(self, name):
        value = await self.check_move(name)
        if not value:
            return None

        move_name = f'Name: `{value.name.replace("-", " ").capitalize()}`'
        if value.accuracy:
            move_accuracy = f"Accuracy: `{value.accuracy}`"
        else:
            move_accuracy = f"Accuracy: `N/A`"
        move_effect_entry = f"Description: `{value.effect_entries[0]['effect']}`"
        move_type = f"Type: `{value.type.name.capitalize()}`"
        move_damage_class = f"Move Class: `{value.damage_class.name.capitalize()}`"
        if value.power:
            move_power = f"Power: `{value.power}`"
        else:
            move_power = "Power: `N/A`"
        move_pp = f"PP: `{value.pp}`"
        move_max_pp = f"Max PP: `{math.ceil(float(value.pp) * 8.0 / 5.0)}`"
        move_priority = f"Priority: `{value.priority}`"
        move_target = f"Target: `{value.target.name.replace('-', ' ').capitalize()}`"
        stat_changes = [(stat.stat.name, stat.change) for stat in value.stat_changes]
        move_stat_changes = "User Stat Changes: "
        if not stat_changes:
            move_stat_changes += "`N/A`"
        else:
            for stat_name, stat_change_amount in stat_changes:
                if stat_change_amount < 0:
                    r_or_l = "Lowers"
                else:
                    r_or_l = "Raises"
                if math.fabs(stat_change_amount) == 1.0:
                    spell = "stage"
                else:
                    spell = "stages"
                move_stat_changes += f"{r_or_l} the user's {stat_name} by {int(math.fabs(stat_change_amount))} {spell}\n"
        return (move_name, move_effect_entry, move_type, move_damage_class, move_power, move_accuracy,
                move_target, move_pp, move_max_pp, move_priority, move_stat_changes)

    async def get_dex_sprite(self, name):
        value = await self.check_pokemon(name)
        return value.sprites.front_default, value.sprites.front_shiny

    async def get_move_status_icon(self, name):
        value = await self.get_move_entry(name)
        if "physical" in value[3].lower():
            return move_status_icon_urls[0]
        elif "special" in value[3].lower():
            return move_status_icon_urls[1]
        elif "status" in value[3].lower():
            return move_status_icon_urls[2]

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

    @pokedex.command(aliases=['-m', 'moves'])
    async def move(self, ctx, *, move_name: str):
        move_name_sent = move_name.replace(" ", "-").lower()
        value = await self.get_move_entry(move_name_sent)
        if value:
            embed = discord.Embed(title=move_name.capitalize(),
                                  description=f"{ctx.author.mention}, here is {move_name.capitalize()}'s move entry\n\n",
                                  color=discord.Color.blue())
            embed.description += "\n".join(value)
            embed.set_thumbnail(url=await self.get_move_status_icon(move_name_sent))
            return await ctx.channel.send(embed=embed)
        else:
            invalid = discord.Embed(title="Invalid Move Name",
                                    description = f"{ctx.author.mention}, `{move_name}` is not a valid move",
                                    color=discord.Color.dark_red())
            return await ctx.channel.send(embed=invalid, delete_after=5)


def setup(client):
    client.add_cog(Pokedex(client))
