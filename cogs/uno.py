import asyncio
import math
from num2words import num2words
import discord
from discord.ext import commands
import random
from random import shuffle, randint
import json
from globalcommands import GlobalCMDS as gcmds

COLORS = ['red', 'yellow', 'green', 'blue']
ALL_COLORS = COLORS + ['black']
NUMBERS = list(range(10)) + list(range(1, 10))
SPECIAL_CARD_TYPES = ['block', 'reverse', '+2']
COLOR_CARD_TYPES = NUMBERS + SPECIAL_CARD_TYPES * 2
BLACK_CARD_TYPES = ['wild', '+4']
CARD_TYPES = NUMBERS + SPECIAL_CARD_TYPES + BLACK_CARD_TYPES


class UnoCard:

    def __init__(self, color, cardtype):
        self.color = color
        self.card_type = cardtype

    def __str__(self):
        return f"{self.color} {self.card_type}"

    def wild_color(self, new_color):
        self.color = new_color


class UnoDeck:

    def __init__(self):
        self.deck = []
        for color in COLORS:
            for card_type in COLOR_CARD_TYPES:
                self.deck.append(UnoCard(color, card_type))
        for btype in BLACK_CARD_TYPES * 4:
            self.deck.append(UnoCard("black", btype))

    def __str__(self):
        return f"Uno Deck: {str(len(self.deck))} cards."

    def shuffle(self):
        shuffle(self.deck)

    def is_empty(self):
        return len(self.deck) == 0

    def deal(self):
        return self.deck.pop()

    def reset(self, pile):
        self.deck = pile.reset_pile()
        shuffle(self.deck)


