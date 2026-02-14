#!/usr/bin/env bash
set -euo pipefail

DB_DIR="${1:-$HOME/metaphlan_db}"
RUN_ID="${2:-DRR764597}"
NPROC="${NPROC:-16}"

FASTQ_DIR="${HOME}/hbv_gut/data/PRJDB36442"
OUT_DIR="${HOME}/hbv_gut/results/pilot/${RUN_ID}"
mkdir -p "${OUT_DIR}"

FQ1="${FASTQ_DIR}/${RUN_ID}_1.fastq.gz"
FQ2="${FASTQ_DIR}/${RUN_ID}_2.fastq.gz"

if [[ ! -f "${FQ1}" || ! -f "${FQ2}" ]]; then
  echo "Missing fastq: ${FQ1} and/or ${FQ2}" >&2
  exit 2
fi

if [[ ! -f "${DB_DIR}/mpa_latest" ]]; then
  echo "Missing ${DB_DIR}/mpa_latest (did DB extract finish?)" >&2
  exit 3
fi

source "${HOME}/miniforge3/etc/profile.d/conda.sh"

echo "== Versions ==" | tee "${OUT_DIR}/run.log"
conda run -n hbv-gut-shotgun metaphlan --version 2>&1 | tee -a "${OUT_DIR}/run.log"

echo "== Inputs ==" | tee -a "${OUT_DIR}/run.log"
ls -lah "${FQ1}" "${FQ2}" | tee -a "${OUT_DIR}/run.log"

echo "== Run MetaPhlAn ==" | tee -a "${OUT_DIR}/run.log"
conda run -n hbv-gut-shotgun metaphlan \
  "${FQ1},${FQ2}" \
  --input_type fastq \
  --bowtie2db "${DB_DIR}" \
  --nproc "${NPROC}" \
  --bowtie2out "${OUT_DIR}/${RUN_ID}.bowtie2.bz2" \
  -o "${OUT_DIR}/${RUN_ID}.metaphlan.tsv" \
  2>&1 | tee -a "${OUT_DIR}/run.log"

echo "== Outputs ==" | tee -a "${OUT_DIR}/run.log"
ls -lah "${OUT_DIR}" | tee -a "${OUT_DIR}/run.log"

echo "Done."
