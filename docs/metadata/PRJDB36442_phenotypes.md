# PRJDB36442 phenotypes (audit trail)

## What we need

For the intended “histology damage + mechanism modules” main story, we need per-sample phenotypes and key covariates (at minimum: histology group; ideally: grading/staging scores + labs + demographics).

## What is publicly available now (good news)

Although ENA/EBI BioSamples metadata do **not** contain histology/fibrosis fields, the corresponding **NGDC (CNCB) BioSample/GSA records do provide a per-sample histology damage group label**:

- `group M` vs `group S` is present in:
  - NGDC BioSample pages, e.g. `SAMC4845367` shows `group M`, `SAMC4845375` shows `group S`
  - NGDC GSA export Excel `CRA023641.xlsx` (sheet `Sample`, column **Public description**)

This is sufficient to reproduce the primary patient stratification used in the paper (binary M vs S), and can be audited from public URLs.

## Source records (public)

- NGDC BioProject: `https://ngdc.cncb.ac.cn/bioproject/browse/PRJCA037061`
- NGDC GSA study: `https://ngdc.cncb.ac.cn/gsa/browse/CRA023641`
- Example NGDC BioSamples:
  - `https://ngdc.cncb.ac.cn/biosample/browse/SAMC4845367` (BF2, `group M`)
  - `https://ngdc.cncb.ac.cn/biosample/browse/SAMC4845375` (BF28, `group S`)

Accessed: 2026-02-04.

## Files in this repo

The raw NGDC Excel export is **not** committed to this repository (downloadable on demand).
To fetch it locally:

- `bash scripts/feasibility/download_ngdc_cra023641_xlsx.sh CRA023641 data/metadata/ngdc/CRA023641.xlsx`

Derived tables (reproducible from the Excel):

- `results/feasibility/PRJCA037061_sample_groups.tsv` (BF* + SAMC + group)
- `results/feasibility/PRJDB36442_run_groups.tsv` (DRR run + BF* + SAMC + group)

Scripts:

- `scripts/feasibility/extract_ngdc_cra023641_groups.py`
- `scripts/feasibility/join_prjdb36442_runs_with_groups.py`

## What is still missing (limits of public metadata)

To elevate the story beyond a binary group comparison and survive reviewer scrutiny, we still need (ideally per sample):

- Histology **grading** and **staging** numeric scores (e.g., Scheuer/Metavir/Ishak) rather than only M/S
- Demographics: age, sex, BMI
- HBV clinical markers: HBeAg/HBsAg, HBV DNA, antiviral treatment status (paper says treatment-naïve but needs per-sample confirmation)
- Liver biochemistry: ALT/AST/ALP/GGT, platelets, etc.
- Any exclusion criteria and sampling timing relative to biopsy

These may be in supplemental tables (publisher site) or require author-provided metadata.