class UnoPile:

    def __init__(self):
        self.pile = []
        self.path = ""

    def __str__(self):
        return f"Pile: {len(self.pile)} cards"

    def top_card(self):
        return self.pile[-1]

    def place(self, card):
        self.pile.append(card)

    def reset_pile(self):
        newdeck = self.pile
        newdeck.remove(-1)
        self.pile = self.pile[-1]
        return newdeck

    def embed_color(self):
        if self.pile[-1].color == "red":
            return discord.Color.red()
        if self.pile[-1].color == "blue":
            return discord.Color.blue()
        if self.pile[-1].color == "green":
            return discord.Color.green()
        if self.pile[-1].color == "yellow":
            return discord.Color.gold()
        if self.pile[-1].color == "black":
            return discord.Color.darker_grey()

    def top_thumbnail(self):
        top_card = self.pile[-1]
        url = ""
        if top_card.color == "red":
            if top_card.card_type == 0:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903129520177162/0_r.png"
            if top_card.card_type == 1:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903130770079834/1_r.png"
            if top_card.card_type == 2:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903132061925386/2_r.png"
            if top_card.card_type == 3:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903133479600129/3_r.png"
            if top_card.card_type == 4:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903135027560498/4_r.png"
            if top_card.card_type == 5:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903136394903672/5_r.png"
            if top_card.card_type == 6:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903137812316170/6_r.png"
            if top_card.card_type == 7:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903139213213696/7_r.png"
            if top_card.card_type == 8:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903140677025873/8_r.png"
            if top_card.card_type == 9:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903141801099364/9_r.png"
            if top_card.card_type == "block":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903209803612200/block_r.png"
            if top_card.card_type == "+2":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903214475804742/plus2_r.png"
            if top_card.card_type == "reverse":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903217789305003/rev_r.png"
            if top_card.card_type == "wild":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906512671211661/wild.png"
            if top_card.card_type == "+4":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906507730321439/plus4.png"
        if top_card.color == "blue":
            if top_card.card_type == 0:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903614616600576/0_b.png"
            if top_card.card_type == 1:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903618274033824/1_b.png"
            if top_card.card_type == 2:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903621931466822/2_b.png"
            if top_card.card_type == 3:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903625534373958/3_b.png"
            if top_card.card_type == 4:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903629716226119/4_b.png"
            if top_card.card_type == 5:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903633751146706/5_b.png"
            if top_card.card_type == 6:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903638335520788/6_b.png"
            if top_card.card_type == 7:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903642475167814/7_b.png"
            if top_card.card_type == 8:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903646292115456/8_b.png"
            if top_card.card_type == 9:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903650356265050/9_b.png"
            if top_card.card_type == "block":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903705465487410/block_b.png"
            if top_card.card_type == "+2":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903708946628689/plus2_b.png"
            if top_card.card_type == "reverse":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739903711450628256/rev_b.png"
            if top_card.card_type == "wild":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906512671211661/wild.png"
            if top_card.card_type == "+4":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906507730321439/plus4.png"
        if top_card.color == "green":
            if top_card.card_type == 0:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739904049163272382/0_g.png"
            if top_card.card_type == 1:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739904054024470598/1_g.png"
            if top_card.card_type == 2:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739904052950990929/2_g.png"
            if top_card.card_type == 3:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739904054850748536/3_g.png"
            if top_card.card_type == 4:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739904057128255568/4_g.png"
            if top_card.card_type == 5:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739904059330527242/5_g.png"
            if top_card.card_type == 6:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739904061461102652/6_g.png"
            if top_card.card_type == 7:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739904064107708456/7_g.png"
            if top_card.card_type == 8:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739904065747550218/8_g.png"
            if top_card.card_type == 9:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739904072030879786/9_g.png"
            if top_card.card_type == "block":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739905458776703049/block_g.png"
            if top_card.card_type == "+2":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739905462836658197/plus2_g.png"
            if top_card.card_type == "reverse":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739905465076547654/rev_g.png"
            if top_card.card_type == "wild":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906512671211661/wild.png"
            if top_card.card_type == "+4":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906507730321439/plus4.png"
        if top_card.color == "yellow":
            if top_card.card_type == 0:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906035107627058/0_y.png"
            if top_card.card_type == 1:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906040187060234/1_y.png"
            if top_card.card_type == 2:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906044641280050/2_y.png"
            if top_card.card_type == 3:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906048306970725/3_y.png"
            if top_card.card_type == 4:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906053117837342/4_y.png"
            if top_card.card_type == 5:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906056947368036/5_y.png"
            if top_card.card_type == 6:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906061737132072/6_y.png"
            if top_card.card_type == 7:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906066481021049/7_y.png"
            if top_card.card_type == 8:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906070851354735/8_y.png"
            if top_card.card_type == 9:
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906075280539748/9_y.png"
            if top_card.card_type == "block":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906086102106142/block_y.png"
            if top_card.card_type == "+2":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906090023518269/plus2_y.png"
            if top_card.card_type == "reverse":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906094318485665/rev_y.png"
            if top_card.card_type == "wild":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906512671211661/wild.png"
            if top_card.card_type == "+4":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906507730321439/plus4.png"
        if top_card.color == "black":
            if top_card.card_type == "wild":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906512671211661/wild.png"
            if top_card.card_type == "+4":
                url += "https://cdn.discordapp.com/attachments/734962101432615006/739906507730321439/plus4.png"
        return url


class UnoPlayer:

    def __init__(self, member: discord.Member):
        self.hand = []
        self.member = member
        self.name = member.display_name

    def get_hand(self):
        return self.hand

    def seven_draw(self, deck):
        i = 0
        while i < 7:
            self.hand.append(deck.deal())
            deck.shuffle()
            i += 1

    def draw(self, deck):
        card = deck.deal()
        self.hand.append(card)

    def place(self, card, pile):
        self.hand.remove(card)
        pile.place(card)

    def remove_wild(self, card):
        self.hand.remove(card)

    def can_play(self, pile):
        topcard = pile.top_card()
        if topcard.card_type == 'wild':
            for card in self.hand:
                if card.color == topcard.color:
                    return True
        if topcard.color == 'black':
            return True

        else:
            for card in self.hand:
                if card.color == topcard.color or card.card_type == topcard.card_type:
                    return True
                elif card.color == 'black':
                    return True
            return False

    def auto_play(self, pile):
        topcard = pile.top_card()
        for card in self.hand:
            if card.color == topcard.color or card.card_type == topcard.card_type:
                return card

    def is_uno(self):
        if int(len(self.hand)) == 1:
            return True
        else:
            return False


