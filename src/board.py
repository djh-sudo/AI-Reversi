# -*- coding: utf-8 -*-
"""
Reversi Game Board

@author djh-sudo
If you have any question, pls contact me
at djh113@126.com
"""
import numpy as np
from collections import Counter
from itertools import chain

EMPTY = 0
BLACK = 1
WHITE = 2
OPTION = 3
TODO = None


class Board(object):
    def __init__(self, width=8, height=8):
        self.width = width
        self.height = height
        assert width == height, 'Invalid Board'
        # role of two player
        self.role = [BLACK, WHITE]
        self.current_player = BLACK
        # board status
        self.status = None
        # other init
        self.available = list()
        self.last_board = None

    def init_board(self, start_player=0):
        self.current_player = self.role[start_player]
        # available localtion
        # self.available = [19, 26, 37, 44]
        # init status
        self.status = np.zeros(self.width * self.height, int)
        self.status = np.array(self.status).reshape(self.width, self.height)
        # place the piece
        self.status[3][4], self.status[4][3] = BLACK, BLACK
        self.status[3][3], self.status[4][4] = WHITE, WHITE
        # option
        self.status[3][2] = OPTION
        self.status[5][4] = OPTION
        self.status[4][5] = OPTION
        self.status[2][3] = OPTION
        self.can_play()
        self.last_board = self.status

    def point_to_location(self, point: int):
        """
        8 * 8 board:
            0   1   2   3   4   5   6   7
            -----------------------------
        0   0   1   2   3   4   5   6   7
        1   8   9   10  11  12  13  14  15
        2   16  17  18  19  20  21  22  23
        3   24  25  26  27  28  29  30  31
        4   32  33  34  35  36  37  38  39
        5   40  41  42  43  44  45  46  47
        6   48  49  50  51  52  53  54  55
        7   56  57  58  59  60  61  62  63
            -----------------------------
        the f(26) -> location(3, 2)
        at the beginning of game, The scene is as follows:
            27(WHITE) 28(BLACK)
            35(BLACK) 36(WHITE)
        """
        h = point // self.width
        w = point % self.height
        return h, w

    def location_to_point(self, location):
        assert len(location) == 2, 'Invalid location!'
        h = location[0]
        w = location[1]
        if h not in range(self.height) or w not in range(self.width):
            print('Invalid height or width!')
            return -1
        return h * self.width + w

    def current_state(self):
        """
        state shape : 4 * w * h
        :return: state of current player
        """
        features = np.zeros((4, self.width, self.height))
        opponent = self.role[0] if self.current_player == self.role[1] else self.role[1]

        for i in range(self.height):
            for j in range(self.width):
                if self.status[i][j] == self.current_player:
                    features[0][i][j] = 1.0
                elif self.status[i][j] == opponent:
                    features[1][i][j] = 1.0
                elif self.status[i][j] == OPTION:
                    features[2][i][j] = 1.0

        # who is current player
        if self.current_player == self.role[0]:
            features[3][:, :] = 1.0
        return features

    def judge(self, x: int, y: int, eat_flag=False, grid_num=8):
        """
        given position(x, y) and return number of eating opponent piece
        eat_flag means whether modify the state
        """
        direction = [(1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1)]
        temp_x, temp_y = x, y
        eat_num = 0
        if not (self.status[temp_x][temp_y] == EMPTY or self.status[temp_x][temp_y] == OPTION):
            return 0
        opponent = self.role[0] if self.current_player == self.role[1] else self.role[1]
        for i in range(grid_num):
            # go in some direction
            temp_x += direction[i][0]
            temp_y += direction[i][1]
            if 0 <= temp_x < grid_num and 0 <= temp_y < grid_num \
                    and self.status[temp_x][temp_y] == opponent:
                temp_x += direction[i][0]
                temp_y += direction[i][1]
                while grid_num > temp_x >= 0 and grid_num > temp_y >= 0:
                    # empty place, can't take a pawn
                    if self.status[temp_x][temp_y] == EMPTY or self.status[temp_x][temp_y] == OPTION:
                        break
                    # find your own piece
                    if self.status[temp_x][temp_y] == self.current_player:
                        if eat_flag:
                            self.status[x][y] = self.current_player
                            temp_x -= direction[i][0]
                            temp_y -= direction[i][1]
                            while temp_x != x or temp_y != y:
                                # mark as own
                                self.status[temp_x][temp_y] = self.current_player
                                # back up
                                temp_x -= direction[i][0]
                                temp_y -= direction[i][1]
                                # update eat number
                                eat_num += 1
                        else:
                            temp_x -= direction[i][0]
                            temp_y -= direction[i][1]
                            while temp_x != x or temp_y != y:
                                # back up
                                temp_x -= direction[i][0]
                                temp_y -= direction[i][1]
                                # update eat number
                                eat_num += 1
                        break
                    # not find own piece
                    temp_x += direction[i][0]
                    temp_y += direction[i][1]
            # change the direction
            temp_x, temp_y = x, y
        return eat_num

    def can_play(self):
        flag = False
        self.available = []
        for i in range(8):
            for j in range(8):
                if self.status[i][j] == OPTION:
                    self.status[i][j] = EMPTY
                if self.judge(i, j) > 0:
                    self.status[i][j] = OPTION
                    self.available.append(self.location_to_point([i, j]))
                    flag = True
        return flag

    def draw(self, point):
        x, y = self.point_to_location(point)
        self.last_board = self.status
        self.judge(x, y, True)
        # change the player
        self.current_player = self.role[0] \
            if self.current_player == self.role[1] else self.role[1]

    def game_end(self):
        """ check who win the game """
        if not self.can_play():
            self.current_player = self.role[0] \
                if self.current_player == self.role[1] else self.role[1]

            if not self.can_play():
                flatten = list(chain.from_iterable(self.status))
                res = Counter(flatten)
                black = res[self.role[0]]
                white = res[self.role[1]]
                if black < white:
                    res = self.role[1]
                elif black > white:
                    res = self.role[0]
                else:
                    res = -1
                return True, res
            else:
                return False, -1
        else:
            return False, -1

    def get_current_player(self):
        return self.current_player


