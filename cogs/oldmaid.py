import asyncio
import random
import discord
import json
from globalcommands import GlobalCMDS as gcmds
import typing
from discord.ext import commands

suits = {'Hearts', 'Diamonds', 'Spades', 'Clubs'}
ranks = {'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King', 'Ace'}


class Card:

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank} of {self.suit}"


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

    def __init__(self, player: discord.Member):
        self.cards = []
        self.pairs = []
        self.player = player

    def add(self, card):
        self.cards.append(card)

    def remove_pairs(self):
        original_cards = self.cards[:]
        for card in original_cards:
            orig = card
            match = Card(orig.suit, orig.rank)
            for selfCard in self.cards:
                if match.rank == selfCard.rank:
                    self.pairs.append(f"{match.__str__()}")
                    self.pairs.append(f"{selfCard.__str__()}")
                    self.cards.remove(match)
                    self.cards.remove(selfCard)
        print(self.pairs)
        return self.pairs


def emoji_to_player(hand):
    for card in hand:
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


def emoji_to_game(hand):
    string = "<:back:739620076180865062>"
    return string * int(len(hand))


class OldMaid(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" has been loaded')

    @commands.command(aliases=['oldmaid', 'om', 'maid'])
    async def oldMaid(self, ctx, bet: typing.Optional[int] = 1, members: commands.Greedy[discord.Member] = None):
        await gcmds.invkDelete(gcmds, ctx)

        if members is None:
            errorEmbed = discord.Embed(title="No Opponents Specified",
                                       description=f"{ctx.author.mention}, you need to mention at least one person to "
                                                   f"start a game",
                                       color=discord.Color.dark_red())
            await ctx.channel.send(embed=errorEmbed, delete_after=10)
            return
        elif int(len(members)) > 7:
            tooMany = discord.Embed(title="Too Many Opponents",
                                    description=f"{ctx.author.mention}, you have mentioned too many opponents! Please "
                                                f"mention up to 7 other people",
                                    color=discord.Color.dark_red())
            await ctx.channel.send(embed=tooMany, delete_after=10)
            return
        else:
            for member in members:
                if member == ctx.author:
                    errorEmbed = discord.Embed(title="Invalid Opponent Specified",
                                               description=f"{ctx.author.mention}, you cannot select yourself as an "
                                                           f"opponent",
                                               color=discord.Color.dark_red())
                    await ctx.channel.send(embed=errorEmbed)
                    return

        betAmount = bet
        if betAmount != 1:
            spell = "credits"
        else:
            spell = "credit"
        init = {'Balance': {}}
        gcmds.json_load(gcmds, 'balance.json', init)
        with open('balance.json', 'r') as f:
            file = json.load(f)
            insufMembers = []
            description = f"Confirm bet amount: ```{bet} {spell}```\nConfirm: ✅  | Cancel: ❌"
            for member in members:
                try:
                    file['Balance'][str(member.id)]
                except KeyError:
                    file['Balance'][str(member.id)] = 1000
                    balance = 1000
                else:
                    balance = file['Balance'][str(member.id)]
                if balance < betAmount:
                    insufMembers.append(member)
            if len(insufMembers) != 0:
                description = ""
                if len(insufMembers) != 1:
                    doesSpell = "does"
                else:
                    doesSpell = "do"
                for insuf in insufMembers:
                    description += f"{insuf.mention}, "
                errorEmbed = discord.Embed(title="Insufficient Funds",
                                           description=f"{description[:-2]} {doesSpell} not have enough credits for "
                                                       f"the bet",
                                           color=discord.Color.dark_red())
                await ctx.channel.send(embed=errorEmbed, delete_after=20)
                return

            omEmbed = discord.Embed(title="Old Maid",
                                    description=description,
                                    color=discord.Color.blue())
            message = await ctx.channel.send(embed=omEmbed)
            confirmEmoji = "✅"
            cancelEmoji = "❌"
            await message.add_reaction(confirmEmoji)
            await message.add_reaction(cancelEmoji)

            players = [ctx.author]
            for member in members:
                players.append(member)

            def confirmStart(reaction, user):
                if user in players and reaction.emoji == confirmEmoji:
                    print("True")
                    return True
                if user in players and reaction.emoji == cancelEmoji:
                    print("True Canceled")
                    return True
                else:
                    print("False")
                    return False

            try:
                confirmed = await commands.AutoShardedBot.wait_for(self.client, 'reaction_add', timeout=60,
                                                                   check=confirmStart)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                timeout = discord.Embed(title="Game Timed Out",
                                        description="No bet confirmation from any players",
                                        color=discord.Color.dark_red())
                await message.edit(embed=timeout, delete_after=10)
                return
            else:
                for item in confirmed:
                    if str(item) == '❌':
                        await message.clear_reactions()
                        cancelled = discord.Embed(title="Game Canceled",
                                                  description="Old Maid game was cancelled by a player",
                                                  color=discord.Color.dark_red())
                        await message.edit(embed=cancelled, delete_after=10)
                        break
                    else:
                        await message.clear_reactions()

            gameMembers = []
            for player in players:
                gameMembers.append(Hand(player))
            gameMembers = random.shuffle(gameMembers)
            index = 0

            omEmbed = discord.Embed(title="Old Maid",
                                    color=discord.Color.blue())
            descriptions = ["Distributing cards...", "Removing all pairs in all hands...", "Randomly assigning turn "
                                                                                           "order..."]
            loading = discord.Embed(title="Loading Game",
                                    color=discord.Color.blue())
            loadMessage = await ctx.channel.send(embed=loading)
            await asyncio.sleep(2.0)

            for description in descriptions:
                loading = discord.Embed(title="Loading Game",
                                        description=description,
                                        color=discord.Color.blue())
                await loadMessage.edit(embed=loading)
                await asyncio.sleep(3.0)
            await loadMessage.delete()

            while True:
                user = gameMembers[index].player
                omEmbed.set_author(name=f"{user.display_name}'s Turn",
                                   icon_url=gameMembers[index].player.avatar_url)

                for gameMember in gameMembers:
                    omEmbed.add_field(name=gameMember.player.display_name,
                                      value=emoji_to_game(gameMember),
                                      inline=False)




def setup(client):
    client.add_cog(OldMaid(client))
