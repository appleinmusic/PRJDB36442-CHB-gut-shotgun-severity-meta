#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import math
import random
from dataclasses import dataclass
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
    # pooled SD
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
    # Benjamini-Hochberg q-values; preserves input order.
    n = len(pvals)
    indexed = [(i, p) for i, p in enumerate(pvals) if not math.isnan(p)]
    indexed.sort(key=lambda x: x[1])

    q = [float("nan")] * n
    if not indexed:
        return q

    m = len(indexed)
    prev = 1.0
    for rank, (i, p) in enumerate(reversed(indexed), start=1):
        # going from largest to smallest
        k = m - rank + 1
        val = min(prev, p * m / k)
        q[i] = val
        prev = val

    return q


@dataclass
class FeatureStats:
    clade_name: str
    mean_clr_m: float
    mean_clr_s: float
    diff_s_minus_m: float
    cohens_d: float
    prev_m: int
    prev_s: int
    p_perm: float


def main() -> int:
    ap = argparse.ArgumentParser(description="Basic, auditable pilot analysis for PRJDB36442 MetaPhlAn outputs.")
    ap.add_argument(
        "--species-matrix",
        type=Path,
        default=Path("results/processed/metaphlan/PRJDB36442/metaphlan_species.tsv.gz"),
        help="Species-level MetaPhlAn matrix (tsv or tsv.gz).",
    )
    ap.add_argument(
        "--sample-sheet",
        type=Path,
        default=Path("results/processed/metadata/PRJDB36442_sample_sheet.tsv"),
        help="Sample sheet with run_accession and group (M/S).",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("results/processed/analysis/PRJDB36442"),
        help="Output directory.",
    )
    ap.add_argument("--pseudocount", type=float, default=1e-9, help="Pseudocount added to proportions for CLR.")
    ap.add_argument("--n-perm", type=int, default=2000, help="Permutation count for two-sided test.")
    ap.add_argument("--seed", type=int, default=20260205, help="Random seed for permutations.")
    args = ap.parse_args()

    sample_rows = _read_tsv(args.sample_sheet)
    run_to_group: dict[str, str] = {}
    for r in sample_rows:
        run = (r.get("run_accession") or "").strip()
        grp = (r.get("group") or "").strip()
        if run and grp:
            run_to_group[run] = grp

    if not run_to_group:
        raise SystemExit(f"No run_accession/group found in {args.sample_sheet}")

    # Read matrix header
    with _open_text(args.species_matrix) as f:
        header = ""
        for line in f:
            if line.startswith("#"):
                continue
            header = line.rstrip("\n")
            break
        if not header:
            raise SystemExit(f"Could not read header from {args.species_matrix}")

        cols = header.split("\t")
        if not cols or cols[0] != "clade_name":
            raise SystemExit(f"Unexpected first column: {cols[0] if cols else ''}")

        matrix_samples = cols[1:]

        # Map matrix sample columns to groups
        sample_groups: dict[str, str] = {}
        for s in matrix_samples:
            # handle merged header like DRR764581.metaphlan
            run = s.replace(".metaphlan", "")
            grp = run_to_group.get(run, "")
            if grp:
                sample_groups[s] = grp

        keep_samples = [s for s in matrix_samples if s in sample_groups]
        if not keep_samples:
            raise SystemExit("No overlapping samples between matrix and sample sheet.")

        # Precompute indices for M/S
        idx_by_group: dict[str, list[int]] = {"M": [], "S": []}
        for i, s in enumerate(keep_samples):
            g = sample_groups[s]
            if g in idx_by_group:
                idx_by_group[g].append(i)

        n_m = len(idx_by_group["M"])
        n_s = len(idx_by_group["S"])
        if n_m == 0 or n_s == 0:
            raise SystemExit(f"Need both groups. Found M={n_m} S={n_s}")

        # Prepare permutation subsets (indices of S group); reuse across features.
        rng = random.Random(args.seed)
        all_idx = list(range(len(keep_samples)))
        perm_subsets: list[list[int]] = []
        for _ in range(args.n_perm):
            perm_subsets.append(rng.sample(all_idx, k=n_s))

        # Alpha diversity accumulators
        shannon: dict[str, float] = {s: 0.0 for s in keep_samples}
        richness: dict[str, int] = {s: 0 for s in keep_samples}

        features: list[FeatureStats] = []

        # helper for faster lookup
        keep_pos = [cols.index(s) for s in keep_samples]

        for line in f:
            if not line or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            clade = parts[0]

            # relative abundance (%) for kept samples
            vals_pct: list[float] = []
            prev_m = 0
            prev_s = 0
            for i, pos in enumerate(keep_pos):
                try:
                    v = float(parts[pos])
                except (ValueError, IndexError):
                    v = 0.0
                vals_pct.append(v)

                if v > 0.0:
                    sname = keep_samples[i]
                    if sample_groups[sname] == "M":
                        prev_m += 1
                    else:
                        prev_s += 1

            # update alpha-diversity per sample
            for i, v in enumerate(vals_pct):
                if v <= 0.0:
                    continue
                p = v / 100.0
                shannon[keep_samples[i]] += -p * math.log(p)
                richness[keep_samples[i]] += 1

            # CLR transform for this feature across samples
            logs = [math.log((v / 100.0) + args.pseudocount) for v in vals_pct]
            mean_log = sum(logs) / len(logs)
            clr = [x - mean_log for x in logs]

            clr_m = [clr[i] for i in idx_by_group["M"]]
            clr_s = [clr[i] for i in idx_by_group["S"]]
            obs = _mean(clr_s) - _mean(clr_m)

            # Two-sided permutation p-value (fixed group sizes)
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
                FeatureStats(
                    clade_name=clade,
                    mean_clr_m=_mean(clr_m),
                    mean_clr_s=_mean(clr_s),
                    diff_s_minus_m=obs,
                    cohens_d=_cohens_d(clr_m, clr_s),
                    prev_m=prev_m,
                    prev_s=prev_s,
                    p_perm=p_perm,
                )
            )

    # write alpha diversity
    args.out_dir.mkdir(parents=True, exist_ok=True)
    alpha_path = args.out_dir / "alpha_diversity.tsv"
    with alpha_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "sample_id",
                "run_accession",
                "group",
                "shannon",
                "richness",
            ],
            delimiter="\t",
        )
        w.writeheader()
        for s in keep_samples:
            run = s.replace(".metaphlan", "")
            w.writerow(
                {
                    "sample_id": s,
                    "run_accession": run,
                    "group": sample_groups[s],
                    "shannon": f"{shannon[s]:.6f}",
                    "richness": str(richness[s]),
                }
            )

    # BH-FDR on permutation p-values
    pvals = [fs.p_perm for fs in features]
    qvals = _bh_fdr(pvals)

    # write feature table
    feat_path = args.out_dir / "species_differential_clr.tsv"
    with feat_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "clade_name",
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
        for i, fs in enumerate(features):
            w.writerow(
                {
                    "clade_name": fs.clade_name,
                    "mean_clr_M": f"{fs.mean_clr_m:.6f}",
                    "mean_clr_S": f"{fs.mean_clr_s:.6f}",
                    "diff_S_minus_M": f"{fs.diff_s_minus_m:.6f}",
                    "cohens_d": f"{fs.cohens_d:.6f}",
                    "prev_M": str(fs.prev_m),
                    "prev_S": str(fs.prev_s),
                    "p_perm": f"{fs.p_perm:.8f}",
                    "q_fdr": f"{qvals[i]:.8f}" if not math.isnan(qvals[i]) else "",
                }
            )

    print(str(alpha_path))
    print(str(feat_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
