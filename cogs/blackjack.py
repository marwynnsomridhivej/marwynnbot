import asyncio
import json
import random
import discord
from discord.ext import commands
from utils import globalcommands

gcmds = globalcommands.GlobalCMDS()
suits = {'Hearts', 'Diamonds', 'Spades', 'Clubs'}
ranks = {'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King', 'Ace'}
values = {'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5, 'Six': 6, 'Seven': 7, 'Eight': 8, 'Nine': 9, 'Ten': 10,
          'Jack': 10, 'Queen': 10, 'King': 10, 'Ace': 11}


class Card:

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return self.rank + ' of ' + self.suit


class Deck:

    def __init__(self):
        self.deck = []
        for suit in suits:
            for rank in ranks:
                self.deck.append(Card(suit, rank))

    def __str__(self):
        deck_comp = ""
        for card in self.deck:
            deck_comp += "\n " + card.__str__()
        return "The deck has:" + deck_comp

    def shuffle(self):
        random.shuffle(self.deck)

    def deal(self):
        single_card = self.deck.pop()
        return single_card


class Hand:

    def __init__(self):
        self.cards = []
        self.value = 0
        self.aces = 0
        self.acecount = 0
        self.iter = 0

    def add_card(self, card):
        self.cards.append(card)
        self.value += values[card.rank]
        if card.rank == 'Ace':
            self.aces += 1

    def adjust_for_ace(self):
        while self.value > 21 and self.aces:
            self.value -= 10
            self.aces -= 1

    def list_hand(self, isDealer=False, gameEnd=False):
        string = ""
        if isDealer is False:
            for card in self.cards:
                if self.value > 21:
                    if card.rank == "Ace" and (self.aces >= 1 or self.acecount >= 1):
                        string += "1+"
                        if self.aces >= 1:
                            self.adjust_for_ace()
                            self.acecount += 1
                    elif gameEnd:
                        if card.rank == "Ace" and self.acecount >= 1:
                            string += "1+"
                            self.acecount -= 1
                        else:
                            string += f"{values[card.rank]}+"
                    else:
                        string += f"{values[card.rank]}+"
                else:
                    if card.rank == "Ace" and self.acecount >= 1:
                        string += "1+"
                    else:
                        string += f"{values[card.rank]}+"
        else:
            cardlist = []
            for card in self.cards:
                cardlist.append(card.rank)
            cardlist.pop(0)
            for card in cardlist:
                if self.value > 21:
                    if card == 'Ace' and (self.aces >= 1 or self.acecount >= 1):
                        string += "1+"
                        if self.aces >= 1:
                            self.adjust_for_ace()
                            self.acecount += 1
                    else:
                        string += f"{values[card]}"
                else:
                    if card == "Ace" and self.acecount >= 1:
                        string += "1+"
                    else:
                        string += f"{values[card]}+"
        self.iter += 1
        return string

    def added(self):
        return self.value


class Chips:

    def __init__(self, balance, bet, ctx):
        self.total = balance
        self.bet = bet
        self.ctx = ctx

    def win_bet(self):
        self.total += self.bet
        with open('db/db/balance.json', 'r') as f:
            file = json.load(f)
            file['Balance'][str(self.ctx.author.id)] = self.total
            with open('db/db/balance.json', 'w') as k:
                json.dump(file, k, indent=4)

    def lose_bet(self):
        self.total -= self.bet
        with open('db/db/balance.json', 'r') as f:
            file = json.load(f)
            file['Balance'][str(self.ctx.author.id)] = self.total
            with open('db/db/balance.json', 'w') as k:
                json.dump(file, k, indent=4)


def take_bet(chips):
    while True:
        try:
            bet = chips.bet
        except ValueError:
            print("NonInt passed into bet")
            break
        else:
            if bet > chips.total:
                return False
            else:
                return True


def hit(deck, hand):
    hand.add_card(deck.deal())


def hit_or_stand(deck, hand, choice):
    x = choice
    if x == 'hit':
        hit(deck, hand)
        return True
    elif x == 'stand':
        return False


