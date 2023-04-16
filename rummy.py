import sys
from os import path
from random import shuffle, choice
from copy import deepcopy
from threading import Thread
from itertools import combinations
from collections import defaultdict
import pygame
from enums import Suits, Ranks, Scores, Moves, States
from ISMCTS import ISMCTS

resolution = (1280, 720)
#resolution = (1920, 1080)

class Card():

    def __init__(self, suit, rank, score, front, back):
        self.suit = suit
        self.rank = rank
        self.score = score
        self.back = back
        self.front = front
        self.sprite = pygame.sprite.Sprite()
        self.sprite.image = front.copy()
        self.sprite.rect = self.sprite.image.get_rect()
        self.drop_pos = [0, 0]
        self.snapped_pos = [0, 0]
        self.selected = False
        self.detached = False
        self.fixed = False
        self.hidden = False

    def __eq__(self, other):
        return isinstance(other, Card) and self.suit == other.suit and self.rank == other.rank

    def __hash__(self):
        return hash((self.suit, self.rank))

    def __repr__(self):
        #return Ranks(self.rank).name + ' OF ' + Suits(self.suit).name
        return Ranks(self.rank).name + ' OF ' + str(self.suit)

    def __deepcopy__(self, _):
        new = Card.__new__(Card)
        new.suit = self.suit
        new.rank = self.rank
        return new

    def animate(self, destination, speed):
        self.drop_pos[0] += (destination[0] - self.drop_pos[0]) * speed / 10
        self.drop_pos[1] += (destination[1] - self.drop_pos[1]) * speed / 10   
        self.sprite.rect.x = round(self.drop_pos[0])
        self.sprite.rect.y = round(self.drop_pos[1])

    def update(self, index, length, hand=False):
        self.sprite.image = self.front
        if self.hidden:
            self.sprite.image = self.back
            self.animate((500, -300), 1)
        else:
            self.sprite.image = self.front
        if hand:
            self.snapped_pos = (resolution[0]//2 - (length / 2) * (self.sprite.rect.width - 35) 
                            + index * (self.sprite.rect.width - 35) - self.sprite.rect.width / 8, 
                            resolution[1] - self.sprite.rect.height)
            if self.detached: 
                self.sprite.rect.x = self.drop_pos[0]
                self.sprite.rect.y = self.drop_pos[1]
            elif self.selected:
                self.animate((self.drop_pos[0], self.snapped_pos[1] - 30), 1)
            else:
                self.animate(self.snapped_pos, 1)


class Hand():

    def __init__(self):
        self.cards = []
        self.known_cards = set()
        self.group = pygame.sprite.OrderedUpdates()
        self.possible_melds = []
        self.possible_layoffs = []
        self.swapped_joker = 0
        self.sorted = False
        self.computers = False

    def __deepcopy__(self, _):
        new = Hand.__new__(Hand)
        new.cards = deepcopy(self.cards)
        new.known_cards = deepcopy(self.known_cards)
        new.possible_melds = []
        new.possible_layoffs = []
        new.swapped_joker = self.swapped_joker
        return new

    def add_card(self, card):
        self.cards.append(card)

    def sort_by_rank(self):
        self.cards.sort(key = lambda card: (card.rank, card.suit))

    def sort_by_suit(self):
        self.cards.sort(key = lambda card: (card.suit, card.rank))

    def discard(self, card):
        return self.cards.pop(self.cards.index(card))

    def calculate_score(self):
        return sum(card.score for card in self.cards)

    def find_card(self, card):
        return next(c for c in self.cards if c.suit == card.suit and c.rank == card.rank)

    def find_melds(self):
        self.possible_melds = []
        ranks = defaultdict(set)
        suits = defaultdict(list)
        self.sort_by_suit()
        for card in self.cards:
            ranks[card.rank].add(card)
            suits[card.suit].append(card)
        joker = None
        if Ranks.JOKER in ranks:
            joker = ranks[Ranks.JOKER].pop()
            del suits[4]
        for _, cards in suits.items():
            for i, first_card in enumerate(cards):
                for j, last_card in enumerate(cards[i+1:]):
                    if first_card.rank + j + 1 == last_card.rank:
                        if joker and j > 0:
                            self.possible_melds.append([joker] + cards[i:i+j+1])
                            self.possible_melds.append(cards[i:i+j+1] + [joker])
                        if j > 1:
                            self.possible_melds.append(cards[i:i+j+1])
                    elif joker and first_card.rank + j + 2 == last_card.rank:
                        for k, card in enumerate(cards[i+1:]):
                            if card.rank != first_card.rank + 1:
                                break
                        self.possible_melds.append(cards[i:i+k+1] + [joker] + cards[i+k+1:i+j+2])
        for _, cards in ranks.items():
            if len(cards) >= 3:
                for meld in combinations(cards, 3):
                    self.possible_melds.append(meld)
                    if joker:
                        self.possible_melds.append(list(meld) + [joker])
                if len(cards) == 4:
                    self.possible_melds.append(cards)

    def find_layoffs(self, melds):
        self.possible_layoffs = [(m, card) for m, meld in enumerate(melds[:-1]) 
                                 for card in self.cards 
                                 if meld.layoff_possible(card)]

    def update(self):
        self.group.empty()
        for index, card in enumerate(self.cards):
            self.group.add(card.sprite)
            if self.computers:
                card.hidden = True
                card.update(index, len(self.cards))
            else:
                card.hidden = False
                card.update(index, len(self.cards), True)
                     

