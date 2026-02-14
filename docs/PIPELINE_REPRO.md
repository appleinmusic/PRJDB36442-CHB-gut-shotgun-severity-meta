# Repro pipeline (public CHB gut shotgun)

This repo tracks (1) feasibility discovery, (2) download manifests, (3) cloud execution, and (4) small, audit-friendly outputs suitable for GitHub.

## Prereq (local)

If `gcloud` fails on macOS due to a broken embedded Python, set:

```bash
export CLOUDSDK_PYTHON=/usr/bin/python3
```

(Cloud scripts under `scripts/cloud/` also set this automatically.)

## 1) Feasibility scan (ENA + NGDC)

```bash
python3 scripts/feasibility/ena_scan_hbv_gut.py
python3 scripts/feasibility/make_fastq_manifest.py results/feasibility/ena_hbv_gut_runs.tsv PRJDB36442
bash scripts/feasibility/download_ngdc_cra023641_xlsx.sh CRA023641 data/metadata/ngdc/CRA023641.xlsx
python3 scripts/feasibility/extract_ngdc_cra023641_groups.py
python3 scripts/feasibility/fetch_biosamples_tsv.py results/feasibility/ena_hbv_gut_runs.tsv PRJDB36442
python3 scripts/feasibility/join_prjdb36442_runs_with_groups.py
```

Key outputs:

- `results/feasibility/PRJDB36442_fastq_manifest.tsv` (URL/size/md5)
- `data/metadata/ngdc/CRA023641.xlsx` (public per-sample `group M/S`, downloaded locally; not committed)
- `results/feasibility/PRJDB36442_run_groups.tsv` (run↔group join)

## 2) GCP compute (recommended)

Create VM:

```bash
bash scripts/cloud/gcp_create_instance.sh
```

Bootstrap tools + conda + MetaPhlAn:

```bash
gcloud compute scp --zone us-west1-c scripts/cloud/gcp_bootstrap_hbv_gut.sh hbv-gut-shotgun-1:~/gcp_bootstrap_hbv_gut.sh
gcloud compute ssh hbv-gut-shotgun-1 --zone us-west1-c --command 'bash ~/gcp_bootstrap_hbv_gut.sh'
```

Download MetaPhlAn DB:

```bash
gcloud compute scp --zone us-west1-c scripts/cloud/gcp_download_metaphlan_db.sh hbv-gut-shotgun-1:~/gcp_download_metaphlan_db.sh
gcloud compute scp --zone us-west1-c scripts/cloud/gcp_download_metaphlan_aux.sh hbv-gut-shotgun-1:~/gcp_download_metaphlan_aux.sh
gcloud compute ssh hbv-gut-shotgun-1 --zone us-west1-c --command 'bash ~/gcp_download_metaphlan_db.sh ~/metaphlan_db'
gcloud compute ssh hbv-gut-shotgun-1 --zone us-west1-c --command 'bash ~/gcp_download_metaphlan_aux.sh ~/metaphlan_db'
```

## 3) MetaPhlAn batch (PRJDB36442)

Submit + run in tmux:

```bash
bash scripts/cloud/gcp_submit_prjdb36442_batch.sh
```

Check status:

```bash
bash scripts/cloud/gcp_status_prjdb36442.sh
```

Fetch results + audit bundle (merged table, per-run logs, remote env snapshot):

```bash
FETCH_PER_RUN=1 FETCH_REMOTE_AUDIT=1 bash scripts/cloud/gcp_fetch_prjdb36442_results.sh
```

Local postprocess (small tables only):

```bash
python3 scripts/postprocess/metaphlan_qc_from_outputs.py \
  --in-dir results/cloud/PRJDB36442/per_run \
  --out results/processed/metaphlan/PRJDB36442_metaphlan_qc.tsv

python3 scripts/postprocess/metaphlan_export_levels.py \
  --in results/cloud/PRJDB36442/merged_metaphlan.tsv.gz \
  --out-dir results/processed/metaphlan/PRJDB36442 \
  --levels species,genus,phylum \
  --compress

python3 scripts/postprocess/make_prjdb36442_sample_sheet.py
```

## 4) HUMAnN3 functional profiling (optional; cloud-only)

This stage is for mechanism-oriented results (pathways/gene families). Databases can be large; we start with a **nucleotide-only** setup (ChocoPhlAn) to keep downloads smaller.

Bootstrap HUMAnN env:

```bash
gcloud compute scp --zone us-west1-c scripts/cloud/gcp_bootstrap_humann3.sh hbv-gut-shotgun-1:~/gcp_bootstrap_humann3.sh
gcloud compute ssh hbv-gut-shotgun-1 --zone us-west1-c --command 'bash ~/gcp_bootstrap_humann3.sh'
```

Download HUMAnN DBs (default: ChocoPhlAn only):

```bash
gcloud compute scp --zone us-west1-c scripts/cloud/gcp_download_humann_dbs.sh hbv-gut-shotgun-1:~/gcp_download_humann_dbs.sh
gcloud compute ssh hbv-gut-shotgun-1 --zone us-west1-c --command 'bash ~/gcp_download_humann_dbs.sh'
```

Patch HUMAnN↔MetaPhlAn CLI compatibility (required for `mpa_vJan25` MetaPhlAn DB on this VM):

```bash
bash scripts/cloud/gcp_patch_humann_metaphlan_compat.sh
```

Run HUMAnN batch (nucleotide-only, paired-end concatenation):

```bash
bash scripts/cloud/gcp_submit_prjdb36442_humann_batch.sh
```

Notes:
- Failed runs create `*.FAIL` markers and are skipped on restart by default (`SKIP_FAILED=1`). To force re-running failed samples, set `SKIP_FAILED=0`.

Check status:

```bash
bash scripts/cloud/gcp_status_prjdb36442_humann.sh
```

## 5) Publication figure boards (local)

After the required anchor tables exist under `results/`, generate the submission-ready multi-panel figure boards:

```bash
python3 scripts/postprocess/make_figure_boards_v2.py --base-dir .
```

Outputs:

- `plots/publication/Figure1_Cohort_Profile.(pdf|png|meta.json)`
- `plots/publication/Figure2_Module_Mechanisms.(pdf|png|meta.json)`
- `plots/publication/Figure3_Pathway_and_Drivers.(pdf|png|meta.json)`
- `plots/publication/Figure4_External_Validation.(pdf|png|meta.json)`
- `plots/publication/Figure5_Mechanistic_Integration.(pdf|png|meta.json)`
- `plots/publication/FigureS1_Audit_Traceability.(pdf|png|meta.json)`

## 6) Submission package (figures + audit bundle)

Build a journal-ready bundle containing PDF masters, TIFF exports, and audit/governance documents:

```bash
python3 scripts/postprocess/build_submission_package.py --base-dir . --dpi 600 --tag Medicine
```
