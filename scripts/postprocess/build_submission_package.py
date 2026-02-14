#!/usr/bin/env python3
"""
Build a submission-ready package for the PRJDB36442 meta project.

Outputs a self-contained folder (and a zip) containing:
  - Figure boards: PDF (vector) + TIFF (raster) + meta.json
  - Audit inventories: _input_checksums.json + submission_manifest.json (+ sha256 file)
  - Governance docs: PLOT_STYLE_GUIDE.md, FIGURE_STYLE_BENCHMARK.md, FIGURE_PROVENANCE.tsv
  - Repro bundle: results/repro/* (hashes + env + report)

This script packages only the PRJDB36442 repository artifacts and excludes raw sequencing data and large databases.

Usage:
  python3 scripts/postprocess/build_submission_package.py --base-dir . --dpi 600
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FIGURE_STEMS = [
    "Figure1_Cohort_Profile",
    "Figure2_Module_Mechanisms",
    "Figure3_Pathway_and_Drivers",
    "Figure4_External_Validation",
    "Figure5_Mechanistic_Integration",
    "FigureS1_Audit_Traceability",
]


EXTRA_FILES = [
    "plots/publication/_input_checksums.json",
    "docs/AUDIT_TRAIL.md",
    "docs/PIPELINE_REPRO.md",
    "docs/REPRODUCIBILITY.md",
    "docs/PLOT_STYLE_GUIDE.md",
    "docs/FIGURE_STYLE_BENCHMARK.md",
    "docs/FIGURE_PROVENANCE.tsv",
    "docs/data/PRJDB36442.md",
    "docs/metadata/PRJDB36442_phenotypes.md",
    "results/repro/artifact_hashes.sha256",
    "results/repro/repro_env_snapshot.txt",
    "results/repro/repro_check_report_20260208.md",
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _render_pdf_to_tiff_pdftoppm(pdf_path: Path, tif_path: Path, dpi: int) -> None:
    if not _which("pdftoppm"):
        raise RuntimeError("pdftoppm not found")
    out_prefix = tif_path.with_suffix("")
    cmd = [
        "pdftoppm",
        "-tiff",
        "-singlefile",
        "-tiffcompression",
        "lzw",
        "-r",
        str(dpi),
        str(pdf_path),
        str(out_prefix),
    ]
    _run(cmd)
    produced = out_prefix.with_suffix(".tif")
    if not produced.exists():
        raise RuntimeError(f"pdftoppm did not produce expected file: {produced}")
    if produced.resolve() != tif_path.resolve():
        tif_path.parent.mkdir(parents=True, exist_ok=True)
        produced.replace(tif_path)


def _zip_dir(src_dir: Path, zip_path: Path) -> None:
    if not _which("zip"):
        raise RuntimeError("zip not found")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    cwd = os.getcwd()
    try:
        os.chdir(src_dir.parent)
        _run(["zip", "-r", str(zip_path.name), str(src_dir.name)])
        (src_dir.parent / zip_path.name).replace(zip_path)
    finally:
        os.chdir(cwd)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build submission package (meta-only).")
    p.add_argument("--base-dir", type=Path, default=Path("."))
    p.add_argument("--fig-dir", type=Path, default=Path("plots/publication"))
    p.add_argument("--out-root", type=Path, default=Path("plots/submission"))
    p.add_argument("--dpi", type=int, default=600)
    p.add_argument("--tag", type=str, default=None, help="Optional package tag (e.g., Medicine).")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    base_dir = args.base_dir.resolve()
    fig_dir = (base_dir / args.fig_dir).resolve()

    tag = args.tag or "submission"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = (base_dir / args.out_root / f"{tag}_{stamp}").resolve()

    out_fig_dir = out_dir / "figures"
    out_audit_dir = out_dir / "audit"
    out_docs_dir = out_dir / "docs"
    out_repro_dir = out_dir / "repro"

    out_dir.mkdir(parents=True, exist_ok=True)

    if not fig_dir.exists():
        raise FileNotFoundError(f"Figure directory not found: {fig_dir}")

    if not _which("pdftoppm"):
        raise RuntimeError("pdftoppm is required (Poppler). Install it and retry.")

    manifest: dict[str, Any] = {
        "project": "meta/PRJDB36442",
        "generated_utc": _now_utc(),
        "source_fig_dir": str(args.fig_dir),
        "dpi_tiff": int(args.dpi),
        "software": {
            "python": sys.version,
            "platform": platform.platform(),
            "pdftoppm": subprocess.check_output(["pdftoppm", "-v"], text=True, stderr=subprocess.STDOUT).splitlines()[0],
        },
        "figures": [],
        "included_files": [],
    }

    # ── Figures ───────────────────────────────────────────────────────────
    for stem in FIGURE_STEMS:
        pdf = fig_dir / f"{stem}.pdf"
        png = fig_dir / f"{stem}.png"
        meta = fig_dir / f"{stem}.meta.json"
        for pth in [pdf, png, meta]:
            if not pth.exists():
                raise FileNotFoundError(f"Missing expected figure artifact: {pth}")

        dest_pdf = out_fig_dir / f"{stem}.pdf"
        dest_meta = out_fig_dir / f"{stem}.meta.json"
        dest_tif = out_fig_dir / f"{stem}.tif"

        out_fig_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf, dest_pdf)
        shutil.copy2(meta, dest_meta)

        _render_pdf_to_tiff_pdftoppm(dest_pdf, dest_tif, dpi=args.dpi)

        manifest["figures"].append(
            {
                "stem": stem,
                "pdf": str(dest_pdf.relative_to(out_dir)),
                "tif": str(dest_tif.relative_to(out_dir)),
                "meta_json": str(dest_meta.relative_to(out_dir)),
                "sha256": {
                    "pdf": _sha256(dest_pdf),
                    "tif": _sha256(dest_tif),
                    "meta_json": _sha256(dest_meta),
                },
            }
        )

    # ── Extra audit/governance/repro docs ─────────────────────────────────
    for rel in EXTRA_FILES:
        src = base_dir / rel
        if not src.exists():
            raise FileNotFoundError(f"Missing required package file: {src}")
        if rel.startswith("docs/"):
            dst = out_docs_dir / Path(rel).name
        elif rel.startswith("results/repro/"):
            dst = out_repro_dir / Path(rel).name
        elif rel.startswith("plots/publication/"):
            dst = out_audit_dir / Path(rel).name
        else:
            dst = out_audit_dir / Path(rel).name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        manifest["included_files"].append(
            {"path": str(dst.relative_to(out_dir)), "sha256": _sha256(dst)}
        )

    # ── README for humans ────────────────────────────────────────────────
    readme = f"""# Submission Package (meta/PRJDB36442)