class Deck():

    def __init__(self, images):
        self.cards = []
        self.sprite = pygame.sprite.Sprite()
        self.sprite.image = images[0]
        self.sprite.rect = self.sprite.image.get_rect(center=(80, 100))
        self.generate(images)
        self.shuffle()

    def __deepcopy__(self, _):
        new = Deck.__new__(Deck)
        new.cards = deepcopy(self.cards)
        return new

    def generate(self, images):
        num = 1
        for suit in Suits:
            for rank in range(Ranks.TWO, Ranks.JOKER):
                self.cards.append(Card(suit, rank, Scores[Ranks(rank).name], images[num], images[0]))
                num+=1
        self.cards.append(Card(4, Ranks.JOKER, Scores.JOKER, images[53], images[0]))
        self.cards.append(Card(4, Ranks.JOKER, Scores.JOKER, images[53], images[0]))

    def shuffle(self):
        shuffle(self.cards)

    def deal(self):
        return self.cards.pop()


class Pile():

    def __init__(self):
        self.cards = []
        self.group = pygame.sprite.OrderedUpdates()
        self.group.rect = pygame.Rect(18, 200, 125, 176)

    def __deepcopy__(self, _):
        new = Pile.__new__(Pile)
        new.cards = deepcopy(self.cards)
        return new

    def deal(self):
        return self.cards.pop()

    def put(self, card):
        self.cards.append(card)

    def update(self):
        self.group.empty()
        for card in self.cards[-2:]:
            card.hidden = False
            self.group.add(card.sprite)
            card.update(0, 0)
            card.animate((18, 200), 1.5)