def player_busts(player, dealer, chips, ctx):
    chips.lose_bet()
    load = False
    success = False
    init = {'Blackjack': {}}
    gcmds.json_load('db/db/gamestats.json', init)
    with open('db/db/gamestats.json', 'r') as f:
        file = json.load(f)
        while not load:
            try:
                file['Blackjack'][str(ctx.author.id)]['lose'] += 1
                load = True
            except KeyError:
                if not success:
                    try:
                        file['Blackjack'][str(ctx.author.id)]
                    except KeyError:
                        file['Blackjack'][str(ctx.author.id)] = {}
                        success = True
                file['Blackjack'][str(ctx.author.id)]['lose'] = 0
        with open('db/db/gamestats.json', 'w') as f:
            json.dump(file, f, indent=4)
    gcmds.ratio(ctx.author, 'db/db/gamestats.json', 'Blackjack')


def player_wins(player, dealer, chips, ctx):
    chips.win_bet()
    load = False
    success = False
    init = {'Blackjack': {}}
    gcmds.json_load('db/db/gamestats.json', init)
    with open('db/db/gamestats.json', 'r') as f:
        file = json.load(f)
        while not load:
            try:
                file['Blackjack'][str(ctx.author.id)]['win'] += 1
                load = True
            except KeyError:
                if not success:
                    try:
                        file['Blackjack'][str(ctx.author.id)]
                    except KeyError:
                        file['Blackjack'][str(ctx.author.id)] = {}
                        success = True
                file['Blackjack'][str(ctx.author.id)]['win'] = 0
        with open('db/db/gamestats.json', 'w') as f:
            json.dump(file, f, indent=4)
    gcmds.ratio(ctx.author, 'db/db/gamestats.json', 'Blackjack')


def dealer_busts(player, dealer, chips, ctx):
    chips.win_bet()
    load = False
    success = False
    init = {'Blackjack': {}}
    gcmds.json_load('db/db/gamestats.json', init)
    with open('db/db/gamestats.json', 'r') as f:
        file = json.load(f)
        while not load:
            try:
                file['Blackjack'][str(ctx.author.id)]['win'] += 1
                load = True
            except KeyError:
                if not success:
                    try:
                        file['Blackjack'][str(ctx.author.id)]
                    except KeyError:
                        file['Blackjack'][str(ctx.author.id)] = {}
                        success = True
                file['Blackjack'][str(ctx.author.id)]['win'] = 0
        with open('db/db/gamestats.json', 'w') as f:
            json.dump(file, f, indent=4)
    gcmds.ratio(ctx.author, 'db/db/gamestats.json', 'Blackjack')


def dealer_wins(player, dealer, chips, ctx):
    chips.lose_bet()
    load = False
    success = False
    init = {'Blackjack': {}}
    gcmds.json_load('db/db/gamestats.json', init)
    with open('db/db/gamestats.json', 'r') as f:
        file = json.load(f)
        while not load:
            try:
                file['Blackjack'][str(ctx.author.id)]['lose'] += 1
                load = True
            except KeyError:
                if not success:
                    try:
                        file['Blackjack'][str(ctx.author.id)]
                    except KeyError:
                        file['Blackjack'][str(ctx.author.id)] = {}
                        success = True
                file['Blackjack'][str(ctx.author.id)]['lose'] = 0
        with open('db/db/gamestats.json', 'w') as f:
            json.dump(file, f, indent=4)
    gcmds.ratio(ctx.author, 'db/db/gamestats.json', 'Blackjack')


def push(player, dealer, ctx):
    load = False
    success = False
    init = {'Blackjack': {}}
    gcmds.json_load('db/db/gamestats.json', init)
    with open('db/db/gamestats.json', 'r') as f:
        file = json.load(f)
        while not load:
            try:
                file['Blackjack'][str(ctx.author.id)]['tie'] += 1
                load = True
            except KeyError:
                if not success:
                    try:
                        file['Blackjack'][str(ctx.author.id)]
                    except KeyError:
                        file['Blackjack'][str(ctx.author.id)] = {}
                        success = True
                file['Blackjack'][str(ctx.author.id)]['tie'] = 0
        with open('db/db/gamestats.json', 'w') as f:
            json.dump(file, f, indent=4)


