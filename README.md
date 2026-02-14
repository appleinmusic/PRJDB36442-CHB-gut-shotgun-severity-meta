# HBV gut shotgun (public, reproducible)

This repository is a reproducible, audit-friendly workflow for:

1) discovering HBV gut microbiome datasets in ENA,
2) extracting public phenotype labels where available (e.g., NGDC `group M/S`),
3) running shotgun metagenomics taxonomic profiling (MetaPhlAn) on a cloud VM,
4) producing outputs that a reviewer can re-run from public links + scripts.

Scope note: this repo **does not** contain identifiable human data.

Terminology note: the repository name includes “meta” as a project label (shotgun metagenomics workflow), **not** a
systematic-review meta-analysis.

## Current primary dataset

- ENA study: `PRJDB36442` (20 runs)
- NGDC BioProject: `PRJCA037061`
- NGDC GSA: `CRA023641`

Public phenotype currently recoverable from NGDC: per-sample `group M` vs `group S` (see `docs/metadata/PRJDB36442_phenotypes.md`).

## Quickstart (local)

Minimal Python dependency (for NGDC Excel parsing):

```bash
python3 -m pip install -r requirements.txt
```

Run feasibility + metadata extraction:

```bash
python3 scripts/feasibility/ena_scan_hbv_gut.py
python3 scripts/feasibility/make_fastq_manifest.py results/feasibility/ena_hbv_gut_runs.tsv PRJDB36442
bash scripts/feasibility/download_ngdc_cra023641_xlsx.sh CRA023641 data/metadata/ngdc/CRA023641.xlsx
python3 scripts/feasibility/extract_ngdc_cra023641_groups.py
python3 scripts/feasibility/fetch_biosamples_tsv.py results/feasibility/ena_hbv_gut_runs.tsv PRJDB36442
python3 scripts/feasibility/join_prjdb36442_runs_with_groups.py
```

## Cloud execution (GCP)

Cloud is recommended because MetaPhlAn databases are large.

Scripts:

- Create VM: `scripts/cloud/gcp_create_instance.sh`
- Bootstrap (Miniforge + MetaPhlAn): `scripts/cloud/gcp_bootstrap_hbv_gut.sh`
- Download MetaPhlAn DB: `scripts/cloud/gcp_download_metaphlan_db.sh` + `scripts/cloud/gcp_download_metaphlan_aux.sh`
- Batch MetaPhlAn for PRJDB36442: `scripts/cloud/gcp_prjdb36442_metaphlan_batch.sh`

Notes:

- Do **not** commit your live IP/project info. Use `docs/cloud/GCP_INSTANCE.local.md` for private notes.
- See `docs/PIPELINE_REPRO.md` for step-by-step commands.

## Documentation

- Audit trail for phenotypes: `docs/metadata/PRJDB36442_phenotypes.md`
- Overall audit trail: `docs/AUDIT_TRAIL.md`
- Data overview: `docs/data/PRJDB36442.md`
- Analysis framing: `docs/ANALYSIS_STRATEGY.md`
- Reproducibility guide: `docs/REPRODUCIBILITY.md`

## Publication figures

Generate the submission-ready figure boards (PDF + PNG + `meta.json` for audit):

```bash
python3 scripts/postprocess/make_figure_boards_v2.py --base-dir .
```

Optional (journal upload bundle with TIFF exports at 600 dpi):

```bash
python3 scripts/postprocess/build_submission_package.py --base-dir . --dpi 600 --tag Medicine
```

## External validation source (optional)

This repo stores the derived, analysis-ready TSVs under `results/external/`. If you need to reproduce the original
Table 1 Excel file from the PMC OA package, use:

```bash
bash scripts/external/fetch_frontiers_hbvlc_table1.sh
```
