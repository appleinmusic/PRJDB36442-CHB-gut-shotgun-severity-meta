#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import math
import random
from pathlib import Path


def _open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def _sd(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return math.sqrt(var)


def _cohens_d(x1: list[float], x2: list[float]) -> float:
    if not x1 or not x2:
        return float("nan")
    s1 = _sd(x1)
    s2 = _sd(x2)
    n1 = len(x1)
    n2 = len(x2)
    if n1 + n2 - 2 <= 0:
        return float("nan")
    sp = math.sqrt(((n1 - 1) * s1 * s1 + (n2 - 1) * s2 * s2) / (n1 + n2 - 2))
    if sp == 0:
        return 0.0
    return (_mean(x2) - _mean(x1)) / sp


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


def main() -> int:
    ap = argparse.ArgumentParser(description="Basic pilot analysis for HUMAnN merged pathabundance (M vs S).")
    ap.add_argument(
        "--merged-pathabundance",
        type=Path,
        default=Path("results/cloud/PRJDB36442_humann/merged/merged_pathabundance.tsv.gz"),
        help="Input merged_pathabundance table from HUMAnN (tsv or tsv.gz).",
    )
    ap.add_argument(
        "--sample-sheet",
        type=Path,
        default=Path("results/processed/metadata/PRJDB36442_sample_sheet.tsv"),
        help="Sample sheet with run_accession and group (M/S).",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("results/processed/analysis/PRJDB36442/humann_pathabundance_differential.tsv"),
        help="Output TSV.",
    )
    ap.add_argument("--pseudocount", type=float, default=1e-9, help="Pseudocount added before log.")
    ap.add_argument("--n-perm", type=int, default=5000, help="Permutation count for two-sided test.")
    ap.add_argument("--seed", type=int, default=20260205, help="Random seed.")
    ap.add_argument(
        "--drop-stratified",
        action="store_true",
        help="Drop stratified rows containing '|' (recommended for first-pass).",
    )
    args = ap.parse_args()

    run_to_group = {r["run_accession"].strip(): r["group"].strip() for r in _read_tsv(args.sample_sheet)}

    with _open_text(args.merged_pathabundance) as f:
        header = ""
        for line in f:
            if line.startswith("#"):
                continue
            header = line.rstrip("\n")
            break
        if not header:
            raise SystemExit(f"Could not read header from {args.merged_pathabundance}")

        cols = header.split("\t")
        if len(cols) < 2:
            raise SystemExit("Header has <2 columns")

        feature_col = cols[0]
        sample_cols = cols[1:]

        # map sample columns to groups
        keep_samples: list[str] = []
        sample_groups: dict[str, str] = {}
        for s in sample_cols:
            run = s
            for suffix in ("_pathabundance", ".pathabundance"):
                if run.endswith(suffix):
                    run = run[: -len(suffix)]
            grp = run_to_group.get(run, "")
            if grp:
                keep_samples.append(s)
                sample_groups[s] = grp

        if not keep_samples:
            raise SystemExit("No overlapping samples between HUMAnN table and sample sheet.")

        idx_by_group = {"M": [], "S": []}
        for i, s in enumerate(keep_samples):
            g = sample_groups[s]
            if g in idx_by_group:
                idx_by_group[g].append(i)

        n_m = len(idx_by_group["M"])
        n_s = len(idx_by_group["S"])
        if n_m == 0 or n_s == 0:
            raise SystemExit(f"Need both groups. Found M={n_m} S={n_s}")

        pos = [cols.index(s) for s in keep_samples]
        rng = random.Random(args.seed)
        all_idx = list(range(len(keep_samples)))
        perm_subsets = [rng.sample(all_idx, k=n_s) for _ in range(args.n_perm)]

        features: list[dict[str, str]] = []
        pvals: list[float] = []

        for line in f:
            if not line or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            feat = parts[0]
            if args.drop_stratified and "|" in feat:
                continue

            vals = []
            prev_m = 0
            prev_s = 0
            for i, p in enumerate(pos):
                try:
                    v = float(parts[p])
                except (ValueError, IndexError):
                    v = 0.0
                vals.append(v)
                if v > 0.0:
                    g = sample_groups[keep_samples[i]]
                    if g == "M":
                        prev_m += 1
                    else:
                        prev_s += 1

            logs = [math.log(v + args.pseudocount) for v in vals]
            mean_log = sum(logs) / len(logs)
            clr = [x - mean_log for x in logs]

            clr_m = [clr[i] for i in idx_by_group["M"]]
            clr_s = [clr[i] for i in idx_by_group["S"]]
            obs = _mean(clr_s) - _mean(clr_m)

            total = sum(clr)
            extreme = 0
            for subset in perm_subsets:
                ssum = 0.0
                for j in subset:
                    ssum += clr[j]
                diff = (ssum / n_s) - ((total - ssum) / n_m)
                if abs(diff) >= abs(obs):
                    extreme += 1
            p_perm = (extreme + 1) / (args.n_perm + 1)

            features.append(
                {
                    "feature": feat,
                    "mean_clr_M": f"{_mean(clr_m):.6f}",
                    "mean_clr_S": f"{_mean(clr_s):.6f}",
                    "diff_S_minus_M": f"{obs:.6f}",
                    "cohens_d": f"{_cohens_d(clr_m, clr_s):.6f}",
                    "prev_M": str(prev_m),
                    "prev_S": str(prev_s),
                    "p_perm": f"{p_perm:.8f}",
                }
            )
            pvals.append(p_perm)

    qvals = _bh_fdr(pvals)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "feature",
                "mean_clr_M",
                "mean_clr_S",
                "diff_S_minus_M",
                "cohens_d",
                "prev_M",
                "prev_S",
                "p_perm",
                "q_fdr",
            ],
            delimiter="\t",
        )
        w.writeheader()
        for row, q in zip(features, qvals, strict=True):
            row["q_fdr"] = f"{q:.8f}" if not math.isnan(q) else ""
            w.writerow(row)

    print(str(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