class Game(object):
    def __init__(self, board: Board):
        self.board = board

    def update(self, player1, player2):
        """ draw the board """
        width, height = self.board.width, self.board.height

        for x in range(width):
            print("{0:4}".format(x), end='')
        print('\r\n')
        for i in range(height):
            print("{0:2d}".format(i), end='')
            for j in range(width):
                p = self.board.status[i][j]
                if p == player1:
                    print('X'.center(4), end='')
                elif p == player2:
                    print('O'.center(4), end='')
                elif p == OPTION:
                    print('*'.center(4), end='')
                else:
                    print('_'.center(4), end='')
            print('\n')

    def start_play(self, player1, player2, start_player=0, shown=True):
        if start_player not in (0, 1):
            raise Exception('player index error')

        self.board.init_board(start_player)
        p1, p2 = self.board.role
        player1.set_index(p1)
        player2.set_index(p2)
        players = {p1: player1, p2: player2}
        if shown:
            self.update(player1.player, player2.player)
        while True:
            current_player = self.board.get_current_player()
            who = players[current_player]
            point = who.action(self.board)
            # place the piece and change the role
            self.board.draw(point)
            # check game state
            end, winner = self.board.game_end()
            if shown:
                self.update(player1.player, player2.player)
            if end:
                return winner

    def start_self_play(self, player, shown=False, p=1e-3):
        """
        start a self-play, using MCTS player
        then store the self-play data(status, probability,z-score) for training
        """
        self.board.init_board()
        p1, p2 = self.board.role
        states, mcts_p, current = [], [], []
        while True:
            point, move_p = player.action(self.board, p, True)
            # store
            states.append(self.board.current_state())
            mcts_p.append(move_p)
            current.append(self.board.current_player)
            # go step
            self.board.draw(point)
            # check game is over
            end, winner = self.board.game_end()
            if shown:
                self.update(p1, p2)
            if end:
                winner_score = np.zeros(len(current))
                if winner != -1:
                    winner_score[np.array(current) == winner] = 1.0
                    winner_score[np.array(current) != winner] = -1.0
                # reset
                player.reset()

                return winner, zip(states, mcts_p, winner_score)
