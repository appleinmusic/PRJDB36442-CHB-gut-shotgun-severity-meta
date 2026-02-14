#!/usr/bin/env bash
set -euo pipefail

# End-to-end local metadata build for PRJDB36442:
# - ENA studies + runs
# - ENA fastq manifest (URLs, sizes, md5)
# - NGDC CRA023641 export (xlsx) + group M/S extraction
# - EBI BioSamples flatten (audit)
# - Join run ↔ group labels

study="${1:-PRJDB36442}"

python3 scripts/feasibility/ena_scan_hbv_gut.py
python3 scripts/feasibility/make_fastq_manifest.py results/feasibility/ena_hbv_gut_runs.tsv "${study}"

bash scripts/feasibility/download_ngdc_cra023641_xlsx.sh CRA023641 data/metadata/ngdc/CRA023641.xlsx
python3 scripts/feasibility/extract_ngdc_cra023641_groups.py

python3 scripts/feasibility/fetch_biosamples_tsv.py results/feasibility/ena_hbv_gut_runs.tsv "${study}"
python3 scripts/feasibility/join_prjdb36442_runs_with_groups.py

echo "Done."
