"""
Monte Carlo Tree Search implementation(MCTS)
Also See
https://en.wikipedia.org/wiki/Monte_Carlo_tree_search

@author : djh-sudo
If you have any question, pls contact me
at djh113@126.com
"""

import numpy as np
import copy
import board
from operator import itemgetter


def rollout_policy_fn(b: board.Board):
    """ fast policy """
    # rollout randomly
    action_p = np.random.rand(len(b.available))
    return zip(b.available, action_p)


def policy_val_fn(b: board.Board):
    """  output score of the state """
    action_p = np.ones(len(b.available)) / len(b.available)
    return zip(b.available, action_p), 0


def softmax(x):
    p = np.exp(x - np.max(x))
    p /= np.sum(p)
    return p


class TreeNode(object):
    """
    Each node in MCTS, which keeps track of its own value Q,
    prior probability P, and score u
    """

    def __init__(self, parent, prior):
        self.m_parent = parent
        # map(action, TreeNode)
        self.m_child = {}
        self.m_visit = 0
        self.m_Q = 0
        self.m_u = 0
        self.m_P = prior

    def expand(self, action_p):
        """
        Creating new node (child)
        action_p is list of action and corresponding prior probability
        according to policy function
        """
        for action, pro in action_p:
            if action not in self.m_child:
                self.m_child[action] = TreeNode(self, pro)

    def select(self, c):
        """
        Select action among child which Q is max
        Return (action, node)
        """
        return max(self.m_child.items(), key=lambda node: node[1].get_value(c))

    def update(self, leaf_val):
        """
        Update node value from leaf
        leaf_val : value evaluated from subtree
        """
        self.m_visit += 1
        # update Q
        self.m_Q += 1.0 * (leaf_val - self.m_Q) / self.m_visit

    def updates(self, leaf_val):
        """
        Update node value recursively
        """
        if self.m_parent:
            self.m_parent.updates(-leaf_val)
        self.update(leaf_val)

    def get_value(self, c):
        """
        calculate the value for this node
        c is a hyper-parameter, which measure the degree of
        impact of the value Q
        Q / ni + c * p * sqrt(n / (ni + 1))
        """

        self.m_u = (c * self.m_P * np.sqrt(self.m_parent.m_visit) / (1 + self.m_visit))
        return self.m_Q + self.m_u

    def is_leaf(self):
        """ check node is leaf """
        return self.m_child == {}

    def is_root(self):
        return self.m_parent is None


class MCTS(object):
    """ Monte Carlo Tree Search """

    def __init__(self, policy_val_f, c=5, n_play=1000):
        """
        policy_val_f: function that takes board status as input,
        output the (action, probability) and score
        c: hyperparameter, which controls how quickly exploration
        converges to max-val policy
        """
        self.m_root = TreeNode(None, 1.0)
        self.m_policy = policy_val_f
        self.m_c = c
        self.m_nplay = n_play

    def m_playout(self, state: board.Board):
        node = self.m_root
        while True:
            if node.is_leaf():
                break
            # select next node to go
            action, node = node.select(self.m_c)
            state.draw(action)
            # update
            state.can_play()
        action_p, _ = self.m_policy(state)
        # check
        end, winner = state.game_end()
        if not end:
            node.expand(action_p)
        # evaluation the leaf node
        leaf_val = self.m_eval_rollout(state)
        # update value
        node.updates(-leaf_val)

    def m_eval_rollout(self, state: board.Board, limit=128):
        """
        using rollout policy to play game until game over
        return 1 if current player win,
        -1 if it is lost and 0 if it is a tie
        """
        player = state.get_current_player()
        for i in range(limit):
            end, winner = state.game_end()
            if end:
                break
            action_p = rollout_policy_fn(state)
            max_action = max(action_p, key=itemgetter(1))[0]
            state.draw(max_action)
        if winner == -1:
            return 0
        else:
            return 1 if winner == player else -1

    def get_move(self, state: board.Board):
        """ return selected state """
        for n in range(self.m_nplay):
            state_copy = copy.deepcopy(state)
            self.m_playout(state_copy)
        return max(self.m_root.m_child.items(), key=lambda node: node[1].m_visit)[0]

    def update_and_move(self, last_move):
        """
        Step forward in the tree
        """
        if last_move in self.m_root.m_child:
            self.m_root = self.m_root.m_child[last_move]
            self.m_root.m_parent = None
        else:
            self.m_root = TreeNode(None, 1.0)

    def __str__(self):
        return 'MCTS'


