#!/usr/bin/env python3
"""
Publication figure boards for PRJDB36442 CHB severity manuscript.
Generates Figures 1–5 + FigureS1 with full provenance metadata.

Usage:
    python scripts/postprocess/make_figure_boards_v2.py --base-dir /path/to/meta
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from scipy.stats import mannwhitneyu, gaussian_kde

# ── Global rcParams (per PLOT_STYLE_GUIDE.md §11) ──────────────────────────
mpl.rcParams.update({
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "axes.grid": False,
    "lines.linewidth": 1.4,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "figure.dpi": 150,
})

# ── Semantic color palette (color-blind safe, per PLOT_STYLE_GUIDE.md §5) ──
C = {
    "M": "#4878CF",
    "S": "#D65F5F",
    "HC": "#59A14F",
    "LC": "#B07AA1",
    "match": "#59A14F",
    "mismatch": "#D65F5F",
    "neutral": "#999999",
    "conservative": "#4878CF",
    "expanded": "#E8853D",
}
CAT8 = ["#4878CF", "#D65F5F", "#59A14F", "#E8853D", "#B07AA1", "#76B7B2", "#EDC949", "#AF7AA1"]

SEED = 20260208
FDR_THRESHOLD = 0.25  # exploratory threshold for suggestive signals


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Utility helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_tsv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t")


def _save_fig(fig: plt.Figure, stem: Path, meta: dict[str, Any], base_dir: Path | None = None) -> None:
    """Save PDF + PNG + meta.json."""
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)

    # Write provenance meta.json
    if isinstance(meta.get("inputs"), dict):
        relpaths = [p for p in meta["inputs"].values() if isinstance(p, str)]
        meta["inputs_sha256"] = {p: INPUT_CHECKSUMS.get(p) for p in relpaths if p in INPUT_CHECKSUMS}
    out_pdf = stem.with_suffix(".pdf")
    out_png = stem.with_suffix(".png")
    if base_dir is not None:
        try:
            meta["output_pdf"] = str(out_pdf.relative_to(base_dir))
            meta["output_png"] = str(out_png.relative_to(base_dir))
        except ValueError:
            meta["output_pdf"] = str(out_pdf)
            meta["output_png"] = str(out_png)
    else:
        meta["output_pdf"] = str(out_pdf)
        meta["output_png"] = str(out_png)
    meta["generated_utc"] = datetime.now(timezone.utc).isoformat()
    meta["software"] = {
        "python": sys.version,
        "matplotlib": mpl.__version__,
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "platform": platform.platform(),
    }
    json_path = stem.with_suffix(".meta.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)


def _clean_run_col(column: str) -> str:
    return re.sub(r"_(Abundance|Coverage)(-RPKs)?$", "", column)


def _short_feature_name(feature: str) -> str:
    if ": " in feature:
        return feature.split(": ", 1)[0]
    return feature.split(":", 1)[0]


def _short_pathway_label(feature: str, max_len: int = 32) -> str:
    if ": " in feature:
        label = feature.split(": ", 1)[1].strip()
    else:
        label = _short_feature_name(feature).strip()
    if len(label) <= max_len:
        return label
    return label[: max_len - 1] + "…"


def _abbrev_species_from_strat(feature: str, max_len: int = 28) -> str:
    token = feature.split("|")[-1]
    token = token.replace("g__", "").replace("s__", "").replace(".", " ").replace("_", " ")
    token = re.sub(r"\s+", " ", token).strip()
    if len(token) <= max_len:
        return token
    parts = token.split()
    if len(parts) >= 2:
        short = f"{parts[0][0]}. {' '.join(parts[1:])}"
        if len(short) <= max_len:
            return short
    return token[: max_len - 1] + "…"


def _bootstrap_ci_delta(
    m_vals: np.ndarray, s_vals: np.ndarray, seed: int, n_boot: int = 5000
) -> tuple[float, float, float]:
    """Return (median_delta, ci_lo, ci_hi) via bootstrap."""
    rng = np.random.default_rng(seed)
    deltas = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        m = rng.choice(m_vals, size=len(m_vals), replace=True)
        s = rng.choice(s_vals, size=len(s_vals), replace=True)
        deltas[i] = float(np.median(s) - np.median(m))
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    return float(np.median(deltas)), float(lo), float(hi)


def _panel_label(ax: plt.Axes, label: str) -> None:
    """Add bold lowercase panel label outside plot area."""
    ax.text(
        -0.12, 1.10, label,
        transform=ax.transAxes,
        fontsize=14, fontweight="bold",
        va="top", ha="left",
    )


def _annotate_n(ax: plt.Axes, x_pos: float, y_pos: float, n: int, fontsize: int = 8) -> None:
    ax.text(x_pos, y_pos, f"n={n}", ha="center", va="top", fontsize=fontsize, color="#555555")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Raincloud plot component
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _raincloud(
    ax: plt.Axes,
    data_list: list[np.ndarray],
    positions: list[float],
    colors: list[str],
    labels: list[str],
    seed: int,
    orientation: str = "vertical",
) -> None:
    """Draw a raincloud: half-violin + jittered swarm + miniature boxplot."""
    width = 0.35
    for idx, (vals, pos, col, lab) in enumerate(zip(data_list, positions, colors, labels)):
        vals = vals[np.isfinite(vals)]
        if len(vals) < 3:
            continue

        try:
            kde = gaussian_kde(vals, bw_method=0.4)
        except np.linalg.LinAlgError:
            continue
        y_range = np.linspace(vals.min() - 0.05 * np.ptp(vals),
                              vals.max() + 0.05 * np.ptp(vals), 200)
        density = kde(y_range)
        density = density / density.max() * width

        if orientation == "vertical":
            ax.fill_betweenx(y_range, pos - density, pos, alpha=0.3, color=col, linewidth=0)
            ax.plot(pos - density, y_range, color=col, lw=0.8)
            rng = np.random.default_rng(seed + idx)
            jitter = rng.uniform(0.02, width * 0.6, size=len(vals))
            ax.scatter(pos + jitter, vals, s=12, color=col, alpha=0.6, edgecolors="none", zorder=3)
            med = np.median(vals)
            q1, q3 = np.percentile(vals, [25, 75])
            ax.plot([pos - 0.02, pos + 0.02], [med, med], color="black", lw=2, zorder=4)
            ax.plot([pos, pos], [q1, q3], color="black", lw=1.2, zorder=4)
        else:
            ax.fill_between(y_range, pos - density, pos, alpha=0.3, color=col, linewidth=0)
            ax.plot(y_range, pos - density, color=col, lw=0.8)
            rng = np.random.default_rng(seed + idx)
            jitter = rng.uniform(0.02, width * 0.6, size=len(vals))
            ax.scatter(vals, pos + jitter, s=12, color=col, alpha=0.6, edgecolors="none", zorder=3)
            med = np.median(vals)
            q1, q3 = np.percentile(vals, [25, 75])
            ax.plot([med, med], [pos - 0.02, pos + 0.02], color="black", lw=2, zorder=4)
            ax.plot([q1, q3], [pos, pos], color="black", lw=1.2, zorder=4)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Data loading
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT_MANIFEST = {
    "groups": "results/feasibility/PRJDB36442_run_groups.tsv",
    "alpha": "results/processed/analysis/PRJDB36442/alpha_diversity.tsv",
    "phylum": "results/processed/metaphlan/PRJDB36442/metaphlan_phylum.tsv.gz",
    "module_cons": "results/processed/PRJDB36442_humann/module_M_vs_S_stats_conservative.tsv",
    "module_exp": "results/processed/PRJDB36442_humann/module_M_vs_S_stats_expanded.tsv",
    "module_set_cons": "results/processed/PRJDB36442_humann/module_sets_conservative.tsv",
    "module_set_exp": "results/processed/PRJDB36442_humann/module_sets_expanded.tsv",
    "path_stats": "results/processed/PRJDB36442_humann/pathway_M_vs_S_stats.tsv",
    "path_dir": "results/external/pathway_direction_validation.tsv",
    "mod_dir": "results/external/module_direction_validation.tsv",
    "pathabundance": "results/processed/PRJDB36442_humann/merged_pathabundance.tsv.gz",
}

INPUT_CHECKSUMS: dict[str, str] = {}


def _load_inputs(base_dir: Path) -> dict[str, pd.DataFrame]:
    d: dict[str, pd.DataFrame] = {}
    for key, relpath in INPUT_MANIFEST.items():
        d[key] = pd.read_csv(base_dir / relpath, sep="\t")
    return d


def _input_checksums(base_dir: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for key, relpath in INPUT_MANIFEST.items():
        p = base_dir / relpath
        if p.exists():
            checksums[relpath] = _sha256(p)
    return checksums


def _build_module_scores(base_dir: Path, groups: pd.DataFrame, module_set: pd.DataFrame) -> pd.DataFrame:
    path = base_dir / "results/processed/PRJDB36442_humann/merged_pathabundance.tsv.gz"
    df = pd.read_csv(path, sep="\t")
    df = df.rename(columns={"# Pathway": "feature"})
    df = df[~df["feature"].str.contains(r"\|", regex=True)]
    df = df[~df["feature"].isin(["UNMAPPED", "UNINTEGRATED"])]

    rename_map: dict[str, str] = {}
    for column in df.columns:
        if column == "feature":
            continue
        rename_map[column] = _clean_run_col(column)
    df = df.rename(columns=rename_map)
    run_cols = [c for c in df.columns if c != "feature"]

    rel = df[run_cols].div(df[run_cols].sum(axis=0), axis=1)
    rel.insert(0, "feature", df["feature"].values)
    rel = rel.set_index("feature")

    modules = module_set.groupby("module")["feature"].apply(list).to_dict()
    rows: list[dict[str, object]] = []
    group_map = dict(zip(groups["run_accession"], groups["group"]))
    valid_runs = [r for r in groups["run_accession"].tolist() if r in rel.columns]
    for module, features in modules.items():
        picked = [f for f in features if f in rel.index]
        if not picked:
            continue
        score = rel.loc[picked, valid_runs].mean(axis=0)
        for run, value in score.items():
            rows.append({
                "run_accession": run,
                "group": group_map.get(run, ""),
                "module": module,
                "score": float(value),
            })
    return pd.DataFrame(rows)


def _pathway_matrix_for_targets(path_table: Path, runs: list[str],
                                 target_features: list[str]) -> pd.DataFrame:
    usecols = ["# Pathway"] + [f"{run}_Abundance" for run in runs]
    existing = pd.read_csv(path_table, sep="\t", nrows=0).columns.tolist()
    usecols = [c for c in usecols if c in existing]
    matrix = pd.read_csv(path_table, sep="\t", usecols=usecols)
    matrix = matrix.rename(columns={"# Pathway": "feature"})
    matrix = matrix[~matrix["feature"].str.contains(r"\|", regex=True)]
    matrix = matrix[matrix["feature"].isin(target_features)]
    rename_map = {f"{run}_Abundance": run for run in runs if f"{run}_Abundance" in matrix.columns}
    matrix = matrix.rename(columns=rename_map).set_index("feature")
    return matrix


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIGURE 1: Cohort Profile & Primary Readouts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def make_figure1(data: dict[str, pd.DataFrame], outdir: Path, base_dir: Path) -> None:
    groups = data["groups"].copy()
    alpha = data["alpha"].copy()
    phylum = data["phylum"].copy()

    fig = plt.figure(figsize=(7.2, 2.8))
    gs = fig.add_gridspec(1, 3, wspace=0.40, width_ratios=[1.0, 1.2, 1.4])

    # ── Panel a: Cohort overview ──
    ax_a = fig.add_subplot(gs[0, 0])
    n_m = int((groups["group"] == "M").sum())
    n_s = int((groups["group"] == "S").sum())
    n_total = n_m + n_s

    box_kw = dict(boxstyle="round,pad=0.4", lw=0.8)
    ax_a.text(0.5, 0.88, f"PRJDB36442\n(n={n_total} shotgun)", ha="center", va="center",
              fontsize=8, fontweight="bold",
              bbox=dict(**box_kw, facecolor="#f0f0f0", edgecolor="#888888"))
    ax_a.annotate("", xy=(0.22, 0.62), xytext=(0.5, 0.76),
                  arrowprops=dict(arrowstyle="-|>", lw=1.0, color="#666666"))
    ax_a.annotate("", xy=(0.78, 0.62), xytext=(0.5, 0.76),
                  arrowprops=dict(arrowstyle="-|>", lw=1.0, color="#666666"))
    ax_a.text(0.22, 0.50, f"Mild (M)\nn={n_m}", ha="center", va="center", fontsize=7,
              bbox=dict(**box_kw, facecolor=C["M"], edgecolor=C["M"], alpha=0.2))
    ax_a.text(0.78, 0.50, f"Significant (S)\nn={n_s}", ha="center", va="center", fontsize=7,
              bbox=dict(**box_kw, facecolor=C["S"], edgecolor=C["S"], alpha=0.2))
    ax_a.annotate("", xy=(0.5, 0.28), xytext=(0.5, 0.38),
                  arrowprops=dict(arrowstyle="-|>", lw=0.8, color="#999999"))
    ax_a.text(0.5, 0.18, "MetaPhlAn → HUMAnN\n(taxonomy + function)", ha="center", va="center",
              fontsize=7, color="#555555",
              bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#cccccc", lw=0.6))
    ax_a.set_xlim(0, 1)
    ax_a.set_ylim(0, 1)
    ax_a.set_xticks([])
    ax_a.set_yticks([])
    for spine in ax_a.spines.values():
        spine.set_visible(False)
    _panel_label(ax_a, "a")

    # ── Panel b: Alpha-diversity raincloud ──
    ax_b = fig.add_subplot(gs[0, 1])
    m_vals = alpha.loc[alpha["group"] == "M", "shannon"].to_numpy()
    s_vals = alpha.loc[alpha["group"] == "S", "shannon"].to_numpy()

    _raincloud(ax_b, [m_vals, s_vals], [1.0, 2.0], [C["M"], C["S"]], ["M", "S"], seed=SEED)

    stat, p = mannwhitneyu(m_vals, s_vals, alternative="two-sided")
    med_delta, ci_lo, ci_hi = _bootstrap_ci_delta(m_vals, s_vals, SEED)
    ymax = max(m_vals.max(), s_vals.max())
    ax_b.text(1.5, ymax + 0.15,
              f"Δmedian={med_delta:.2f} [{ci_lo:.2f}, {ci_hi:.2f}]\np={p:.3f}",
              ha="center", va="bottom", fontsize=7, color="#333333")
    _annotate_n(ax_b, 1.0, min(m_vals.min(), s_vals.min()) - 0.12, len(m_vals))
    _annotate_n(ax_b, 2.0, min(m_vals.min(), s_vals.min()) - 0.12, len(s_vals))
    ax_b.set_xticks([1.0, 2.0], ["M", "S"])
    ax_b.set_ylabel("Shannon index")
    _panel_label(ax_b, "b")

    # ── Panel c: Phylum composition stacked bars ──
    ax_c = fig.add_subplot(gs[0, 2])
    ph = phylum.copy()
    ph["phylum"] = ph["clade_name"].str.split("|").str[-1].str.replace("p__", "", regex=False)
    ph = ph.set_index("phylum").drop(columns=["clade_name"])
    ph.columns = [c.replace(".metaphlan", "") for c in ph.columns]

    run_order = groups.sort_values(["group", "run_accession"])["run_accession"].tolist()
    run_order = [r for r in run_order if r in ph.columns]

    top = ph.mean(axis=1).sort_values(ascending=False).head(6).index.tolist()
    ph_plot = ph.loc[top, run_order].copy()
    ph_plot.loc["Other"] = ph.loc[~ph.index.isin(top), run_order].sum(axis=0)

    bottom = np.zeros(len(run_order))
    for i, name in enumerate(ph_plot.index.tolist()):
        vals = ph_plot.loc[name].to_numpy()
        ax_c.bar(np.arange(len(run_order)), vals, bottom=bottom,
                 color=CAT8[i % len(CAT8)], width=0.85, label=name, linewidth=0)
        bottom += vals

    cut = int((groups["group"] == "M").sum())
    ax_c.axvline(cut - 0.5, color="black", lw=0.8, ls="--", alpha=0.6)
    ax_c.text(cut / 2, bottom.max() * 1.01, "M", ha="center", fontsize=8,
              color=C["M"], fontweight="bold")
    ax_c.text(cut + (len(run_order) - cut) / 2, bottom.max() * 1.01, "S", ha="center",
              fontsize=8, color=C["S"], fontweight="bold")

    ax_c.set_xlim(-0.6, len(run_order) - 0.4)
    ax_c.set_xticks([])
    ax_c.set_ylabel("Relative abundance (%)")
    ax_c.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False, fontsize=7)
    _panel_label(ax_c, "c")

    meta = {
        "figure": "Figure1_Cohort_Profile",
        "panels": ["a:cohort_flow", "b:alpha_diversity_raincloud", "c:phylum_composition"],
        "inputs": {k: INPUT_MANIFEST[k] for k in ["groups", "alpha", "phylum"]},
        "parameters": {"seed": SEED, "n_boot": 5000, "alpha_metric": "shannon", "top_phyla": 6,
                        "test": "Mann-Whitney U (two-sided)"},
        "n_M": n_m, "n_S": n_s,
    }
    _save_fig(fig, outdir / "Figure1_Cohort_Profile", meta, base_dir=base_dir)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIGURE 2: Module-Level Mechanisms
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def make_figure2(data: dict[str, pd.DataFrame], module_scores: pd.DataFrame,
                 outdir: Path, base_dir: Path) -> None:
    mod_cons = data["module_cons"].copy()
    mod_exp = data["module_exp"].copy()
    set_cons = data["module_set_cons"].copy()
    set_exp = data["module_set_exp"].copy()

    modules = mod_cons["module"].tolist()
    n_mod = len(modules)
    n_m_total = int((data["groups"]["group"] == "M").sum())
    n_s_total = int((data["groups"]["group"] == "S").sum())

    fig = plt.figure(figsize=(7.2, 7.2))
    gs = fig.add_gridspec(2, 2, wspace=0.42, hspace=0.38)

    # ── Panel a: Raincloud per module ──
    ax_a = fig.add_subplot(gs[0, 0])
    for i, module in enumerate(modules):
        m_vals = module_scores.loc[
            (module_scores["module"] == module) & (module_scores["group"] == "M"), "score"
        ].to_numpy()
        s_vals = module_scores.loc[
            (module_scores["module"] == module) & (module_scores["group"] == "S"), "score"
        ].to_numpy()
        pos_m = i * 2.5
        pos_s = i * 2.5 + 1.0
        _raincloud(ax_a, [m_vals, s_vals], [pos_m, pos_s], [C["M"], C["S"]],
                   ["M", "S"], seed=SEED + i, orientation="horizontal")

    yticks = [i * 2.5 + 0.5 for i in range(n_mod)]
    ax_a.set_yticks(yticks, [m.replace("_", "\n") for m in modules], fontsize=7)
    ax_a.set_xlabel("Module score (relative abundance)")
    ax_a.invert_yaxis()
    _panel_label(ax_a, "a")

    # ── Panel b: Forest plot with CI + q + n ──
    ax_b = fig.add_subplot(gs[0, 1])
    forest_rows = []
    for idx, row in mod_cons.iterrows():
        module = row["module"]
        m_vals = module_scores.loc[
            (module_scores["module"] == module) & (module_scores["group"] == "M"), "score"
        ].to_numpy()
        s_vals = module_scores.loc[
            (module_scores["module"] == module) & (module_scores["group"] == "S"), "score"
        ].to_numpy()
        med_d, lo, hi = _bootstrap_ci_delta(m_vals, s_vals, SEED + idx)
        forest_rows.append((
            module, float(row["delta_S_minus_M"]), lo, hi,
            float(row["p"]), float(row["q"]), len(m_vals), len(s_vals)
        ))
    forest = pd.DataFrame(forest_rows,
                           columns=["module", "delta", "ci_lo", "ci_hi", "p", "q", "n_m", "n_s"])
    forest = forest.sort_values("delta")

    y = np.arange(len(forest))
    ax_b.errorbar(
        forest["delta"], y,
        xerr=[forest["delta"] - forest["ci_lo"], forest["ci_hi"] - forest["delta"]],
        fmt="none", ecolor="#555555", capsize=3, lw=0.8, zorder=2,
    )
    colors_forest = [C["S"] if d > 0 else C["M"] for d in forest["delta"]]
    ax_b.scatter(forest["delta"], y, s=50, color=colors_forest,
                 edgecolors="white", lw=0.4, zorder=3)
    ax_b.axvline(0, color="#333333", lw=0.8, ls="--", zorder=1)

    ax_b.set_yticks(y, forest["module"].str.replace("_", " ", regex=False).tolist(), fontsize=7)
    ax_b.set_xlabel("Median Δ (S − M), 95% CI")

    for yi, (_, r) in zip(y, forest.iterrows()):
        tag = " (expl.)" if r["q"] >= FDR_THRESHOLD else ""
        ax_b.annotate(f"q={r['q']:.3f}{tag}  n={r['n_m']}+{r['n_s']}",
                      xy=(1.02, yi), xycoords=("axes fraction", "data"),
                      fontsize=5.5, color="#555555", va="center", annotation_clip=False)
    _panel_label(ax_b, "b")

    # ── Panel c: Sensitivity dumbbell ──
    ax_c = fig.add_subplot(gs[1, 0])
    merged = mod_cons[["module", "delta_S_minus_M"]].merge(
        mod_exp[["module", "delta_S_minus_M"]], on="module", suffixes=("_cons", "_exp"),
    ).sort_values("delta_S_minus_M_cons")

    y_c = np.arange(len(merged))
    for i, (_, row) in enumerate(merged.iterrows()):
        ax_c.plot([row["delta_S_minus_M_cons"], row["delta_S_minus_M_exp"]], [i, i],
                  color="#999999", lw=1.4, zorder=1)
    ax_c.scatter(merged["delta_S_minus_M_cons"], y_c, color=C["conservative"], s=40,
                 label="Conservative", zorder=3, edgecolors="white", lw=0.4)
    ax_c.scatter(merged["delta_S_minus_M_exp"], y_c, color=C["expanded"], s=40,
                 label="Expanded", zorder=3, edgecolors="white", lw=0.4)
    ax_c.axvline(0, color="#333333", lw=0.8, ls="--")
    ax_c.set_yticks(y_c, merged["module"].str.replace("_", " ", regex=False), fontsize=7)
    ax_c.set_xlabel("Delta (S − M)")
    ax_c.legend(frameon=False, loc="lower right", fontsize=7)
    _panel_label(ax_c, "c")

    # ── Panel d: Module dictionary transparency ──
    ax_d = fig.add_subplot(gs[1, 1])
    n_cons = set_cons.groupby("module")["feature"].nunique()
    n_exp = set_exp.groupby("module")["feature"].nunique()
    union_modules = sorted(set(n_cons.index).union(set(n_exp.index)))
    y_d = np.arange(len(union_modules))
    cons_vals = np.array([n_cons.get(m, 0) for m in union_modules], dtype=float)
    exp_vals = np.array([n_exp.get(m, 0) for m in union_modules], dtype=float)

    for i in range(len(union_modules)):
        ax_d.plot([cons_vals[i], exp_vals[i]], [y_d[i], y_d[i]], color="#999999", lw=1.2, zorder=1)
    ax_d.scatter(cons_vals, y_d, color=C["conservative"], s=40, label="Conservative",
                 zorder=3, edgecolors="white", lw=0.4)
    ax_d.scatter(exp_vals, y_d, color=C["expanded"], s=40, label="Expanded",
                 zorder=3, edgecolors="white", lw=0.4)
    ax_d.set_yticks(y_d, [m.replace("_", " ") for m in union_modules], fontsize=7)
    ax_d.set_xlabel("Pathways per module")
    ax_d.legend(frameon=False, fontsize=7)
    _panel_label(ax_d, "d")

    meta = {
        "figure": "Figure2_Module_Mechanisms",
        "panels": ["a:raincloud_modules", "b:forest_effects", "c:sensitivity_dumbbell",
                    "d:dictionary_transparency"],
        "inputs": {k: INPUT_MANIFEST[k] for k in
                   ["module_cons", "module_exp", "module_set_cons", "module_set_exp", "pathabundance"]},
        "parameters": {"seed": SEED, "n_boot": 5000, "fdr_threshold": FDR_THRESHOLD},
        "n_M": n_m_total, "n_S": n_s_total,
    }
    _save_fig(fig, outdir / "Figure2_Module_Mechanisms", meta, base_dir=base_dir)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIGURE 3: Pathway Landscape & Drivers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def make_figure3(base_dir: Path, data: dict[str, pd.DataFrame], outdir: Path) -> None:
    path_stats = data["path_stats"].copy()
    groups = data["groups"].copy()

    fig = plt.figure(figsize=(9.0, 7.5))
    gs = fig.add_gridspec(2, 2, wspace=0.42, hspace=0.45)

    # ── Panel a: Enhanced volcano ──
    ax_a = fig.add_subplot(gs[0, 0])
    df = path_stats.copy()
    df["neglog10p"] = -np.log10(df["p"] + 1e-300)

    sig_strong = df["q"] < 0.1
    sig_suggest = (df["q"] >= 0.1) & (df["q"] < FDR_THRESHOLD)
    ns = df["q"] >= FDR_THRESHOLD

    ax_a.scatter(df.loc[ns, "delta_S_minus_M"], df.loc[ns, "neglog10p"],
                 s=10, color=C["neutral"], alpha=0.4, label=f"q≥{FDR_THRESHOLD}", zorder=1)
    ax_a.scatter(df.loc[sig_suggest, "delta_S_minus_M"], df.loc[sig_suggest, "neglog10p"],
                 s=18, color="#EDC949", alpha=0.7, label=f"q<{FDR_THRESHOLD} (suggestive)", zorder=2)

    pos = sig_strong & (df["delta_S_minus_M"] > 0)
    neg = sig_strong & (df["delta_S_minus_M"] <= 0)
    ax_a.scatter(df.loc[pos, "delta_S_minus_M"], df.loc[pos, "neglog10p"],
                 s=24, color=C["S"], alpha=0.85, label="q<0.1, S↑", zorder=3)
    ax_a.scatter(df.loc[neg, "delta_S_minus_M"], df.loc[neg, "neglog10p"],
                 s=24, color=C["M"], alpha=0.85, label="q<0.1, M↑", zorder=3)

    ax_a.axvline(0, lw=0.8, color="#333333", ls="--")
    ax_a.axhline(-math.log10(0.05), lw=0.7, color="#999999", ls=":")

    # Label only top 5 pathways, stagger with increasing offsets to prevent overlap
    _top_labels = df.nsmallest(5, "p").reset_index(drop=True)
    _offsets = [(22, 8), (-22, 28), (22, 48), (-22, 68), (22, 88)]  # alternate L/R, wide Y gaps
    for _li, (_, row) in enumerate(_top_labels.iterrows()):
        _xoff, _yoff = _offsets[_li]
        _ha = "left" if _xoff > 0 else "right"
        ax_a.annotate(
            _short_feature_name(row["feature"]),
            xy=(row["delta_S_minus_M"], row["neglog10p"]),
            xytext=(_xoff, _yoff),
            textcoords="offset points", fontsize=5.5, alpha=0.85, ha=_ha, va="bottom",
            arrowprops=dict(arrowstyle="-", color="#999999", lw=0.4),
        )
    ax_a.set_xlabel("Delta (S − M)")
    ax_a.set_ylabel("-log10(p)")
    ax_a.legend(frameon=False, fontsize=6, loc="upper left")
    _panel_label(ax_a, "a")

    # ── Panel b: Top pathway heatmap ──
    ax_b = fig.add_subplot(gs[0, 1])
    ordered_runs = groups.sort_values(["group", "run_accession"])["run_accession"].tolist()
    top_features = df.nsmallest(20, "p")["feature"].tolist()
    matrix = _pathway_matrix_for_targets(
        base_dir / "results/processed/PRJDB36442_humann/merged_pathabundance.tsv.gz",
        ordered_runs, top_features,
    )
    matrix = matrix.reindex(top_features).dropna(how="all")
    matrix = np.log10(matrix + 1e-9)
    row_mean = matrix.mean(axis=1)
    row_std = matrix.std(axis=1).replace(0, np.nan)
    matrix = matrix.sub(row_mean, axis=0).div(row_std, axis=0).fillna(0)

    heat = ax_b.imshow(matrix.values, aspect="auto", cmap="RdBu_r", vmin=-2.5, vmax=2.5)
    ax_b.set_yticks(np.arange(len(matrix.index)),
                     [_short_pathway_label(x) for x in matrix.index], fontsize=6)
    ax_b.set_xticks([])

    n_m_count = int((groups["group"] == "M").sum())
    for xi in range(len(ordered_runs)):
        col = C["M"] if xi < n_m_count else C["S"]
        ax_b.plot(xi, -0.8, marker="s", color=col, markersize=3, clip_on=False)

    plt.colorbar(heat, ax=ax_b, fraction=0.04, pad=0.04, label="Row z-score")
    _panel_label(ax_b, "b")

    # ── Panel c: Stratified pathway drivers ──
    ax_c = fig.add_subplot(gs[1, 0])
    contrib_files = [
        "strat_contrib_ARGSYN-PWY.tsv",
        "strat_contrib_ARGSYNBSUB-PWY.tsv",
        "strat_contrib_GLUTORN-PWY.tsv",
    ]
    rows = []
    for fname in contrib_files:
        fp = base_dir / f"results/processed/PRJDB36442_humann/{fname}"
        if not fp.exists():
            continue
        t = _read_tsv(fp)
        t["abs_delta"] = t["delta_S_minus_M"].abs()
        t = t.nlargest(8, "abs_delta")
        pathway_code = fname.replace("strat_contrib_", "").replace(".tsv", "")
        for _, row in t.iterrows():
            species = _abbrev_species_from_strat(str(row["feature"]))
            rows.append({"pathway": pathway_code, "species": species,
                         "delta": float(row["delta_S_minus_M"])})
    contrib = pd.DataFrame(rows)
    if not contrib.empty:
        score = (contrib.groupby("species")["delta"]
                 .apply(lambda s: float(np.abs(s).sum()))
                 .sort_values(ascending=False))
        top_species = score.head(12).index.tolist()
        mat = (contrib[contrib["species"].isin(top_species)]
               .pivot_table(index="species", columns="pathway", values="delta", aggfunc="sum")
               .fillna(0.0).reindex(top_species))
        vmax = max(abs(mat.values.min()), abs(mat.values.max()), 0.01)
        heat2 = ax_c.imshow(mat.values, aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)
        ax_c.set_yticks(np.arange(len(mat.index)), mat.index.tolist(), fontsize=6)
        ax_c.set_xticks(np.arange(len(mat.columns)),
                         [c.replace("-PWY", "") for c in mat.columns.tolist()],
                         rotation=40, ha="right", fontsize=6)
        plt.colorbar(heat2, ax=ax_c, fraction=0.04, pad=0.04, label="Delta (S − M)")
    _panel_label(ax_c, "c")

    # ── Panel d: Q-value cumulative landscape ──
    ax_d = fig.add_subplot(gs[1, 1])
    q_vals = df["q"].dropna().sort_values().to_numpy()
    thresholds = np.arange(0, 1.01, 0.05)
    counts = [int(np.sum(q_vals <= t)) for t in thresholds]

    ax_d.fill_between(thresholds, 0, counts, alpha=0.15, color=C["M"])
    ax_d.plot(thresholds, counts, color=C["M"], lw=1.5)
    ax_d.scatter([0.1, FDR_THRESHOLD],
                 [int(np.sum(q_vals <= 0.1)), int(np.sum(q_vals <= FDR_THRESHOLD))],
                 color=[C["S"], "#EDC949"], s=40, zorder=3, edgecolors="white", lw=0.4)

    ax_d.axvline(0.1, color=C["S"], lw=0.7, ls=":", alpha=0.6)
    ax_d.axvline(FDR_THRESHOLD, color="#EDC949", lw=0.7, ls=":", alpha=0.6)
    ax_d.text(0.12, max(counts) * 0.9, f"q=0.10\n({int(np.sum(q_vals <= 0.1))})",
              fontsize=7, color=C["S"])
    ax_d.text(FDR_THRESHOLD + 0.02, max(counts) * 0.75,
              f"q={FDR_THRESHOLD}\n({int(np.sum(q_vals <= FDR_THRESHOLD))})",
              fontsize=7, color="#B07AA1")

    ax_d.set_xlabel("FDR (q) threshold")
    ax_d.set_ylabel("Pathways passing")
    _panel_label(ax_d, "d")

    meta = {
        "figure": "Figure3_Pathway_and_Drivers",
        "panels": ["a:volcano", "b:top_pathway_heatmap", "c:stratified_drivers", "d:q_distribution"],
        "inputs": {k: INPUT_MANIFEST[k] for k in ["path_stats", "pathabundance"]},
        "parameters": {"top_n_volcano_labels": 8, "top_n_heatmap_rows": 20,
                        "strat_contrib_files": contrib_files, "top_species_driver": 12,
                        "fdr_threshold": FDR_THRESHOLD},
        "filter_rules": {"heatmap_rows": "top 20 pathways by raw p-value",
                          "driver_species": "top 8 by |delta| per pathway, then top 12 overall"},
    }
    _save_fig(fig, outdir / "Figure3_Pathway_and_Drivers", meta, base_dir=base_dir)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIGURE 4: External Validation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def make_figure4(data: dict[str, pd.DataFrame], outdir: Path, base_dir: Path) -> None:
    mod = data["mod_dir"].copy()
    pw = data["path_dir"].copy()
    mod["direction_match_bool"] = mod["direction_match"].astype(str).str.lower().isin(["true", "1", "yes"])
    pw["direction_match_bool"] = pw["direction_match"].astype(str).str.lower().isin(["true", "1", "yes"])

    fig = plt.figure(figsize=(7.2, 7.2))
    gs = fig.add_gridspec(2, 2, wspace=0.38, hspace=0.38)

    # ── Panel a: Dumbbell ──
    ax_a = fig.add_subplot(gs[0, 0])
    mod_sorted = mod.sort_values("delta_S_minus_M").reset_index(drop=True)
    std_chb = max(float(mod_sorted["delta_S_minus_M"].std(ddof=0)), 1e-12)
    std_ext = max(float(mod_sorted["delta_LC_minus_HC"].std(ddof=0)), 1e-12)
    mod_sorted["z_chb"] = mod_sorted["delta_S_minus_M"] / std_chb
    mod_sorted["z_ext"] = mod_sorted["delta_LC_minus_HC"] / std_ext

    y_a = np.arange(len(mod_sorted))
    for i, (_, row) in enumerate(mod_sorted.iterrows()):
        col = C["match"] if row["direction_match_bool"] else C["mismatch"]
        ax_a.plot([row["z_chb"], row["z_ext"]], [i, i], color=col, alpha=0.5, lw=1.4, zorder=1)
    ax_a.scatter(mod_sorted["z_chb"], y_a, color=C["M"], s=50, zorder=3,
                 edgecolors="white", lw=0.4, label="CHB (S−M)")
    ax_a.scatter(mod_sorted["z_ext"], y_a, color=C["LC"], s=50, zorder=3,
                 edgecolors="white", lw=0.4, marker="D", label="Ext (LC−HC)")
    ax_a.axvline(0, color="#333333", lw=0.8, ls="--")
    ax_a.set_yticks(y_a, mod_sorted["module"].str.replace("_", " ", regex=False), fontsize=7)
    ax_a.set_xlabel("Standardized effect size")
    ax_a.legend(frameon=False, fontsize=7, loc="upper left")

    for i, (_, row) in enumerate(mod_sorted.iterrows()):
        tag = "Y" if row["direction_match_bool"] else "N"
        col = C["match"] if row["direction_match_bool"] else C["mismatch"]
        ax_a.text(max(row["z_chb"], row["z_ext"]) + 0.15, i, tag, color=col,
                  fontsize=8, fontweight="bold", va="center")
    _panel_label(ax_a, "a")

    # ── Panel b: Direction match rate bar ──
    ax_b = fig.add_subplot(gs[0, 1])
    n_match = int(mod["direction_match_bool"].sum())
    n_mismatch = int(len(mod) - n_match)
    n_total = len(mod)
    rate = 100.0 * n_match / n_total if n_total else 0

    ax_b.barh([0], [n_match], color=C["match"], height=0.5, label=f"Match (n={n_match})")
    ax_b.barh([0], [n_mismatch], left=[n_match], color=C["mismatch"], height=0.5,
              label=f"Mismatch (n={n_mismatch})")
    ax_b.text(n_total / 2, 0, f"{rate:.0f}%", ha="center", va="center",
              fontsize=14, fontweight="bold", color="white")

    pw_n_match = int(pw["direction_match_bool"].sum())
    pw_n_total = len(pw)
    pw_rate = 100.0 * pw_n_match / pw_n_total if pw_n_total else 0
    ax_b.barh([1], [pw_n_match], color=C["match"], height=0.5, alpha=0.6)
    ax_b.barh([1], [pw_n_total - pw_n_match], left=[pw_n_match], color=C["mismatch"],
              height=0.5, alpha=0.6)
    ax_b.text(pw_n_total / 2, 1, f"{pw_rate:.0f}%", ha="center", va="center",
              fontsize=11, fontweight="bold", color="white")
    ax_b.set_yticks([0, 1], ["Modules", "Pathways"], fontsize=8)
    ax_b.tick_params(axis="y", pad=12)
    ax_b.set_xlim(0, max(n_total, pw_n_total) * 1.1)
    ax_b.set_xlabel("Count")
    ax_b.legend(frameon=False, fontsize=7, loc="upper right")
    _panel_label(ax_b, "b")

    # ── Panel c: Pathway concordance scatter ──
    ax_c = fig.add_subplot(gs[1, 0])
    matched = pw["direction_match_bool"]
    ax_c.scatter(pw.loc[~matched, "delta_S_minus_M"], pw.loc[~matched, "delta_LC_minus_HC"],
                 s=14, color=C["mismatch"], alpha=0.45, label="Mismatch", zorder=2)
    ax_c.scatter(pw.loc[matched, "delta_S_minus_M"], pw.loc[matched, "delta_LC_minus_HC"],
                 s=14, color=C["match"], alpha=0.55, label="Match", zorder=3)
    ax_c.axhline(0, lw=0.7, color="#444444", alpha=0.5)
    ax_c.axvline(0, lw=0.7, color="#444444", alpha=0.5)
    ax_c.set_xlabel("CHB delta (S − M)")
    ax_c.set_ylabel("HBV-LC delta (LC − HC)")
    ax_c.legend(frameon=False, fontsize=7)
    _panel_label(ax_c, "c")

    # ── Panel d: Concordance by q bin ──
    ax_d = fig.add_subplot(gs[1, 1])
    bins_def = [
        ("q≤0.01", pw[pw["q_HBVLC"] <= 0.01]),
        ("0.01<q≤0.05", pw[(pw["q_HBVLC"] > 0.01) & (pw["q_HBVLC"] <= 0.05)]),
        ("0.05<q≤0.10", pw[(pw["q_HBVLC"] > 0.05) & (pw["q_HBVLC"] <= 0.10)]),
        ("q>0.10", pw[pw["q_HBVLC"] > 0.10]),
    ]
    labels_d, rates_d, ns_d = [], [], []
    for label, sub in bins_def:
        n = len(sub)
        labels_d.append(label)
        ns_d.append(n)
        rates_d.append(float(sub["direction_match_bool"].mean() * 100.0) if n else np.nan)

    x_d = np.arange(len(labels_d))
    y_rates = np.array(rates_d, dtype=float)
    bar_colors = [C["match"] if (not np.isnan(r) and r >= 50) else C["mismatch"] for r in y_rates]
    ax_d.bar(x_d, y_rates, color=bar_colors, alpha=0.6, width=0.6)
    ax_d.axhline(50, lw=0.7, color="#999999", ls=":")
    for i, (r, n) in enumerate(zip(rates_d, ns_d)):
        txt = "NA" if np.isnan(r) else f"{r:.0f}%"
        ax_d.text(i, max(0, r if not np.isnan(r) else 0) + 2,
                  f"{txt}\n(n={n})", ha="center", fontsize=7)
    ax_d.set_xticks(x_d, labels_d, fontsize=7)
    ax_d.set_ylim(0, 105)
    ax_d.set_ylabel("Direction match rate (%)")
    _panel_label(ax_d, "d")

    meta = {
        "figure": "Figure4_External_Validation",
        "panels": ["a:dumbbell_cross_cohort", "b:match_rate_bar", "c:quadrant_scatter", "d:q_bin_trend"],
        "inputs": {k: INPUT_MANIFEST[k] for k in ["mod_dir", "path_dir"]},
        "parameters": {"standardization": "divide by ddof=0 std within each cohort",
                        "direction_match_def": "same sign of delta"},
        "n_modules": len(mod), "n_pathways": len(pw),
        "module_match_rate": f"{rate:.1f}%", "pathway_match_rate": f"{pw_rate:.1f}%",
    }
    _save_fig(fig, outdir / "Figure4_External_Validation", meta, base_dir=base_dir)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIGURE 5: Evidence Chain / Triangulation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MECHANISM_MAP = {
    "scfa_acetate": {"pathway": "GPR41/43 → NF-κB modulation", "ref_key": "Koh2016_Cell",
                     "note": "Acetate signals via GPR41/43 in colonocytes; anti-inflammatory"},
    "scfa_butyrate": {"pathway": "Barrier integrity via HDAC inhibition", "ref_key": "Furusawa2013_Nature",
                      "note": "Butyrate maintains tight junctions and Treg induction"},
    "scfa_lactate_succinate": {"pathway": "pH modulation + T-cell metabolism", "ref_key": "Louis2017_NatRevMicro",
                               "note": "Succinate/lactate cross-feeding shapes immune milieu"},
    "tryptophan_indole": {"pathway": "AhR ligand → IL-22 → barrier", "ref_key": "Agus2018_CellHostMicrobe",
                          "note": "Indole derivatives activate AhR in gut epithelium"},
    "lps_lipidA": {"pathway": "TLR4 → MyD88 → pro-inflammatory", "ref_key": "Park2009_ImmunolRev",
                   "note": "LPS/lipid-A activates hepatic Kupffer cells via portal vein"},
    "bile_acids": {"pathway": "FXR/TGR5 axis → bile homeostasis", "ref_key": "Wahlstrom2016_CellMetab",
                   "note": "Microbial bile acid metabolism modulates host FXR signaling"},
}

DRIVER_FILTER = {
    "rule": "direction_match_bool == True AND q_CHB < 1.0",
    "sort_by": "-log10(p_CHB)", "top_n": 8,
    "description": "Select concordant-direction pathways; rank by CHB p; top 12. All exploratory.",
}

TRIANGULATION_CHECKLIST = [
    {"criterion": "Within-cohort signal", "test": "Mann-Whitney + bootstrap CI", "pass_if": "p<0.05 AND CI excludes 0"},
    {"criterion": "Definition robustness", "test": "Conservative vs expanded", "pass_if": "Same direction in both"},
    {"criterion": "External direction", "test": "Cross-cohort delta sign", "pass_if": "Same sign in HBV-LC"},
    {"criterion": "Mechanistic plausibility", "test": "Literature mapping", "pass_if": "Published mechanism ref exists"},
    {"criterion": "Multiplicity awareness", "test": "q-value reported", "pass_if": "q + classification stated"},
]


def make_figure5_mechanism(base_dir: Path, data: dict[str, pd.DataFrame], outdir: Path) -> None:
    mod_primary = data["module_cons"].copy()
    mod_external = data["mod_dir"].copy()
    pw = data["path_dir"].copy()

    mod = mod_primary.merge(
        mod_external[["module", "delta_LC_minus_HC", "p_HBVLC", "direction_match"]],
        on="module", how="left",
    )
    mod["direction_match_bool"] = mod["direction_match"].astype(str).str.lower().isin(["true", "1", "yes"])
    pw["direction_match_bool"] = pw["direction_match"].astype(str).str.lower().isin(["true", "1", "yes"])

    fig = plt.figure(figsize=(7.2, 7.8))
    gs = fig.add_gridspec(2, 2, wspace=0.36, hspace=0.40)

    # ── Panel a: Evidence Bridge ──
    ax_a = fig.add_subplot(gs[0, 0])
    mod_sorted = mod.sort_values("delta_S_minus_M").reset_index(drop=True)
    std_chb = max(mod_sorted["delta_S_minus_M"].std(ddof=0), 1e-12)
    std_ext = max(mod_sorted["delta_LC_minus_HC"].std(ddof=0), 1e-12)
    mod_sorted["z_chb"] = mod_sorted["delta_S_minus_M"] / std_chb
    mod_sorted["z_ext"] = mod_sorted["delta_LC_minus_HC"] / std_ext

    y_a = np.arange(len(mod_sorted))
    for i, (_, row) in enumerate(mod_sorted.iterrows()):
        col = C["match"] if row["direction_match_bool"] else C["mismatch"]
        ax_a.plot([row["z_chb"], row["z_ext"]], [i, i], color=col, alpha=0.5, lw=1.4, zorder=1)
    ax_a.scatter(mod_sorted["z_chb"], y_a, color=C["M"], s=55, zorder=3,
                 edgecolors="white", lw=0.4, label="Discovery (S−M)")
    ax_a.scatter(mod_sorted["z_ext"], y_a, color=C["LC"], s=55, zorder=3,
                 edgecolors="white", lw=0.4, marker="D", label="Validation (LC−HC)")
    ax_a.axvline(0, color="#333333", lw=0.8, ls="--")
    ax_a.set_yticks(y_a, mod_sorted["module"].str.replace("_", " ", regex=False), fontsize=7)
    ax_a.set_xlabel("Standardized effect")
    ax_a.legend(frameon=False, fontsize=7, loc="upper left")

    for i, (_, row) in enumerate(mod_sorted.iterrows()):
        ax_a.annotate(f"q={row['q']:.3f}", xy=(1.02, i), xycoords=("axes fraction", "data"),
                      fontsize=5.5, color="#555555", va="center", annotation_clip=False)
    _panel_label(ax_a, "a")

    # ── Panel b: Driver Transparency ──
    ax_b = fig.add_subplot(gs[0, 1])
    candidate = pw[pw["direction_match_bool"]].copy()
    candidate["confidence"] = -np.log10(candidate["p_CHB"] + 1e-300)
    top = candidate.sort_values("confidence", ascending=False).head(DRIVER_FILTER["top_n"]).copy()
    top = top.sort_values("delta_S_minus_M", ascending=True)

    y_b = np.arange(len(top))
    bar_colors = [C["S"] if d > 0 else C["M"] for d in top["delta_S_minus_M"]]
    ax_b.barh(y_b, top["delta_S_minus_M"], color=bar_colors, alpha=0.65, height=0.65)
    ax_b.set_yticks(y_b, [_short_pathway_label(x, 22) for x in top["feature"]], fontsize=5.5)
    ax_b.axvline(0, color="#333333", lw=0.8, ls="--")

    for i, (_, row) in enumerate(top.iterrows()):
        q_chb = row["q_CHB"]
        tag = " (expl.)" if q_chb >= 0.1 else ""
        ax_b.annotate(f"q={q_chb:.2f}{tag}", xy=(1.02, i), xycoords=("axes fraction", "data"),
                      fontsize=5.5, color="#555555", va="center", annotation_clip=False)
    ax_b.set_xlabel("CHB delta (S − M)")
    ax_b.text(0.5, -0.22, f"Filter: concordant dir.; top {DRIVER_FILTER['top_n']} by -log10(p_CHB)",
              transform=ax_b.transAxes, fontsize=4.5, color="#777777", ha="center")
    _panel_label(ax_b, "b")

    # ── Panel c: Mechanistic Logic Matrix ──
    ax_c = fig.add_subplot(gs[1, 0])
    ax_c.axis("off")

    col_headers = ["Module", "Dir", "Val", "Mechanism", "Ref"]
    cell_data = []
    for _, row in mod.iterrows():
        m = row["module"]
        mech = MECHANISM_MAP.get(m, {"pathway": "--", "ref_key": "--"})
        direction = "v S" if row["delta_S_minus_M"] < 0 else "^ S"
        validated = "Y" if row["direction_match_bool"] else "N"
        # Shorter labels to prevent table cell overflow
        mech_short = mech["pathway"].split("→")[0].strip()[:18]
        ref_short = mech["ref_key"].split("_")[0][:14]
        cell_data.append([m.replace("_", " ")[:14], direction, validated,
                          mech_short, ref_short])

    table = ax_c.table(cellText=cell_data, colLabels=col_headers, loc="center", cellLoc="left")
    table.auto_set_font_size(False)
    table.set_fontsize(6)
    table.auto_set_column_width(col=list(range(len(col_headers))))
    table.scale(1.0, 1.6)

    for (row_idx, col_idx), cell in table.get_celld().items():
        cell.set_linewidth(0.4)
        if row_idx == 0:
            cell.set_facecolor("#e8e8e8")
            cell.set_text_props(fontweight="bold")
        elif col_idx == 2:
            text = cell.get_text().get_text()
            if text == "Y":
                cell.set_facecolor("#e6f5e6")
            elif text == "N":
                cell.set_facecolor("#fde8e8")
    _panel_label(ax_c, "c")

    # ── Panel d: Triangulation Workflow ──
    ax_d = fig.add_subplot(gs[1, 1])
    ax_d.axis("off")
    ax_d.set_xlim(0, 1)
    ax_d.set_ylim(0, 1)

    stages = [
        (0.5, 0.92, "Discovery\n(CHB, n=20)", "#f0f0f0", "#888888"),
        (0.5, 0.70, "Robustness\n(definition sensitivity)", "#e8f0f8", C["conservative"]),
        (0.5, 0.48, "Cross-Cohort\n(direction replication)", "#e8f4e8", C["match"]),
        (0.5, 0.26, "Mechanistic\n(literature mapping)", "#f5f0e8", "#B07AA1"),
    ]
    box_w, box_h = 0.52, 0.12
    for x, y, text, fc, ec in stages:
        bbox = FancyBboxPatch((x - box_w / 2, y - box_h / 2), box_w, box_h,
                               boxstyle="round,pad=0.02", facecolor=fc, edgecolor=ec,
                               linewidth=1.2, transform=ax_d.transData)
        ax_d.add_patch(bbox)
        ax_d.text(x, y, text, ha="center", va="center", fontsize=7, fontweight="bold")

    for i in range(len(stages) - 1):
        y_start = stages[i][1] - box_h / 2 - 0.01
        y_end = stages[i + 1][1] + box_h / 2 + 0.01
        ax_d.annotate("", xy=(0.5, y_end), xytext=(0.5, y_start),
                      arrowprops=dict(arrowstyle="-|>", lw=1.2, color="#666666"))

    ax_d.text(0.08, 0.59, "Noise\nfiltered", fontsize=6, color=C["mismatch"],
              fontweight="bold", ha="center", va="center", alpha=0.7)
    ax_d.text(0.92, 0.59, "Signal\nretained", fontsize=6, color=C["match"],
              fontweight="bold", ha="center", va="center", alpha=0.7)
    ax_d.text(0.5, 0.10, "Outcome: hypothesis-generating candidates\nranked by concordance + plausibility",
              ha="center", va="center", fontsize=6.5, color="#555555", style="italic")
    _panel_label(ax_d, "d")

    meta = {
        "figure": "Figure5_Mechanistic_Integration",
        "panels": ["a:evidence_bridge", "b:driver_transparency", "c:mechanistic_logic_matrix",
                    "d:triangulation_workflow"],
        "inputs": {k: INPUT_MANIFEST[k] for k in ["module_cons", "mod_dir", "path_dir"]},
        "parameters": {"seed": SEED, "fdr_threshold": FDR_THRESHOLD, "driver_filter": DRIVER_FILTER,
                        "mechanism_map": MECHANISM_MAP, "triangulation_checklist": TRIANGULATION_CHECKLIST},
        "narrative_constraints": {"discovery_classification": "exploratory / hypothesis-generating",
                                   "validation_classification": "direction replication / robustness evidence",
                                   "no_post_hoc_selection": True},
    }
    _save_fig(fig, outdir / "Figure5_Mechanistic_Integration", meta, base_dir=base_dir)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIGURE S1: Audit & Traceability
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def make_figure_s1_audit_map(base_dir: Path, data: dict[str, pd.DataFrame], outdir: Path) -> None:
    fig = plt.figure(figsize=(7.2, 3.8))
    gs = fig.add_gridspec(1, 2, wspace=0.30, width_ratios=[1.3, 1])

    ax_a = fig.add_subplot(gs[0, 0])
    steps = [
        ("Registry", "PRJDB36442\nlabels"),
        ("Cloud QC", "MetaPhlAn\nHUMAnN"),
        ("Statistics", "Module +\npathway"),
        ("Validation", "HBV-LC\nreplication"),
        ("Repro", "hash + env\nhashes"),
    ]
    stage_colors = [CAT8[i] for i in range(len(steps))]
    x = np.arange(len(steps))
    y = np.zeros(len(steps))

    ax_a.plot(x, y, color="#c0c0c0", lw=2.5, zorder=1)
    ax_a.scatter(x, y, s=240, color=stage_colors, edgecolor="white", linewidth=1.2, zorder=3)

    for i, (name, sub) in enumerate(steps):
        ax_a.text(i, 0.22, name, ha="center", va="bottom", fontsize=6.5, fontweight="bold")
        ax_a.text(i, -0.24, sub, ha="center", va="top", fontsize=5.5, color="#555555")
        if i < len(steps) - 1:
            ax_a.annotate("", xy=(i + 0.75, 0), xytext=(i + 0.25, 0),
                          arrowprops={"arrowstyle": "-|>", "lw": 1.0, "color": "#888888"})

    ax_a.set_xlim(-0.7, len(steps) - 0.3)
    ax_a.set_ylim(-0.52, 0.42)
    ax_a.set_xticks([])
    ax_a.set_yticks([])
    for spine in ax_a.spines.values():
        spine.set_visible(False)
    _panel_label(ax_a, "a")

    ax_b = fig.add_subplot(gs[0, 1])
    hash_file = base_dir / "results/repro/artifact_hashes.sha256"
    hash_n = 0
    if hash_file.exists():
        with hash_file.open("r", encoding="utf-8", errors="ignore") as f:
            hash_n = sum(1 for line in f if line.strip())

    metrics = [
        ("Samples with labels", int(len(data["groups"]))),
        ("Primary pathways tested", int(len(data["path_stats"]))),
        ("Primary modules tested", int(len(data["module_cons"]))),
        ("External pathways checked", int(len(data["path_dir"]))),
        ("External modules checked", int(len(data["mod_dir"]))),
        ("Artifacts hashed", int(hash_n)),
    ]
    metrics = sorted(metrics, key=lambda kv: kv[1])
    labels_b = [m[0] for m in metrics]
    values = np.array([m[1] for m in metrics], dtype=float)
    y_b = np.arange(len(metrics))

    ax_b.hlines(y_b, 0, values, color="#c0c0c0", lw=1.4)
    ax_b.scatter(values, y_b, s=65, color=C["M"], zorder=3, edgecolors="white", lw=0.4)
    for yi, v in zip(y_b, values):
        ax_b.text(v + max(values) * 0.02, yi, f"{int(v)}", va="center", fontsize=8)
    ax_b.set_yticks(y_b, labels_b, fontsize=7)
    ax_b.set_xlabel("Count")
    _panel_label(ax_b, "b")

    meta = {
        "figure": "FigureS1_Audit_Traceability",
        "panels": ["a:pipeline_timeline", "b:audit_lollipop"],
        "inputs": {"groups": INPUT_MANIFEST["groups"],
                    "artifact_hashes": "results/repro/artifact_hashes.sha256"},
        "audit_counts": dict(metrics),
    }
    _save_fig(fig, outdir / "FigureS1_Audit_Traceability", meta, base_dir=base_dir)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build publication figure boards (redesigned v2).")
    parser.add_argument("--base-dir", type=Path, default=Path("."))
    parser.add_argument("--outdir", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=SEED)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_dir = args.base_dir.resolve()
    outdir = args.outdir.resolve() if args.outdir else (base_dir / "plots/publication")
    outdir.mkdir(parents=True, exist_ok=True)

    global SEED
    SEED = args.seed
    global INPUT_CHECKSUMS
    INPUT_CHECKSUMS = _input_checksums(base_dir)

    print(f"[info] loading inputs from: {base_dir}")
    data = _load_inputs(base_dir)
    module_scores = _build_module_scores(base_dir, data["groups"], data["module_set_cons"])

    print("[1/6] Figure 1: Cohort Profile")
    make_figure1(data, outdir, base_dir)

    print("[2/6] Figure 2: Module Mechanisms")
    make_figure2(data, module_scores, outdir, base_dir)

    print("[3/6] Figure 3: Pathway & Drivers")
    make_figure3(base_dir, data, outdir)

    print("[4/6] Figure 4: External Validation")
    make_figure4(data, outdir, base_dir)

    print("[5/6] Figure 5: Mechanistic Integration")
    make_figure5_mechanism(base_dir, data, outdir)

    print("[6/6] Figure S1: Audit Traceability")
    make_figure_s1_audit_map(base_dir, data, outdir)

    with open(outdir / "_input_checksums.json", "w") as f:
        json.dump(INPUT_CHECKSUMS, f, indent=2)

    print(f"[ok] all figure boards written to: {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
