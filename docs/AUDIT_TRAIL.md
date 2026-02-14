# Audit trail

This project is designed so an external reviewer can reproduce results from public sources.

## Public sources

- ENA (EBI) Portal API:
  - Study/run discovery: `scripts/feasibility/ena_scan_hbv_gut.py`
  - Per-FASTQ manifest with sizes and MD5: `scripts/feasibility/make_fastq_manifest.py`
- EBI BioSamples:
  - Sample characteristics snapshot (as published): `scripts/feasibility/fetch_biosamples_tsv.py`
- NGDC (CNCB):
  - BioProject: `PRJCA037061`
  - GSA: `CRA023641`
  - Exported metadata (Sample/Experiment/Run tables): downloadable via
    `bash scripts/feasibility/download_ngdc_cra023641_xlsx.sh CRA023641 data/metadata/ngdc/CRA023641.xlsx`

## Derived, reproducible tables (small)

- ENA studies/runs: `results/feasibility/ena_hbv_gut_studies.tsv`, `results/feasibility/ena_hbv_gut_runs.tsv`
- ENA FASTQ manifest: `results/feasibility/PRJDB36442_fastq_manifest.tsv`
- NGDC group labels: `results/feasibility/PRJCA037061_sample_groups.tsv`
- ENA run ↔ group join: `results/feasibility/PRJDB36442_run_groups.tsv`

## Cloud computation logs

All long-running compute should write per-run logs and a progress table. The recommended batch script is:

- `scripts/cloud/gcp_prjdb36442_metaphlan_batch.sh`

Avoid committing large intermediate files; `.gitignore` excludes FASTQs, DBs, and bowtie2 intermediates.
