# -*- coding: utf-8 -*-
"""
training the AI-Reversi model

@author : djh-sudo
If you have any question, pls contact me
at djh113@126.com
"""
import random
from collections import deque, defaultdict

import numpy as np
from board import Board, Game
from mcts import AI_MCTS_Player, MCTS_Player
from policyValueNet import ValueNet


class Train(object):
    """ training network """

    def __init__(self, model=None):
        self.width = 8
        self.height = 8
        self.episode = 0
        self.board = Board(self.width, self.height)
        self.game = Game(self.board)
        # parameter setting
        self.learning_rate = 5e-4
        self.mul_lr = 1.0
        self.tmp = 1.0
        self.n_playout = 5
        self.c = 4
        self.buffer_size = 20000
        self.batch_size = 2048
        self.data_buffer = deque(maxlen=self.buffer_size)
        self.play_bs = 1
        self.epochs = 5
        self.kl_target = 0.02
        self.check = 50
        self.game_number = 15000
        self.win_ratio = 0.0
        self.mcts_play_num = 6
        if model:
            self.policy_val_net = ValueNet(self.width, self.height, model)
        else:
            self.policy_val_net = ValueNet(self.width, self.height)

        self.mcts_player = AI_MCTS_Player(self.policy_val_net.policy_value_fn,
                                          self.c, self.n_playout, True)

    def get_extend_data(self, play_data):
        """
        extending data through rotating and flipping
        play_data: [(state, mcts_p, winner_score)]
        """

        extend_data = []
        for state, mcts_p, win_score in play_data:
            for i in range(1, 5):
                # rotating the data
                equi_state = np.array([np.rot90(s, i) for s in state])
                equi_mcts_prob = np.rot90(np.flipud(mcts_p.reshape(self.width, self.height)), i)
                extend_data.append((equi_state,
                                    np.flipud(equi_mcts_prob).flatten(), win_score))
                # flip horizontally
                equi_state = np.array([np.fliplr(s) for s in equi_state])
                equi_mcts_prob = np.fliplr(equi_mcts_prob)
                extend_data.append((equi_state,
                                    np.flipud(equi_mcts_prob).flatten(), win_score))
        return extend_data

    def collect_data(self, game_num=1):
        for i in range(game_num):
            winner, play_data = self.game.start_self_play(self.mcts_player, p=self.tmp, shown=False)
            play_data = list(play_data)[:]
            self.episode = len(play_data)
            play_data = self.get_extend_data(play_data)
            self.data_buffer.extend(play_data)

    def policy_update(self, step: int):
        """
        update the policy value network
        """
        mini_batch = random.sample(self.data_buffer, self.batch_size)
        state_batch = [data[0] for data in mini_batch]
        mcts_p_batch = [data[1] for data in mini_batch]
        win_batch = [data[2] for data in mini_batch]
        old_p, old_v = self.policy_val_net.policy_value(state_batch)
        for i in range(self.epochs):
            loss, entropy = self.policy_val_net.train_step(
                state_batch, mcts_p_batch, win_batch, self.learning_rate * self.mul_lr, step * self.epochs + i)
            new_p, new_v = self.policy_val_net.policy_value(state_batch)
            kl = np.mean(np.sum(old_p * (
                    np.log(old_p + 1e-10) - np.log(new_p + 1e-10)), axis=1))
            if kl > self.kl_target * 5:
                break
        # adjust lr adaptively
        if kl > self.kl_target * 2 and self.mul_lr > 0.05:
            self.mul_lr /= 1.5
        elif kl < self.kl_target / 2 and self.mul_lr < 10:
            self.mul_lr *= 1.5

        print(("kl:{:.5f},"
               "lr_multiplier:{:.3f},"
               "loss:{},"
               "entropy:{}").format(kl, self.mul_lr, loss, entropy))
        return loss, entropy

    def policy_eval(self, game_num=10):
        """
        evaluating the trained policy by playing with MCTS-player
        using for training process
        """
        cur_mcts_player = AI_MCTS_Player(self.policy_val_net.policy_value_fn,
                                         self.c, self.n_playout)
        mcts_player = MCTS_Player(self.c, self.mcts_play_num)

        win_cnt = defaultdict(int)
        for i in range(game_num):
            winner = self.game.start_play(cur_mcts_player, mcts_player, i % 2, shown=False)
            win_cnt[winner] += 1
        win_ratio = 1.0 * (win_cnt[1] + 0.5 * win_cnt[-1]) / game_num
        print("num_playouts:{}, win: {}, lose: {}, tie:{}".format(
            self.mcts_play_num, win_cnt[1], win_cnt[2], win_cnt[-1]))
        return win_ratio

    def run(self):
        """  running the train network """
        try:
            for i in range(self.game_number):
                self.collect_data(self.play_bs)
                print("batch i:{}, episode_len:{}".format(
                    i + 1, self.episode))
                if len(self.data_buffer) > self.batch_size:
                    loss, entropy = self.policy_update(i)
                # check model and save parameter
                if (i + 1) % self.check == 0:
                    win_ratio = self.policy_eval()
                    self.policy_val_net.save_model('./cur_{}_policy_model'.format(self.mcts_play_num))
                    if win_ratio > self.win_ratio:
                        self.win_ratio = win_ratio
                        # update the best policy
                        self.policy_val_net.save_model('./best_{}_policy_model'.format(self.mcts_play_num))
                        if win_ratio >= 0.90 and self.mcts_play_num <= 30:
                            self.mcts_play_num += 2
                            self.win_ratio = 0.0
        except KeyboardInterrupt:
            print('quit by user')


if __name__ == '__main__':
    train_obj = Train()
    train_obj.run()
