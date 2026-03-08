"""
RL-based move generator (v4).

At inference time this loads a trained DQN model and uses it to pick the
best move from the legal move list – no exploration (epsilon = 0).

Usage: works as a drop-in replacement for v1/v2/v3 via the AI dispatcher.
"""

import os
import torch
import numpy as np

from .rl.agent import BlokusNet
from ..configurations.constants import BOARD_SIZE, ALL_PIECES, NUM_PLAYERS

# Path to the trained model weights
MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "blokus_dqn_final.pt"
)

# Lazy-loaded singleton so we only load weights once
_net: BlokusNet | None = None


def _get_net() -> BlokusNet:
    global _net
    if _net is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _net = BlokusNet(max_actions=5000).to(device)
        if os.path.exists(MODEL_PATH):
            _net.load_state_dict(torch.load(MODEL_PATH, map_location=device))
            _net.eval()
            print(f"[v4_rl] Loaded model from {MODEL_PATH}")
        else:
            print(f"[v4_rl] WARNING: No trained model found at {MODEL_PATH} – using random weights!")
    return _net


def generate_move(legal_moves, board, round):
    """Pick the best move according to the trained DQN.

    Falls back to the first legal move if something goes wrong.
    """
    if not legal_moves:
        return None

    net = _get_net()
    device = next(net.parameters()).device

    # Build observation tensors (same format the agent was trained on)
    board_t = torch.tensor(board, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(device)

    # We don't have full piece-mask info here, so pass zeros as placeholder
    # TODO: thread full observation through once you wire this into the env
    aux_dim = len(ALL_PIECES) * NUM_PLAYERS + NUM_PLAYERS
    aux_t = torch.zeros(1, aux_dim, dtype=torch.float32).to(device)

    with torch.no_grad():
        q_values = net(board_t, aux_t).squeeze(0)
        # Only consider the first len(legal_moves) slots
        q_legal = q_values[: len(legal_moves)]
        best_idx = int(q_legal.argmax().item())

    return legal_moves[best_idx]