class MCTS_Player(object):
    def __init__(self, c=5, playout=20):
        self.mcts = MCTS(policy_val_fn, c, playout)

    def set_index(self, p):
        self.player = p

    def reset(self):
        self.mcts.update_and_move(-1)

    def action(self, b: board.Board):
        option = b.available
        if len(option) > 0:
            move = self.mcts.get_move(b)
            self.mcts.update_and_move(-1)
            return move
        else:
            print('[WARNING]')

    def __str__(self):
        return 'MCTS{}'.format(self.player)


class AI_MCTS(object):
    """ Monte Carlo Tree Search """

    def __init__(self, policy_val_f, c=5, n_play=1000):
        """
        policy_val_f: function that takes board status as input,
        output the (action, probability) and score
        c: hyperparameter, which controls how quickly exploration
        converges to max-val policy
        """
        self.m_root = TreeNode(None, 1.0)
        self.m_policy = policy_val_f
        self.m_c = c
        self.m_nplay = n_play

    def m_playout(self, state: board.Board):
        node = self.m_root
        while True:
            if node.is_leaf():
                break
            # select next node
            action, node = node.select(self.m_c)
            state.draw(action)
            # update available
            state.can_play()
        # eval
        action_p, leaf_val = self.m_policy(state)
        # check game is end
        end, winner = state.game_end()
        if not end:
            node.expand(action_p)
        else:
            # tie
            if winner == -1:
                leaf_val = 0.0
            else:
                leaf_val = 1.0 if winner == state.get_current_player() else -1.0
        # update
        node.updates(-leaf_val)

    def get_move_p(self, state: board.Board, tmp=1e-3):
        self.m_nplay = len(state.available) * 2
        for n in range(self.m_nplay):
            state_copy = copy.deepcopy(state)
            self.m_playout(state_copy)

        # calculate the move probability
        act_visit = [(act, node.m_visit) for act, node in self.m_root.m_child.items()]
        acts, visits = zip(*act_visit)
        act_p = softmax(1.0 / tmp * np.log(np.array(visits) + 1e-10))
        return acts, act_p

    def update_and_move(self, last_move):
        if last_move in self.m_root.m_child:
            self.m_root = self.m_root.m_child[last_move]
            self.m_root.m_parent = None
        else:
            self.m_root = TreeNode(None, 1.0)


class AI_MCTS_Player(object):
    def __init__(self, policy_val_fun, c=5, playout=200, self_play=False):
        self.mcts = AI_MCTS(policy_val_fun, c, playout)
        self.m_self_play = self_play

    def set_index(self, p):
        self.player = p

    def reset(self):
        self.mcts.update_and_move(-1)

    def action(self, b: board.Board, tmp=1e-3, ret_p=False):
        moves = b.available
        # pi
        moves_p = np.zeros(b.width * b.height)
        if len(moves) > 0:
            acts, prob = self.mcts.get_move_p(b, tmp)
            moves_p[list(acts)] = prob
            if self.m_self_play:
                # self-play training
                move = np.random.choice(
                    acts,
                    p=0.75 * prob + 0.25 * np.random.dirichlet(0.3 * np.ones(len(prob))))
                # update
                self.mcts.update_and_move(move)
            else:
                move = np.random.choice(acts, p=prob)
                self.mcts.update_and_move(-1)

            if ret_p:
                return move, moves_p
            else:
                return move
        else:
            print('[WARNING]')