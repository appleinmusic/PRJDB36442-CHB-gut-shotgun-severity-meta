#!/usr/bin/env bash
set -euo pipefail

# Remote helper (runs on the VM).
# Waits until MetaPhlAn is idle, then runs a verification pass to re-download any corrupted FASTQs
# (MD5 mismatch) and re-run missing/failed samples.

OUT="${OUT:-/home/simanan/hbv_gut/results/metaphlan/PRJDB36442}"
MANIFEST_PATH="${MANIFEST_PATH:-$HOME/PRJDB36442_fastq_manifest.tsv}"
BATCH_SCRIPT="${BATCH_SCRIPT:-$HOME/gcp_prjdb36442_metaphlan_batch.sh}"

DB_DIR="${DB_DIR:-$HOME/metaphlan_db}"
NPROC="${NPROC:-16}"
VERIFY_MD5="${VERIFY_MD5:-1}"
VERIFY_GZIP="${VERIFY_GZIP:-0}"
KEEP_FASTQ="${KEEP_FASTQ:-0}"
KEEP_BOWTIE2="${KEEP_BOWTIE2:-0}"

POLL_SEC="${POLL_SEC:-600}"
QUIET_ROUNDS="${QUIET_ROUNDS:-2}"

is_busy() {
  ps aux | grep -E "metaphlan .*DRR|bowtie2-align" | grep -v grep >/dev/null 2>&1
}

mkdir -p "${OUT}"

echo "== scheduled verify start (wait mode) =="
date -Is
echo "OUT=${OUT}"
echo "MANIFEST_PATH=${MANIFEST_PATH}"
echo "BATCH_SCRIPT=${BATCH_SCRIPT}"
echo "VERIFY_MD5=${VERIFY_MD5} VERIFY_GZIP=${VERIFY_GZIP}"
echo "POLL_SEC=${POLL_SEC} QUIET_ROUNDS=${QUIET_ROUNDS}"
echo

quiet=0
while true; do
  if is_busy; then
    quiet=0
    echo "[$(date -Is)] busy: metaphlan/bowtie2 running; sleep ${POLL_SEC}s"
  else
    quiet=$((quiet + 1))
    echo "[$(date -Is)] quiet round ${quiet}/${QUIET_ROUNDS}"
    if [[ "${quiet}" -ge "${QUIET_ROUNDS}" ]]; then
      break
    fi
  fi
  sleep "${POLL_SEC}"
done

echo
echo "== launching verify pass =="
PROGRESS_PATH="${OUT}/progress.verify.tsv"
DB_DIR="${DB_DIR}" NPROC="${NPROC}" KEEP_FASTQ="${KEEP_FASTQ}" KEEP_BOWTIE2="${KEEP_BOWTIE2}" VERIFY_MD5="${VERIFY_MD5}" VERIFY_GZIP="${VERIFY_GZIP}" PROGRESS_PATH="${PROGRESS_PATH}" \
  bash "${BATCH_SCRIPT}" "${MANIFEST_PATH}" | tee -a "${OUT}/PRJDB36442.verify.batch.log"

echo
echo "== scheduled verify done =="
date -Is

