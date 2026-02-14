#!/usr/bin/env bash
set -euo pipefail

# Work around local gcloud Python issues on macOS (CLOUDSDK_PYTHON may point to a broken venv).
: "${CLOUDSDK_PYTHON:=/usr/bin/python3}"
export CLOUDSDK_PYTHON

# Re-run PRJDB36442 batch on the VM with integrity verification enabled.
#
# Intended use:
# 1) Let an existing session finish (or stop it).
# 2) Run this script to push the latest batch script and restart in a new tmux session.
#
# Notes:
# - The batch script will SKIP runs that already have *.metaphlan.tsv outputs.
# - If VERIFY_MD5=1, existing FASTQs with wrong MD5 will be re-downloaded.

INSTANCE="${INSTANCE:-hbv-gut-shotgun-1}"
ZONE="${ZONE:-us-west1-c}"
MANIFEST_LOCAL="${MANIFEST_LOCAL:-results/feasibility/PRJDB36442_fastq_manifest.tsv}"
SESSION="${SESSION:-prjdb36442-metaphlan-verify}"
VERIFY_MD5="${VERIFY_MD5:-1}"
VERIFY_GZIP="${VERIFY_GZIP:-0}"
NPROC="${NPROC:-16}"
PROGRESS_PATH_REMOTE="${PROGRESS_PATH_REMOTE:-$HOME/hbv_gut/results/metaphlan/PRJDB36442/progress.verify.tsv}"

if [[ ! -f "${MANIFEST_LOCAL}" ]]; then
  echo "Missing manifest: ${MANIFEST_LOCAL}" >&2
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
  tmux new-session -d -s ${SESSION} \"DB_DIR=~/metaphlan_db NPROC=${NPROC} KEEP_FASTQ=0 KEEP_BOWTIE2=0 VERIFY_MD5=${VERIFY_MD5} VERIFY_GZIP=${VERIFY_GZIP} PROGRESS_PATH=${PROGRESS_PATH_REMOTE} bash ~/gcp_prjdb36442_metaphlan_batch.sh ~/PRJDB36442_fastq_manifest.tsv | tee -a ~/hbv_gut/results/metaphlan/PRJDB36442.verify.batch.log\"
  echo \"started ${SESSION}\"
fi
tmux ls || true
'"

echo "Check status:"
echo "  INSTANCE=${INSTANCE} ZONE=${ZONE} bash scripts/cloud/gcp_status_prjdb36442.sh"
