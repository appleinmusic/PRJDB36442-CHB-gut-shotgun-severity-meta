# Reproducibility Check Report (updated 2026-02-14)

## Scope
This report verifies reproducibility readiness for the completed PRJDB36442 workflow **without re-running full cloud computation**.

## What was verified
1. Presence of required inputs, scripts, processed outputs, and external validation files.
2. SHA256 hashes for key artifacts (`artifact_hashes.sha256`, stored with **relative paths**).
3. Shell syntax checks for critical cloud scripts (`script_syntax_check.txt`).
4. Environment snapshot (`repro_env_snapshot.txt`).
5. Basic result-table sanity checks (`repro_data_sanity.txt`).

## Current reproducibility level
- **Level A (artifact reproducibility): PASS**
  - All key artifacts present and hashed.
  - Script syntax checks passed.
  - Analysis tables include both raw p-values and FDR q-values.

- **Level B (cold-start computational reproducibility): NOT RUN**
  - Full cloud rerun from raw FASTQ to final tables was not repeated in this check.

## Why full cloud rerun was not required now
- The original cloud run is complete with 20/20 successful samples and audit logs.
- Full rerun is time/cost intensive and usually reserved for pre-submission final lock or reviewer request.

## If Level B is required later
Run the end-to-end cloud workflow from:
- `scripts/cloud/gcp_create_instance.sh`
- `scripts/cloud/gcp_bootstrap_hbv_gut.sh`
- `scripts/cloud/gcp_bootstrap_humann3.sh`
- `scripts/cloud/gcp_download_humann_dbs.sh`
- `scripts/cloud/gcp_patch_humann_metaphlan_compat.sh`
- `scripts/cloud/gcp_submit_prjdb36442_humann_batch.sh`
- `scripts/cloud/gcp_fetch_prjdb36442_humann_results.sh`

and compare final hashes against `artifact_hashes.sha256` where applicable.

## Files generated in this check
- `results/repro/artifact_hashes.sha256`
- `results/repro/script_syntax_check.txt`
- `results/repro/repro_env_snapshot.txt`
- `results/repro/repro_data_sanity.txt`
- `results/repro/repro_check_report_20260208.md`

## How to rebuild the bundle
From repo root:

- `python3 scripts/repro/rebuild_repro_bundle.py --base-dir .`
