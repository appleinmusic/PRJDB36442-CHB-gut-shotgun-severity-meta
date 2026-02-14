#!/usr/bin/env bash
set -euo pipefail

# Work around local gcloud Python issues on macOS (CLOUDSDK_PYTHON may point to a broken venv).
: "${CLOUDSDK_PYTHON:=/usr/bin/python3}"
export CLOUDSDK_PYTHON

INSTANCE="${INSTANCE:-hbv-gut-shotgun-1}"
ZONE="${ZONE:-us-west1-c}"
DEST_DIR="${DEST_DIR:-results/cloud/PRJDB36442_humann}"
FETCH_PER_RUN="${FETCH_PER_RUN:-0}"
FETCH_REMOTE_AUDIT="${FETCH_REMOTE_AUDIT:-1}"

mkdir -p "${DEST_DIR}"

REMOTE_PATHS="$(gcloud compute ssh "${INSTANCE}" --zone "${ZONE}" --command "FETCH_PER_RUN=${FETCH_PER_RUN} bash -s" 2>/dev/null <<'BASH' || true
set -euo pipefail
shopt -s nullglob

maybe() { if [[ -e "$1" ]]; then echo "$1"; fi; }

maybe "$HOME/hbv_gut/results/humann/PRJDB36442/progress.tsv"
maybe "$HOME/hbv_gut/results/humann/PRJDB36442.humann.batch.log"

for f in "$HOME"/hbv_gut/results/humann/PRJDB36442/merged/*.tsv.gz; do
  [[ -e "$f" ]] && echo "$f"
done

if [[ "${FETCH_PER_RUN:-0}" -eq 1 ]]; then
  for f in "$HOME"/hbv_gut/results/humann/PRJDB36442/*_pathabundance.tsv "$HOME"/hbv_gut/results/humann/PRJDB36442/*_genefamilies.tsv "$HOME"/hbv_gut/results/humann/PRJDB36442/*_pathcoverage.tsv "$HOME"/hbv_gut/results/humann/PRJDB36442/*.log; do
    [[ -e "$f" ]] && echo "$f"
  done
fi
maybe "$HOME/PRJDB36442_fastq_manifest.tsv"
maybe "$HOME/gcp_prjdb36442_humann_batch.sh"
maybe "$HOME/humann_dbs/DB_INVENTORY.txt"
BASH
)"

mkdir -p "${DEST_DIR}/merged" "${DEST_DIR}/audit"

while IFS= read -r remote_path; do
  [[ -n "${remote_path}" ]] || continue

  dest="${DEST_DIR}/$(basename "${remote_path}")"
  case "${remote_path}" in
    */merged/*) dest="${DEST_DIR}/merged/$(basename "${remote_path}")" ;;
    */PRJDB36442_fastq_manifest.tsv) dest="${DEST_DIR}/audit/PRJDB36442_fastq_manifest.remote.tsv" ;;
    */gcp_prjdb36442_humann_batch.sh) dest="${DEST_DIR}/audit/gcp_prjdb36442_humann_batch.remote.sh" ;;
    */DB_INVENTORY.txt) dest="${DEST_DIR}/audit/DB_INVENTORY.remote.txt" ;;
  esac

  mkdir -p "$(dirname "${dest}")"
  gcloud compute scp --zone "${ZONE}" "${INSTANCE}:${remote_path}" "${dest}" || true
done <<< "${REMOTE_PATHS}"

if [[ "${FETCH_PER_RUN}" -eq 1 ]]; then
  mkdir -p "${DEST_DIR}/per_run"
  # Per-run files are now included in REMOTE_PATHS listing above when FETCH_PER_RUN=1.
  true
fi

if [[ "${FETCH_REMOTE_AUDIT}" -eq 1 ]]; then
  gcloud compute ssh "${INSTANCE}" --zone "${ZONE}" --command "bash -s" > "${DEST_DIR}/audit/remote_env_and_db.txt" 2>/dev/null <<'BASH' || true
set -euo pipefail
echo "== TIME =="; date -Is
echo
echo "== OS =="; uname -a
echo
echo "== DISK =="; df -h ~ | sed -n '1,2p'
echo
echo "== CONDA_ENVS =="; source ~/miniforge3/etc/profile.d/conda.sh; conda env list || true
echo
echo "== HUMANN_VERSION =="; conda run -n hbv-gut-humann humann --version || true
echo
echo "== HUMANN_DB_ROOT =="; du -sh ~/humann_dbs/* 2>/dev/null || true
BASH

  gcloud compute ssh "${INSTANCE}" --zone "${ZONE}" --command "bash -s" > "${DEST_DIR}/audit/conda_env_hbv-gut-humann.yml" 2>/dev/null <<'BASH' || true
set -euo pipefail
source ~/miniforge3/etc/profile.d/conda.sh
conda env export -n hbv-gut-humann --no-builds
BASH
fi

echo "Fetched into: ${DEST_DIR}"
