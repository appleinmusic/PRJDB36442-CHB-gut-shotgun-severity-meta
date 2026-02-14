#!/usr/bin/env python3
"""
Rebuild reproducibility bundle (meta/PRJDB36442).

Writes:
  - results/repro/artifact_hashes.sha256   (relative paths)
  - results/repro/repro_env_snapshot.txt
  - results/repro/script_syntax_check.txt (bash -n on cloud scripts)
  - results/repro/repro_data_sanity.txt   (lightweight table sanity)
"""

from __future__ import annotations

import argparse
import hashlib
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HASH_GLOBS = [
    "results/feasibility/*.tsv",
    "results/processed/analysis/PRJDB36442/*.tsv",
    "results/processed/metaphlan/PRJDB36442/*.tsv.gz",
    "results/processed/PRJDB36442_humann/*.tsv",
    "results/processed/PRJDB36442_humann/*.tsv.gz",
    "results/external/*.tsv",
    "results/external/*.md",
]


BASH_SCRIPTS = [
    "scripts/cloud/gcp_patch_humann_metaphlan_compat.sh",
    "scripts/cloud/gcp_prjdb36442_humann_batch.sh",
    "scripts/cloud/gcp_submit_prjdb36442_humann_batch.sh",
    "scripts/cloud/gcp_status_prjdb36442_humann.sh",
    "scripts/cloud/gcp_fetch_prjdb36442_humann_results.sh",
    "scripts/cloud/gcp_stop_instance.sh",
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Rebuild results/repro bundle (relative paths).")
    p.add_argument("--base-dir", type=Path, default=Path("."))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    base = args.base_dir.resolve()
    out_dir = base / "results/repro"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── artifact hashes ──────────────────────────────────────────────────
    files: list[Path] = []
    for pattern in HASH_GLOBS:
        files.extend(sorted(base.glob(pattern)))
    files = [p for p in files if p.is_file()]

    lines = []
    for p in sorted(set(files)):
        rel = p.relative_to(base)
        lines.append(f"{_sha256(p)}  {rel}")
    (out_dir / "artifact_hashes.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ── env snapshot ─────────────────────────────────────────────────────
    pip = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True)
    pip_freeze = pip.stdout.strip()
    env_text = "\n".join(
        [
            f"timestamp_utc={_utc_now()}",
            f"python={sys.version.splitlines()[0]}",
            f"platform={platform.platform()}",
            "",
            "[pip_freeze]",
            pip_freeze,
            "",
        ]
    )
    (out_dir / "repro_env_snapshot.txt").write_text(env_text, encoding="utf-8")

    # ── bash syntax checks ───────────────────────────────────────────────
    bash_lines = []
    for rel in BASH_SCRIPTS:
        p = base / rel
        if not p.exists():
            bash_lines.append(f"MISSING  {rel}")
            continue
        proc = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
        status = "OK" if proc.returncode == 0 else "FAIL"
        bash_lines.append(f"{status}  {rel}")
        if proc.returncode != 0 and proc.stderr.strip():
            bash_lines.append(proc.stderr.rstrip())
    (out_dir / "script_syntax_check.txt").write_text("\n".join(bash_lines) + "\n", encoding="utf-8")

    # ── lightweight data sanity ──────────────────────────────────────────
    sanity = []
    key_tables = [
        "results/processed/PRJDB36442_humann/pathway_M_vs_S_stats.tsv",
        "results/processed/PRJDB36442_humann/module_M_vs_S_stats_conservative.tsv",
        "results/processed/PRJDB36442_humann/module_M_vs_S_stats_expanded.tsv",
    ]
    import pandas as pd  # local import (repo requirement)

    for rel in key_tables:
        p = base / rel
        if not p.exists():
            sanity.append(f"MISSING {rel}")
            continue
        df = pd.read_csv(p, sep="\t")
        sanity.append(f"{Path(rel).name}:rows={len(df)},cols={list(df.columns)}")
    (out_dir / "repro_data_sanity.txt").write_text("\n".join(sanity) + "\n", encoding="utf-8")

    print("[ok] wrote results/repro bundle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
