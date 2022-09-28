# -*- coding: utf-8 -*-
"""
human player
python 3.6 +

@author : djh-sudo
If you have any question, pls contact me
at djh113@126.com
"""

import os
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
    assert os.path.exists(model_path), 'Invalid model path!'
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


class PlayOnline(object):
    def __init__(self):
        self.width = 8
        self.height = 8
        # return obj
        self.is_end = False
        self.who_win = -1
        self.has_error = False
        # parameter
        self.policy_val_net = None
        self.board = None
        self.game = None
        self.mcts_player_AI = None

    def init(self, model_path):
        self.policy_val_net = ValueNet(self.width, self.height, model_path)
        self.board = Board(self.width, self.height)
        self.game = Game(self.board)
        self.mcts_player_AI = mcts.AI_MCTS_Player(
            policy_val_fun=self.policy_val_net.policy_value_fn, c=4)
        self.board.init_board(0)

    def reset(self):
        self.board.init_board(0)

    def two_human_play_online(self, point: int, role: int):
        self.has_error = False
        # Human 1 black piece
        if role in [-1, 1]:
            self.board.draw(point)
        else:
            self.has_error = True
            return {"error": self.has_error,
                    "board": None,
                    "available": None,
                    "is_end": None,
                    "who_win": None,
                    "turn": None}
        self.is_end, self.who_win = self.board.game_end()
        return {"error": self.has_error,
                "board": self.board.status.flatten().tolist(),
                "available": self.board.available,
                "is_end": self.is_end,
                "who_win": self.who_win,
                "turn": self.board.current_player}

    def AI_play_online(self, point: int, role: int):
        self.has_error = False
        # Human black piece
        if role == 1:
            self.board.draw(point)
        # AI write piece
        elif role == -1:
            point = self.mcts_player_AI.action(self.board)
            self.board.draw(point)
        else:
            self.has_error = True
            return {"error": self.has_error,
                    "board": None,
                    "available": None,
                    "is_end": None,
                    "who_win": None,
                    "turn": None,
                    "point": None}
        self.is_end, self.who_win = self.board.game_end()
        return {"error": self.has_error,
                "board": self.board.status.flatten().tolist(),
                "available": self.board.available,
                "is_end": self.is_end,
                "who_win": self.who_win,
                "turn": self.board.current_player,
                "point": str(point)}


if __name__ == '__main__':
    # two_human_run()
    play_with_AI('./model/best_13_policy_model')


