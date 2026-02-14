#!/usr/bin/env python3
"""
Stream a remote .fastq.gz over HTTPS and write the first N reads to a local .fastq.gz.

Why: many public runs are multi-GB; for pilot profiling we only need a subsample.
This avoids downloading full files.
"""

from __future__ import annotations

import argparse
import gzip
import io
import sys
import urllib.request
from pathlib import Path


def _iter_fastq_lines_from_gz_url(url: str, timeout: int = 120):
    req = urllib.request.Request(url, headers={"User-Agent": "codex-meta/fastq-head"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        with gzip.GzipFile(fileobj=resp) as gz:
            # Wrap into text mode for line iteration
            text = io.TextIOWrapper(gz, encoding="utf-8", errors="replace", newline="\n")
            for line in text:
                yield line


def extract(url: str, out_path: Path, n_reads: int, timeout: int = 120) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_lines = n_reads * 4
    wrote = 0
    with gzip.open(out_path, "wt", encoding="utf-8", newline="\n") as out_f:
        for line in _iter_fastq_lines_from_gz_url(url, timeout=timeout):
            out_f.write(line)
            wrote += 1
            if wrote >= n_lines:
                break
    if wrote < n_lines:
        raise RuntimeError(f"EOF before {n_reads} reads: wrote {wrote} lines")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--reads", type=int, required=True, help="number of reads to keep")
    p.add_argument("--timeout", type=int, default=120)
    args = p.parse_args(argv)

    extract(args.url, Path(args.out), args.reads, timeout=args.timeout)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