class UnoGame:

    def __init__(self):
        self.index = 0
        self.reversed = False
        self.blocked = False

    def reverse(self):
        self.reversed = not self.reversed

    def block(self):
        self.blocked = not self.blocked

    def set_index(self, playerlist):
        if self.reversed and self.blocked:
            self.index -= 1
            self.block()
        elif self.reversed and not self.blocked:
            self.index -= 1
        elif not self.reversed and self.blocked:
            self.index += 1
            self.block()
        elif not self.reversed and not self.blocked:
            self.index += 1

        if self.index < 0 or self.index >= int(len(playerlist)):
            if self.reversed and self.blocked:
                self.index = int(len(playerlist)) - 1
                self.block()
            elif self.reversed and not self.blocked:
                self.index = int(len(playerlist)) - 1
            elif not self.reversed and self.blocked:
                self.index = 0
                self.block()
            elif not self.reversed and not self.blocked:
                self.index = 0

        return self.index


def emoji_to_player(player: UnoPlayer):
    string = ""
    index = 1
    for card in player.get_hand():
        string += f"{str(index)}. "
        if card.color == "red":
            if card.card_type == 0:
                string += "<:0_r:739620092597370881>"
            if card.card_type == 1:
                string += "<:1_r:739620093109207150>"
            if card.card_type == 2:
                string += "<:2_r:739620093281042492>"
            if card.card_type == 3:
                string += "<:3_r:739620094266572811>"
            if card.card_type == 4:
                string += "<:4_r:739620093956194345>"
            if card.card_type == 5:
                string += "<:5_r:739620094644191272>"
            if card.card_type == 6:
                string += "<:6_r:739620094287544401>"
            if card.card_type == 7:
                string += "<:7_r:739620094392402040>"
            if card.card_type == 8:
                string += "<:8_r:739620094539333692>"
            if card.card_type == 9:
                string += "<:9_r:739620094325424191>"
            if card.card_type == "block":
                string += "<:block_r:739620094317035522>"
            if card.card_type == "+2":
                string += "<:plus2_r:739620094476288060>"
            if card.card_type == "reverse":
                string += "<:rev_r:739620094455578765>"
        if card.color == "blue":
            if card.card_type == 0:
                string += "<:0_b:739620128395755542>"
            if card.card_type == 1:
                string += "<:1_b:739620128190234726>"
            if card.card_type == 2:
                string += "<:2_b:739620128718585856>"
            if card.card_type == 3:
                string += "<:3_b:739620128416727080>"
            if card.card_type == 4:
                string += "<:4_b:739620128244760607>"
            if card.card_type == 5:
                string += "<:5_b:739620128412401684>"
            if card.card_type == 6:
                string += "<:6_b:739620128475447396>"
            if card.card_type == 7:
                string += "<:7_b:739620128320127046>"
            if card.card_type == 8:
                string += "<:8_b:739620128626442371>"
            if card.card_type == 9:
                string += "<:9_b:739620128433373244>"
            if card.card_type == "block":
                string += "<:block_b:739620128550813807>"
            if card.card_type == "+2":
                string += "<:plus2_b:739620128014204960>"
            if card.card_type == "reverse":
                string += "<:rev_b:739620128123125893>"
        if card.color == "green":
            if card.card_type == 0:
                string += "<:0_g:739620167956430958>"
            if card.card_type == 1:
                string += "<:1_g:739620167700578412>"
            if card.card_type == 2:
                string += "<:2_g:739620167717224470>"
            if card.card_type == 3:
                string += "<:3_g:739620168199700591>"
            if card.card_type == 4:
                string += "<:4_g:739620167897579571>"
            if card.card_type == 5:
                string += "<:5_g:739620168212414464>"
            if card.card_type == 6:
                string += "<:6_g:739620167725613098>"
            if card.card_type == 7:
                string += "<:7_g:739620167541194803>"
            if card.card_type == 8:
                string += "<:8_g:739620167692320801>"
            if card.card_type == 9:
                string += "<:9_g:739620167918813375>"
            if card.card_type == "block":
                string += "<:block_g:739620168019476561>"
            if card.card_type == "+2":
                string += "<:plus2_g:739620167973077002>"
            if card.card_type == "reverse":
                string += "<:rev_g:739620168048705656>"
        if card.color == "yellow":
            if card.card_type == 0:
                string += "<:0_y:739626572675416245>"
            if card.card_type == 1:
                string += "<:1_y:739626572444598322>"
            if card.card_type == 2:
                string += "<:2_y:739626572461375520>"
            if card.card_type == 3:
                string += "<:3_y:739626572734267462>"
            if card.card_type == 4:
                string += "<:4_y:739626572184813700>"
            if card.card_type == 5:
                string += "<:5_y:739626572759302324>"
            if card.card_type == 6:
                string += "<:6_y:739626572767821824>"
            if card.card_type == 7:
                string += "<:7_y:739626572457443429>"
            if card.card_type == 8:
                string += "<:8_y:739626572499124355>"
            if card.card_type == 9:
                string += "<:9_y:739626572931268640>"
            if card.card_type == "block":
                string += "<:block_y:739626573103366154>"
            if card.card_type == "+2":
                string += "<:plus2_y:739626572692062338>"
            if card.card_type == "reverse":
                string += "<:rev_y:739626572616564797>"
        if card.color == "black":
            if card.card_type == "wild":
                string += "<:wild:739620056551653537>"
            if card.card_type == "+4":
                string += "<:plus4:739620056446795946>"
        string += f" `[{card.color} {card.card_type}]`\n"
        index += 1
    return string


