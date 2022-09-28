# -*- coding: utf-8 -*-
"""
human player
python 3.6 +

@author : djh-sudo
If you have any question, pls contact me
at djh113@126.com
"""

from board import *
import mcts
from policyValueNet import ValueNet


class Human(object):
    def __init__(self):
        self.player = None

    def set_index(self, p: int):
        self.player = p

    def action(self, board: Board):
        try:
            print('X is black, O is white | Now is player', self.player)
            location = input("input(x, y) you want to go\n")
            if isinstance(location, str):  # for python3
                x, y = int(location.split(',')[0]), int(location.split(',')[-1])
                point = board.location_to_point([x, y])
            else:
                point = -1
        except Exception as e:
            print(e)
            point = -1
        if point == -1 or point not in board.available:
            print('Invalid position')
            point = self.action(board)
        return point

    def __str__(self):
        return "Human{}".format(self.player)


def two_human_run():
    width, height = 8, 8
    board = Board(width, height)
    game = Game(board)

    h1 = Human()
    h2 = Human()

    game.start_play(h1, h2)


def play_with_AI(model_path: str):
    width, height = 8, 8
    board = Board(width, height)
    game = Game(board)
    policy_val_net = ValueNet(width, height, model_path)
    # AI
    mcts_player_AI = mcts.AI_MCTS_Player(policy_val_fun=policy_val_net.policy_value_fn, c=4)
    # Human
    human = Human()
    # start play
    game.start_play(human, mcts_player_AI, shown=True)


if __name__ == '__main__':
    # two_human_run()
    play_with_AI('./model/best_13_policy_model')


