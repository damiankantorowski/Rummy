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
        self.image = pygame.image.load(img).convert_alpha() #temporary solution
        self.image = pygame.transform.scale(self.image, (int(self.image.get_size()[0]/4), int(self.image.get_size()[1]/4))) #temporary solution
        self.selected = False
        self.detached = False
        self.drop_pos = [0, 0]
        self.snapped_pos = [0, 0]
        self.rect = self.image.get_rect()
    def animate(self, destination, speed):
        self.drop_pos[0] += (destination[0] - self.drop_pos[0]) * speed / 10
        self.drop_pos[1] += (destination[1] - self.drop_pos[1]) * speed / 10   
        self.rect.x = round(self.drop_pos[0])
        self.rect.y = round(self.drop_pos[1])
    def update(self, index):
        self.snapped_pos = (200 + 90 * index, 560)
        if self.detached: 
            self.rect.x = self.drop_pos[0]
            self.rect.y = self.drop_pos[1]
        elif self.selected:
            self.animate((self.drop_pos[0], 530), 1)
        else:
            self.animate(self.snapped_pos, 0.8)

class Hand(pygame.sprite.OrderedUpdates):
    def __init__(self):
        super().__init__()
        self.cards = []
    def add_card(self, card):
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
            card.update(index)

class Deck(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.cards = []
        self.image = pygame.image.load(path.join('cards', 'back.png'))
        self.image = pygame.transform.scale(self.image, (int(self.image.get_size()[0]/4), int(self.image.get_size()[1]/4)))
        self.rect = self.image.get_rect(center=(80, 100))
        self.generate()
        self.shuffle()
    def generate(self):
        num = 1
        for suit in Suits:
            for rank in Ranks:
                self.cards.append(Card(suit, rank, path.join('cards', str(num) + '.png')))
                num+=1
        self.cards.append(Card(5, 15, path.join('cards', '53.png')))
        self.cards.append(Card(5, 15, path.join('cards', '53.png')))
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
            card.animate((18, 200), 3)

class Meld(pygame.sprite.OrderedUpdates):
    def __init__(self, pos):
        super().__init__()
        self.cards = []
        self.rect = pygame.Rect((pos), (125, 181))
    def put(self, card):
        card.kill()
        self.add(card)
        self.cards.append(card)
        self.rect.width = 125+(len(self.cards)-1)*28
        self.update()
    def update(self):
        for index, card in enumerate(self.cards):
            card.animate((self.rect.topleft[0]+index*28, self.rect.topleft[1]), 3)
    def is_valid_run(self):
        if self.cards:
            suit = self.cards[0].suit
            if len(self.cards) < 3 or any(card.suit != suit for card in self.cards):
                return False
        return True
    def is_valid_set(self):
        if self.cards:
            rank = self.cards[0].rank
            if len(self.cards) < 3 or any(card.rank != rank for card in self.cards):
                return False
        return True
            
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
            if overlapped_rect.collidepoint(mouse_pos):
                card.selected = True
                self.selected_card = card
                card.rel_pos = (card.rect.x - mouse_pos[0], card.rect.y - mouse_pos[1] - 30)
    def discard_card(self, card, pile):
        if card in self.hand:
            pile.put(self.hand.discard(card))
    def add_to_meld(self, meld, card):
        if card in self.hand:
            meld.put(self.hand.discard(card))
    def move_card(self, mouse_pos, game_state):
        posx = mouse_pos[0] + self.selected_card.rel_pos[0]
        last = 200 + len(self.hand.sprites()) * 85
        if posx > 180 and posx < last:
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
        self.state = States.DRAW
        self.deck = Deck()
        self.player = Player()
        self.computer = Player()
        self.deal_cards()
        self.pile = Pile(self.deck.deal())
        self.melds = []
        self.melds.append(Meld((170, 10)))
        self.player.hand.sort_by_rank()
        self.sprites_all = pygame.sprite.Group(self.deck)
    def deal_cards(self):
        for i in range(10):
            self.player.hand.add_card(self.deck.deal())
            self.computer.hand.add_card(self.deck.deal())
    def get_computers_move(self):
        for card in self.computer.hand:
            card.drop_pos = [1280, 0]
        self.computer.draw_card(self.deck)
        self.computer.hand.sort_by_rank()
        self.computer.discard_card(self.computer.hand.cards[0], self.pile)
        self.state = States.DRAW
    def validate_melds(self):
        if any(not (meld.is_valid_run() or meld.is_valid_set()) for meld in self.melds):
            return False
        return True
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.state = 0
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == States.DRAW and self.deck.rect.collidepoint(event.pos):
                    self.player.draw_card(self.deck)
                    self.state = States.DISCARD
                elif self.state == States.DRAW and self.pile.rect.collidepoint(event.pos):
                    self.player.draw_card(self.pile)
                    self.state = States.DISCARD
                else:
                    self.player.select_card(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.player.selected_card != None:
                card = self.player.selected_card
                if self.pile.rect.collidepoint(card.rect.center):  
                    if self.validate_melds():
                        self.player.discard_card(card, self.pile)
                        self.state = States.COMPUTERS_TURN
                        self.get_computers_move()
                else: 
                    for meld in self.melds:
                        if meld.rect.collidepoint(card.rect.center):
                             self.player.add_to_meld(meld, card)
                card.selected = card.detached = False
                self.player.selected_card = None
        elif event.type == pygame.MOUSEMOTION:
            if self.player.selected_card != None:
                 self.player.move_card(event.pos, self.state)
    def draw(self, screen):
        screen.fill((7,92,19))
        self.sprites_all.update()
        self.sprites_all.draw(screen)
        self.pile.update()
        self.pile.draw(screen)
        for meld in self.melds:
            meld.update()
            meld.draw(screen)
        self.player.hand.update()
        self.player.hand.draw(screen)
        pygame.display.update()

if __name__ == "__main__":
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption('Remik') 
    game = Game()
    while game.state:
        for event in pygame.event.get():
            game.handle_event(event)
        game.draw(screen)
        clock.tick(60)
    pygame.quit()