# -*- coding: utf-8 -*-
"""
need Tensorflow 1.5
using CNN to evaluate board
Thanks to the open source project!
https://github.com/junxiaosong/AlphaZero_Gomoku

@author : djh-sudo
Also See
If you have any question, pls contact me
at djh113@126.com
"""
import os
import numpy as np
import tensorflow as tf


class ValueNet(object):
    def __init__(self, width=8, height=8, model=None):
        self._width = width
        self._height = height
        # CNN Convolution Neural Network
        # Step 1. Input data
        self.input_state = tf.placeholder(tf.float32, shape=[None, 4, width, height])
        self.input_states = tf.transpose(self.input_state, [0, 2, 3, 1])
        # Step 2. Convolution
        # Conv1
        self.conv1 = tf.layers.conv2d(inputs=self.input_states,
                                      filters=32, kernel_size=[3, 3],
                                      padding="same", data_format="channels_last",
                                      activation=tf.nn.relu)
        # Conv2
        self.conv2 = tf.layers.conv2d(inputs=self.conv1, filters=64,
                                      kernel_size=[3, 3], padding="same",
                                      data_format="channels_last",
                                      activation=tf.nn.relu)
        # Conv3
        self.conv3 = tf.layers.conv2d(inputs=self.conv2, filters=128,
                                      kernel_size=[3, 3], padding="same",
                                      data_format="channels_last",
                                      activation=tf.nn.relu)
        # Step 3. Action Networks
        self.action_conv = tf.layers.conv2d(inputs=self.conv3, filters=4,
                                            kernel_size=[1, 1], padding="same",
                                            data_format="channels_last",
                                            activation=tf.nn.relu)
        # Flatten
        self.action_conv_flat = tf.reshape(self.action_conv, [-1, 4 * width * height])
        # FC
        self.action_fc = tf.layers.dense(inputs=self.action_conv_flat,
                                         units=width * height,
                                         activation=tf.nn.log_softmax)
        # Step 4. Evaluation
        self.evaluation_conv = tf.layers.conv2d(inputs=self.conv3, filters=2,
                                                kernel_size=[1, 1],
                                                padding="same",
                                                data_format="channels_last",
                                                activation=tf.nn.relu)
        self.evaluation_conv_flat = tf.reshape(self.evaluation_conv, [-1, 2 * width * height])
        # Full Connection 1
        self.evaluation_fc1 = tf.layers.dense(inputs=self.evaluation_conv_flat,
                                              units=64, activation=tf.nn.relu)
        # Full Connection 2
        # the score of evaluation on current state
        self.evaluation_fc2 = tf.layers.dense(inputs=self.evaluation_fc1,
                                                  units=1, activation=tf.nn.tanh)
        # Label: win or not
        self.labels = tf.placeholder(tf.float32, shape=[None, 1])

        # Value Loss function
        self.value_loss = tf.losses.mean_squared_error(self.labels,
                                                       self.evaluation_fc2)
        # Policy Loss function
        self.mcts_probs = tf.placeholder(tf.float32, shape=[None, width * height])

        self.policy_loss = tf.negative(tf.reduce_mean(
            tf.reduce_sum(tf.multiply(self.mcts_probs, self.action_fc), 1)))

        # L2 penalty (regularization)
        l2_penalty_beta = 1e-4
        vars = tf.trainable_variables()
        l2_penalty = l2_penalty_beta * tf.add_n(
            [tf.nn.l2_loss(v) for v in vars if 'bias' not in v.name.lower()])
        # sum all loss
        self.loss = self.value_loss + self.policy_loss + l2_penalty
        tf.summary.scalar('loss', self.loss)
        # optimizer
        self.learning_rate = tf.placeholder(tf.float32)
        self.optimizer = tf.train.AdamOptimizer(learning_rate=self.learning_rate).minimize(self.loss)

        # Make a session
        self.session = tf.Session()

        # calc policy entropy, for monitoring only
        self.entropy = tf.negative(tf.reduce_mean(
                tf.reduce_sum(tf.exp(self.action_fc) * self.action_fc, 1)))
        tf.summary.scalar('entropy', self.entropy)
        # Initialize variables
        init = tf.global_variables_initializer()
        self.session.run(init)

        # For saving and restoring
        self.saver = tf.train.Saver()
        if model is not None:
            self.load_model(model)

        # saving logs
        self.merged = tf.summary.merge_all()
        self.writer = tf.summary.FileWriter("logs/")

    def policy_value(self, state_batch):
        """
        input: a batch of states
        output: a batch of action probabilities and state values
        """
        log_act_probs, value = self.session.run(
            [self.action_fc, self.evaluation_fc2],
            feed_dict={self.input_state: state_batch})
        act_probs = np.exp(log_act_probs)
        return act_probs, value

    def policy_value_fn(self, board):
        """
        input: board
        output: a list of (action, probability) tuples for each available
        action and the score of the board state
        """
        legal_positions = board.available
        current_state = np.ascontiguousarray(board.current_state().reshape(
            -1, 4, self._width, self._height))
        act_probs, value = self.policy_value(current_state)
        act_probs = zip(legal_positions, act_probs[0][legal_positions])
        return act_probs, value

    def train_step(self, state_batch, mcts_probs, winner_batch, lr, step: int):
        winner_batch = np.reshape(winner_batch, (-1, 1))
        loss, entropy, _ = self.session.run(
            [self.loss, self.entropy, self.optimizer],
            feed_dict={self.input_state: state_batch,
                       self.mcts_probs: mcts_probs,
                       self.labels: winner_batch,
                       self.learning_rate: lr})
        if step % 5 == 0:
            res = self.session.run(
                self.merged,
                feed_dict={self.input_state: state_batch,
                           self.mcts_probs: mcts_probs,
                           self.labels: winner_batch,
                           self.learning_rate: lr})
            self.writer.add_summary(res, global_step=step // 5)
        return loss, entropy

    def save_model(self, model_path):
        """ save model to local file """
        self.saver.save(self.session, model_path)

    def load_model(self, model_path):
        """ load model from local file """
        self.saver.restore(self.session, model_path)
