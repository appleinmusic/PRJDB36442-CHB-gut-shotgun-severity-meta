#!/usr/bin/env bash
set -euo pipefail

# Work around local gcloud Python issues on macOS (CLOUDSDK_PYTHON may point to a broken venv).
: "${CLOUDSDK_PYTHON:=/usr/bin/python3}"
export CLOUDSDK_PYTHON

INSTANCE="${INSTANCE:-hbv-gut-shotgun-1}"
ZONE="${ZONE:-us-west1-c}"
DEST_DIR="${DEST_DIR:-results/cloud/PRJDB36442}"
FETCH_PER_RUN="${FETCH_PER_RUN:-0}"
FETCH_REMOTE_AUDIT="${FETCH_REMOTE_AUDIT:-1}"

mkdir -p "${DEST_DIR}"

# Progress + logs
gcloud compute scp --zone "${ZONE}" "${INSTANCE}":~/hbv_gut/results/metaphlan/PRJDB36442/progress.tsv "${DEST_DIR}/progress.tsv" || true
gcloud compute scp --zone "${ZONE}" "${INSTANCE}":~/hbv_gut/results/metaphlan/PRJDB36442/progress.verify.tsv "${DEST_DIR}/progress.verify.tsv" || true

gcloud compute scp --zone "${ZONE}" "${INSTANCE}":~/hbv_gut/results/metaphlan/PRJDB36442.batch.log "${DEST_DIR}/PRJDB36442.batch.log" || true
gcloud compute scp --zone "${ZONE}" "${INSTANCE}":~/hbv_gut/results/metaphlan/PRJDB36442/PRJDB36442.verify.batch.log "${DEST_DIR}/PRJDB36442.verify.batch.log" || true

# merged output if present
gcloud compute scp --zone "${ZONE}" "${INSTANCE}":~/hbv_gut/results/metaphlan/PRJDB36442/merged/merged_metaphlan.tsv.gz "${DEST_DIR}/merged_metaphlan.tsv.gz" || true

if [[ "${FETCH_PER_RUN}" -eq 1 ]]; then
  mkdir -p "${DEST_DIR}/per_run"
  gcloud compute scp --zone "${ZONE}" "${INSTANCE}":~/hbv_gut/results/metaphlan/PRJDB36442/*.metaphlan.tsv "${DEST_DIR}/per_run/" || true
  gcloud compute scp --zone "${ZONE}" "${INSTANCE}":~/hbv_gut/results/metaphlan/PRJDB36442/*.log "${DEST_DIR}/per_run/" || true
fi

if [[ "${FETCH_REMOTE_AUDIT}" -eq 1 ]]; then
  mkdir -p "${DEST_DIR}/audit"

  # Remote copies of the exact manifest + batch script used on the VM
  gcloud compute scp --zone "${ZONE}" "${INSTANCE}":~/PRJDB36442_fastq_manifest.tsv "${DEST_DIR}/audit/PRJDB36442_fastq_manifest.remote.tsv" || true
  gcloud compute scp --zone "${ZONE}" "${INSTANCE}":~/gcp_prjdb36442_metaphlan_batch.sh "${DEST_DIR}/audit/gcp_prjdb36442_metaphlan_batch.remote.sh" || true

  # Remote environment + DB marker snapshot (stdout captured locally)
  gcloud compute ssh "${INSTANCE}" --zone "${ZONE}" --command "bash -lc 'set -euo pipefail
  echo ==TIME==; date -Is
  echo
  echo ==OS==; uname -a
  echo
  echo ==DISK==; df -h ~ | sed -n \"1,2p\"
  echo
  echo ==CONDA_ENVS==; source ~/miniforge3/etc/profile.d/conda.sh; conda env list
  echo
  echo ==METAPHLAN_VERSION==; conda run -n hbv-gut-shotgun metaphlan --version
  echo
  echo ==DB_MARKER==; ls -lah ~/metaphlan_db/mpa_latest; cat ~/metaphlan_db/mpa_latest || true
  echo
  echo ==DB_INDEX_FILES_HEAD==
  ls -1 ~/metaphlan_db/*bt2* 2>/dev/null | head -n 10 || true
  '" > "${DEST_DIR}/audit/remote_env_and_db.txt" || true
fi

echo "Fetched into: ${DEST_DIR}"
