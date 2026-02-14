#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _bf_from_title(sample_title: str) -> str:
    # ENA sample_title looks like "BF2 (SAMC4845367)"
    m = re.match(r"^(BF\d+)\b", (sample_title or "").strip())
    return m.group(1) if m else ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Join ENA runs table with NGDC group labels (M/S).")
    ap.add_argument(
        "--ena-runs",
        type=Path,
        default=Path("results/feasibility/ena_hbv_gut_runs.tsv"),
        help="ENA runs TSV (default: results/feasibility/ena_hbv_gut_runs.tsv).",
    )
    ap.add_argument(
        "--biosamples",
        type=Path,
        default=Path("results/feasibility/PRJDB36442_biosamples.tsv"),
        help="EBI BioSamples flat TSV (default: results/feasibility/PRJDB36442_biosamples.tsv).",
    )
    ap.add_argument(
        "--groups",
        type=Path,
        default=Path("results/feasibility/PRJCA037061_sample_groups.tsv"),
        help="NGDC group TSV (default: results/feasibility/PRJCA037061_sample_groups.tsv).",
    )
    ap.add_argument(
        "--study",
        default="PRJDB36442",
        help="Study accession to filter (default: PRJDB36442).",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("results/feasibility/PRJDB36442_run_groups.tsv"),
        help="Output TSV path (default: results/feasibility/PRJDB36442_run_groups.tsv).",
    )
    args = ap.parse_args()

    ena_runs = _read_tsv(args.ena_runs)
    bios = _read_tsv(args.biosamples)
    groups = _read_tsv(args.groups)

    # Build SAMD -> (BF, SAMC)
    samd_to = {}
    for r in bios:
        samd = (r.get("sample_accession") or "").strip()
        bf = _bf_from_title(r.get("sample_title") or r.get("title") or "")
        samc = (r.get("ngdc_sample_id") or r.get("ngdc_sample_accession") or "").strip()
        if samd:
            samd_to[samd] = {"bf": bf, "samc": samc}

    # Build BF -> group from NGDC (Sample name column is BF*)
    bf_to_group = {}
    samc_to_group = {}
    for r in groups:
        bf = (r.get("sample_name") or "").strip()
        group = (r.get("group") or "").strip()
        samc = (r.get("ngdc_sample_accession") or "").strip()
        if bf:
            bf_to_group[bf] = group
        if samc:
            samc_to_group[samc] = group

    out_rows = []
    for r in ena_runs:
        if (r.get("study_accession") or "").strip() != args.study:
            continue
        run = (r.get("run_accession") or "").strip()
        samd = (r.get("sample_accession") or "").strip()
        sample_title = (r.get("sample_title") or "").strip()
        bf = _bf_from_title(sample_title)
        samc = ""
        if samd in samd_to:
            samc = samd_to[samd]["samc"]
            bf = bf or samd_to[samd]["bf"]
        group = ""
        if bf and bf in bf_to_group:
            group = bf_to_group[bf]
        elif samc and samc in samc_to_group:
            group = samc_to_group[samc]

        out_rows.append(
            {
                "study_accession": args.study,
                "run_accession": run,
                "ena_sample_accession": samd,
                "sample_title": sample_title,
                "bf_id": bf,
                "ngdc_sample_accession": samc,
                "group": group,
            }
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "study_accession",
                "run_accession",
                "ena_sample_accession",
                "sample_title",
                "bf_id",
                "ngdc_sample_accession",
                "group",
            ],
            delimiter="\t",
        )
        w.writeheader()
        w.writerows(out_rows)

    print(str(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
