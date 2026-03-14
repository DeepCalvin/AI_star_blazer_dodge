# 🌟💥 AI Star Blazer Dodge 💥🌟

### 🧠 Watch neural networks learn to dodge falling chaos in real-time!

---

> _"What if I threw 50 tiny AI agents into a bullet hell and let natural selection figure it out?"_ — the thought that started it all 🤔💡

**AI Star Blazer Dodge** is a neuroevolution sandbox built with **Pygame** where a population of AI agents evolve to survive an increasingly brutal rain of falling blocks and bullets. No gradients. No backprop. Just survival of the fittest. 🏆🧬

---

## 🎮 What's Happening On Screen?

Imagine this:

🟡 **Yellow blocks** rain down from the sky, accelerating and jerking as they fall.  
🟠 **Orange bullets** fire from those blocks, making the danger zone even spicier.  
🔵 **You (the player)** dodge manually with A/D or arrow keys.  
🩵 **50 AI agents** try their absolute best to not die (emphasis on *try*).  
🟨 **One highlighted agent** shows you its top-K threat perception in real time.  
🟣 **Purple outlines** mark what the debug agent considers its biggest threats.

Every generation, the dead are judged, the strong are cloned, the clones are mutated, and a new generation rises from the ashes. 🔥🐣

---

## 🧬 How The Evolution Works

```
┌──────────────────────────────────────────────┐
│  1. Spawn 50 AI agents with random brains    │
│  2. Let them dodge until all are dead ☠️      │
│  3. Rank by fitness (survival time + bonuses)│
│  4. Keep top 5 elites unchanged 👑            │
│  5. Tournament select parents for the rest   │
│  6. Clone + mutate → new generation 🧪       │
│  7. GOTO 1                                   │
└──────────────────────────────────────────────┘
```

### 🏋️ Fitness Function

It's not just about staying alive! Agents are rewarded and penalized for:

| Factor | Effect |
|---|---|
| ⏱️ **Survival time** | Core fitness — stay alive longer = better |
| 🏃 **Movement** | Bonus for actually moving (no standing still!) |
| 🎯 **Center positioning** | Bonus for staying near the middle of the screen |
| 🚫 **Wall hugging** | Penalty for camping near the edges |

### 🎲 Neuroevolution — How Mutation Actually Works

Here's the thing — there are **zero gradients** in this entire project. No loss functions, no backpropagation, no optimizer.step(). Instead, we let **random noise + natural selection** do the heavy lifting. Here's how: 🧪

**Step 1: Elitism 👑**  
The top 5 fittest brains are cloned **directly** into the next generation, completely unchanged. These are the survivors, the legends, the goats. They earned their spot.

**Step 2: Tournament Selection 🏟️**  
For the remaining 45 slots, we run a tournament: randomly pick 5 agents from the population, and the one with the highest fitness wins. That winner becomes the **parent** for a new child brain.

**Step 3: Gaussian Mutation 🎲**  
This is where the magic happens. After cloning the parent's weights, we walk through **every single weight and bias** in the neural network and ask: _"should we mutate this one?"_

```python
# For each parameter in the network:
if random() < mutation_rate:          # 10% chance per weight
    weight += gaussian(0, mutation_scale)  # Add noise ~ N(0, 0.12)
```

So roughly **10% of all weights** get a small random nudge drawn from a **Gaussian distribution** (mean=0, std=0.12). Most mutations are tiny tweaks. Occasionally, a larger perturbation slips through. This is essentially the neural network equivalent of biological mutation — small random changes that *sometimes* produce something better. 🧬✨

**Why does this work?** 🤯  
Because the elites **preserve** what's already good, while the mutations **explore** nearby weight space for something even better. Over many generations, the population hill-climbs toward increasingly skilled dodge behavior — all without computing a single gradient!

```
Generation 1:   🤡🤡🤡🤡🤡  (random flailing, everyone dies instantly)
Generation 10:  🤡🤡🤡🧐🧐  (a few start dodging... sometimes)
Generation 50:  🧐🧐😎😎😎  (consistent dodging emerges!)
Generation 200: 😎😎🏆🏆🏆  (they're better than you now lol)
```

---

## 🧠 The Brain (Neural Network)

Each agent has a tiny **MLP (Multi-Layer Perceptron)** built with pure NumPy:

```
Input (60 features) → [64 neurons] → tanh → [32 neurons] → tanh → [1 output] → tanh
```

The single output `u ∈ [-1, 1]` controls **continuous horizontal acceleration**. No discrete left/right — these agents can feather their movement like a pro. 🎮✨

### 👁️ What The Agent "Sees" (Observation Vector)

**5 self-features:**
- Normalized X position 📍
- Normalized X velocity 💨
- Distance to left wall 🧱←
- Distance to right wall →🧱
- Agent width 📏

**Top-K threat features (K=5, 11 features each):**
- Is it a bullet? 🔫
- Is this threat slot valid? ✅
- Relative X distance (dx) ↔️
- Relative Y distance (dy) ↕️
- Are we overlapping horizontally? 😰
- Gap distance 📐
- Time-to-collision (TTC) ⏰
- Threat width 📏
- Vertical velocity 📉
- Vertical acceleration 📈
- Vertical jerk 🎢

That's **60 input features** giving each agent a rich understanding of its surroundings!

---

## ⚡ Threat Scoring System

Not all falling objects are equally dangerous. The sensor system computes a **threat score** for every block and bullet:

```
threat_score = x_factor / (time_to_collision + ε)
```

Where:
- **`x_factor = 1 / (horizontal_gap + 1)`** — closer horizontally = scarier 😱
- **`time_to_collision`** — computed via binary search on the cubic motion equation (because solving cubics analytically is hard and binary search is elegant 🧠)
- Only the **top 5 threats** are passed to the neural network

---

## 📈 Difficulty Scaling

The game doesn't stay easy forever 😈

Every **10 seconds**, difficulty ticks up by `0.01`, which affects:
- 🚀 Block fall speed (velocity, acceleration, AND jerk all scale up)
- ⏩ Spawn rate increases (more blocks, shorter intervals)
- 🔫 Shoot cooldown decreases (blocks fire faster)

---

## 🗂️ Project Structure

```
📁 AI_star_blazer_dodge/
├── 🎮 main.py        → Game loop, rendering, evolution orchestration
├── 🧠 brain.py       → MLP architecture + neuroevolution (tournament + elitism)
├── 👁️ sensors.py     → Threat detection, TTC calculation, observation builder
├── 🤖 agents.py      → Agent class (player + AI)
├── 🟡 blocks.py      → Falling block class
├── 🟠 bullets.py     → Bullet class
└── 🛠️ utils.py       → Colors, block spawning logic
```

---

## 🚀 Getting Started

### Prerequisites

- 🐍 Python 3.10+
- 📦 Pygame
- 📦 NumPy

### Installation

```bash
# Clone the repo
git clone https://github.com/DeepCalvin/AI_star_blazer_dodge.git
cd AI_star_blazer_dodge

# Install dependencies
pip install pygame numpy

# RUN IT 🏃💨
python main.py
```

### 🎛️ Controls

| Key | Action |
|---|---|
| `A` / `←` | Move left |
| `D` / `→` | Move right |
| `ESC` | Quit |

---

## 🔧 Tunable Parameters

Want to mess with evolution? Here are the knobs in `main.py`:

| Parameter | Default | What It Does |
|---|---|---|
| `AI_POP` | 50 | Population size per generation |
| `ELITE_COUNT` | 5 | Number of top agents kept unchanged |
| `MUT_RATE` | 0.10 | Probability each weight gets mutated |
| `MUT_SCALE` | 0.12 | Standard deviation of mutation noise |
| `TOURNAMENT_K` | 5 | Tournament selection pool size |
| `K_THREATS` | 5 | Number of top threats fed to the brain |

---

## 🐛 Debug Visualization

Toggle `DEBUG_SHOW_TOPK = True` to see:
- 🟨 **Yellow border** around the tracked agent
- 🟣 **Purple borders** around its top-K perceived threats
- 🔢 **Rank numbers** showing threat priority (1 = most dangerous)

Super useful for understanding what the AI "thinks" is scary! 👀

---

## 💡 Design Philosophy

Ok this part of the README is written by me, not AI. This project made me realize feature engineering is about answer one question:

> _"If I were the neural network, what information would I want to know?"_

These features that are passed into the neural network were carefully designed by me, which is one of the core part of this project.
Parts of the code were made with the help of AI, but no AI were used when I was feature engineering.
When I was first designing the features, I imagined myself being the "block", oblivious to what's going on in the environment.
Then I ask myself, what information should I need to know in order to make me know whether to move left or right?
And that's how these features were built on.

---

## 🔮 Future Considerations

This project is just the beginning. Here's where it could go next:

### 🤖 Reinforcement Learning (PPO)
The current neuroevolution approach is simple and elegant, but it has limits — it's essentially doing **random search** in weight space. The natural next step is to swap in a proper **Reinforcement Learning** algorithm like **PPO (Proximal Policy Optimization)**:

- 📊 **Gradient-based learning** — instead of hoping random noise improves weights, PPO computes *actual gradients* that tell the network exactly which direction to update. Way more sample-efficient!
- 🎯 **Policy + Value network** — PPO learns both a policy (what to do) and a value function (how good is this state?), giving the agent a much richer understanding of its situation
- ⚖️ **Clipped objective** — PPO's clipped surrogate objective prevents catastrophically large updates, keeping training stable even in chaotic environments like this one
- 🔄 **On-policy learning** — the agent learns from its own most recent experiences, which maps perfectly to the "play a generation → learn → repeat" loop already in place
- 🧠 **Could reuse the same observation vector!** — the hand-crafted 60-feature observation is already clean and normalized, so it plugs right into a PPO policy network

### 🌟 Other Ideas
- 🎨 **Better visuals** — particle effects, trails, screen shake, make it look like an actual game
- 💾 **Save/load brains** — serialize the best evolved brain to disk so you don't lose progress
- 📊 **Fitness graphs** — plot generation-over-generation fitness curves in real time
- 🆚 **AI vs AI modes** — pit evolved agents against RL-trained agents and see who survives longer
- 🌐 **Parallelized evolution** — run multiple environments simultaneously for faster training
- 🧩 **Recurrent networks (LSTM/GRU)** — give agents memory so they can plan ahead instead of just reacting

---

## 🫡 Acknowledgements

- 🎮 **Pygame** for making game dev in Python actually enjoyable
- 🔢 **NumPy** for being the backbone of the neural network
- 🧬 **Charles Darwin** for the original evolutionary algorithm (published ~1859, no GitHub repo found) 🦎

---

<p align="center">
  <b>Watch them learn. Watch them dodge. Watch them evolve.</b> 🧠⚡🎮
</p>
