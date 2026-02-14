#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Write the first N reads from a local FASTQ(.gz) to FASTQ.gz.")
    ap.add_argument("--in", dest="in_path", type=Path, required=True, help="Input FASTQ or FASTQ.gz path.")
    ap.add_argument("--out", dest="out_path", type=Path, required=True, help="Output FASTQ.gz path.")
    ap.add_argument("--reads", type=int, default=200_000, help="Number of reads to copy (default: 200000).")
    args = ap.parse_args()

    in_path: Path = args.in_path
    out_path: Path = args.out_path
    n_lines = args.reads * 4

    out_path.parent.mkdir(parents=True, exist_ok=True)

    def _open_in(p: Path):
        if p.suffix == ".gz":
            return gzip.open(p, "rt", encoding="utf-8", errors="replace")
        return p.open("r", encoding="utf-8", errors="replace")

    with _open_in(in_path) as fin, gzip.open(out_path, "wt", encoding="utf-8") as fout:
        for i, line in enumerate(fin, start=1):
            if i > n_lines:
                break
            fout.write(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

