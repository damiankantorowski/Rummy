import pygame
from random import shuffle, choice
from copy import deepcopy
from enums import Suits, Ranks, Scores, States
from ISMCTS import ISMCTS

class Card(pygame.sprite.Sprite):
    def __init__(self, suit, rank, score, img):
        super().__init__()
        self.suit = suit
        self.rank = rank
        self.score = score
        self.image = img
        self.rect = self.image.get_rect()
        self.drop_pos = [0, 0]
        self.snapped_pos = [0, 0]
        self.selected = False
        self.detached = False
        self.fixed = False
        self.in_place = False
    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        for k, v in self.__dict__.items():
            if k != "image":
                setattr(new, k, deepcopy(v, memo))
        return new
    def animate(self, destination, speed):
        self.in_place = False
        self.drop_pos[0] += (destination[0] - self.drop_pos[0]) * speed / 10
        self.drop_pos[1] += (destination[1] - self.drop_pos[1]) * speed / 10   
        self.rect.x = round(self.drop_pos[0])
        self.rect.y = round(self.drop_pos[1])
        if self.rect.x == destination[0] and self.rect.y == destination[1]:
            self.in_place = True
    def update(self, index, length):
        self.snapped_pos = (resolution[0]/2 - (length / 2) * (self.rect.width - 35) + index * (self.rect.width - 35), resolution[1] - self.rect.height)
        if self.detached: 
            self.rect.x = self.drop_pos[0]
            self.rect.y = self.drop_pos[1]
        elif self.selected:
            self.animate((self.drop_pos[0], self.snapped_pos[1] - 30), 1)
        else:
            self.animate(self.snapped_pos, 1)

class Hand(pygame.sprite.OrderedUpdates):
    def __init__(self):
        super().__init__()
        self.cards = []
        self.swapped_joker = 0
    def add_card(self, card):
        if card is not None:
            if card.rank == 1:
                card.rank = Ranks.ACE
            self.cards.append(card)
            self.add(card)
            return True
        return False
    def sort_by_rank(self):
        self.cards.sort(key = lambda card: (card.rank, card.suit))
    def sort_by_suit(self):
        self.cards.sort(key = lambda card: (card.suit, card.rank))
    def discard(self, card):
        return self.cards.pop(self.cards.index(card))
    def calculate_score(self):
        return sum(card.score for card in self.cards)
    def update(self):
        self.empty()
        for index, card in enumerate(self.cards):
            self.add(card)
            card.update(index, len(self.cards))

class Deck(pygame.sprite.Sprite):
    def __init__(self, images):
        super().__init__()
        self.cards = []
        self.image = images[0]
        self.rect = self.image.get_rect(center=(80, 100))
        self.generate(images)
        self.shuffle()
    def generate(self, images):
        num = 1
        for suit in Suits:
            for rank in range(Ranks.TWO, Ranks.JOKER):
                self.cards.append(Card(suit, rank, Scores[Ranks(rank).name], images[num]))
                num+=1
        self.cards.append(Card(5, Ranks.JOKER, Scores.JOKER, images[53]))
        self.cards.append(Card(5, Ranks.JOKER, Scores.JOKER, images[53]))
    def shuffle(self):
        shuffle(self.cards)
    def deal(self):
        return self.cards.pop()

class Pile(pygame.sprite.OrderedUpdates):
    def __init__(self, first_card):
        super().__init__()
        self.cards = []
        self.put(first_card)
        self.rect = pygame.Rect(18, 200, 125, 176)
    def deal(self):
        return self.cards.pop()
    def put(self, card):
        card.kill()
        self.add(card)
        self.cards.append(card)
        self.update()
    def update(self):
        self.empty()
        for card in self.cards[-2:]:
            self.add(card)
            card.animate((18, 200), 1.5)