class Meld():

    def __init__(self):
        self.cards = []
        self.group = pygame.sprite.OrderedUpdates()
        self.group.rect = pygame.Rect((170, 60), (125, 181))
        self.is_run = False
        self.rank = None
        self.suit = None

    def __deepcopy__(self, _):
        new = Meld.__new__(Meld)
        new.cards = deepcopy(self.cards)
        new.is_run = self.is_run
        new.rank = self.rank
        new.suit = self.suit
        return new

    def put_front(self, card):
        self.cards.append(card)
        if self.is_valid_run() or self.is_valid_set():
            return True
        self.cards.pop()
        return False

    def put_back(self, card):
        self.cards.insert(0, card)
        if self.is_valid_run() or self.is_valid_set():
            return True
        self.cards.pop(0)
        return False

    def deal(self):
        for card in reversed(self.cards):
            if not card.fixed:
                return self.cards.pop(self.cards.index(card))
        return None

    def swap_joker(self, Card):
        for i, card in enumerate(self.cards):
            if card.rank == Ranks.JOKER and card.fixed and Card.rank != Ranks.JOKER:
                temp = self.cards[i]
                self.cards[i] = Card
                if not (self.is_valid_run() or self.is_valid_set()):
                    self.cards[i] = temp
                    continue
                self.cards[i].fixed = True
                temp.fixed = False
                return temp
        return None

    def layoff_possible(self, card):
        if self.is_run:
            return (self.suit == card.suit
            and ((card.rank == self.cards[-1].rank + 1 or card.rank == self.cards[0].rank - 1)
            or card.rank == Ranks.JOKER and (self.cards[0].rank >= Ranks.TWO or self.cards[-1].rank <= Ranks.ACE)
            or (self.cards[0].rank == Ranks.JOKER or self.cards[-1].rank == Ranks.JOKER) 
            and (card.rank == self.cards[-2].rank + 2 or card.rank == self.cards[1].rank - 2)))
        else: 
            return self.rank == card.rank

    def is_valid_run(self):
        self.suit = self.cards[0].suit
        self.rank = None
        size = len(self.cards)
        if size > 1:
            if self.cards[0].rank == Ranks.JOKER:
                self.suit = self.cards[1].suit
            if self.cards[-2].rank == Ranks.ACE:
                return False
        if any(card.suit != self.suit 
               and card.rank != Ranks.JOKER 
               for card in self.cards):
            return False
        if any(self.cards[i+1].rank != card.rank + 1 
               and self.cards[i+1].rank != Ranks.JOKER 
               and card.rank != Ranks.JOKER 
               for i, card in enumerate(self.cards[:-1])):
            return False
        if size > 2 and self.cards[0].rank != Ranks.JOKER:
            for i, card in enumerate(self.cards[:-1]):
                if (card.rank == Ranks.JOKER 
                    and self.cards[i+1].rank != self.cards[i-1].rank + 2):
                    return False
        if any(card.rank == Ranks.JOKER 
               and self.cards[i+1].rank == Ranks.JOKER 
               for i, card in enumerate(self.cards[:-1])):
            return False
        if size < 4 and sum(1 for card in self.cards if card.rank == Ranks.JOKER) > 1:
            return False
        self.is_run = True
        return True

    def is_valid_set(self):
        self.rank = self.cards[0].rank
        self.suit = None
        size = len(self.cards)
        if self.cards[0].rank == Ranks.JOKER and size > 1:
            self.rank = self.cards[1].rank
        if any(card.rank != self.rank and card.rank != Ranks.JOKER for card in self.cards):
            return False
        if size < 4 and sum(1 for card in self.cards if card.rank == Ranks.JOKER) > 1:
            return False
        if size > 4:
            return False
        self.is_run = False
        return True

    def update(self):
        self.group.empty()
        for index, card in enumerate(self.cards):
            card.sprite.kill()
            self.group.add(card.sprite)
            card.update(0, 0)
            card.hidden = False
            card.animate((self.group.rect.topleft[0]+index*28, self.group.rect.topleft[1]), 3)
        if self.cards:
            self.group.rect.width = 125+(len(self.cards)-1)*28
       
            
class Player():

    def __init__(self):
        self.hand = Hand()
        self.score = 0
        self.selected_card = None

    def __deepcopy__(self, _):
        new = Player.__new__(Player)
        new.hand = deepcopy(self.hand)
        new.score = self.score
        return new

    def draw_deck(self, deck):
        if deck.cards and self.hand.add_card(deck.deal()):
            return True
        return False

    def draw_pile(self, pile):
        if pile.cards:
            card = pile.deal()
            self.hand.add_card(card)
            self.hand.known_cards.add(card)
            return True
        return False

    def select_card(self, mouse_pos):
        last = len(self.hand.group.sprites()) - 1
        for i, card in enumerate(self.hand.cards):
            if i == last:
                overlapped_rect = pygame.Rect((card.sprite.rect.left, card.sprite.rect.top), 
                                              (card.sprite.rect.width, card.sprite.rect.height))
            else:
                overlapped_rect = pygame.Rect((card.sprite.rect.left, card.sprite.rect.top), 
                                              (card.sprite.rect.width - 35, card.sprite.rect.height))
            if overlapped_rect.collidepoint(mouse_pos) and self.selected_card == None:
                card.selected = True
                self.selected_card = card
                card.rel_pos = (card.sprite.rect.x - mouse_pos[0], card.sprite.rect.y - mouse_pos[1] - 30)
                return

    def discard_card(self, card, pile):
        if card in self.hand.cards:
            pile.put(self.hand.discard(card))

    def add_to_meld(self, meld, card, back=False):
        if not back and meld.put_front(card) or meld.put_back(card):
            if card.rank == Ranks.JOKER and self.hand.swapped_joker:
                self.hand.swapped_joker -= 1
            self.hand.discard(card)
            return True
        return False

    def swap_joker(self, meld, card):
        if card in self.hand.cards:
            joker = meld.swap_joker(card)
            if joker:
                self.hand.discard(card)
                self.hand.add_card(joker)
                self.hand.swapped_joker += 1
                return True
        return False

    def sort_hand(self):
        if self.hand.sorted:
            self.hand.sort_by_suit()
            self.hand.sorted = False
        else:
            self.hand.sort_by_rank()
            self.hand.sorted = True

    def move_card(self, mouse_pos, game_state, is_players_turn):
        posx = mouse_pos[0] + self.selected_card.rel_pos[0]
        first = resolution[0]/2 - (len(self.hand.cards) / 2 + 1) * 80
        last = resolution[0]/2 + (len(self.hand.cards) / 2) * 80
        if posx > first and posx < last:
            self.selected_card.drop_pos[0] = posx
        for card in self.hand.cards:
            cropped_rect = pygame.Rect((card.snapped_pos[0], card.snapped_pos[1]), 
                                       (card.sprite.rect.width - 60, card.sprite.rect.height))
            if cropped_rect.collidepoint(self.selected_card.sprite.rect.center):
                i, j = self.hand.cards.index(self.selected_card), self.hand.cards.index(card)
                self.hand.cards.insert(j, self.hand.cards.pop(i))
                break
        if (game_state == States.DISCARD or game_state == States.LAY_OFF or game_state == States.MELD) and is_players_turn:
            self.selected_card.detached = True
            self.selected_card.drop_pos[0] = mouse_pos[0] + self.selected_card.rel_pos[0]
            self.selected_card.drop_pos[1] = mouse_pos[1] + self.selected_card.rel_pos[1]


