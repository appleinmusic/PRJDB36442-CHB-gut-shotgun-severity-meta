#!/usr/bin/env python3
"""
Build module-level CHB (S vs M) statistics and refresh the cross-cohort direction table.

Outputs (canonical):
  - results/processed/PRJDB36442_humann/module_M_vs_S_stats_conservative.tsv
  - results/processed/PRJDB36442_humann/module_M_vs_S_stats_expanded.tsv
  - results/external/module_direction_validation.tsv

Definitions follow the same conventions used by the publication figure generator:
  - Use HUMAnN unstratified pathways only (drop rows containing '|').
  - Drop UNMAPPED/UNINTEGRATED.
  - Normalize each sample to relative abundance by dividing by the sample's total unstratified abundance.
  - Module score = sum of member pathway relative abundances (membership from module_sets_*.tsv).
  - CHB group label comes from results/feasibility/PRJDB36442_run_groups.tsv (M/S).
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu


def _clean_run_col(column: str) -> str:
    return re.sub(r"_(Abundance|Coverage)(-RPKs)?$", "", column)


def _bh_fdr(pvals: list[float]) -> list[float]:
    n = len(pvals)
    indexed = [(i, p) for i, p in enumerate(pvals) if not math.isnan(p)]
    indexed.sort(key=lambda x: x[1])

    q = [float("nan")] * n
    if not indexed:
        return q

    m = len(indexed)
    prev = 1.0
    for rank, (i, p) in enumerate(reversed(indexed), start=1):
        k = m - rank + 1
        val = min(prev, p * m / k)
        q[i] = val
        prev = val
    return q


def _build_module_scores(
    merged_pathabundance: Path,
    module_set: Path,
    run_groups: Path,
) -> pd.DataFrame:
    groups = pd.read_csv(run_groups, sep="\t")
    group_map = dict(zip(groups["run_accession"], groups["group"]))

    df = pd.read_csv(merged_pathabundance, sep="\t").rename(columns={"# Pathway": "feature"})
    df = df[~df["feature"].str.contains(r"\|", regex=True)]
    df = df[~df["feature"].isin(["UNMAPPED", "UNINTEGRATED"])]

    rename_map = {c: _clean_run_col(c) for c in df.columns if c != "feature"}
    df = df.rename(columns=rename_map)
    run_cols = [c for c in df.columns if c != "feature"]

    rel = df[run_cols].div(df[run_cols].sum(axis=0), axis=1)
    rel.insert(0, "feature", df["feature"].values)
    rel = rel.set_index("feature")

    ms = pd.read_csv(module_set, sep="\t")
    modules = ms.groupby("module")["feature"].apply(list).to_dict()

    rows: list[dict[str, object]] = []
    for module, feats in modules.items():
        feats = [f for f in feats if f in rel.index]
        if not feats:
            continue
        scores = rel.loc[feats].sum(axis=0)
        for run, score in scores.items():
            g = group_map.get(run)
            if g not in {"M", "S"}:
                continue
            rows.append({"module": module, "run_accession": run, "group": g, "score": float(score)})
    return pd.DataFrame(rows)


def _module_stats(scores: pd.DataFrame) -> pd.DataFrame:
    out_rows: list[dict[str, object]] = []
    pvals: list[float] = []

    for module in sorted(scores["module"].unique().tolist()):
        m = scores.loc[(scores["module"] == module) & (scores["group"] == "M"), "score"].to_numpy()
        s = scores.loc[(scores["module"] == module) & (scores["group"] == "S"), "score"].to_numpy()
        median_m = float(np.median(m)) if len(m) else float("nan")
        median_s = float(np.median(s)) if len(s) else float("nan")
        delta = float(median_s - median_m) if (len(m) and len(s)) else float("nan")

        if len(m) and len(s):
            _, p = mannwhitneyu(m, s, alternative="two-sided")
            p = float(p)
        else:
            p = float("nan")

        pvals.append(p)
        out_rows.append(
            {
                "module": module,
                "median_M": median_m,
                "median_S": median_s,
                "delta_S_minus_M": delta,
                "p": p,
            }
        )

    qvals = _bh_fdr(pvals)
    for row, q in zip(out_rows, qvals, strict=True):
        row["q"] = float(q)

    df = pd.DataFrame(out_rows)
    return df[["module", "median_M", "median_S", "delta_S_minus_M", "p", "q"]]


def _write_tsv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, sep="\t", index=False)


def _build_module_direction_validation(chb_stats: Path, hbvlc_stats: Path, out_path: Path) -> None:
    chb = pd.read_csv(chb_stats, sep="\t")
    ext = pd.read_csv(hbvlc_stats, sep="\t")

    merged = chb.merge(ext, on="module", how="inner")
    # both tables have "p" → pandas will suffix as p_x (CHB) and p_y (HBVLC)
    if "p_x" not in merged.columns or "p_y" not in merged.columns:
        raise KeyError(f"Unexpected p-value columns after merge: {merged.columns.tolist()}")
    merged = merged.rename(columns={"p_x": "p_CHB", "p_y": "p_HBVLC"})

    merged["direction_match"] = (
        np.sign(merged["delta_S_minus_M"].astype(float)) == np.sign(merged["delta_LC_minus_HC"].astype(float))
    )

    keep = merged[
        [
            "module",
            "median_M",
            "median_S",
            "delta_S_minus_M",
            "p_CHB",
            "median_LC",
            "median_HC",
            "delta_LC_minus_HC",
            "p_HBVLC",
            "direction_match",
        ]
    ].copy()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    keep.to_csv(out_path, sep="\t", index=False)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Build module-level M vs S stats + external direction table.")
    ap.add_argument(
        "--merged-pathabundance",
        type=Path,
        default=Path("results/processed/PRJDB36442_humann/merged_pathabundance.tsv.gz"),
    )
    ap.add_argument(
        "--run-groups",
        type=Path,
        default=Path("results/feasibility/PRJDB36442_run_groups.tsv"),
    )
    ap.add_argument(
        "--module-set-cons",
        type=Path,
        default=Path("results/processed/PRJDB36442_humann/module_sets_conservative.tsv"),
    )
    ap.add_argument(
        "--module-set-exp",
        type=Path,
        default=Path("results/processed/PRJDB36442_humann/module_sets_expanded.tsv"),
    )
    ap.add_argument(
        "--out-cons",
        type=Path,
        default=Path("results/processed/PRJDB36442_humann/module_M_vs_S_stats_conservative.tsv"),
    )
    ap.add_argument(
        "--out-exp",
        type=Path,
        default=Path("results/processed/PRJDB36442_humann/module_M_vs_S_stats_expanded.tsv"),
    )
    ap.add_argument(
        "--hbvlc-cons",
        type=Path,
        default=Path("results/external/HBVLC_module_stats_conservative.tsv"),
    )
    ap.add_argument(
        "--out-direction",
        type=Path,
        default=Path("results/external/module_direction_validation.tsv"),
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()

    scores_cons = _build_module_scores(args.merged_pathabundance, args.module_set_cons, args.run_groups)
    stats_cons = _module_stats(scores_cons)
    _write_tsv(stats_cons, args.out_cons)

    scores_exp = _build_module_scores(args.merged_pathabundance, args.module_set_exp, args.run_groups)
    stats_exp = _module_stats(scores_exp)
    _write_tsv(stats_exp, args.out_exp)

    _build_module_direction_validation(args.out_cons, args.hbvlc_cons, args.out_direction)

    print(f"[ok] wrote: {args.out_cons}")
    print(f"[ok] wrote: {args.out_exp}")
    print(f"[ok] wrote: {args.out_direction}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
