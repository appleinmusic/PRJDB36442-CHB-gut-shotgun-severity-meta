#!/usr/bin/env bash
set -euo pipefail

# Work around local gcloud Python issues on macOS (CLOUDSDK_PYTHON may point to a broken venv).
: "${CLOUDSDK_PYTHON:=/usr/bin/python3}"
export CLOUDSDK_PYTHON

# Schedule a verification pass that automatically starts after the current MetaPhlAn run is idle.
#
# Designed for: start it now, come back in 10+ hours, and the FAIL runs (e.g., corrupted FASTQ downloads)
# will be re-downloaded (MD5 check) and re-run automatically.

INSTANCE="${INSTANCE:-hbv-gut-shotgun-1}"
ZONE="${ZONE:-us-west1-c}"
MANIFEST_LOCAL="${MANIFEST_LOCAL:-results/feasibility/PRJDB36442_fastq_manifest.tsv}"

SESSION="${SESSION:-prjdb36442-metaphlan-verify-scheduled}"
NPROC="${NPROC:-16}"
VERIFY_MD5="${VERIFY_MD5:-1}"
VERIFY_GZIP="${VERIFY_GZIP:-0}"
POLL_SEC="${POLL_SEC:-600}"
QUIET_ROUNDS="${QUIET_ROUNDS:-2}"

if [[ ! -f "${MANIFEST_LOCAL}" ]]; then
  echo "Missing manifest: ${MANIFEST_LOCAL}" >&2
  exit 2
fi

chmod +x scripts/cloud/gcp_prjdb36442_metaphlan_batch.sh
chmod +x scripts/cloud/prjdb36442_verify_after_current_remote.sh

# Push updated scripts + manifest (safe while a job is running).
gcloud compute scp --zone "${ZONE}" "${MANIFEST_LOCAL}" "${INSTANCE}":~/PRJDB36442_fastq_manifest.tsv
gcloud compute scp --zone "${ZONE}" scripts/cloud/gcp_prjdb36442_metaphlan_batch.sh "${INSTANCE}":~/gcp_prjdb36442_metaphlan_batch.sh
gcloud compute scp --zone "${ZONE}" scripts/cloud/prjdb36442_verify_after_current_remote.sh "${INSTANCE}":~/prjdb36442_verify_after_current.sh

gcloud compute ssh "${INSTANCE}" --zone "${ZONE}" --command "bash -lc 'set -euo pipefail; chmod +x ~/gcp_prjdb36442_metaphlan_batch.sh; chmod +x ~/prjdb36442_verify_after_current.sh; if tmux has-session -t ${SESSION} 2>/dev/null; then echo \"tmux session exists: ${SESSION}\"; else tmux new-session -d -s ${SESSION} \"NPROC=${NPROC} VERIFY_MD5=${VERIFY_MD5} VERIFY_GZIP=${VERIFY_GZIP} POLL_SEC=${POLL_SEC} QUIET_ROUNDS=${QUIET_ROUNDS} bash ~/prjdb36442_verify_after_current.sh\"; echo \"scheduled: ${SESSION}\"; fi; tmux ls || true'"

echo "Scheduled verification tmux session:"
echo "  INSTANCE=${INSTANCE} ZONE=${ZONE} SESSION=${SESSION}"
echo "Check status:"
echo "  INSTANCE=${INSTANCE} ZONE=${ZONE} bash scripts/cloud/gcp_status_prjdb36442.sh"
