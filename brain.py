# NN architecture

# Selects top k threats
# Each top k threats contains:
# - is_bullet: bool
# - is_valid: bool (because sometimes there are fewer than k threats)
# - dx_norm
# - dy_norm
# - overlap: bool
# - gap_norm: 0 if overlap, else magnitude
# - t_hit_norm: TTC (time to collision)
# - w_norm: width of threat block
# - vy_norm
# - ay_norm
# - jy_norm

# and including self-features
# - agent_x_norm
# - agent_vx_norm
# - agent_width_norm
# - left_wall_dist
# - right_wall_dist

# BTW the reason I chose this design is cuz I think all these features (though some are redundant and repeated)
# are all very clean and useful features
# everytime I train an ML model, I always think to myself, "if I were the model, what information would I want to know?"
# and I think this design is quite good

# brain.py
# Simple brains for AI agents:
# - RandomBrain: debugging / baseline
# - MLPBrain: small numpy MLP you can mutate (nice for neuroevolution)

# brain.py
# Continuous MLP brain + simple neuroevolution utilities (NumPy)
# Output: u in [-1, 1] (continuous control). You will do: agent.ax = u * ACCEL

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import numpy as np


def _tanh(x: np.ndarray) -> np.ndarray:
    return np.tanh(x)


@dataclass
class ContinuousMLPBrain:
    """
    Tiny MLP:
      input -> h1 -> h2 -> output(1)
    output is squashed with tanh to be in [-1, 1].
    """
    w1: np.ndarray
    b1: np.ndarray
    w2: np.ndarray
    b2: np.ndarray
    w3: np.ndarray
    b3: np.ndarray

    @staticmethod
    def create(input_dim: int, h1: int = 64, h2: int = 32, seed: Optional[int] = None) -> "ContinuousMLPBrain":
        rng = np.random.default_rng(seed)

        # Small init so actions aren't instantly maxed
        w1 = rng.normal(0.0, 0.25, size=(h1, input_dim)).astype(np.float32)
        b1 = rng.normal(0.0, 0.05, size=(h1,)).astype(np.float32)

        w2 = rng.normal(0.0, 0.25, size=(h2, h1)).astype(np.float32)
        b2 = rng.normal(0.0, 0.05, size=(h2,)).astype(np.float32)

        w3 = rng.normal(0.0, 0.25, size=(1, h2)).astype(np.float32)
        b3 = rng.normal(0.0, 0.02, size=(1,)).astype(np.float32)

        return ContinuousMLPBrain(w1, b1, w2, b2, w3, b3)

    def forward(self, obs: List[float]) -> float:
        x = np.asarray(obs, dtype=np.float32)

        if x.ndim != 1:
            raise ValueError(f"obs must be 1D, got shape {x.shape}")
        if x.shape[0] != self.w1.shape[1]:
            raise ValueError(f"obs length {x.shape[0]} != expected {self.w1.shape[1]}")

        h1 = _tanh(self.w1 @ x + self.b1)
        h2 = _tanh(self.w2 @ h1 + self.b2)
        out = (self.w3 @ h2 + self.b3)[0] # scalar
        u = float(np.tanh(out)) # tabh squash [-1, 1]
        return u

    def clone(self) -> "ContinuousMLPBrain":
        return ContinuousMLPBrain(
            self.w1.copy(), self.b1.copy(),
            self.w2.copy(), self.b2.copy(),
            self.w3.copy(), self.b3.copy(),
        )

    def mutate(self, rate: float = 0.10, scale: float = 0.12) -> None:
        """
        Perturb a fraction of parameters with Gaussian noise.
        rate  = probability each parameter gets mutated
        scale = std of mutation noise
        """
        rng = np.random.default_rng()

        def mut(arr: np.ndarray) -> None:
            mask = rng.random(arr.shape) < rate
            noise = rng.normal(0.0, scale, size=arr.shape).astype(np.float32)
            arr[mask] += noise[mask]

        mut(self.w1); mut(self.b1)
        mut(self.w2); mut(self.b2)
        mut(self.w3); mut(self.b3)


def evolve_next_generation(
    brains: List[ContinuousMLPBrain],
    fitness: List[float],
    pop_size: int,
    elite_count: int = 5,
    mutation_rate: float = 0.10,
    mutation_scale: float = 0.12,
    tournament_k: int = 5,
) -> List[ContinuousMLPBrain]:
    """
    Make next generation brains via:
      - keep top elites unchanged
      - fill the rest with tournament-selected parent clones + mutation
    """
    if len(brains) != len(fitness):
        raise ValueError("brains and fitness must be same length")

    n = len(brains)
    if n == 0:
        raise ValueError("empty population")

    # Sort indices by fitness descending
    idxs = list(range(n))
    idxs.sort(key=lambda i: fitness[i], reverse=True)

    # Elites
    elite_count = max(1, min(elite_count, pop_size, n))
    new_brains: List[ContinuousMLPBrain] = [brains[i].clone() for i in idxs[:elite_count]]

    rng = np.random.default_rng()

    def tournament_pick() -> int:
        k = min(tournament_k, n)
        candidates = rng.choice(idxs, size=k, replace=False)
        best = max(candidates, key=lambda i: fitness[i])
        return int(best)

    # Fill rest
    while len(new_brains) < pop_size:
        parent_i = tournament_pick()
        child = brains[parent_i].clone()
        child.mutate(rate=mutation_rate, scale=mutation_scale)
        new_brains.append(child)

    return new_brains