Generated (UTC): {manifest['generated_utc']}

## Contents
- `figures/`: submission figures
  - PDF = vector master (fonts embedded)
  - TIFF = raster export at {args.dpi} dpi (from PDF via pdftoppm)
  - `*.meta.json` = panel/inputs/parameters/software provenance
- `audit/`: audit inventories (incl. `_input_checksums.json`)
- `docs/`: figure governance docs (style guide / benchmark / provenance map)
- `repro/`: reproducibility bundle (artifact hashes + env snapshot + report)

## Notes
- `_input_checksums.json` lists SHA-256 checksums for the canonical input tables used by the figure generator.
"""
    _write_text(out_dir / "README_submission.md", readme)
    manifest["included_files"].append(
        {"path": "README_submission.md", "sha256": _sha256(out_dir / "README_submission.md")}
    )

    # ── Manifest ─────────────────────────────────────────────────────────
    manifest_path = out_dir / "submission_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    sha_path = out_dir / "submission_manifest.sha256"
    sha_lines = [f"{_sha256(p)}  {p.relative_to(out_dir)}" for p in sorted(out_dir.rglob("*")) if p.is_file()]
    sha_path.write_text("\n".join(sha_lines) + "\n", encoding="utf-8")

    # ── Zip ──────────────────────────────────────────────────────────────
    zip_path = out_dir.with_suffix(".zip")
    _zip_dir(out_dir, zip_path)

    print(f"[ok] submission folder: {out_dir}")
    print(f"[ok] submission zip:    {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
