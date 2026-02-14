# Reproducibility (PRJDB36442 CHB gut shotgun)

This repository is designed so a reviewer can:

1) trace all key inputs to public sources,
2) regenerate the submission-ready figure boards from the tracked processed tables, and
3) verify integrity via checksums.

## What is (and is not) included

- Included:
  - small, analysis-ready tables under `results/`
  - final figure boards under `plots/publication/`
  - scripts under `scripts/`
- Not included:
  - raw FASTQ files
  - MetaPhlAn/HUMAnN databases
  - large per-run intermediate files under `results/cloud/`

## Quick reproduction (figures from tracked tables)

```bash
python3 -m pip install -r requirements.txt
python3 scripts/postprocess/make_figure_boards_v2.py --base-dir .
```

Outputs are written to `plots/publication/` as:
- `Figure*.pdf` (vector)
- `Figure*.png` (300 dpi)
- `Figure*.meta.json` (provenance)

## Audit: input checksums for figures

The figure generator also writes:

- `plots/publication/_input_checksums.json`

This is a SHA-256 inventory of the canonical input tables used by the figure boards.

## Repro bundle (relative-path checksums + environment)

```bash
python3 scripts/repro/rebuild_repro_bundle.py --base-dir .
```

This writes/updates:
- `results/repro/artifact_hashes.sha256`
- `results/repro/repro_env_snapshot.txt`
- `results/repro/script_syntax_check.txt`
- `results/repro/repro_data_sanity.txt`

## Cold-start regeneration from public sequencing (optional)

End-to-end regeneration from public FASTQs requires cloud compute and large reference databases.
See `docs/PIPELINE_REPRO.md` for the GCP workflow.

