"""
Training loop for the Deep RL Blokus agent.

Run from the project root:
    python -m src.ai.rl.training

TODO – Things to add as you iterate:
  • TensorBoard / Weights & Biases logging
  • Curriculum learning (start vs v1_random, then v2, then v3)
  • Self-play (train against past versions of itself)
  • Hyperparameter sweeps
  • Checkpointing best model by win-rate
"""

import os
import sys
import time

# Ensure project root is importable when running as a script
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.ai.rl.env import BlokusEnv
from src.ai.rl.agent import DQNAgent

# ---------------------------------------------------------------------------
# Hyperparameters  (TODO: move to a config / argparse)
# ---------------------------------------------------------------------------
NUM_EPISODES      = 1_000       # total training games
TARGET_SYNC_EVERY = 10          # sync target network every N episodes
SAVE_EVERY        = 100         # save checkpoint every N episodes
LOG_EVERY         = 10          # print stats every N episodes
MODEL_DIR         = os.path.join(PROJECT_ROOT, "models")


def train():
    os.makedirs(MODEL_DIR, exist_ok=True)

    env = BlokusEnv(rl_player_colour=1, opponent_ai="v3")
    agent = DQNAgent(
        max_actions=env.max_actions,
        lr=1e-3,
        gamma=0.99,
        epsilon_start=1.0,
        epsilon_end=0.05,
        epsilon_decay=5_000,
        batch_size=64,
    )

    # ---- Metrics ----
    total_rewards = []
    wins = 0
    start = time.time()

    for episode in range(1, NUM_EPISODES + 1):
        obs, info = env.reset()
        episode_reward = 0.0

        while not env.done:
            num_legal = info["num_legal_moves"]
            if num_legal == 0:
                break

            action = agent.select_action(obs, num_legal)
            next_obs, reward, done, truncated, info = env.step(action)

            # Store transition
            agent.replay.push(obs, action, reward, next_obs, done)

            # Learn from replay
            agent.learn()

            obs = next_obs
            episode_reward += reward

        total_rewards.append(episode_reward)

        # Check if RL player won (lowest remaining score = winner)
        rl_score = env.players[env.rl_colour - 1].current_score()
        if rl_score == min(p.current_score() for p in env.players):
            wins += 1

        # Sync target network
        if episode % TARGET_SYNC_EVERY == 0:
            agent.sync_target()

        # Logging
        if episode % LOG_EVERY == 0:
            avg_reward = sum(total_rewards[-LOG_EVERY:]) / LOG_EVERY
            elapsed = time.time() - start
            win_rate = wins / episode * 100
            print(
                f"Episode {episode:>5d} | "
                f"Avg Reward: {avg_reward:>7.1f} | "
                f"Win Rate: {win_rate:>5.1f}% | "
                f"Epsilon: {agent.epsilon:.3f} | "
                f"Buffer: {len(agent.replay):>6d} | "
                f"Time: {elapsed:.0f}s"
            )

        # Save checkpoint
        if episode % SAVE_EVERY == 0:
            path = os.path.join(MODEL_DIR, f"blokus_dqn_ep{episode}.pt")
            agent.save(path)
            print(f"  ✓ Saved checkpoint → {path}")

    # Final save
    final_path = os.path.join(MODEL_DIR, "blokus_dqn_final.pt")
    agent.save(final_path)
    print(f"\nTraining complete – final model saved to {final_path}")
    print(f"Win rate: {wins / NUM_EPISODES * 100:.1f}%")


if __name__ == "__main__":
    train()
