import asyncio
import math
import random
from random import randint, shuffle
from typing import Union

import discord
from discord.ext import commands
from num2words import num2words
from utils import cards, customerrors, globalcommands

gcmds = globalcommands.GlobalCMDS()
COLORS = ['red', 'yellow', 'green', 'blue']
ALL_COLORS = COLORS + ['black']
NUMBERS = list(range(10)) + list(range(1, 10))
SPECIAL_CARD_TYPES = ['block', 'reverse', '+2']
COLOR_CARD_TYPES = NUMBERS + SPECIAL_CARD_TYPES * 2
BLACK_CARD_TYPES = ['wild', '+4'] * 4
CARD_TYPES = NUMBERS + SPECIAL_CARD_TYPES + BLACK_CARD_TYPES
TIMEOUT = 60
CANCEL = 'Enter "cancel" to cancel the game when it is your turn'


class UnoCard:
    def __init__(self, color: str, cardtype):
        self.color = color
        self.card_type = cardtype

    def __str__(self):
        return f"{self.color} {self.card_type}"

    def __repr__(self):
        return self.__str__()

    def wild_color(self, new_color: str):
        self.color = new_color


class UnoPile:
    def __init__(self):
        self.pile = []

    def __str__(self):
        return f"Pile: {len(self.pile)} cards"

    @property
    def top_card(self) -> UnoCard:
        return self.pile[-1]

    def place(self, card: UnoCard) -> UnoCard:
        self.pile.append(card)
        return card

    def set_black_color(self, color: str):
        self.top_card.wild_color(color)

    @property
    def reset_pile(self):
        newdeck = self.pile
        newdeck.remove(-1)
        self.pile = newdeck
        return newdeck

    @property
    def embed_color(self) -> discord.Color:
        if self.pile[-1].color == "red":
            return discord.Color.red()
        elif self.pile[-1].color == "blue":
            return discord.Color.blue()
        elif self.pile[-1].color == "green":
            return discord.Color.green()
        elif self.pile[-1].color == "yellow":
            return discord.Color.gold()
        else:
            return discord.Color.darker_grey()

    @property
    def top_thumbnail(self) -> str:
        top_card = self.pile[-1]
        return cards.uno_thumbnail[str(top_card.card_type)][top_card.color]


class UnoDeck:
    def __init__(self):
        self.deck = [UnoCard(color, card_type) for card_type in COLOR_CARD_TYPES for color in COLORS]
        for black_type in BLACK_CARD_TYPES:
            self.deck.append(UnoCard("black", black_type))

    def __str__(self):
        return f"Uno Deck: {str(len(self.deck))} cards."

    def shuffle(self):
        shuffle(self.deck)

    @property
    def is_empty(self) -> bool:
        return len(self.deck) == 0

    def deal(self) -> UnoCard:
        return self.deck.pop()

    def reset(self, pile: UnoPile):
        self.deck = pile.reset_pile()
        shuffle(self.deck)


class UnoPlayer:
    def __init__(self, member: discord.Member):
        self.hand = []
        self.member = member
        self.name = member.display_name
        self.id = member.id
        self.mention = member.mention
        self.avatar_url = member.avatar_url

    def __str__(self):
        return f"<{self.name}, hand={str(self.hand)}>"

    def __len__(self):
        return len(self.hand)

    def seven_draw(self, deck: UnoDeck):
        for num in range(7):
            self.hand.append(deck.deal())
            deck.shuffle()
        return self

    def draw(self, deck: UnoDeck):
        self.hand.append(deck.deal())

    def place(self, card: UnoCard, pile: UnoPile) -> UnoCard:
        self.hand.remove(card)
        return pile.place(card)

    def remove_wild(self, card: UnoCard):
        self.hand.remove(card)

    def can_play(self, pile: UnoPile) -> bool:
        topcard = pile.top_card
        if topcard.color == "black":
            return True
        for card in self.hand:
            if card.color == "black":
                return True
            elif card.color == topcard.color or card.card_type == topcard.card_type:
                return True
        return False

    def validate(self, index: Union[str, int], pile: UnoPile) -> bool:
        if str(index).lower() == "cancel":
            return True
        card = self.hand[int(index) - 1]
        topcard = pile.top_card
        if topcard.color == "black":
            return True
        elif card.color == "black":
            return True
        elif card.color == topcard.color or card.card_type == topcard.card_type:
            return True
        else:
            return False

    def auto_play(self, pile: UnoPile) -> UnoCard:
        topcard = pile.top_card
        try:
            card = self.place(random.choice([card for card in self.hand
                                             if card.color != "black" and
                                             (card.color == topcard.color or
                                              card.card_type == topcard.card_type)]), pile)
        except Exception:
            card = self.place(random.choice([card for card in self.hand if card.color == "black"]), pile)
        return card

    async def send(self, *args, **kwargs):
        return await self.member.send(*args, **kwargs)

    @property
    def is_uno(self) -> bool:
        return int(len(self.hand)) == 1

    @property
    def emoji_to_player(self) -> str:
        return "\n".join(
            f"{counter}. {cards.uno_cards[str(card.card_type)][card.color]} `[{card.color} {card.card_type}]`"
            for counter, card in enumerate(self.hand, 1))

    @property
    def emoji_to_game(self) -> str:
        return "<:unoback:739620076180865062>" * len(self.hand)


