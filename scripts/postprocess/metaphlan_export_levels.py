#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
from pathlib import Path


def _open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def _open_out(path: Path, compress: bool):
    path.parent.mkdir(parents=True, exist_ok=True)
    if compress:
        return gzip.open(path.with_suffix(path.suffix + ".gz"), "wt", encoding="utf-8")
    return path.open("w", encoding="utf-8", newline="")


def _is_level(clade: str, level: str) -> bool:
    if level == "species":
        return "|s__" in clade and "|t__" not in clade
    if level == "genus":
        return "|g__" in clade and "|s__" not in clade
    if level == "family":
        return "|f__" in clade and "|g__" not in clade
    if level == "order":
        return "|o__" in clade and "|f__" not in clade
    if level == "class":
        return "|c__" in clade and "|o__" not in clade
    if level == "phylum":
        return "|p__" in clade and "|c__" not in clade
    if level == "kingdom":
        return "|k__" in clade and "|p__" not in clade
    raise ValueError(f"Unknown level: {level}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Export selected taxonomic levels from a merged MetaPhlAn table.")
    ap.add_argument("--in", dest="in_path", type=Path, required=True, help="Input merged MetaPhlAn table (.tsv or .tsv.gz).")
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("results/processed/metaphlan"),
        help="Output directory (default: results/processed/metaphlan).",
    )
    ap.add_argument(
        "--levels",
        default="species,genus,phylum",
        help="Comma-separated levels: kingdom,phylum,class,order,family,genus,species (default: species,genus,phylum).",
    )
    ap.add_argument("--compress", action="store_true", help="Write gzip-compressed outputs.")
    args = ap.parse_args()

    levels = [x.strip().lower() for x in args.levels.split(",") if x.strip()]
    for lvl in levels:
        _is_level("k__Bacteria|p__X|c__Y|o__Z|f__A|g__B|s__C", lvl)  # validate

    with _open_text(args.in_path) as fin:
        header = ""
        for line in fin:
            if not line.startswith("#"):
                header = line.rstrip("\n")
                break
        if not header:
            raise SystemExit("Could not find header row (non-# line).")

        cols = header.split("\t")
        if not cols or cols[0] != "clade_name":
            # Some merge scripts use '#clade_name' but we already removed leading '#'
            if cols and cols[0].lstrip("#") == "clade_name":
                cols[0] = "clade_name"
            else:
                raise SystemExit(f"Unexpected first column: {cols[0] if cols else ''}")

        out_handles: dict[str, object] = {}
        try:
            for lvl in levels:
                out_path = args.out_dir / f"metaphlan_{lvl}.tsv"
                out = _open_out(out_path, compress=args.compress)
                out.write("\t".join(cols) + "\n")
                out_handles[lvl] = out

            for line in fin:
                if not line or line.startswith("#"):
                    continue
                line = line.rstrip("\n")
                parts = line.split("\t")
                if not parts:
                    continue
                clade = parts[0]
                for lvl in levels:
                    if _is_level(clade, lvl):
                        out_handles[lvl].write(line + "\n")
        finally:
            for out in out_handles.values():
                out.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