def _blackjack(player, dealer, chips, ctx):
    chips.win_bet()
    chips.win_bet()
    load = False
    success = False
    init = {'Blackjack': {}}
    gcmds.json_load('db/db/gamestats.json', init)
    with open('db/db/gamestats.json', 'r') as f:
        file = json.load(f)
        while not load:
            try:
                file['Blackjack'][str(ctx.author.id)]['win'] += 1
                file['Blackjack'][str(ctx.author.id)]['blackjack'] += 1
                load = True
            except KeyError:
                if not success:
                    try:
                        file['Blackjack'][str(ctx.author.id)]
                    except KeyError:
                        file['Blackjack'][str(ctx.author.id)] = {}
                        success = True
                file['Blackjack'][str(ctx.author.id)]['win'] = 0
                file['Blackjack'][str(ctx.author.id)]['blackjack'] = 0

        with open('db/db/gamestats.json', 'w') as f:
            json.dump(file, f, indent=4)
    gcmds.ratio(ctx.author, 'db/db/gamestats.json', 'Blackjack')


def show_dealer(dealer, won):
    if won:
        index = 0
        string = ""
        while index < len(dealer.cards):
            string += emoji(dealer.cards[index])
            index += 1
        return string
    else:
        index = 1
        string = "<:cardback:738063418832978070>"
        while index < len(dealer.cards):
            string += emoji(dealer.cards[index])
            index += 1
        return string


def show_player(player):
    index = 0
    string = ""
    while index < len(player.cards):
        string += emoji(player.cards[index])
        index += 1
    return string


def emoji(card):
    if card.rank == "Two":
        if card.suit == "Hearts":
            return "<:2H:738096935692402819>"
        if card.suit == "Diamonds":
            return "<:2D:738096998644973648>"
        if card.suit == "Spades":
            return "<:2S:738097035584077856>"
        if card.suit == "Clubs":
            return "<:2C:738097069637763092>"
    if card.rank == "Three":
        if card.suit == "Hearts":
            return "<:3H:738096936308965446>"
        if card.suit == "Diamonds":
            return "<:3D:738096998410092655>"
        if card.suit == "Spades":
            return "<:3S:738097035466637403>"
        if card.suit == "Clubs":
            return "<:3C:738097069675511848>"
    if card.rank == "Four":
        if card.suit == "Hearts":
            return "<:4H:738096936040792076>"
        if card.suit == "Diamonds":
            return "<:4D:738096998758088704>"
        if card.suit == "Spades":
            return "<:4S:738097035529683045>"
        if card.suit == "Clubs":
            return "<:4C:738097069738295306>"
    if card.rank == "Five":
        if card.suit == "Hearts":
            return "<:5H:738096936447508591>"
        if card.suit == "Diamonds":
            return "<:5D:738096998938574991>"
        if card.suit == "Spades":
            return "<:5S:738097035856576542>"
        if card.suit == "Clubs":
            return "<:5C:738097070228897793>"
    if card.rank == "Six":
        if card.suit == "Hearts":
            return "<:6H:738096936485388319>"
        if card.suit == "Diamonds":
            return "<:6D:738096999358005310>"
        if card.suit == "Spades":
            return "<:6S:738097036037193839>"
        if card.suit == "Clubs":
            return "<:6C:738097070094680127>"
    if card.rank == "Seven":
        if card.suit == "Hearts":
            return "<:7H:738096936586051684>"
        if card.suit == "Diamonds":
            return "<:7D:738096999173193838>"
        if card.suit == "Spades":
            return "<:7S:738097036104171520>"
        if card.suit == "Clubs":
            return "<:7C:738097070358921597>"
    if card.rank == "Eight":
        if card.suit == "Hearts":
            return "<:8H:738096936657223850>"
        if card.suit == "Diamonds":
            return "<:8D:738096999282376774>"
        if card.suit == "Spades":
            return "<:8S:738097035621695530>"
        if card.suit == "Clubs":
            return "<:8C:738097070530887760>"
    if card.rank == "Nine":
        if card.suit == "Hearts":
            return "<:9H:738096936728395837>"
        if card.suit == "Diamonds":
            return "<:9D:738096999026524231>"
        if card.suit == "Spades":
            return "<:9S:738097035936268289>"
        if card.suit == "Clubs":
            return "<:9C:738097070489206925>"
    if card.rank == "Ten":
        if card.suit == "Hearts":
            return "<:10H:738096936363491330>"
        if card.suit == "Diamonds":
            return "<:10D:738096999139639377>"
        if card.suit == "Spades":
            return "<:10S:738097035772690534>"
        if card.suit == "Clubs":
            return "<:10C:738097159647264769>"
    if card.rank == "Jack":
        if card.suit == "Hearts":
            return "<:JH:738096936703492243>"
        if card.suit == "Diamonds":
            return "<:JD:738096998959284347>"
        if card.suit == "Spades":
            return "<:JS:738097037379371038>"
        if card.suit == "Clubs":
            return "<:JC:738097070476361779>"
    if card.rank == "Queen":
        if card.suit == "Hearts":
            return "<:QH:738096936262828073>"
        if card.suit == "Diamonds":
            return "<:QD:738096999190233178>"
        if card.suit == "Spades":
            return "<:QS:738097036041257100>"
        if card.suit == "Clubs":
            return "<:QC:738097070530887770>"
    if card.rank == "King":
        if card.suit == "Hearts":
            return "<:KH:738096936615149578>"
        if card.suit == "Diamonds":
            return "<:KD:738096999353549067>"
        if card.suit == "Spades":
            return "<:KS:738097035818827877>"
        if card.suit == "Clubs":
            return "<:KC:738097159764967495>"
    if card.rank == "Ace":
        if card.suit == "Hearts":
            return "<:AH:738096936644771931>"
        if card.suit == "Diamonds":
            return "<:AD:738096999278051448>"
        if card.suit == "Spades":
            return "<:AS:738097037186170921>"
        if card.suit == "Clubs":
            return "<:AC:738097070233092208>"


