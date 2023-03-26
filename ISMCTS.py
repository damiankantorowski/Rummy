from math import sqrt, log
from random import choice

class Node:
    def __init__(self, move=None, parent=None, player=None):
        self.move = move
        self.parent = parent
        self.children = []
        self.player = player
        self.visits = 0
        self.considerations = 1
        self.wins = 0
    def get_untried_moves(self, legal_moves):
        tried_moves = [child.move for child in self.children]
        return [move for move in legal_moves if move not in tried_moves]
    def select_child(self, legal_moves, exploration=0.7):
        legal_children = [child for child in self.children if child.move in legal_moves]
        UCB1 = max(legal_children, key=lambda c: float(c.wins) / float(c.visits) + exploration * sqrt(log(c.considerations) / float(c.visits)))
        for child in legal_children:
            child.considerations += 1
        return UCB1
    def add_child(self, move, player):
        new = Node(move, self, player)
        self.children.append(new)
        return new
    def update(self, terminal_state):
        self.visits += 1
        self.wins += terminal_state.get_result(self.player)

class ISMCTS:
    def __init__(self, root_state, limit=50):
        root_node = Node()
        for i in range(limit):
            node = root_node
            state = root_state.clone_and_randomize(root_state.player)
            while state.get_moves() and not node.get_untried_moves(state.get_moves()):
                node = node.select_child(state.get_moves())
                state.do_move(node.move)
            untried_moves = node.get_untried_moves(state.get_moves())
            if untried_moves:
                m = choice(untried_moves)
                player = state.computer
                state.do_move(m)
                node = node.add_child(m, player) 
            while state.get_moves():
                state.do_move(choice(state.get_moves()))
            while node is not None:
                node.update(state)
                node = node.parent
        self.best_move = max(root_node.children, key=lambda child: child.visits).move 