class UnoGame:
    def __init__(self, bot: commands.AutoShardedBot, players: list):
        self.bot = bot
        self.index = 0
        self.turns = 1
        self.players = players
        shuffle(self.players)
        self.current_player: UnoPlayer = self.players[0]
        self.finished = []
        self.newly_reversed = False
        self.reversed = False

    @classmethod
    def _reset(cls, *args, **kwargs):
        return UnoGame(*args, **kwargs)

    def reverse(self):
        self.newly_reversed = True
        self.reversed = not self.reversed

    def get_next_player(self) -> UnoPlayer:
        if self.newly_reversed:
            if len(self.players) == 2:
                return self.current_player

        if self.turns == 1:
            return self.current_player

        if self.reversed:
            self.index -= 1
        else:
            self.index += 1

        if self.index < 0:
            self.index = int(len(self.players)) - 1
        elif self.index > int(len(self.players)) - 1:
            self.index = 0

        self.current_player = self.players[self.index]
        return self.current_player

    async def calc_reward(self, player: UnoPlayer) -> int:
        return int(math.ceil(randint(10, 100) * self.turns / randint(2, 10))) \
            if self.turns >= 100 else \
            int(math.ceil(randint(1, 10) * self.turns / randint(2, 5)))

    async def finish(self, ctx, player: UnoPlayer) -> discord.Message:
        reward_amount = await self.calc_reward(player)
        if len(self.finished) == 0:
            description = f"Congratulations {player.mention}! You won {reward_amount} credits!"
            await win(self, player, self.bot, reward_amount)
        else:
            description = f"Congratulations {player.mention}! Thank you for playing!"
        embed = discord.Embed(title=f"{num2words(len(self.finished) + 1, to='ordinal_num')} Place",
                              description=description,
                              color=discord.Color.blue())
        self.finished.append(player)
        self.players.remove(player)
        return await ctx.channel.send(embed=embed)

    async def send_panel(self, ctx, pile: UnoPile, **kwargs) -> discord.Message:
        embed = discord.Embed(title="Uno", color=pile.embed_color)
        embed.set_thumbnail(url=pile.top_thumbnail)
        embed.set_author(name=kwargs.get("author", f"{self.current_player.name}'s Turn"),
                         icon_url=self.current_player.avatar_url)
        embed.set_footer(text=f"Turn {self.turns}\n{CANCEL}")
        for player in self.players:
            embed.add_field(name=f'{player.name}{" - Uno!" if player.is_uno else ""}',
                            value=(player.emoji_to_game),
                            inline=False)
        return await ctx.channel.send(embed=embed)


async def win(game: UnoGame, player: UnoPlayer, bot: commands.AutoShardedBot, reward_amount: int):
    async with bot.db.acquire() as con:
        result = await con.fetch(f"SELECT * FROM uno WHERE user_id={player.member.id}")
        if not result:
            await con.execute(f"INSERT INTO uno(user_id, win) VALUES ({player.member.id}, 1)")
        else:
            await con.execute(f"UPDATE uno SET win = win + 1 WHERE user_id = {player.member.id}")
    await gcmds.ratio(player.member, 'uno')
    await gcmds.balance_db(f"UPDATE balance SET amount= amount + {reward_amount} WHERE user_id={player.id}")
    return