class Meld(pygame.sprite.OrderedUpdates):
    def __init__(self):
        super().__init__()
        self.cards = []
        self.rect = pygame.Rect((170, 60), (125, 181))
    def put_front(self, card):
        self.cards.append(card)
        if self.is_valid_run() or self.is_valid_set():
            card.kill()
            return True
        self.cards.pop()
        return False
    def put_back(self, card):
        self.cards.insert(0, card)
        if self.is_valid_run() or self.is_valid_set():
            card.kill()
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
                Card.kill()
                return temp
        return None
    def is_valid_run(self):
        if self.cards:
            suit = self.cards[0].suit
            if len(self.cards) > 1: 
                if self.cards[0].rank == Ranks.ACE and self.cards[1].rank != Ranks.ACE and self.cards[1].rank != Ranks.KING:
                    self.cards[0].rank = 1
                elif self.cards[0].rank == Ranks.JOKER:
                    suit = self.cards[1].suit
                if self.cards[-2].rank == Ranks.ACE:
                    return False
            if len(self.cards) < 4 and sum(1 for card in self.cards if card.rank == Ranks.JOKER) > 1:
                return False
            if any(card.rank == Ranks.JOKER 
                   and self.cards[i+1].rank == Ranks.JOKER for i, card in enumerate(self.cards[:-1])):
                return False
            if any(card.suit != suit and card.rank != Ranks.JOKER for card in self.cards):
                return False
            if any(self.cards[i+1].rank != card.rank + 1 and self.cards[i+1].rank != Ranks.JOKER and card.rank != Ranks.JOKER for i, card in enumerate(self.cards[:-1])):
                return False
            if len(self.cards) > 2 and self.cards[0].rank != Ranks.JOKER:
                for i, card in enumerate(self.cards[:-1]):
                    if card.rank == Ranks.JOKER and self.cards[i+1].rank != self.cards[i-1].rank + 2:
                        return False
        return True
    def is_valid_set(self):
        if self.cards:
            rank = self.cards[0].rank
            if self.cards[0].rank == Ranks.JOKER and len(self.cards) > 1:
                rank = self.cards[1].rank
            if len(self.cards) > 4:
                return False
            if len(self.cards) < 4 and sum(1 for card in self.cards if card.rank == Ranks.JOKER) > 1:
                return False
            if any(card.rank != rank and card.rank != Ranks.JOKER for card in self.cards):
                return False
            if any(card.rank == Ranks.JOKER and self.cards[i+1].rank == Ranks.JOKER for i, card in enumerate(self.cards[:-1])):
                return False 
        return True
    def update(self):
        self.empty()
        for index, card in enumerate(self.cards):
            self.add(card)
            card.animate((self.rect.topleft[0]+index*28, self.rect.topleft[1]), 3)
        if self.cards:
            self.rect.width = 125+(len(self.cards)-1)*28
            
class Player:
    def __init__(self):
        self.hand = Hand()
        self.points = 0
        self.selected_card = None
    def draw_card(self, pile):
        if pile.cards and self.hand.add_card(pile.deal()):
            return True
        return False
    def select_card(self, mouse_pos):
        last = len(self.hand.sprites()) - 1
        for i, card in enumerate(self.hand):
            if i == last:
                overlapped_rect = pygame.Rect((card.rect.left, card.rect.top), (card.rect.width, card.rect.height))
            else:
                overlapped_rect = pygame.Rect((card.rect.left, card.rect.top), (card.rect.width - 35, card.rect.height))
            if overlapped_rect.collidepoint(mouse_pos) and self.selected_card == None:
                card.selected = True
                self.selected_card = card
                card.rel_pos = (card.rect.x - mouse_pos[0], card.rect.y - mouse_pos[1] - 30)
                return
    def discard_card(self, card, pile):
        if card in self.hand:
            pile.put(self.hand.discard(card))
    def add_to_meld(self, meld, card, back=False):
        if card in self.hand and (not back and meld.put_front(card) or meld.put_back(card)):
            if card.rank == Ranks.JOKER and self.hand.swapped_joker:
                self.hand.swapped_joker -= 1
            self.hand.discard(card)
            return True
        return False
    def swap_joker(self, meld, card):
        if card in self.hand:
            joker = meld.swap_joker(card)
            if joker:
                self.hand.discard(card)
                self.hand.add_card(joker)
                self.hand.swapped_joker += 1
                return True
        return False
    def move_card(self, mouse_pos, game_state):
        posx = mouse_pos[0] + self.selected_card.rel_pos[0]
        first = resolution[0]/2 - (len(self.hand.cards) / 2 + 1) * 80
        last = resolution[0]/2 + (len(self.hand.cards) / 2) * 80
        if posx > first and posx < last:
            self.selected_card.drop_pos[0] = posx
        for card in self.hand:
            cropped_rect = pygame.Rect((card.snapped_pos[0], card.snapped_pos[1]), (card.rect.width - 60, card.rect.height))
            if cropped_rect.collidepoint(self.selected_card.rect.center):
                a, b = self.hand.cards.index(self.selected_card), self.hand.cards.index(card)
                self.hand.cards.insert(b, self.hand.cards.pop(a))
        if game_state != States.DRAW:
            self.selected_card.detached = True
            self.selected_card.drop_pos[0] = mouse_pos[0] + self.selected_card.rel_pos[0]
            self.selected_card.drop_pos[1] = mouse_pos[1] + self.selected_card.rel_pos[1]

