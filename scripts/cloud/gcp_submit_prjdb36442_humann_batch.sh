#!/usr/bin/env bash
set -euo pipefail

# Work around local gcloud Python issues on macOS (CLOUDSDK_PYTHON may point to a broken venv).
: "${CLOUDSDK_PYTHON:=/usr/bin/python3}"
export CLOUDSDK_PYTHON

# Submit PRJDB36442 HUMAnN batch job to a running GCP VM.
#
# VM prerequisites:
# - scripts/cloud/gcp_bootstrap_humann3.sh has been run
# - scripts/cloud/gcp_download_humann_dbs.sh has been run

INSTANCE="${INSTANCE:-hbv-gut-shotgun-1}"
ZONE="${ZONE:-us-west1-c}"
MANIFEST_LOCAL="${MANIFEST_LOCAL:-results/feasibility/PRJDB36442_fastq_manifest.tsv}"
SESSION="${SESSION:-prjdb36442-humann}"

if [[ ! -f "${MANIFEST_LOCAL}" ]]; then
  echo "Missing manifest: ${MANIFEST_LOCAL}" >&2
  exit 2
fi

chmod +x scripts/cloud/gcp_prjdb36442_humann_batch.sh

gcloud compute scp --zone "${ZONE}" "${MANIFEST_LOCAL}" "${INSTANCE}":~/PRJDB36442_fastq_manifest.tsv
gcloud compute scp --zone "${ZONE}" scripts/cloud/gcp_prjdb36442_humann_batch.sh "${INSTANCE}":~/gcp_prjdb36442_humann_batch.sh

gcloud compute ssh "${INSTANCE}" --zone "${ZONE}" --command "bash -lc 'set -euo pipefail
chmod +x ~/gcp_prjdb36442_humann_batch.sh
mkdir -p ~/hbv_gut/results/humann
if tmux has-session -t ${SESSION} 2>/dev/null; then
  echo \"tmux session exists: ${SESSION}\"
else
  tmux new-session -d -s ${SESSION} \"ENV_NAME=hbv-gut-humann DB_ROOT=~/humann_dbs NPROC=16 KEEP_FASTQ=0 VERIFY_MD5=1 VERIFY_GZIP=0 BYPASS_TRANSLATED=1 bash ~/gcp_prjdb36442_humann_batch.sh ~/PRJDB36442_fastq_manifest.tsv | tee -a ~/hbv_gut/results/humann/PRJDB36442.humann.batch.log\"
  echo \"started ${SESSION}\"
fi
tmux ls || true
'"

echo "Check status (remote):"
echo "  gcloud compute ssh ${INSTANCE} --zone ${ZONE} --command \"bash -lc 'tail -n 30 ~/hbv_gut/results/humann/PRJDB36442/progress.tsv 2>/dev/null || true'\""