def emoji_to_game(player: UnoPlayer):
    string = "<:unoback:739620076180865062>"
    return string * int(len(player.hand))


def win(player: UnoPlayer):
    load = False
    success = False
    init = {'Uno': {}}
    gcmds.json_load(gcmds, 'gamestats.json', init)
    with open('gamestats.json', 'r') as f:
        file = json.load(f)
        while not load:
            try:
                file['Uno'][str(player.member.id)]['win']
            except KeyError:
                if not success:
                    try:
                        file['Uno'][str(player.member.id)]
                    except KeyError:
                        try:
                            file['Uno']
                        except KeyError:
                            file['Uno'] = {}
                        file['Uno'][str(player.member.id)] = {}
                        success = True
                file['Uno'][str(player.member.id)]['win'] = 0
            else:
                file['Uno'][str(player.member.id)]['win'] += 1
                load = True
        with open('gamestats.json', 'w') as f:
            json.dump(file, f, indent=4)
    gcmds.ratio(gcmds, player.member, 'gamestats.json', 'Uno')


def lose(player: UnoPlayer):
    load = False
    success = False
    init = {'Uno': {}}
    gcmds.json_load(gcmds, 'gamestats.json', init)
    with open('gamestats.json', 'r') as f:
        file = json.load(f)
        while not load:
            try:
                file['Uno'][str(player.member.id)]['lose']
            except KeyError:
                if not success:
                    try:
                        file['Uno'][str(player.member.id)]
                    except KeyError:
                        try:
                            file['Uno']
                        except KeyError:
                            file['Uno'] = {}
                        file['Uno'][str(player.member.id)] = {}
                        success = True
                file['Uno'][str(player.member.id)]['lose'] = 0
            else:
                file['Uno'][str(player.member.id)]['lose'] += 1
                load = True
        with open('gamestats.json', 'w') as f:
            json.dump(file, f, indent=4)
    gcmds.ratio(gcmds, player.member, 'gamestats.json', 'Uno')


