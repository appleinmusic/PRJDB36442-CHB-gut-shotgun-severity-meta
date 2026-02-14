#!/usr/bin/env bash
set -euo pipefail

# Remote helper (runs on the VM).
# Wait for HUMAnN ChocoPhlAn database download to complete (DB_INVENTORY.txt exists), then run batch HUMAnN.

DB_INVENTORY="${DB_INVENTORY:-/home/simanan/humann_dbs/DB_INVENTORY.txt}"
MANIFEST_PATH="${MANIFEST_PATH:-/home/simanan/PRJDB36442_fastq_manifest.tsv}"
BATCH_SCRIPT="${BATCH_SCRIPT:-/home/simanan/gcp_prjdb36442_humann_batch.sh}"

OUT_LOG="${OUT_LOG:-/home/simanan/hbv_gut/results/humann/PRJDB36442.humann.batch.log}"

POLL_SEC="${POLL_SEC:-600}"

mkdir -p "$(dirname "${OUT_LOG}")"

echo "== WAIT_DB_INVENTORY =="
date -Is
while true; do
  if [[ -s "${DB_INVENTORY}" ]]; then
    break
  fi
  echo "waiting_for_DB_INVENTORY"
  date -Is
  sleep "${POLL_SEC}"
done

echo "== START_HUMANN =="
date -Is

ENV_NAME="${ENV_NAME:-hbv-gut-humann}"
DB_ROOT="${DB_ROOT:-/home/simanan/humann_dbs}"
NPROC="${NPROC:-16}"
KEEP_FASTQ="${KEEP_FASTQ:-0}"
VERIFY_MD5="${VERIFY_MD5:-1}"
VERIFY_GZIP="${VERIFY_GZIP:-0}"
BYPASS_TRANSLATED="${BYPASS_TRANSLATED:-1}"

# Ensure HUMAnN utility mapping DB is available for regrouping later (small download).
if [[ ! -d "${DB_ROOT}/utility_mapping" ]]; then
  echo "== DOWNLOAD_UTILITY_MAPPING =="
  date -Is
  if [[ -d /home/simanan/miniforge3 ]]; then
    # shellcheck disable=SC1091
    source /home/simanan/miniforge3/etc/profile.d/conda.sh
    conda run -n "${ENV_NAME}" humann_databases --download utility_mapping full "${DB_ROOT}"
  fi
fi

date -Is
ENV_NAME="${ENV_NAME}" DB_ROOT="${DB_ROOT}" NPROC="${NPROC}" KEEP_FASTQ="${KEEP_FASTQ}" VERIFY_MD5="${VERIFY_MD5}" VERIFY_GZIP="${VERIFY_GZIP}" BYPASS_TRANSLATED="${BYPASS_TRANSLATED}" \
  bash "${BATCH_SCRIPT}" "${MANIFEST_PATH}" | tee -a "${OUT_LOG}"

echo "== DONE_HUMANN =="
date -Is
