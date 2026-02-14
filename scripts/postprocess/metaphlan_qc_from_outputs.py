#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


READS_RE = re.compile(r"^#\s*(\d+)\s+reads\s+processed", re.IGNORECASE)


def _parse_one(path: Path) -> dict[str, str]:
    reads_processed = ""
    db_id = ""
    sample_id = ""
    cmd = ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#mpa_") or line.startswith("#mpa_v"):
            db_id = line.lstrip("#").strip()
        if line.startswith("#/") and "metaphlan" in line:
            cmd = line.lstrip("#").strip()
        m = READS_RE.match(line.strip())
        if m:
            reads_processed = m.group(1)
        if line.startswith("#SampleID"):
            # next non-comment line should be SampleID row, but MetaPhlAn uses a two-column pair
            continue
        if line.startswith("#") and "SampleID" in line:
            continue
        if line.startswith("#"):
            continue
        # data section begins: clade_name ...
        break

    # infer sample id from filename
    sample_id = path.name.split(".metaphlan.tsv")[0]

    return {
        "sample_id": sample_id,
        "path": str(path),
        "db_id": db_id,
        "reads_processed": reads_processed,
        "command": cmd,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract simple QC fields from MetaPhlAn per-sample outputs.")
    ap.add_argument("--in-dir", type=Path, required=True, help="Directory containing *.metaphlan.tsv files.")
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("results/processed/metaphlan/metaphlan_qc.tsv"),
        help="Output TSV (default: results/processed/metaphlan/metaphlan_qc.tsv).",
    )
    args = ap.parse_args()

    files = sorted(args.in_dir.glob("*.metaphlan.tsv"))
    if not files:
        raise SystemExit(f"No *.metaphlan.tsv found in {args.in_dir}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["sample_id", "reads_processed", "db_id", "path", "command"],
            delimiter="\t",
        )
        w.writeheader()
        for p in files:
            w.writerow(_parse_one(p))

    print(str(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

