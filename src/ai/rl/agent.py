"""
Deep RL Agent for Blokus

This module defines the neural network architecture and the agent wrapper
that the training loop will use.

Architecture placeholder: a simple CNN + MLP that takes the board + piece
mask and outputs Q-values (or policy logits) over the action space.

TODO – Replace / extend with your preferred approach:
  • DQN  – simple to start, discrete action space fits well
  • PPO  – more stable for self-play
  • AlphaZero-style MCTS + policy-value network – strongest, most complex
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import random
from collections import deque

from ...configurations.constants import BOARD_SIZE, ALL_PIECES, NUM_PLAYERS


# ---------------------------------------------------------------------------
# Neural network
# ---------------------------------------------------------------------------

class BlokusNet(nn.Module):
    """Minimal CNN that reads the board + auxiliary features and outputs
    a value for each possible action slot.

    Input
    -----
    board  : (batch, 1, BOARD_SIZE, BOARD_SIZE)  – raw cell values 0..4
    aux    : (batch, aux_dim)                    – piece mask + current player

    Output
    ------
    q_values : (batch, max_actions)
    """

    def __init__(self, max_actions: int = 5000):
        super().__init__()

        self.aux_dim = len(ALL_PIECES) * NUM_PLAYERS + NUM_PLAYERS

        # --- Board encoder (small CNN) ---
        self.conv = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(4),  # → (batch, 64, 4, 4)
        )
        conv_flat = 64 * 4 * 4  # 1024

        # --- Fully-connected head ---
        self.fc = nn.Sequential(
            nn.Linear(conv_flat + self.aux_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, max_actions),
        )

    def forward(self, board: torch.Tensor, aux: torch.Tensor) -> torch.Tensor:
        x = self.conv(board)
        x = x.view(x.size(0), -1)
        x = torch.cat([x, aux], dim=1)
        return self.fc(x)


# ---------------------------------------------------------------------------
# Replay buffer (for DQN-style training)
# ---------------------------------------------------------------------------

class ReplayBuffer:
    """Simple fixed-size experience replay buffer."""

    def __init__(self, capacity: int = 50_000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return states, actions, rewards, next_states, dones

    def __len__(self):
        return len(self.buffer)


# ---------------------------------------------------------------------------
# Agent wrapper
# ---------------------------------------------------------------------------

class DQNAgent:
    """Minimal DQN agent that wraps BlokusNet for action selection & learning.

    TODO – Extend with:
    * Target network + periodic sync
    * Epsilon decay schedule
    * Double DQN / Dueling DQN
    * Prioritised experience replay
    """

    def __init__(
        self,
        max_actions: int = 5000,
        lr: float = 1e-3,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
        epsilon_decay: int = 10_000,
        buffer_capacity: int = 50_000,
        batch_size: int = 64,
        device: str | None = None,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.max_actions = max_actions
        self.gamma = gamma
        self.batch_size = batch_size

        # Epsilon-greedy schedule
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.steps_done = 0

        # Networks
        self.policy_net = BlokusNet(max_actions).to(self.device)
        self.target_net = BlokusNet(max_actions).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = torch.optim.Adam(self.policy_net.parameters(), lr=lr)
        self.replay = ReplayBuffer(capacity=buffer_capacity)

    # ----- helpers to convert observations → tensors -----

    def _obs_to_tensors(self, obs: dict):
        board = torch.tensor(obs["board"], dtype=torch.float32).unsqueeze(0).unsqueeze(0)
        aux = np.concatenate([obs["pieces"], obs["current_player"]])
        aux = torch.tensor(aux, dtype=torch.float32).unsqueeze(0)
        return board.to(self.device), aux.to(self.device)

    # ----- action selection -----

    @property
    def epsilon(self) -> float:
        return self.epsilon_end + (self.epsilon_start - self.epsilon_end) * \
            np.exp(-self.steps_done / self.epsilon_decay)

    def select_action(self, obs: dict, num_legal_moves: int) -> int:
        """Epsilon-greedy action selection over *legal* moves only."""
        self.steps_done += 1

        if random.random() < self.epsilon:
            return random.randrange(num_legal_moves)

        with torch.no_grad():
            board_t, aux_t = self._obs_to_tensors(obs)
            q_values = self.policy_net(board_t, aux_t).squeeze(0)
            # Mask illegal actions to -inf
            q_values[num_legal_moves:] = float("-inf")
            return int(q_values.argmax().item())

    # ----- learning step -----

    def learn(self):
        """Sample a mini-batch and do one gradient step.

        TODO – This is a bare-bones DQN update.  Improve with:
        * Target network sync every N steps
        * Gradient clipping
        * Logging losses to TensorBoard / W&B
        """
        if len(self.replay) < self.batch_size:
            return None  # not enough data yet

        states, actions, rewards, next_states, dones = self.replay.sample(self.batch_size)

        # Convert to tensors (simple loop – optimise later with vectorisation)
        boards, auxs = [], []
        next_boards, next_auxs = [], []
        for s, ns in zip(states, next_states):
            b, a = self._obs_to_tensors(s)
            nb, na = self._obs_to_tensors(ns)
            boards.append(b); auxs.append(a)
            next_boards.append(nb); next_auxs.append(na)

        boards = torch.cat(boards)
        auxs = torch.cat(auxs)
        next_boards = torch.cat(next_boards)
        next_auxs = torch.cat(next_auxs)
        actions_t = torch.tensor(actions, dtype=torch.long, device=self.device)
        rewards_t = torch.tensor(rewards, dtype=torch.float32, device=self.device)
        dones_t = torch.tensor(dones, dtype=torch.float32, device=self.device)

        # Q(s, a)
        q_values = self.policy_net(boards, auxs).gather(1, actions_t.unsqueeze(1)).squeeze(1)

        # max_a' Q_target(s', a')
        with torch.no_grad():
            next_q = self.target_net(next_boards, next_auxs).max(dim=1).values
            target = rewards_t + self.gamma * next_q * (1 - dones_t)

        loss = F.mse_loss(q_values, target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()

    def sync_target(self):
        """Copy policy net weights → target net."""
        self.target_net.load_state_dict(self.policy_net.state_dict())

    # ----- persistence -----

    def save(self, path: str):
        torch.save(self.policy_net.state_dict(), path)

    def load(self, path: str):
        self.policy_net.load_state_dict(torch.load(path, map_location=self.device))
        self.target_net.load_state_dict(self.policy_net.state_dict())
