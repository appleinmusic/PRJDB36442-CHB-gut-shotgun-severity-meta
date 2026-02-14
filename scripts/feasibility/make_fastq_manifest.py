#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def _split_semicolon(value: str) -> list[str]:
    value = (value or "").strip()
    if not value:
        return []
    return [part.strip() for part in value.split(";") if part.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a per-fastq download manifest from ENA runs TSV.")
    ap.add_argument("runs_tsv", type=Path, help="Input ENA runs TSV (with fastq_ftp/fastq_bytes).")
    ap.add_argument("study_accession", help="Study accession to filter (e.g. PRJDB36442).")
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output TSV path (default: results/feasibility/<study>_fastq_manifest.tsv).",
    )
    args = ap.parse_args()

    lines = args.runs_tsv.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    idx = {name: i for i, name in enumerate(header)}

    required = ["study_accession", "run_accession", "fastq_ftp", "fastq_bytes", "first_public"]
    missing = [c for c in required if c not in idx]
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")
    has_md5 = "fastq_md5" in idx

    out_path = args.out or Path("results/feasibility") / f"{args.study_accession}_fastq_manifest.tsv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    out_header = ["study_accession", "run_accession", "mate", "url", "size_bytes"]
    if has_md5:
        out_header.append("md5")
    out_header.append("first_public")
    out_lines = ["\t".join(out_header)]

    for row in lines[1:]:
        cols = row.split("\t")
        if cols[idx["study_accession"]] != args.study_accession:
            continue

        run = cols[idx["run_accession"]]
        fastq_ftp = _split_semicolon(cols[idx["fastq_ftp"]])
        fastq_bytes = _split_semicolon(cols[idx["fastq_bytes"]])
        fastq_md5 = _split_semicolon(cols[idx["fastq_md5"]]) if has_md5 else []
        first_public = cols[idx["first_public"]]

        for i, path in enumerate(fastq_ftp, start=1):
            url = path
            if url.startswith("ftp."):
                url = "https://" + url
            elif url.startswith("sra-download."):
                url = "https://" + url
            elif not (url.startswith("http://") or url.startswith("https://")):
                url = "https://" + url.lstrip("/")

            size = fastq_bytes[i - 1] if i - 1 < len(fastq_bytes) else ""
            md5 = fastq_md5[i - 1] if i - 1 < len(fastq_md5) else ""
            row = [args.study_accession, run, str(i), url, size]
            if has_md5:
                row.append(md5)
            row.append(first_public)
            out_lines.append("\t".join(row))

    out_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