class AI(Player):
    def __init__(self):
        super().__init__()
        self.next_move = States.DRAW
        self.possible_melds = []
    def find_melds(self):
        group = Meld()
        self.hand.sort_by_rank()
        if len(self.hand.cards) >= 4:
            for four in list(zip(self.hand.cards, self.hand.cards[1:], self.hand.cards[2:], self.hand.cards[3:])):
                group.cards = list(four)
                if group.is_valid_set():
                    self.possible_melds.append(four)
        if len(self.hand.cards) >= 3:
            for three in list(zip(self.hand.cards, self.hand.cards[1:], self.hand.cards[2:])):
                group.cards = list(three)
                if group.is_valid_set():
                    self.possible_melds.append(three)
        self.hand.sort_by_suit()
        if len(self.hand.cards) >= 4:
            for four in list(zip(self.hand.cards, self.hand.cards[1:], self.hand.cards[2:], self.hand.cards[3:])):
                group.cards = list(four)
                if group.is_valid_set():
                    self.possible_melds.append(four)
        if len(self.hand.cards) >= 3:
            for three in list(zip(self.hand.cards, self.hand.cards[1:], self.hand.cards[2:])):
                group.cards = list(three)
                if group.is_valid_set():
                    self.possible_melds.append(three)
    def lay_off(self, melds):
        self.find_melds()
        for meld in self.possible_melds:
            for card in meld:
                self.add_to_meld(melds[-1], card)
            self.possible_melds.remove(meld)
        for card in self.hand.cards:
            for meld in melds[:-1]:
                self.add_to_meld(meld, card)

