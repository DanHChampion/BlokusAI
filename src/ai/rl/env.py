"""
Blokus Gymnasium Environment

Wraps the core Blokus game logic into a Gymnasium-compatible environment
so that a Deep RL agent can interact with it through step / reset.

Key design decisions
--------------------
* Observation  – Dict with the 20×20 board, a binary mask of remaining pieces
                 per player, and a one-hot current-player indicator.
* Action       – An integer index into the list of legal moves that the game
                 engine produces each turn.  The legal-move list changes every
                 step, so the agent receives it alongside the observation.
* Reward       – Placeholder; you will want to experiment with shaping.
* Opponents    – By default the other 3 seats are filled by the existing v3
                 evaluator so the RL agent can learn against a reasonable
                 baseline from day one.
"""

import copy
import gymnasium as gym
import numpy as np
from gymnasium import spaces

from ...configurations.constants import BOARD_SIZE, NUM_PLAYERS, ALL_PIECES
from ...helpers import logic
from ...helpers.piece import Piece
from ...helpers.player import Player


class BlokusEnv(gym.Env):
    """Single-agent Blokus environment (1 RL seat, 3 opponent seats)."""

    metadata = {"render_modes": ["ansi"]}

    def __init__(self, rl_player_colour: int = 1, opponent_ai: str = "v3"):
        super().__init__()

        self.board_size = BOARD_SIZE
        self.num_players = NUM_PLAYERS
        self.all_piece_types = ALL_PIECES
        self.num_piece_types = len(ALL_PIECES)

        self.rl_colour = rl_player_colour
        self.opponent_ai = opponent_ai

        # --- Observation space --------------------------------------------------
        self.observation_space = spaces.Dict({
            # Board: each cell is 0 (empty) or player colour 1-4
            "board": spaces.Box(
                low=0, high=NUM_PLAYERS,
                shape=(BOARD_SIZE, BOARD_SIZE), dtype=np.int8,
            ),
            # Binary mask: 1 = piece still available (per player)
            "pieces": spaces.MultiBinary(self.num_piece_types * NUM_PLAYERS),
            # One-hot current player
            "current_player": spaces.MultiBinary(NUM_PLAYERS),
        })

        # Action space is variable (depends on legal moves), but Gymnasium needs
        # a fixed upper-bound.  We use Discrete with a generous cap and mask
        # illegal actions at inference time.
        self.max_actions = 5000  # empirical upper-bound; legal moves rarely exceed this
        self.action_space = spaces.Discrete(self.max_actions)

        # Will be populated in reset()
        self.board = None
        self.players = None
        self.current_player = None
        self.legal_moves = []
        self.round = 0
        self.done = False

    # ------------------------------------------------------------------
    # Gymnasium API
    # ------------------------------------------------------------------

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.board = [[0] * self.board_size for _ in range(self.board_size)]
        self.round = 0
        self.done = False

        # Create players – colour 1..4
        self.players = []
        for colour in range(1, self.num_players + 1):
            ai_version = "rl" if colour == self.rl_colour else self.opponent_ai
            p = Player(colour, ai=ai_version)
            p.remaining_pieces = [Piece(pt, colour) for pt in self.all_piece_types]
            self.players.append(p)

        self.turn_index = 0
        self.round = 1

        # Fast-forward opponent turns that come before the RL player
        self._advance_to_rl_turn()

        obs = self._get_obs()
        info = self._get_info()
        return obs, info

    def step(self, action: int):
        """Execute the RL agent's chosen action, then let opponents play."""
        assert not self.done, "Episode is done – call reset()."

        reward = 0.0

        # Validate action
        if action >= len(self.legal_moves):
            # Illegal / out-of-range action → small penalty, turn is skipped
            reward = -1.0
            obs = self._get_obs()
            return obs, reward, self.done, False, self._get_info()

        # Apply the RL agent's move
        move = self.legal_moves[action]
        self._apply_move(self.current_player, move)

        # --- Reward shaping (placeholder – tweak these!) ----------------------
        reward += self._compute_reward(move)

        # Let opponents take their turns
        self._advance_to_rl_turn()

        obs = self._get_obs()
        info = self._get_info()
        truncated = False

        return obs, reward, self.done, truncated, info

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _advance_to_rl_turn(self):
        """Play all opponent turns until it's the RL player's turn again,
        or until the game ends."""
        while not self.done:
            self.current_player = self.players[self.turn_index % self.num_players]
            if self.turn_index % self.num_players == 0 and self.turn_index > 0:
                self.round += 1

            # Check global game-over
            if all(p.finished for p in self.players):
                self.done = True
                return

            if self.current_player.finished:
                self.turn_index += 1
                continue

            legal_corners = self._get_legal_corners(self.current_player)
            moves = logic.find_legal_moves(
                self.board, legal_corners,
                self.current_player.remaining_pieces, self.current_player.colour,
            )

            if not moves:
                self.current_player.finished = True
                self.turn_index += 1
                continue

            # Is this the RL player's turn?
            if self.current_player.colour == self.rl_colour:
                self.legal_moves = moves
                return  # hand control back to the agent

            # Opponent turn – let the existing AI pick a move
            opponent_move = self.current_player.generate_move(
                moves, self.board, self.round,
            )
            self._apply_move(self.current_player, opponent_move)
            self.turn_index += 1

        # Game ended while opponents were playing
        self.legal_moves = []

    def _apply_move(self, player, move):
        """Place a piece on the board and update the player's piece list."""
        self.board = logic.place_piece(self.board, player.colour, move)
        player.remaining_pieces.remove(move[2])
        self.turn_index += 1

    def _get_legal_corners(self, player):
        if self.round == 1:
            return logic.get_starting_corner(self.board_size, player.colour)
        return logic.find_legal_corners(self.board, player.colour)

    # ------------------------------------------------------------------
    # Observation / info helpers
    # ------------------------------------------------------------------

    def _get_obs(self) -> dict:
        board_np = np.array(self.board, dtype=np.int8)

        pieces_mask = np.zeros(self.num_piece_types * self.num_players, dtype=np.int8)
        for i, player in enumerate(self.players):
            remaining_types = {p.type for p in player.remaining_pieces}
            for j, pt in enumerate(self.all_piece_types):
                if pt in remaining_types:
                    pieces_mask[i * self.num_piece_types + j] = 1

        current_player_oh = np.zeros(self.num_players, dtype=np.int8)
        if self.current_player is not None:
            current_player_oh[self.current_player.colour - 1] = 1

        return {
            "board": board_np,
            "pieces": pieces_mask,
            "current_player": current_player_oh,
        }

    def _get_info(self) -> dict:
        return {
            "round": self.round,
            "legal_moves": self.legal_moves,
            "num_legal_moves": len(self.legal_moves),
            "scores": {p.name: p.current_score() for p in self.players},
        }

    # ------------------------------------------------------------------
    # Reward (placeholder – this is where you experiment!)
    # ------------------------------------------------------------------

    def _compute_reward(self, move) -> float:
        """Return a scalar reward for the RL agent after its move.

        TODO – Ideas to try:
        * +piece.value  for placing large pieces early
        * +len(new_corners) to reward expanding territory
        * -opponent_corners to reward blocking
        * Large +/- bonus at game end based on final ranking
        """
        reward = 0.0

        # Simple baseline: reward = number of cells placed (piece value)
        reward += move[2].value

        # End-of-game bonus
        if self.done:
            rl_player = self.players[self.rl_colour - 1]
            scores = sorted(self.players, key=lambda p: p.current_score())
            if scores[0] == rl_player:
                reward += 100.0   # winner (lowest remaining score)
            else:
                reward -= 50.0

        return reward