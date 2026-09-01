"""Generates the Kaggle thumbnail programmatically (reproducible, no external
image assets or logos). Produces a 1280x720 (16:9) PNG.

Design goal (per market-research-driven positioning update): communicate
within ~2 seconds at small Kaggle card size. Dominated by two short lines
-- "AI AGENTS" and "FAILURE + RECOVERY" -- not by the full 7-stage
pipeline as small text (that diagram now lives at full size in the README
schema section and Kaggle description body, where it can actually be
read). A single 3-node motif (agent -> failure -> recovery) stands in for
the pipeline here as a recognizable icon, not a documentation diagram.
"""
import os

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = os.path.join(os.path.dirname(__file__), "kaggle_thumbnail.png")

fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
fig.patch.set_facecolor("#0b1d26")
ax.set_facecolor("#0b1d26")
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis("off")

# --- primary message: readable in ~2 seconds -------------------------------
ax.text(5, 8.35, "AI AGENTS", fontsize=46, fontweight="bold", ha="center",
        va="center", color="#f4f1de", family="monospace")
ax.text(5, 7.15, "FAILURE + RECOVERY", fontsize=34, fontweight="bold",
        ha="center", va="center", color="#f4a261", family="monospace")

# --- minimal 3-node motif: agent -> failure -> recovery --------------------
NODES = ["AGENT", "FAILURE", "RECOVERY"]
COLORS = ["#2a6f77", "#e9c46a", "#2a9d8f"]
box_w, box_h = 2.0, 1.05
y = 4.9
xs = [2.1, 5.0, 7.9]

for i, (x, label, color) in enumerate(zip(xs, NODES, COLORS)):
    box = FancyBboxPatch((x - box_w / 2, y - box_h / 2), box_w, box_h,
                          boxstyle="round,pad=0.08,rounding_size=0.14",
                          linewidth=2, edgecolor="#f4f1de", facecolor=color, alpha=0.95)
    ax.add_patch(box)
    ax.text(x, y, label, fontsize=17, fontweight="bold", ha="center", va="center",
             color="#0b1d26", family="monospace")
    if i < len(NODES) - 1:
        arrow = FancyArrowPatch((x + box_w / 2 + 0.08, y), (xs[i + 1] - box_w / 2 - 0.08, y),
                                 arrowstyle="-|>", mutation_scale=22, linewidth=2.4, color="#f4f1de")
        ax.add_patch(arrow)

# --- secondary line: brand + extended title, small and out of the way ------
ax.text(5, 3.05, "Agent Failure Atlas 2026", fontsize=17, fontweight="bold",
        ha="center", va="center", color="#e9e5d6", family="monospace")
ax.text(5, 2.45, "AI Agent Trajectory, Failure & Recovery Benchmark", fontsize=12.5,
        ha="center", va="center", color="#8ab17d", family="monospace")

ax.text(5, 1.15, "Synthetic, reproducible benchmark for agent reliability research",
        fontsize=10.5, ha="center", va="center", color="#5c7a89", family="monospace")

ax.text(5, 0.45, "Abishek9342  ·  Kaggle 2026", fontsize=9.5, ha="center", va="center",
        color="#3d5560", family="monospace")

plt.tight_layout()
plt.savefig(OUT, facecolor=fig.get_facecolor(), bbox_inches="tight")
print(f"wrote {OUT}")