class Button(pygame.sprite.Sprite):

    def __init__(self, pos, surface):
        super().__init__()
        self.pos = pos
        self.image = surface
        self.rect = self.image.get_rect()
        self.clicked = False

    def update(self):
        if self.clicked:
            self.rect.y = self.pos[1] + 2
        else:
           self.rect.x, self.rect.y = self.pos

class Game():

    def __init__(self):
        self.screen = pygame.display.set_mode(resolution)
        self.font = pygame.font.SysFont(None, 50)
        self.images = self.load_images()
        self.deck = Deck(self.images)
        self.player = Player()
        self.computer = Player()
        self.computer.hand.computers = True
        self.search = ISMCTS()
        self.state = States.MENU
        self.current_player = None
        self.pile = Pile()
        self.sort_button = Button((25, resolution[1]-135), self.images['sort'])
        self.melds = []
        self.sprites_all = pygame.sprite.Group(self.deck.sprite, self.sort_button)
        self.melds_valid = True
        self.joker_swapping_finished = True
        self.reshuffles = 0

    def load_images(self):
        base_path = getattr(sys, '_MEIPASS', path.dirname(path.abspath(__file__))) 
        pygame.display.set_icon(pygame.image.load(path.join(base_path, 'images', 'rummy.ico')))
        images = {i: pygame.image.load(path.join(base_path, 'images', f'{i}.png')).convert_alpha() 
                  for i in range(54)}
        for i, image in images.items():
            images[i] = pygame.transform.scale(image, (int(image.get_width()/4), int(image.get_height()/4)))
        images['sort'] = (pygame.image.load(path.join(base_path, 'images', 'sort.png')).convert_alpha())
        images['sort'] = pygame.transform.scale(images['sort'], (int(images['sort'].get_width()/7), int(images['sort'].get_height()/7)))
        return images

    def deal_cards(self):
        for i in range(10):
            self.player.hand.add_card(self.deck.deal())
            self.computer.hand.add_card(self.deck.deal())

    def get_computers_move(self):
        if not self.is_players_turn() and self.state in [States.DRAW, States.MELD, States.LAY_OFF, States.DISCARD]:
            if self.search.best_move is not None:
                self.do_move(self.search.best_move)
                self.search.best_move = None
                self.fix_cards()
            elif self.get_moves() == [Moves.PASS]:
                self.do_move(Moves.PASS)
            elif self.search.thread is None or not self.search.thread.is_alive():
                self.search.thread = Thread(target=self.search.run, args = [self], daemon = True)
                self.search.thread.start()
            #Non threaded
            #self.search.run(self)
            #self.do_move(self.search.best_move)

    def validate_melds(self):
        if any(meld.cards 
               and (len(meld.cards) < 3 
                    or not (meld.is_valid_run() or meld.is_valid_set())) 
               for meld in self.melds):
            return False
        return True

    def set_placeholders(self):
        if self.validate_melds() and all(meld.cards for meld in self.melds):
            self.melds.append(Meld())
        if sum(1 for meld in self.melds if not meld.cards) > 1:
            self.melds.pop()
        row = 0
        for i, meld in enumerate(self.melds[:-1]):
            self.melds[i+1].group.rect.x = meld.group.rect.right + 20
            if self.melds[i+1].group.rect.right > resolution[0]:
                row += 1
                self.melds[i+1].group.rect.x = 170
            self.melds[i+1].group.rect.y = self.melds[0].group.rect.y + 201 * row

    def pile_to_deck(self):
        self.deck.cards = list(self.pile.cards)
        self.deck.shuffle()
        for card in self.deck.cards:
            card.snapped_pos = card.drop_pos = [0, 0]
        self.pile.cards.clear()
        self.reshuffles += 1

    def fix_cards(self):
        for meld in self.melds:
            for card in meld.cards:
                card.fixed = True
        for card in self.player.hand.cards:
            card.fixed = False

    def clone_and_randomize(self):
        new = Game.__new__(Game)
        new.deck = Deck.__new__(Deck)
        new.deck.cards = deepcopy(self.deck.cards)
        new.deck.shuffle()
        new.player = deepcopy(self.player)
        new.computer = deepcopy(self.computer)
        new.pile = deepcopy(self.pile)
        new.melds = deepcopy(self.melds)
        new.player.cards = [card for card in self.player.hand.cards if card in self.player.hand.known_cards]
        while len(self.player.hand.cards) < len(new.player.hand.cards):
            self.player.draw_deck(new.deck)
        if self.is_players_turn():
            new.current_player = new.player
        else: new.current_player = new.computer
        new.state = self.state
        new.reshuffles = 0
        return new

    def get_moves(self):
        moves = []
        if self.reshuffles >= 20:
            self.state = States.OVER
        elif self.state == States.DRAW:
            moves = [Moves.DRAW_DECK, Moves.DRAW_PILE]
        elif self.state == States.MELD:
            self.current_player.hand.find_melds()
            moves = [(Moves.MELD, possible_meld) 
                        for possible_meld in self.current_player.hand.possible_melds]
            moves.append(Moves.PASS)
        elif self.state == States.LAY_OFF:
            self.current_player.hand.find_layoffs(self.melds)
            moves = [(Moves.LAY_OFF, possible_layoff[0], possible_layoff[1]) 
                        for possible_layoff in self.current_player.hand.possible_layoffs]
            moves.append(Moves.PASS)
        elif self.state == States.DISCARD:
            moves = [(Moves.DISCARD, card) for card in self.current_player.hand.cards]
        return moves

    def do_move(self, move):
        if move == Moves.PASS:
            self.progress_state()
        elif move == Moves.DRAW_DECK:
            self.current_player.draw_deck(self.deck)
            self.progress_state()
        elif move == Moves.DRAW_PILE:
            self.current_player.draw_pile(self.pile)
            self.progress_state()
        elif move[0] == Moves.DISCARD:
            self.current_player.discard_card(self.current_player.hand.find_card(move[1]), self.pile)
            self.progress_state()
        elif move[0] == Moves.MELD:
            for card in move[1]:
                self.current_player.add_to_meld(self.melds[-1], self.current_player.hand.find_card(card))
            self.melds.append(Meld())
        elif move[0] == Moves.LAY_OFF:
            self.current_player.add_to_meld(self.melds[move[1]], self.current_player.hand.find_card(move[2]))
        
    def progress_state(self):
        if self.state == States.DISCARD:
            if self.get_result(self.current_player):
                self.state = States.OVER
                return
            if self.is_players_turn():
                self.current_player = self.computer
            else:
                self.current_player = self.player
            self.state = States.DRAW
        else:
            self.state += 1
        if not self.deck.cards:
            self.pile_to_deck()

    def is_players_turn(self):
        return self.current_player == self.player

    def get_result(self, player):
        if self.reshuffles >= 20:
            return 0.5
        return 0 if player.hand.cards else 1

    def check_winners(self):
        if self.get_result(self.player):
            self.player.score += self.computer.hand.calculate_score()
        elif self.get_result(self.computer):
            self.computer.score += self.player.hand.calculate_score()

    def restart(self):
        self.player.hand.cards.clear()
        self.computer.hand.cards.clear()
        self.pile.cards.clear()
        self.melds.clear()
        self.melds.append(Meld())
        self.deck = Deck(self.images)
        self.deal_cards()
        self.pile.put(self.deck.deal())
        self.joker_swapping_finished = True
        self.melds_valid = True
        self.state = States.DRAW
        self.current_player = choice((self.computer,))

    def draw_menu(self):
        self.draw_text('Start')

    def draw_leaderboard(self):
        self.draw_text('Koniec gry')

    def draw_text(self, text):
        text = self.font.render(text, True, (255, 255, 255))
        text.set_alpha(100)
        rect = text.get_rect()
        rect.center = (self.screen.get_width() / 2, self.screen.get_height() * 5 / 7)
        self.screen.blit(text, rect)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.state = States.CLOSED
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = States.MENU
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == States.MENU:
                self.restart()
            elif self.sort_button.rect.collidepoint(event.pos):
                self.sort_button.clicked = True
                self.player.sort_hand()
            elif self.is_players_turn() and self.state == States.DRAW and self.deck.sprite.rect.collidepoint(event.pos):
                self.do_move(Moves.DRAW_DECK)
                self.state = States.DISCARD
                self.player.hand.sorted = not self.player.hand.sorted
            elif self.is_players_turn() and self.state == States.DRAW and self.pile.group.rect.collidepoint(event.pos):
                self.do_move(Moves.DRAW_PILE)
                self.state = States.DISCARD
                self.player.hand.sorted = not self.player.hand.sorted
            elif self.player.selected_card == None:
                self.player.select_card(event.pos)
            for meld in self.melds:
                if self.state == States.DISCARD and meld.group.rect.collidepoint(event.pos):
                    if self.player.draw_deck(meld):
                        self.joker_swapping_finished = self.melds_valid = True
                        self.player.hand.sorted = not self.player.hand.sorted
            return
        if event.type == pygame.MOUSEBUTTONUP:
            self.sort_button.clicked = False
            if self.player.selected_card != None:
                card = self.player.selected_card
                if self.pile.group.rect.collidepoint(card.sprite.rect.center):
                    self.melds_valid = self.validate_melds()
                    self.joker_swapping_finished = not self.player.hand.swapped_joker
                    if self.melds_valid and self.joker_swapping_finished:
                        self.do_move((Moves.DISCARD, card))
                        self.fix_cards()
                else: 
                    for meld in self.melds:
                        if meld.group.rect.collidepoint(card.sprite.rect.center):
                            self.player.swap_joker(meld, card)
                            half_rect = pygame.Rect((meld.group.rect.left, meld.group.rect.top), 
                                                    (meld.group.rect.width/2, meld.group.rect.height))
                            if card.rank == Ranks.JOKER and len(meld.cards) > 1 and half_rect.collidepoint(card.sprite.rect.center):
                                self.player.add_to_meld(meld, card, back=True)
                            else:
                                self.player.add_to_meld(meld, card)
                card.selected = card.detached = False
                self.player.selected_card = None
            return
        if event.type == pygame.MOUSEMOTION and self.player.selected_card:
            self.player.move_card(event.pos, self.state, self.is_players_turn())

    def update(self):
        self.pile.update()
        self.sprites_all.update()
        self.set_placeholders()
        for meld in self.melds:
            meld.update()
        self.player.hand.update()
        self.computer.hand.update()
        self.get_computers_move()
        self.check_winners()

    def draw(self):
        self.screen.fill((7,92,19))
        if self.state == States.CLOSED:
            return
        if self.state == States.MENU:
            self.draw_menu()
            return
        if self.state == States.OVER:
            self.draw_leaderboard()
            return
        self.sprites_all.draw(self.screen)
        if not self.melds[-1].cards:
            pygame.draw.rect(self.screen, (255, 255, 255), self.melds[-1].group.rect,  2, 3)
        if not self.pile.cards:
            pygame.draw.rect(self.screen, (255, 255, 255), self.pile.group.rect,  2, 3)
        if not self.melds_valid:
            self.draw_text('Nieprawid\u0142owe u\u0142o\u017Cenie kart!')        
        if not self.joker_swapping_finished:
            self.draw_text('Nie zako\u0144czono podmiany Jokera!')
        if not self.is_players_turn():
            self.draw_text('Komputer my\u015Bli...')
        elif self.state == States.DRAW:
            self.draw_text('Dobierz kart\u0119')
        for i, _ in enumerate(self.computer.hand.cards):
            self.screen.blit(self.images[0], (300 + i * 30, -130))
        for meld in self.melds:
            meld.group.draw(self.screen)
        self.pile.group.draw(self.screen)
        self.player.hand.group.draw(self.screen)
        self.computer.hand.group.draw(self.screen)


if __name__ == '__main__':
    pygame.init()
    clock = pygame.time.Clock()
    pygame.display.set_caption('Remik')
    game = Game()
    while game.state:
        for event in pygame.event.get():
            game.handle_event(event)
        game.update()
        game.draw()
        pygame.display.update()
        clock.tick(60)
    pygame.quit()