#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path


def _fastq_total_bytes(fastq_bytes: str) -> int:
    parts = [p.strip() for p in (fastq_bytes or "").split(";") if p.strip()]
    total = 0
    for p in parts:
        try:
            total += int(p)
        except ValueError:
            return 0
    return total


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: pick_smallest_run.py <runs_tsv> <study_accession> <top_n>", file=sys.stderr)
        return 2
    runs_tsv = Path(argv[0])
    study = argv[1]
    top_n = int(argv[2])

    rows = []
    with runs_tsv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            if r.get("study_accession") != study:
                continue
            total = _fastq_total_bytes(r.get("fastq_bytes", ""))
            r["_fastq_total_bytes"] = str(total)
            rows.append(r)

    rows.sort(key=lambda r: int(r["_fastq_total_bytes"]) or 10**30)
    for r in rows[:top_n]:
        print(
            "\t".join(
                [
                    r.get("run_accession", ""),
                    r.get("_fastq_total_bytes", ""),
                    (r.get("fastq_ftp", "") or "").split(";")[0],
                ]
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

