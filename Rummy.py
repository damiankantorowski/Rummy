import pygame
from operator import index
from random import shuffle
from os import path
from enum import IntEnum

class Suits(IntEnum):
    CLUBS = 1
    SPADES = 2
    HEARTS = 3
    DIAMONDS = 4

class Ranks(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14
    JOKER = 15

class States(IntEnum):
    CLOSED = 0
    MENU = 1
    DRAW = 2
    DISCARD = 3
    COMPUTERS_TURN = 4
    OVER = 5

class Card(pygame.sprite.Sprite):
    def __init__(self, suit, rank, img):
        super().__init__()
        self.suit = suit
        self.rank = rank
        self.image = img
        self.image = pygame.transform.scale(self.image, (int(self.image.get_width()/4), int(self.image.get_height()/4)))
        self.selected = False
        self.detached = False
        self.fixed = False
        self.drop_pos = [0, 0]
        self.snapped_pos = [0, 0]
        self.rect = self.image.get_rect()
    def animate(self, destination, speed):
        self.drop_pos[0] += (destination[0] - self.drop_pos[0]) * speed / 10
        self.drop_pos[1] += (destination[1] - self.drop_pos[1]) * speed / 10   
        self.rect.x = round(self.drop_pos[0])
        self.rect.y = round(self.drop_pos[1])
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
    def add_card(self, card):
        if card is not None:
            if card.rank == 1:
                card.rank = Ranks.ACE
            self.cards.append(card)
            self.add(card)
    def sort_by_rank(self):
        self.cards.sort(key = lambda card: (card.rank, card.suit))
    def sort_by_suit(self):
        self.cards.sort(key = lambda card: (card.suit, card.rank))
    def discard(self, card):
        return self.cards.pop(self.cards.index(card))
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
        self.image = pygame.transform.scale(self.image, (int(self.image.get_size()[0]/4), int(self.image.get_size()[1]/4)))
        self.rect = self.image.get_rect(center=(80, 100))
        self.generate(images)
        self.shuffle()
    def generate(self, images):
        num = 1
        for suit in Suits:
            for rank in range(Ranks.TWO, Ranks.JOKER):
                self.cards.append(Card(suit, rank, images[num]))
                num+=1
        self.cards.append(Card(5, Ranks.JOKER, images[53]))
        self.cards.append(Card(5, Ranks.JOKER, images[53]))
    def shuffle(self):
        shuffle(self.cards)
    def deal(self):
        return self.cards.pop()
    def update(self):
        if len(self.cards) == 0:
            self.image = pygame.Surface((0,0))

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
        for card in self.cards:
            card.animate((18, 200), 1.5)

class Meld(pygame.sprite.OrderedUpdates):
    def __init__(self, pos):
        super().__init__()
        self.cards = []
        self.rect = pygame.Rect(pos, (125, 181))
    def put(self, card):
        self.cards.append(card)
        if self.is_valid_run() or self.is_valid_set():
            card.kill()
            return True
        self.cards.pop()
        self.cards.insert(0, card)
        if self.is_valid_run() or self.is_valid_set():
            card.kill()
            return True
        self.cards.pop(0)
        return False
    def deal(self):
        if not self.cards[-1].fixed:
            return self.cards.pop()
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
                Card.kill()
                return True
        return False
    def is_valid_run(self):
        if self.cards:
            suit = self.cards[0].suit
            if len(self.cards) > 1: 
                if self.cards[0].rank == Ranks.ACE and self.cards[1].rank != Ranks.ACE:
                    self.cards[0].rank = 1
                elif self.cards[0].rank == Ranks.JOKER:
                    suit = self.cards[1].suit
            if len(self.cards) < 4 and sum(1 for card in self.cards if card.rank == Ranks.JOKER) > 1:
                return False
            if any(card.rank == Ranks.JOKER and self.cards[i+1].rank == Ranks.JOKER for i, card in enumerate(self.cards[:-1])):
                return False
            if any(card.suit != suit and card.rank != Ranks.JOKER for card in self.cards):
                return False
            if any(self.cards[i+1].rank != card.rank + 1 and self.cards[i+1].rank != Ranks.JOKER and card.rank != Ranks.JOKER for i, card in enumerate(self.cards[:-1])):
                return False
            if len(self.cards) > 2:
                for i, card in enumerate(self.cards[:-1]):
                    if card.rank == Ranks.JOKER and self.cards[i+1].rank != self.cards[i-1].rank + 2:
                        return False
        return True
    def is_valid_set(self):
        if self.cards:
            rank = self.cards[0].rank
            if self.cards[0].rank == Ranks.JOKER and len(self.cards) > 1:
                rank = self.cards[1].rank
            if len(self.cards) < 4 and sum(1 for card in self.cards if card.rank == Ranks.JOKER) > 1:
                return False
            if any(card.rank != rank and card.rank != Ranks.JOKER for card in self.cards):
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
        if len(pile.cards) > 0:
            self.hand.add_card(pile.deal())
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
                break
    def discard_card(self, card, pile):
        if card in self.hand:
            pile.put(self.hand.discard(card))
    def add_to_meld(self, meld, card):
        if card in self.hand and meld.put(card):
            self.hand.discard(card)
    def swap_joker(self, meld, card):
        if card in self.hand:
            joker = next((card for card in meld.cards if card.rank == Ranks.JOKER), None)
            if joker and meld.swap_joker(card):
                self.hand.discard(card)
                self.hand.add_card(joker)
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

class Game:
    def __init__(self):
        self.images = self.load_images()
        self.deck = Deck(self.images)
        self.player = Player()
        self.computer = Player()
        self.state = States.DRAW
        self.deal_cards()
        self.pile = Pile(self.deck.deal())
        self.melds = []
        self.melds.append(Meld((170, 10)))
        self.player.hand.sort_by_rank()
        self.sprites_all = pygame.sprite.Group(self.deck)
        self.melds_valid = True
    def load_images(self):
        images = {}
        for i in range(54):
            images[i] = pygame.image.load(path.join('cards', f'{i}.png')).convert_alpha()
        return images
    def deal_cards(self):
        for i in range(10):
            self.player.hand.add_card(self.deck.deal())
            self.computer.hand.add_card(self.deck.deal())
    def get_computers_move(self):
        self.computer.draw_card(self.deck)
        for card in self.computer.hand:
            card.snapped_pos = card.drop_pos = [resolution[0], 0]
        self.computer.hand.sort_by_rank()
        self.computer.discard_card(self.computer.hand.cards[0], self.pile)
        self.state = States.DRAW
        self.check_winners()
    def validate_melds(self):
        if any(len(meld.cards) > 0 and len(meld.cards) < 3 or not (meld.is_valid_run() or meld.is_valid_set()) for meld in self.melds):
            return False
        return True
    def add_meld(self):
        if self.validate_melds() and all(meld.cards for meld in self.melds):
            self.melds.append(Meld((self.melds[-1].rect.right + 70, 10)))
    def incorrect_meld(self, screen):
        font = pygame.font.SysFont(None, 50)
        text = font.render('Nieprawid\u0142owe u\u0142o\u017Cenie kart!', True, (255, 255, 255))
        text.set_alpha(100)
        rect = text.get_rect()
        rect.center = (screen.get_width() / 2, screen.get_height() * 5 / 7)
        screen.blit(text, rect)
    def fix_cards(self):
        for meld in self.melds:
            for card in meld.cards:
                card.fixed = True
        for card in self.player.hand:
            card.fixed = False
    def check_winners(self):
        if self.state == States.DRAW:
            if len(self.player.hand.cards) == 0:
                self.state = States.OVER
            elif len(self.computer.hand.cards) == 0:
                self.state = States.OVER
    def restart(self):
        self.deck = Deck(self.images)
        self.player.hand = Hand()
        self.computer.hand = Hand()
        self.state = States.DRAW
        self.deal_cards()
        self.pile = Pile(self.deck.deal())
        self.melds = []
        self.melds.append(Meld((170, 10)))
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
                        self.player.draw_card(meld)
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.player.selected_card != None:
                card = self.player.selected_card
                if self.pile.rect.collidepoint(card.rect.center):  
                    self.melds_valid = self.validate_melds()
                    if self.melds_valid:
                        self.player.discard_card(card, self.pile)
                        self.state = States.COMPUTERS_TURN
                        self.fix_cards()
                        self.check_winners()
                        self.get_computers_move()
                else: 
                    for meld in self.melds:
                        if meld.rect.collidepoint(card.rect.center):
                             self.player.swap_joker(meld, card)
                             self.player.add_to_meld(meld, card)
                             self.add_meld()
                card.selected = card.detached = False
                self.player.selected_card = None
        elif event.type == pygame.MOUSEMOTION and self.player.selected_card:
            self.player.move_card(event.pos, self.state)
    def draw(self, screen):
        screen.fill((7,92,19))
        self.sprites_all.update()
        self.sprites_all.draw(screen)
        self.pile.update()
        self.pile.draw(screen)
        row = 0
        for i, meld in enumerate(self.melds[:-1]):
            self.melds[i+1].rect.x = meld.rect.right + 20
            self.melds[i+1].rect.y = self.melds[0].rect.y + 201 * row
            if meld.rect.right + 145 > resolution[0]:
                row += 1
        for meld in self.melds:
            meld.update()
            meld.draw(screen)
        if not self.melds[-1].cards:
            pygame.draw.rect(screen, (255, 255, 255), self.melds[-1].rect,  2, 3)
        if not self.pile.cards:
            pygame.draw.rect(screen, (255, 255, 255), self.pile.rect,  2, 3)
        if not self.melds_valid:
            self.incorrect_meld(screen)
        for i in range(len(self.computer.hand.cards)):
            screen.blit(self.deck.image, (resolution[0] - 200 - i * 30, -130))
        self.player.hand.update()
        self.player.hand.draw(screen)
        pygame.display.update()

if __name__ == "__main__":
    pygame.init()
    clock = pygame.time.Clock()
    #resolution = (1280, 720)
    resolution = (1920, 1080)
    screen = pygame.display.set_mode(resolution)
    pygame.display.set_caption('Remik') 
    game = Game()
    while game.state:
        for event in pygame.event.get():
            game.handle_event(event)
        game.draw(screen)
        clock.tick(60)
    pygame.quit()