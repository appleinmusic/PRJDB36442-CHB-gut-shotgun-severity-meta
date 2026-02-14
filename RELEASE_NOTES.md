# Release Notes: PRJDB36442 CHB gut shotgun severity (M vs S)

This repository provides a reproducible, audit-friendly workflow and a submission-ready figure set for a public
shotgun metagenomics cohort (`PRJDB36442`, n=20 runs) stratified by NGDC-provided histology severity labels
(`group M` vs `group S`).

## What this repo contains

- **Scripts** (`scripts/`): feasibility discovery, cloud batch workflows, postprocessing, and figure generation.
- **Analysis-ready tables** (`results/`): small/medium artifacts needed to reproduce figures.
- **Final publication figures** (`plots/publication/`): multi-panel boards exported as:
  - `Figure*.pdf` (vector)
  - `Figure*.png` (300 dpi)
  - `Figure*.meta.json` (provenance: inputs, parameters, software versions, input checksums)

## What is intentionally not included

- Raw FASTQ files
- MetaPhlAn/HUMAnN reference databases
- Large cloud intermediates under `results/cloud/`
- Source Excel downloads (reproducible via scripts; see below)

## Data provenance (public sources)

- **Primary cohort**: ENA study `PRJDB36442`
- **Severity labels**: NGDC GSA export for `CRA023641` (contains `group M/S` in BioSample descriptions)
- **External directional support**: HBV-LC vs HC Table 1 from a PMC OA package (derived TSVs are included under `results/external/`)

See:
- `docs/AUDIT_TRAIL.md`
- `docs/metadata/PRJDB36442_phenotypes.md`
- `results/external/Frontiers_HBVLC_sources.md`

## Reproduce the submission figures (from tracked tables)

```bash
python3 -m pip install -r requirements.txt
python3 scripts/postprocess/make_figure_boards_v2.py --base-dir .
```

Expected outputs:
- `plots/publication/Figure1_Cohort_Profile.(pdf|png|meta.json)`
- `plots/publication/Figure2_Module_Mechanisms.(pdf|png|meta.json)`
- `plots/publication/Figure3_Pathway_and_Drivers.(pdf|png|meta.json)`
- `plots/publication/Figure4_External_Validation.(pdf|png|meta.json)`
- `plots/publication/Figure5_Mechanistic_Integration.(pdf|png|meta.json)`
- `plots/publication/FigureS1_Audit_Traceability.(pdf|png|meta.json)`
- `plots/publication/_input_checksums.json`

## Rebuild the reproducibility bundle (checksums + environment)

```bash
python3 scripts/repro/rebuild_repro_bundle.py --base-dir .
```

Writes/updates:
- `results/repro/artifact_hashes.sha256`
- `results/repro/repro_env_snapshot.txt`
- `results/repro/script_syntax_check.txt`
- `results/repro/repro_data_sanity.txt`

## Optional: reproduce source Excel downloads (not committed)

NGDC export (phenotype labels):
```bash
bash scripts/feasibility/download_ngdc_cra023641_xlsx.sh CRA023641 data/metadata/ngdc/CRA023641.xlsx
```

PMC OA package extraction (external Table 1 Excel):
```bash
bash scripts/external/fetch_frontiers_hbvlc_table1.sh
```

## Optional: journal upload bundle (TIFF exports)

```bash
python3 scripts/postprocess/build_submission_package.py --base-dir . --dpi 600 --tag Medicine
```

This builds a local bundle under `plots/submission/` (ignored by git). If needed, upload the generated `.zip` as a
GitHub Release asset.