class Blackjack(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=['bj', 'Blackjack'])
    async def blackjack(self, ctx, bet=1):

        won = False
        bet = bet
        deck = Deck()
        deck.shuffle()
        if bet != 1:
            spell = 'credits'
        else:
            spell = 'credit'

        player_hand = Hand()
        player_hand.add_card((deck.deal()))
        player_hand.add_card((deck.deal()))
        player_value = player_hand.list_hand()
        pv_int = player_hand.added()

        dealer_hand = Hand()
        dealer_hand.add_card((deck.deal()))
        dealer_hand.add_card((deck.deal()))
        dealer_value = dealer_hand.list_hand(True)

        init = {'Balance': {}}
        gcmds.json_load('db/db/balance.json', init)
        with open('db/db/balance.json', 'r') as f:
            file = json.load(f)
            try:
                file['Balance'][str(ctx.author.id)]
            except KeyError:
                file['Balance'][str(ctx.author.id)] = 1000
                balance = 1000
                initEmbed = discord.Embed(title="Initialised Credit Balance",
                                          description=f"{ctx.author.mention}, you have been credited `1000` credits "
                                                      f"to start!\n\nCheck your current"
                                                      f" balance using `{gcmds.prefix(ctx)}balance`",
                                          color=discord.Color.blue())
                initEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/734962101432615006"
                                            "/738390147514499163/chips.png")
                await ctx.channel.send(embed=initEmbed, delete_after=10)

            else:
                balance = file['Balance'][str(ctx.author.id)]

        with open('db/db/balance.json', 'w') as f:
            json.dump(file, f, indent=4)

        player_chips = Chips(balance, bet, ctx)
        if not take_bet(player_chips):
            insuf = discord.Embed(title="Insufficient Credit Balance",
                                  description=f"{ctx.author.mention}, you have `{balance}` credits"
                                              f"\nYour bet of `{bet}` credits exceeds your current balance",
                                  color=discord.Color.dark_red())
            await ctx.channel.send(embed=insuf, delete_after=10)
            return

        hitEmoji = '✅'
        standEmoji = '❌'
        cancelEmoji = '🛑'

        bjEmbed = discord.Embed(title="Blackjack",
                                description=f"To hit, react to {hitEmoji}, to stand, react to {standEmoji}, to cancel "
                                            f"the game, react to {cancelEmoji} (only before first turn)",
                                color=discord.Color.blue())
        bjEmbed.set_author(name=f"{ctx.author.name} bet {bet} {spell} to play Blackjack",
                           icon_url=ctx.author.avatar_url)
        bjEmbed.add_field(name=f"Dealer `[?+{dealer_value[:-1]}=?]`",
                          value=show_dealer(dealer_hand, won))
        bjEmbed.add_field(name=f"{ctx.author.name} `[{player_value[:-1]}={pv_int}]`",
                          value=show_player(player_hand))
        message = await ctx.channel.send(embed=bjEmbed)
        await message.add_reaction(hitEmoji)
        await message.add_reaction(standEmoji)
        await message.add_reaction(cancelEmoji)

        def check(reaction, user):
            if ctx.author == user and str(reaction.emoji) == '✅':
                return True
            elif ctx.author == user and str(reaction.emoji) == '❌':
                return True
            elif ctx.author == user and str(reaction.emoji) == '🛑':
                return True
            else:
                return False

        while True:
            await message.add_reaction(hitEmoji)
            await message.add_reaction(standEmoji)
            try:
                choice = await self.client.wait_for('reaction_add', timeout=60.0, check=check)
                for item in choice:
                    if str(item) == '✅':
                        choice = 'hit'
                        break
                    if str(item) == '❌':
                        choice = 'stand'
                        break
                    if str(item) == '🛑':
                        await message.clear_reactions()
                        bjEmbed = discord.Embed(title="Blackjack Game Canceled",
                                                description=f"{ctx.author.mention}, your game was cancelled",
                                                color=discord.Color.dark_red())
                        await message.edit(embed=bjEmbed, delete_after=10)
                        return
                stopiter = hit_or_stand(deck, player_hand, choice)

                player_value = player_hand.list_hand()
                pv_int = player_hand.added()
                dealer_value = dealer_hand.list_hand(True)

                await message.clear_reactions()
                bjEmbed = discord.Embed(title="Blackjack",
                                        description=f"To hit, react to {hitEmoji}, to stand, react to {standEmoji}, "
                                                    f"to cancel the game, react to {cancelEmoji}",
                                        color=discord.Color.blue())
                bjEmbed.set_author(name=f"{ctx.author.name} bet {bet} {spell} to play Blackjack",
                                   icon_url=ctx.author.avatar_url)
                bjEmbed.add_field(name=f"Dealer `[?+{dealer_value[:-1]}=?]`",
                                  value=show_dealer(dealer_hand, won))
                bjEmbed.add_field(name=f"{ctx.author.name} `[{player_value[:-1]}={pv_int}]`",
                                  value=show_player(player_hand))
                await message.edit(embed=bjEmbed)
            except asyncio.TimeoutError:
                if won:
                    return
                else:
                    await message.clear_reactions()
                    canceled = discord.Embed(title="Game Timeout",
                                             description=f"{ctx.author.mention}, game canceled due to inactivity, "
                                                         f"create a new game",
                                             color=discord.Color.dark_red())
                    canceled.set_thumbnail(url='https://cdn.discordapp.com/attachments/734962101432615006'
                                               '/738083697726849034/nocap.jpg')
                    canceled.set_footer(text=f"{ctx.author.name} did not provide a valid reaction within 60 seconds")
                    await message.edit(embed=canceled, delete_after=10)
                    return

            if player_hand.value > 21:
                player_busts(player_hand, dealer_hand, player_chips, ctx)
                won = True

                player_value = player_hand.list_hand(gameEnd=won)
                pv_int = player_hand.added()
                dealer_value = dealer_hand.list_hand(gameEnd=won)
                dr_int = dealer_hand.added()

                await message.clear_reactions()
                bjEmbedEdit = discord.Embed(title="Blackjack",
                                            description=f"{ctx.author.mention}, you busted! Lost **{bet}** {spell}",
                                            color=discord.Color.blue())
                bjEmbedEdit.set_author(name="Results",
                                       icon_url=ctx.author.avatar_url)
                bjEmbedEdit.add_field(name=f"Dealer `[{dealer_value[:-1]}={dr_int}]`",
                                      value=show_dealer(dealer_hand, won))
                bjEmbedEdit.add_field(name=f"{ctx.author.name} `[{player_value[:-1]}={pv_int}]`",
                                      value=show_player(player_hand))
                await message.edit(embed=bjEmbedEdit)
                gcmds.incrCounter(ctx, 'blackjack')
                return

            if player_hand.value <= 21 and not stopiter:
                while dealer_hand.value < 17:
                    hit(deck, dealer_hand)

                player_value = player_hand.list_hand(gameEnd=won)
                pv_int = player_hand.added()
                dealer_value = dealer_hand.list_hand(gameEnd=won)
                dr_int = dealer_hand.added()

                won = True

                large_bet_win = False

                if (player_hand.iter - 3) == 0 and player_hand.value == 21:
                    _blackjack(player_hand, dealer_hand, player_chips, ctx)
                    description = f"Blackjack! {ctx.author.mention} wins **{bet * 2}** credits"
                    if bet >= 1000:
                        large_bet_win = True
                elif dealer_hand.value > 21:
                    dealer_busts(player_hand, dealer_hand, player_chips, ctx)
                    description = f"Dealer busts! {ctx.author.mention} wins **{bet}** {spell}"
                    if bet >= 1000:
                        large_bet_win = True
                elif dealer_hand.value > player_hand.value:
                    dealer_wins(player_hand, dealer_hand, player_chips, ctx)
                    description = f"Dealer wins! {ctx.author.mention} lost **{bet}** {spell}"
                elif player_hand.value > dealer_hand.value:
                    player_wins(player_hand, dealer_hand, player_chips, ctx)
                    description = f"{ctx.author.mention} wins **{bet}** {spell}"
                    if bet >= 1000:
                        large_bet_win = True
                else:
                    push(player_hand, dealer_hand, ctx)
                    description = "Its a tie! No credits lost or gained"

                await message.clear_reactions()
                bjEmbedEdit = discord.Embed(title="Blackjack",
                                            description=description,
                                            color=discord.Color.blue())
                bjEmbedEdit.set_author(name="Results",
                                       icon_url=ctx.author.avatar_url)
                bjEmbedEdit.add_field(name=f"Dealer `[{dealer_value[:-1]}={dr_int}]`",
                                      value=show_dealer(dealer_hand, won))
                bjEmbedEdit.add_field(name=f"{ctx.author.name} `[{player_value[:-1]}={pv_int}]`",
                                      value=show_player(player_hand))
                await message.edit(embed=bjEmbedEdit)

                if ((player_hand.iter - 3) == 0 and player_hand.value == 21) or large_bet_win:
                    await message.add_reaction("📌")
                    await message.add_reaction("🛑")

                    bjEmbedEdit.set_footer(text="To pin, react with 📌, otherwise, react with 🛑")
                    await message.edit(embed=bjEmbedEdit)

                    def check_pin(reaction, user):
                        if ctx.author == user and str(reaction.emoji) == '📌':
                            return True
                        elif ctx.author == user and str(reaction.emoji) == '🛑':
                            return True
                        else:
                            return False

                    try:
                        pin_choice = await self.client.wait_for('reaction_add', timeout=20.0,
                                                                check=check_pin)
                    except asyncio.TimeoutError:
                        await message.clear_reactions()
                        bjEmbedEdit.set_footer(text="Not pinned 🛑")
                        await message.edit(embed=bjEmbedEdit)
                        return
                    else:
                        for item in pin_choice:
                            if str(item) == '📌':
                                await message.clear_reactions()
                                await message.pin()
                                bjEmbedEdit.set_footer(text="Pinned 📌")
                                break
                            if str(item) == '🛑':
                                await message.clear_reactions()
                                bjEmbedEdit.set_footer(text="Not pinned 🛑")
                                return

                        await message.edit(embed=bjEmbedEdit)

                gcmds.incrCounter(ctx, 'blackjack')
                return


def setup(client):
    client.add_cog(Blackjack(client))
