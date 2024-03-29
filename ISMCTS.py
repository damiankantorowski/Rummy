# Written by Peter Cowling, Edward Powley, Daniel Whitehouse (University of York, UK) September 2012 - August 2013.
# Licence is granted to freely use and distribute for any sensible/legal purpose so long as this comment remains in any distributed code.
# Read the article accompanying this code https://www.aifactory.co.uk/newsletter/2013_01_reduce_burden.htm
from math import sqrt, log
from random import choice
from time import time
from enums import Moves


class Node:

    def __init__(self, move=None, parent=None, player=None):
        self.move = move
        self.parent = parent
        self.player = player
        self.children = []
        self.visits = 0
        self.wins = 0
        self.considerations = 1

    def get_untried_moves(self, legal_moves):
        tried_moves = [child.move for child in self.children]
        return [move for move in legal_moves if move not in tried_moves]

    def select_child(self, legal_moves, exploration=0.7):
        legal_children = [child for child in self.children if child.move in legal_moves]
        for child in legal_children:
            child.considerations += 1
        return max(legal_children, 
                   key=lambda c: float(c.wins) / float(c.visits) 
                   + exploration * sqrt(log(c.considerations) / float(c.visits)))

    def add_child(self, move, player):
        new = Node(move, self, player)
        self.children.append(new)
        return new

    def update(self, terminal_state):
        self.visits += 1
        if self.player is not None:
            self.wins += terminal_state.get_result(self.player)


class ISMCTS:

    def __init__(self):
        self.best_move = None
        self.thread = None

    def run(self, root_state, timeout=2):
        start = time()
        root_node = Node()
        while time() < start + timeout:
            node = root_node
            state = root_state.clone_and_randomize()
            while True:
                while (legal_moves := state.get_moves()) and not node.get_untried_moves(legal_moves):
                    node = node.select_child(legal_moves)
                    state.do_move(node.move)
                if (legal_moves := state.get_moves()) and (untried_moves := node.get_untried_moves(legal_moves)):
                    if legal_moves == [Moves.PASS]:
                        state.do_move(Moves.PASS)
                        continue
                    move = choice(untried_moves)
                    player = state.current_player
                    node = node.add_child(move, player)
                    state.do_move(move)
                while legal_moves := state.get_moves():
                    state.do_move(choice(legal_moves))
                while node is not None:
                    node.update(state)
                    node = node.parent
                break
        self.best_move = max(root_node.children, key=lambda c: c.visits).move