class UNO(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" has been loaded')

    @commands.command()
    async def uno(self, ctx, members: commands.Greedy[discord.Member] = None):
        await gcmds.invkDelete(gcmds, ctx)

        if members is None:
            noPlayers = discord.Embed(title="No Opponents",
                                      description=f"{ctx.author.mention}, please mention other players to start a game",
                                      color=discord.Color.dark_red())
            await ctx.channel.send(embed=noPlayers, delete_after=10)
            return
        elif members:
            if int(len(members)) > 9:
                tooMany = discord.Embed(title="Too Many Opponents",
                                        description=f"{ctx.author.mention}, please mention up to 9 other players to "
                                                    f"start a game",
                                        color=discord.Color.dark_red())
                await ctx.channel.send(embed=tooMany, delete_after=10)
                return
            for player in members:
                if ctx.author == player:
                    noSelf = discord.Embed(title="Invalid Opponent Selection",
                                           description=f"{ctx.author.mention}, you cannot mention yourself as an "
                                                       f"opponent",
                                           color=discord.Color.dark_red())
                    await ctx.channel.send(embed=noSelf, delete_after=10)
                    return

        playerlist = [ctx.author]
        for member in members:
            playerlist.append(member)

        description = "Uno game between: "

        for desc in playerlist:
            description += f"{desc.mention}, "

        unoEmbed = discord.Embed(title="Uno",
                                 description=description[:-2],
                                 color=discord.Color.blue())
        orig_embed = await ctx.channel.send(file=None, embed=unoEmbed)
        await asyncio.sleep(5.0)

        deck = UnoDeck()
        deck.shuffle()
        pile = UnoPile()
        pile.place(deck.deal())

        gameMembers = []
        index = 0
        for player in playerlist:
            gameMembers.append(UnoPlayer(player))
            gameMembers[index].seven_draw(deck)
            index += 1
        shuffle(gameMembers)

        index = 0
        game = UnoGame()
        placement = []
        special_count = 0
        turns_to_win = 0
        turn_count = 0

        try:
            while True:
                turns_to_win += 1
                turn_count += 1
                user = gameMembers[index].member
                uno = discord.Embed(title="Uno",
                                    description=f"Turns Played: {turn_count}",
                                    color=pile.embed_color())
                if placement:
                    p_index = 0
                    uno.set_author(name=f"👑 {placement[0].member.display_name} wins!",
                                   icon_url=placement[0].member.avatar_url)
                    for p in placement:
                        uno.add_field(name=f"{num2words(int(p_index + 1), to='ordinal_num')} Place:",
                                      value=f"{p.member.mention}",
                                      inline=False)
                        p_index += 1
                if not gameMembers:
                    uno.set_thumbnail(url=pile.top_thumbnail())
                    await orig_embed.edit(embed=uno)
                    break
                elif int(len(gameMembers)) < 2:
                    uno.add_field(name="Last Place:",
                                  value=f"{gameMembers[0].member.mention}",
                                  inline=False)
                    await orig_embed.edit(embed=uno)
                    placement.append(gameMembers[0])
                    break
                for gameMember in gameMembers:
                    if gameMember.member.id == user.id:
                        uno.add_field(name=f"{gameMember.name} 🟢",
                                      value=emoji_to_game(gameMember),
                                      inline=False)
                    else:
                        uno.add_field(name=gameMember.name,
                                      value=emoji_to_game(gameMember),
                                      inline=False)
                uno.set_thumbnail(url=pile.top_thumbnail())
                uno.set_author(name=f"{user.display_name}'s turn",
                               icon_url=user.avatar_url)
                await orig_embed.edit(embed=uno)

                if pile.top_card().card_type == "block" and special_count == 0:
                    game.block()
                    uno.set_footer(text=f"{user.display_name} was blocked! Skipping turn...")
                    bully = discord.Embed(title="HA YOU GOT BLOCKED LOL",
                                          description=f"{user.mention} imagine getting bullied by a bot...",
                                          color=discord.Color.dark_red())
                    bully.set_thumbnail(url="https://media.tenor.com/images/2c4d4cad3406cc58b96280d6a8be3c98/tenor.gif")
                    await user.send(embed=bully)

                    await orig_embed.edit(embed=uno)
                    index = game.set_index(gameMembers)
                    special_count = 1
                    await asyncio.sleep(3.0)
                    continue
                if pile.top_card().card_type == "reverse" and special_count == 0:
                    game.reverse()
                    uno.set_footer(text="Turn rotation order was reversed!")
                    bully = discord.Embed(title="NICE TURN LOL",
                                          description=f"{user.mention}, no turn for you hehe :)",
                                          color=discord.Color.dark_red())
                    bully.set_thumbnail(url="https://i.pinimg.com/originals/56/3d/72/563d72539bbd9fccfbb427cfefdee05a"
                                            ".png")
                    await user.send(embed=bully)
                    await orig_embed.edit(embed=uno)
                    if int(len(gameMembers)) != 2:
                        for _ in range(2):
                            index = game.set_index(gameMembers)
                    else:
                        index = game.set_index(gameMembers)
                    special_count = 1
                    await asyncio.sleep(3.0)
                    continue
                if pile.top_card().card_type == "+2" and special_count == 0:
                    i = 0
                    uno.set_footer(text=f"{user.display_name} is drawing 2 cards and will have their turn skipped...")
                    bully = discord.Embed(title="You're Actually Just Bad at the Game",
                                          description=f"{user.mention}, at least it wasn't a `+4`...",
                                          color=discord.Color.dark_red())
                    bully.set_thumbnail(url="https://images.squarespace-cdn.com/content/v1/5a01e930e5dd5bc02c923380"
                                            "/1562183286399-8WCGCUPVA711FOT47134"
                                            "/ke17ZwdGBToddI8pDm48kCtmdKdgAsruTpHwXjl_sP57gQa3H78H3Y0txjaiv_0fDoOvxcdMm"
                                            "MKkDsyUqMSsMWxHk725yiiHCCLfrh8O1z5QPOohDIaIeljMHgDF5CVlOqpeNLcJ80NK65_fV7S"
                                            "1UbdmNwkhqNrL_bbPxyPyPGuzrAAY8ajaVMZ62lb7SCEndyCkb1b6Zgi5IDAmkjIgAQ/%232+"
                                            "June+19.jpg?format=2500w")
                    await user.send(embed=bully)
                    await orig_embed.edit(embed=uno)
                    while i < 2:
                        gameMembers[index].draw(deck)
                        i += 1
                    index = game.set_index(gameMembers)
                    special_count = 1
                    await asyncio.sleep(3.0)
                    continue
                if pile.top_card().card_type == "+4" and special_count == 0:
                    i = 0
                    bully = discord.Embed(title="Might as Well Quit Now",
                                          description=f"{user.mention} just got rekt",
                                          color=discord.Color.dark_red())
                    bully.set_thumbnail(url="https://i.ytimg.com/vi/8bdwR_qrzm0/maxresdefault.jpg")
                    await user.send(embed=bully)
                    uno.set_footer(text=f"{user.display_name} is drawing 4 cards and will have their turn skipped...")
                    await orig_embed.edit(embed=uno)
                    while i < 4:
                        gameMembers[index].draw(deck)
                        i += 1
                    index = game.set_index(gameMembers)
                    special_count = 1
                    await asyncio.sleep(3.0)
                    continue

                if not gameMembers[index].can_play(pile):
                    DM = discord.Embed(title=user.display_name,
                                       description=f"*no playable cards in hand, drawing a card...*"
                                                   f"\n{emoji_to_player(gameMembers[index])}",
                                       color=pile.embed_color())
                    DM.set_thumbnail(url=pile.top_thumbnail())
                    dm_message = await user.send(embed=DM)
                    uno.set_footer(text=f"{user.display_name} is drawing a card...")
                    await orig_embed.edit(embed=uno)
                    await asyncio.sleep(3.0)

                    gameMembers[index].draw(deck)

                    if not gameMembers[index].can_play(pile):
                        DM = discord.Embed(title=user.display_name,
                                           description=f"*no playable cards in hand. You have ended your turn."
                                                       f"\n{emoji_to_player(gameMembers[index])}",
                                           color=pile.embed_color())
                        DM.set_thumbnail(url=pile.top_thumbnail())
                        uno.set_footer(text=f"{user.display_name} cannot place a valid card. Ending turn...")
                        await dm_message.edit(embed=DM)
                        await orig_embed.edit(embed=uno)
                        index = game.set_index(gameMembers)
                        await asyncio.sleep(3.0)
                        continue
                    else:
                        await dm_message.delete()

                DM = discord.Embed(title=user.display_name,
                                   description=f"*to pick a card, type in the number the card is in the order of cards "
                                               f"in the channel that contains the main UNO game within 60 seconds*\n"
                                               f"\n{emoji_to_player(gameMembers[index])}",
                                   color=pile.embed_color())
                DM.set_thumbnail(url=pile.top_thumbnail())
                dm_message = await user.send(embed=DM)
                uno.set_footer(text=f"{user.display_name} is picking a card to place...")
                await orig_embed.edit(embed=uno)

                def from_player(message):
                    if message.author == user and message.channel == ctx.channel:
                        return True
                    else:
                        return False

                loop = True

                while loop:
                    try:
                        choice = await self.client.wait_for('message', timeout=60,
                                                                        check=from_player)
                    except asyncio.TimeoutError:
                        played_card = gameMembers[index].auto_play(pile)
                        gameMembers[index].place(played_card, pile)
                        DM = discord.Embed(title=user.display_name,
                                           description=f"*you did not pick a card within 60 seconds, so a valid card "
                                                       f"has been selected for you*"
                                                       f"\n\nYou placed: {played_card.__str__()}",
                                           color=pile.embed_color())
                        DM.set_thumbnail(url=pile.top_thumbnail())
                        await dm_message.edit(embed=DM)
                        if not gameMembers[index].hand:
                            placement.append(gameMembers[index])
                            gameMembers.pop(index)
                        index = game.set_index(gameMembers)
                        special_count = 0
                        await asyncio.sleep(3.0)
                        loop = False
                    else:
                        try:
                            if choice.content == "cancel":
                                await choice.delete()
                                cancelEmbed = discord.Embed(title="Uno Game Canceled",
                                                            description=f"The current uno game was canceled by {user.mention}",
                                                            color=discord.Color.dark_red())
                                await orig_embed.edit(embed=cancelEmbed)
                                loop = False
                                return
                            else:
                                int_choice = int(choice.content)
                        except (ValueError, IndexError):
                            pass
                        else:
                            if 0 < int_choice <= (int(len(gameMembers[index].hand))):
                                await choice.delete()
                                hand = gameMembers[index].get_hand()

                                try:
                                    played_card = hand[int_choice - 1]
                                except IndexError:
                                    not_int = discord.Embed(title="Not a Valid Selection",
                                                            description=f"{user.mention}, {choice.content} is not a "
                                                                        f"valid selection. Please try again.",
                                                            color=discord.Color.dark_red())
                                    await ctx.channel.send(embed=not_int, delete_after=5)
                                else:
                                    played_card = hand[int_choice - 1]

                                if played_card.color != pile.top_card().color:
                                    if played_card.card_type != pile.top_card().card_type:
                                        if pile.top_card().color != 'black':
                                            if played_card.color != 'black':
                                                not_match = discord.Embed(title="Not a Valid Selection",
                                                                          description=f"{user.mention}, {choice.content} is not a "
                                                                                      f"valid selection. Please try again.",
                                                                          color=discord.Color.dark_red())
                                                await ctx.channel.send(embed=not_match, delete_after=5)
                                                break

                                if played_card.color == 'black':
                                    played_card_original = played_card
                                    reaction_confirmed = False
                                    red = "🟥"
                                    blue = "🟦"
                                    green = "🟩"
                                    yellow = "🟨"
                                    rlist = [red, blue, green, yellow]
                                    choose_color = discord.Embed(title="What color will the card be?",
                                                                 description="*react to choose the "
                                                                             "color in 20 seconds*"
                                                                             "\nRed: 🟥\nBlue: 🟦\nGreen: "
                                                                             "🟩\nYellow: 🟨\n")
                                    color_choice = await ctx.channel.send(embed=choose_color)
                                    await color_choice.add_reaction(red)
                                    await color_choice.add_reaction(blue)
                                    await color_choice.add_reaction(green)
                                    await color_choice.add_reaction(yellow)

                                    def check(reaction, game_player):
                                        if game_player == user and reaction.emoji in rlist:
                                            return True

                                    while not reaction_confirmed:
                                        try:
                                            choice_check = await self.client.wait_for('reaction_add',
                                                                                       timeout=20.0,
                                                                                       check=check)
                                        except asyncio.TimeoutError:
                                            await color_choice.clear_reactions()
                                            color = random.choice(rlist)
                                        else:
                                            for item in choice_check:
                                                if isinstance(item, discord.Reaction):
                                                    if str(item) in rlist:
                                                        color = item
                                            await color_choice.remove_reaction(color, user)

                                        if str(color) == str(red):
                                            played_card.wild_color("red")
                                        if str(color) == str(blue):
                                            played_card.wild_color("blue")
                                        if str(color) == str(green):
                                            played_card.wild_color("green")
                                        if str(color) == str(yellow):
                                            played_card.wild_color("yellow")
                                        reaction_confirmed = True

                                    gameMembers[index].remove_wild(played_card_original)
                                    pile.place(played_card)

                                    wildEmbed = discord.Embed(title="Card Color Set",
                                                              description=f"The card's color is now {played_card.color}",
                                                              color=pile.embed_color())
                                    await color_choice.edit(embed=wildEmbed, delete_after=60)
                                    DM = discord.Embed(title=user.display_name,
                                                       description=f"\n\nYou placed: {played_card.__str__()}",
                                                       color=pile.embed_color())
                                    DM.set_thumbnail(url=pile.top_thumbnail())
                                    await dm_message.edit(embed=DM)
                                    special_count = 0

                                    if not gameMembers[index].hand:
                                        placement.append(gameMembers[index])
                                        gameMembers.remove(gameMembers[index])
                                        index = game.set_index(gameMembers)
                                        await asyncio.sleep(2.0)
                                        break

                                    await asyncio.sleep(2.0)
                                    break
                                else:
                                    gameMembers[index].place(played_card, pile)
                                    DM = discord.Embed(title=user.display_name,
                                                       description=f"\n\nYou placed: {played_card.__str__()}",
                                                       color=pile.embed_color())
                                    DM.set_thumbnail(url=pile.top_thumbnail())
                                    await dm_message.edit(embed=DM)
                                    special_count = 0

                                    try:
                                        await color_choice.delete()
                                    except (UnboundLocalError, discord.NotFound):
                                        pass

                                    if not gameMembers[index].hand:
                                        placement.append(gameMembers[index])
                                        gameMembers.remove(gameMembers[index])
                                        index = game.set_index(gameMembers)
                                        await asyncio.sleep(2.0)
                                        break

                                    await asyncio.sleep(2.0)
                                    loop = False

                            else:
                                await choice.delete()
                                not_int = discord.Embed(title="Not a Valid Selection",
                                                        description=f"{user.mention}, {choice.content} is not a "
                                                                    f"valid selection. Please try again.",
                                                        color=discord.Color.dark_red())
                                await ctx.channel.send(embed=not_int, delete_after=5)
        except discord.NotFound:
            cancelEmbed = discord.Embed(title="Uno Game Canceled",
                                        description="The original game message was deleted",
                                        color=discord.Color.dark_red())
            await ctx.channel.send(embed=cancelEmbed, delete_after=30)
            return

        init = {'Balance': {}}
        gcmds.json_load(gcmds, 'balance.json', init)
        with open('balance.json', 'r') as f:
            file = json.load(f)

            try:
                file['Balance'][str(placement[0].member.id)]
            except KeyError:
                file['Balance'][str(placement[0].member.id)] = 1000
                initEmbed = discord.Embed(title="Initialised Credit Balance",
                                          description=f"{ctx.author.mention}, you have been credited `1000` credits "
                                                      f"to start!\n\nCheck your current"
                                                      f" balance using `{gcmds.prefix(gcmds, ctx)}balance`",
                                          color=discord.Color.blue())
                initEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/734962101432615006"
                                            "/738390147514499163/chips.png")
                await ctx.channel.send(embed=initEmbed, delete_after=10)
                balance = file['Balance'][str(placement[0].member.id)]
            else:
                balance = file['Balance'][str(placement[0].member.id)]

            if turns_to_win > 300:
                award_amount = int(math.floor(randint(10, 100) * turns_to_win / randint(2, 20)))
            else:
                award_amount = int(math.floor(randint(1, 10) * turns_to_win / randint(2, 5)))
            balance += award_amount
            with open('balance.json', 'w') as g:
                json.dump(file, g, indent=4)

        rewardEmbed = discord.Embed(title="Winnings",
                                    description=f"{placement[0].member.mention}, you won ```{award_amount} credits!```",
                                    color=discord.Color.blue())
        await ctx.channel.send(embed=rewardEmbed)

        win(placement[0])
        lose(placement[-1])
        gcmds.incrCounter(gcmds, ctx, 'uno')
        return


def setup(client):
    client.add_cog(UNO(client))