async def lose(player: UnoPlayer, bot: commands.AutoShardedBot):
    async with bot.db.acquire() as con:
        result = await con.fetch(f"SELECT * FROM uno WHERE user_id={player.member.id}")
        if not result:
            await con.execute(f"INSERT INTO uno(user_id, lose) VALUES ({player.member.id}, 1)")
        else:
            await con.execute(f"UPDATE uno SET lose = lose + 1 WHERE user_id = {player.member.id}")
    await gcmds.ratio(player.member, 'uno')
    return


class Uno(commands.Cog):
    def __init__(self, bot):
        global gcmds
        self.bot = bot
        gcmds = globalcommands.GlobalCMDS(self.bot)
        self.bot.loop.create_task(self.init_uno())

    async def init_uno(self):
        await self.bot.wait_until_ready()
        async with self.bot.db.acquire() as con:
            await con.execute("CREATE TABLE IF NOT EXISTS uno(user_id bigint "
                              "PRIMARY KEY, win NUMERIC DEFAULT 0, lose "
                              "NUMERIC DEFAULT 0, ratio NUMERIC DEFAULT 0)")

    async def check_valid(self, ctx, members):
        if not members:
            embed = discord.Embed(title="No Opponents",
                                  description=f"{ctx.author.mention}, please "
                                  "mention other players to start a game",
                                  color=discord.Color.dark_red())
            return await ctx.channel.send(embed=embed)
        elif len(members) > 9:
            embed = discord.Embed(title="Too Many Opponents",
                                  description=f"{ctx.author.mention}, please "
                                  "mention up to 9 other players to start a game",
                                  color=discord.Color.dark_red())
            return await ctx.channel.send(embed=embed)
        elif ctx.author in members:
            embed = discord.Embed(title="Invalid Opponent Selection",
                                  description=f"{ctx.author.mention}, you cannot"
                                  " mention yourself as an opponent",
                                  color=discord.Color.dark_red())
            return await ctx.channel.send(embed=embed)
        else:
            return None

    async def init_game(self, ctx, members) -> tuple:
        deck = UnoDeck()
        deck.shuffle()
        pile = UnoPile()
        pile.place(deck.deal())

        members.append(ctx.author)
        players = members
        embed = discord.Embed(title="Setting up Uno Game...",
                              description="Uno game between: " + ", ".join(
                                  [player.mention for player in players]
                              ),
                              color=discord.Color.blue())
        await ctx.channel.send(embed=embed)
        await asyncio.sleep(3.0)

        game = UnoGame(self.bot, [UnoPlayer(player).seven_draw(deck) for player in players])
        return deck, pile, game

    async def calc_actions(self, ctx, game: UnoGame, deck: UnoDeck, pile: UnoPile,
                           n_rev: bool, blocked: bool, force_plus: int):
        playable = True
        game.get_next_player()
        author = None
        if game.turns != 1:
            if blocked:
                author = f"{game.current_player.name} was blocked! Skipping turn..."
                playable = False
            elif force_plus != 0:
                for _ in range(force_plus):
                    game.current_player.draw(deck)
                author = f"{game.current_player.name} drew {force_plus} cards! Skipping turn..."
                playable = False
            elif n_rev:
                author = f"Order was reversed! It is now {game.current_player.name}'s turn!"
        return game, game.current_player, playable, author

    async def playable(self, player: UnoPlayer, deck: UnoDeck, pile: UnoPile) -> bool:
        embed = discord.Embed(title="Your Hand", description=player.emoji_to_player, color=pile.embed_color)
        embed.set_thumbnail(url=pile.top_thumbnail)
        if not player.can_play(pile):
            player.draw(deck)
            embed.set_footer(text="You had to draw a card because you were "
                             f"previously unable to place any card\n{CANCEL}")
            if not player.can_play(pile):
                return False
        try:
            await player.send(embed=embed)
        except Exception:
            raise customerrors.UnoCannotDM(player.member)
        return True

    async def choose_black_color(self, ctx, game: UnoGame, pile: UnoPile):
        def from_cur_player(message: discord.Message):
            return (message.channel.id == ctx.channel.id and
                    message.content.lower() in COLORS and
                    message.author.id == game.current_player.id)

        embed = discord.Embed(title="Card Color",
                              description=f"{game.current_player.mention}, please choose which "
                              "color you would like the card to become. The valid "
                              "colors are: " + ", ".join([f'*"{color}"*' for color in COLORS]),
                              color=pile.embed_color)
        embed.set_footer(text="Please respond within 30 seconds, or a random color will "
                         f"be chosen for you\n{CANCEL}")
        await ctx.channel.send(embed=embed)

        try:
            message = await self.bot.wait_for("message", check=from_cur_player, timeout=TIMEOUT / 2)
        except asyncio.TimeoutError:
            color = random.choice([card.color for card in game.current_player.hand if card.color != "black"])
        else:
            color = message.content.lower()
        pile.set_black_color(color)
        return

    async def process_selection(self, ctx, game: UnoGame, pile: UnoPile):
        def from_cur_player(message: discord.Message):
            try:
                if message.content.lower() == "cancel":
                    pass
                elif 0 <= int(message.content) - 1 < len(player):
                    raise Exception
            except Exception:
                return False
            else:
                return (message.channel.id == ctx.channel.id and
                        message.author.id == player.id and
                        player.validate(message.content, pile))

        player = game.current_player
        n_rev = False

        try:
            message = await self.bot.wait_for("message", check=from_cur_player, timeout=TIMEOUT)
        except asyncio.TimeoutError:
            card = player.auto_play(pile)
        else:
            if message.content.lower() == "cancel":
                return player, None, None, None, True
            card = player.place(player.hand[int(message.content) - 1], pile)
        if card.color == "black":
            await self.choose_black_color(ctx, game, pile)
        elif card.card_type == "reverse":
            game.reverse()
            game.newly_reversed = True
            n_rev = True
        return player, card, game, n_rev, False

    async def check_finish(self, ctx, game: UnoGame, player: UnoPlayer):
        if len(player) == 0:
            await game.finish(ctx, player)
        game.turns += 1

    async def game_cancelled(self, ctx, player: UnoPlayer):
        embed = discord.Embed(title="Game Cancelled",
                              description=f"The game was cancelled by {player.mention}. "
                              "All progress for the game has been lost",
                              color=discord.Color.dark_red())
        return await ctx.channel.send(embed=embed)

    @commands.command(desc="Uno in Discord!",
                      usage="uno [@member]*va",
                      note="You must specify up to 9 other members.\n\nWhen it is your turn, "
                      "you can type \"cancel\" to cancel the game")
    async def uno(self, ctx, members: commands.Greedy[discord.Member] = None):
        if await self.check_valid(ctx, members):
            return

        deck, pile, game = await self.init_game(ctx, members)
        n_rev = False
        blocked = False
        force_plus = 0

        while len(game.players) != 1:
            game, player, playable, author = await self.calc_actions(ctx, game, deck, pile, n_rev, blocked, force_plus)
            if not (playable and await self.playable(player, deck, pile)):
                if not author:
                    author = f"{game.current_player.name} could not place a card. Skipping turn..."
                await game.send_panel(ctx, pile, author=author)
                blocked = False
                n_rev = False
                force_plus = 0
                game.turns += 1
                continue

            if not author:
                author = f"{game.current_player.name}'s Turn"
            await game.send_panel(ctx, pile, author=author)
            player, card, game, n_rev, cancelled = await self.process_selection(ctx, game, pile)
            if cancelled:
                return await self.game_cancelled(ctx, player)
            else:
                await self.check_finish(ctx, game, player)

            force_plus = int(card.card_type[1]) if card.card_type in ["+2", "+4"] else 0
            blocked = True if card.card_type == "block" else False

        last_player = game.players[0]
        await lose(last_player, self.bot)
        game.finished.append(last_player)

        description = "\n".join(
            [f"**{num2words(counter, to='ordinal_num')} Place:**\n{player.mention}"
                for counter, player in enumerate(game.finished, 1)]
        )
        embed = discord.Embed(title="Results", description=description, color=discord.Color.blue())
        await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Uno(bot))
