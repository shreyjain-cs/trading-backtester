"""
Plot equity curves: strategy vs benchmarks.

Produces a PNG for the README. Run after backtest.py's components are importable.
"""

import matplotlib
matplotlib.use("Agg")           # render to file, no GUI window needed
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter


# --- palette -------------------------------------------------------------
# Three categorical hues, validated for colorblind separation against a light
# surface. Fixed order: never cycle or reassign these per-run.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]   # blue, orange, aqua
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"


def _dollars(x, _pos):
    return f"${x/1000:,.0f}k"


def _spread_labels(ys, min_gap):
    """
    Nudge label y-positions apart so near-identical end values don't overprint.
    Returns adjusted positions in the same order as the input.
    """
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    adjusted = list(ys)
    for n, i in enumerate(order):
        if n == 0:
            continue
        prev = adjusted[order[n - 1]]
        if adjusted[i] - prev < min_gap:
            adjusted[i] = prev + min_gap
    return adjusted


def plot_equity_curves(curves: dict, title: str, outfile: str = "equity_curve.png"):
    """
    curves: {"label": equity_curve, ...} preserving the order you want colors in.
            Each equity_curve is a list of {"date": ..., "equity": ...}.
    """
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    end_values = []
    for (label, curve), color in zip(curves.items(), SERIES):
        dates = [p["date"] for p in curve]
        equity = [p["equity"] for p in curve]
        ax.plot(dates, equity, color=color, linewidth=2, label=label, solid_capstyle="round")
        end_values.append((label, color, dates[-1], equity[-1]))

    # --- direct labels at the right end, de-collided ---------------------
    y_lo, y_hi = ax.get_ylim()
    min_gap = (y_hi - y_lo) * 0.05
    spread = _spread_labels([v[3] for v in end_values], min_gap)

    for (label, color, x, y), y_label in zip(end_values, spread):
        ax.annotate(
            f"{label}  ${y:,.0f}",
            xy=(x, y_label), xytext=(8, 0), textcoords="offset points",
            va="center", fontsize=9, color=color,
            annotation_clip=False,
        )

    # --- chrome -----------------------------------------------------------
    ax.set_title(title, color=INK, fontsize=13, pad=14, loc="left", fontweight="semibold")
    ax.yaxis.set_major_formatter(FuncFormatter(_dollars))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))

    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(BASELINE)
        ax.spines[side].set_linewidth(1)

    ax.tick_params(colors=MUTED, labelsize=9, length=0)

    ax.legend(frameon=False, loc="upper left", fontsize=9, labelcolor=MUTED)

    # room on the right for the direct labels
    fig.subplots_adjust(right=0.74, left=0.08, top=0.88, bottom=0.12)

    fig.savefig(outfile, facecolor=SURFACE)
    print(f"wrote {outfile}")
    return outfile