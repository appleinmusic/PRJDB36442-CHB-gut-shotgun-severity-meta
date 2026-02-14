#!/usr/bin/env bash
set -euo pipefail

# Work around local gcloud Python issues on macOS (CLOUDSDK_PYTHON may point to a broken venv).
: "${CLOUDSDK_PYTHON:=/usr/bin/python3}"
export CLOUDSDK_PYTHON

# Submit PRJDB36442 MetaPhlAn batch job to a running GCP VM.
#
# Required local files:
# - results/feasibility/PRJDB36442_fastq_manifest.tsv
# - scripts/cloud/gcp_prjdb36442_metaphlan_batch.sh
#
# VM prerequisites:
# - MetaPhlAn + DB installed (see scripts/cloud/gcp_bootstrap_hbv_gut.sh and gcp_download_metaphlan_*.sh)

INSTANCE="${INSTANCE:-hbv-gut-shotgun-1}"
ZONE="${ZONE:-us-west1-c}"
MANIFEST_LOCAL="${MANIFEST_LOCAL:-results/feasibility/PRJDB36442_fastq_manifest.tsv}"
SESSION="${SESSION:-prjdb36442-metaphlan}"

if [[ ! -f "${MANIFEST_LOCAL}" ]]; then
  echo "Missing manifest: ${MANIFEST_LOCAL}" >&2
  echo "Generate it with:" >&2
  echo "  python3 scripts/feasibility/ena_scan_hbv_gut.py" >&2
  echo "  python3 scripts/feasibility/make_fastq_manifest.py results/feasibility/ena_hbv_gut_runs.tsv PRJDB36442" >&2
  exit 2
fi

chmod +x scripts/cloud/gcp_prjdb36442_metaphlan_batch.sh
gcloud compute scp --zone "${ZONE}" "${MANIFEST_LOCAL}" "${INSTANCE}":~/PRJDB36442_fastq_manifest.tsv
gcloud compute scp --zone "${ZONE}" scripts/cloud/gcp_prjdb36442_metaphlan_batch.sh "${INSTANCE}":~/gcp_prjdb36442_metaphlan_batch.sh

gcloud compute ssh "${INSTANCE}" --zone "${ZONE}" --command "bash -lc 'set -euo pipefail
chmod +x ~/gcp_prjdb36442_metaphlan_batch.sh
mkdir -p ~/hbv_gut/results/metaphlan
if tmux has-session -t ${SESSION} 2>/dev/null; then
  echo \"tmux session exists: ${SESSION}\"
else
  tmux new-session -d -s ${SESSION} \"DB_DIR=~/metaphlan_db NPROC=16 KEEP_FASTQ=0 KEEP_BOWTIE2=0 VERIFY_MD5=0 bash ~/gcp_prjdb36442_metaphlan_batch.sh ~/PRJDB36442_fastq_manifest.tsv | tee -a ~/hbv_gut/results/metaphlan/PRJDB36442.batch.log\"
  echo \"started ${SESSION}\"
fi
tmux ls || true
'"

echo "Check status:"
echo "  INSTANCE=${INSTANCE} ZONE=${ZONE} bash scripts/cloud/gcp_status_prjdb36442.sh"
