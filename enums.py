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

class Scores(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 10
    QUEEN = 10
    KING = 10
    ACE = 11
    JOKER = 15

class States(IntEnum):
    CLOSED = 0
    MENU = 1
    DRAW = 2
    DISCARD = 3
    OVER = 4

class Moves(IntEnum):
    DRAW_DECK = 1
    DRAW_PILE = 2
    DISCARD = 3
    MELD = 4
    LAY_OFF = 5
    SWAP_JOKER = 6