class Game():
    def __init__(self):
        self.images = self.load_images()
        self.deck = Deck(self.images)
        self.player = Player()
        self.computer = AI()
        self.state = States.DRAW
        self.deal_cards()
        self.pile = Pile(self.deck.deal())
        self.melds = []
        self.melds.append(Meld())
        self.player.hand.sort_by_rank()
        self.sprites_all = pygame.sprite.Group(self.deck)
        self.melds_valid = True
        self.joker_swapping_finished = True
    def load_images(self):
        images = {}
        for i in range(54):
            images[i] = pygame.image.load(f'cards/{i}.png').convert_alpha()
            images[i] = pygame.transform.scale(images[i], (int(images[i].get_size()[0]/4), int(images[i].get_size()[1]/4)))
        return images
    def deal_cards(self):
        for i in range(13):
            self.player.hand.add_card(self.deck.deal())
            self.computer.hand.add_card(self.deck.deal())
    def get_computers_move(self):
        if self.state in (States.COMPUTER_DRAW, States.COMPUTER_DISCARD) and self.done_animating():
            self.computer.hand.sort_by_rank()
            best_move = ISMCTS(self).best_move
            #if best_move[1] == 'discard':
            #    card = self.computer.hand.cards[best_move[2]]
            #    if card.rank == Ranks.JOKER:
            #        print(best_move[0], best_move[1], Ranks(card.rank).name)
            #    else: print(best_move[0], best_move[1], Ranks(card.rank).name, Suits(card.suit).name)
            #elif best_move[1] == 'draw': 
            #    print(best_move[0], best_move[1], best_move[2])
            #elif best_move[1] == 'lay_off':
            #    print(best_move[0], best_move[1])
            self.do_move(best_move)
            #for card in self.computer.hand.cards:
            #    if card.rank == Ranks.JOKER:
            #        print("JOKER")
            #    elif card.rank == 1: 
            #        print("ACE", Suits(card.suit).name)
            #    else:
            #        print(Ranks(card.rank).name, Suits(card.suit).name)
    def validate_melds(self):
        if any(len(meld.cards) > 0 and len(meld.cards) < 3 or not (meld.is_valid_run() or meld.is_valid_set()) for meld in self.melds):
            return False
        return True
    def set_placeholders(self):
        if self.validate_melds() and all(meld.cards for meld in self.melds):
            self.melds.append(Meld())
        if sum(1 for meld in self.melds if not meld.cards) > 1:
            self.melds.pop()
        row = 0
        for i, meld in enumerate(self.melds[:-1]):
            self.melds[i+1].rect.x = meld.rect.right + 20
            if self.melds[i+1].rect.right > resolution[0]:
                row += 1
                self.melds[i+1].rect.x = 170
            self.melds[i+1].rect.y = self.melds[0].rect.y + 201 * row
    def done_animating(self):
        if any(not card.in_place for card in self.pile.cards):
            return False
        if any(not card.in_place for card in self.player.hand.cards):
            return False
        return True
    def print_error(self, screen, text):
        font = pygame.font.SysFont(None, 50)
        text = font.render(text, True, (255, 255, 255))
        text.set_alpha(100)
        rect = text.get_rect()
        rect.center = (screen.get_width() / 2, screen.get_height() * 5 / 7)
        screen.blit(text, rect)
    def pile_to_deck(self):
        self.deck.cards = list(self.pile.cards)
        self.deck.shuffle()
        for card in self.deck.cards:
            card.snapped_pos = card.drop_pos = [0, 0]
        self.pile.empty()
        self.pile.cards.clear()
    def fix_cards(self):
        for meld in self.melds:
            for card in meld.cards:
                card.fixed = True
        for card in self.player.hand:
            card.fixed = False
    def clone_and_randomize(self, player):
        new = Game.__new__(Game)
        new.deck = Deck.__new__(Deck)
        new.deck.cards = deepcopy(self.deck.cards)
        new.player = deepcopy(self.player)
        new.computer = deepcopy(self.computer)
        new.state = self.state
        new.pile = deepcopy(self.pile)
        new.melds = deepcopy(self.melds)
        return new
    def get_moves(self):
        moves = []
        if self.state == States.DRAW:
            moves.append(("player", "draw", "deck"))
            moves.append(("player", "draw", "pile"))
        elif self.state == States.DISCARD:
            moves = [("player", "discard", c) for c, card in enumerate(self.player.hand.cards)]
        elif self.state == States.COMPUTER_DRAW:
            moves.append(("computer", "draw", "deck"))
            moves.append(("computer", "draw", "pile"))
        elif self.state == States.COMPUTER_DISCARD:
            moves = [("computer", "discard", c) for c, card in enumerate(self.computer.hand.cards)]
            #moves.insert(0, ("computer", "lay_off"))
        return moves
    def do_move(self, move):
        if move == ("player", "draw", "deck"):
            self.player.draw_card(self.deck)
        elif move == ("player", "draw", "pile"):
            self.player.draw_card(self.pile)
        elif move == ("computer", "draw", "deck"):
            self.computer.draw_card(self.deck)
            self.computer.lay_off(self.melds)
        elif move == ("computer", "draw", "pile"):
            self.computer.draw_card(self.pile)
            self.computer.lay_off(self.melds)
        elif move[1] == "lay_off":
            if move[0] == "computer":
                self.computer.lay_off(self.melds)
        elif move[1] == "discard":
            if move[0] == "player":
                self.player.discard_card(self.player.hand.cards[move[2]], self.pile)
            elif move[0] == "computer":
                self.computer.discard_card(self.computer.hand.cards[move[2]], self.pile)
        if self.state == States.DRAW:
            self.state = States.DISCARD
        elif self.state == States.DISCARD:
            self.state = States.COMPUTER_DRAW
        elif self.state == States.COMPUTER_DRAW:
            self.state = States.COMPUTER_DISCARD
        elif self.state == States.COMPUTER_DISCARD and move[1] != 'lay_off':
            self.state = States.DRAW
        self.check_winners()
    def get_result(self, player):
        return 1 / (self.computer.hand.calculate_score() + 1)
    def check_winners(self):
        if len(self.player.hand.cards) == 0 and self.state == States.COMPUTER_DRAW:
            self.player.points += self.computer.hand.calculate_score()
        elif len(self.computer.hand.cards) == 0 and self.state == States.DRAW:
            self.computer.points += self.player.hand.calculate_score()
        else: return
        self.state = States.OVER
        #self.restart()
    def restart(self):
        self.deck = Deck(self.images)
        self.player.hand = Hand()
        self.computer.hand = Hand()
        self.state = States.DRAW
        self.deal_cards()
        self.pile = Pile(self.deck.deal())
        self.melds.clear()
        self.melds.append(Meld())
        self.player.hand.sort_by_rank()
        self.melds_valid = True
    def handle_event(self, event):
        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = 0
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == States.DRAW and self.deck.rect.collidepoint(event.pos):
                self.player.draw_card(self.deck)
                self.state = States.DISCARD
            elif self.state == States.DRAW and self.pile.rect.collidepoint(event.pos):
                self.player.draw_card(self.pile)
                self.state = States.DISCARD
            elif self.player.selected_card == None:
                self.player.select_card(event.pos)
            for meld in self.melds:
                if self.state == States.DISCARD and meld.rect.collidepoint(event.pos):
                    if self.player.draw_card(meld):
                        self.joker_swapping_finished = self.melds_valid = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.player.selected_card != None:
                card = self.player.selected_card
                if self.pile.rect.collidepoint(card.rect.center):
                    self.melds_valid = self.validate_melds()
                    self.joker_swapping_finished = not self.player.hand.swapped_joker
                    if self.melds_valid and self.joker_swapping_finished:
                        self.player.discard_card(card, self.pile)
                        self.fix_cards()
                        self.state = States.COMPUTER_DRAW
                else: 
                    for meld in self.melds:
                        if meld.rect.collidepoint(card.rect.center):
                            self.player.swap_joker(meld, card)
                            half_rect = pygame.Rect((meld.rect.left, meld.rect.top), (meld.rect.width/2, meld.rect.height))
                            if card.rank == Ranks.JOKER and meld.cards and half_rect.collidepoint(card.rect.center):
                                self.player.add_to_meld(meld, card, back=True)
                            else:
                                self.player.add_to_meld(meld, card)
                card.selected = card.detached = False
                self.player.selected_card = None
        elif event.type == pygame.MOUSEMOTION and self.player.selected_card:
            self.player.move_card(event.pos, self.state)
    def update(self):
        self.check_winners()
        self.pile.update()
        self.sprites_all.update()
        self.set_placeholders()
        if not self.deck.cards:
            self.pile_to_deck()
        for meld in self.melds:
            meld.update()
        self.player.hand.update()
        self.get_computers_move()
    def draw(self, screen):
        screen.fill((7,92,19))
        self.sprites_all.draw(screen)
        if not self.melds[-1].cards:
            pygame.draw.rect(screen, (255, 255, 255), self.melds[-1].rect,  2, 3)
        if not self.pile.cards:
            pygame.draw.rect(screen, (255, 255, 255), self.pile.rect,  2, 3)
        if not self.melds_valid:
            self.print_error(screen, 'Nieprawid\u0142owe u\u0142o\u017Cenie kart!')        
        if not self.joker_swapping_finished:
            self.print_error(screen, 'Nie zako\u0144czono podmiany Jokera!')   
        for i, _ in enumerate(self.computer.hand.cards):
            screen.blit(self.images[0], (300 + i * 30, -130))
        for meld in self.melds:
            meld.draw(screen)
        self.pile.draw(screen)
        self.player.hand.draw(screen)

if __name__ == "__main__":
    pygame.init()
    clock = pygame.time.Clock()
    resolution = (1280, 720)
    #resolution = (1920, 1080)
    screen = pygame.display.set_mode(resolution)
    pygame.display.set_caption('Remik') 
    game = Game()
    while game.state:
        for event in pygame.event.get():
            game.handle_event(event)
        game.update()
        game.draw(screen)
        pygame.display.update()
        clock.tick(60)
    pygame.quit()
