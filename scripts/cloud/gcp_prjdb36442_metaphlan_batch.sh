#!/usr/bin/env bash
set -euo pipefail

MANIFEST_PATH="${1:-$HOME/PRJDB36442_fastq_manifest.tsv}"
DB_DIR="${DB_DIR:-$HOME/metaphlan_db}"
FASTQ_DIR="${FASTQ_DIR:-$HOME/hbv_gut/data/PRJDB36442}"
OUT_DIR="${OUT_DIR:-$HOME/hbv_gut/results/metaphlan/PRJDB36442}"
BOWTIE2_DIR="${BOWTIE2_DIR:-$OUT_DIR/bowtie2}"
PROGRESS_PATH="${PROGRESS_PATH:-$OUT_DIR/progress.tsv}"
NPROC="${NPROC:-16}"
KEEP_FASTQ="${KEEP_FASTQ:-0}"
KEEP_BOWTIE2="${KEEP_BOWTIE2:-0}"
VERIFY_MD5="${VERIFY_MD5:-0}"
VERIFY_GZIP="${VERIFY_GZIP:-0}"

mkdir -p "${FASTQ_DIR}" "${OUT_DIR}" "${BOWTIE2_DIR}"

if [[ ! -f "${MANIFEST_PATH}" ]]; then
  echo "Missing manifest: ${MANIFEST_PATH}" >&2
  exit 2
fi

if [[ ! -f "${DB_DIR}/mpa_latest" ]]; then
  echo "Missing ${DB_DIR}/mpa_latest (MetaPhlAn DB not ready?)" >&2
  exit 3
fi

if [[ ! -d "${HOME}/miniforge3" ]]; then
  echo "Missing Miniforge at ${HOME}/miniforge3" >&2
  exit 4
fi

source "${HOME}/miniforge3/etc/profile.d/conda.sh"

echo "MANIFEST_PATH=${MANIFEST_PATH}"
echo "DB_DIR=${DB_DIR}"
echo "FASTQ_DIR=${FASTQ_DIR}"
echo "OUT_DIR=${OUT_DIR}"
echo "BOWTIE2_DIR=${BOWTIE2_DIR}"
echo "PROGRESS_PATH=${PROGRESS_PATH}"
echo "NPROC=${NPROC}"
echo "KEEP_FASTQ=${KEEP_FASTQ}"
echo "KEEP_BOWTIE2=${KEEP_BOWTIE2}"
echo "VERIFY_MD5=${VERIFY_MD5}"
echo "VERIFY_GZIP=${VERIFY_GZIP}"
echo

echo "== Disk usage (start) =="
df -h "${HOME}" | sed -n '1,2p'
echo

col_idx() {
  local col_name="$1"
  awk -F'\t' -v name="${col_name}" 'NR==1{for(i=1;i<=NF;i++){if($i==name){print i; exit}}}' "${MANIFEST_PATH}"
}

URL_COL="$(col_idx url)"
MATE_COL="$(col_idx mate)"
RUN_COL="$(col_idx run_accession)"
MD5_COL="$(col_idx md5 || true)"
if [[ -z "${URL_COL}" || -z "${MATE_COL}" || -z "${RUN_COL}" ]]; then
  echo "Manifest header missing required columns. Expected at least: run_accession, mate, url" >&2
  head -n 1 "${MANIFEST_PATH}" >&2 || true
  exit 6
fi

echo "== Building run list from manifest =="
runs="$(
  awk -F'\t' -v c="${RUN_COL}" 'NR>1 {print $c}' "${MANIFEST_PATH}" | sort -u
)"
echo "${runs}" | wc -l | awk '{print "n_runs=" $1}'
echo

download_one() {
  local run="$1"
  local mate="$2"

  local url
  url="$(awk -F'\t' -v r="${run}" -v m="${mate}" -v rc="${RUN_COL}" -v mc="${MATE_COL}" -v uc="${URL_COL}" 'NR>1 && $rc==r && $mc==m {print $uc; exit}' "${MANIFEST_PATH}")"
  if [[ -z "${url}" ]]; then
    echo "No url for run=${run} mate=${mate}" >&2
    return 10
  fi

  local out="${FASTQ_DIR}/${run}_${mate}.fastq.gz"
  if [[ -s "${out}" ]]; then
    if [[ "${VERIFY_MD5}" -eq 1 && -n "${MD5_COL}" ]]; then
      local expected
      expected="$(awk -F'\t' -v r="${run}" -v m="${mate}" -v rc="${RUN_COL}" -v mc="${MATE_COL}" -v dc="${MD5_COL}" 'NR>1 && $rc==r && $mc==m {print $dc; exit}' "${MANIFEST_PATH}")"
      if [[ -n "${expected}" ]]; then
        local got
        got="$(md5sum "${out}" | awk '{print $1}')"
        if [[ "${got}" != "${expected}" ]]; then
          echo "FASTQ MD5 mismatch (will re-download): ${out} got=${got} expected=${expected}" >&2
          rm -f "${out}"
        else
          echo "FASTQ exists (md5 ok): ${out}"
          return 0
        fi
      else
        echo "FASTQ exists: ${out}"
        return 0
      fi
    else
      echo "FASTQ exists: ${out}"
      return 0
    fi
  fi

  echo "Downloading ${run} mate${mate}"
  curl -fL --retry 20 --retry-all-errors --retry-delay 10 --continue-at - -o "${out}" "${url}"

  if [[ "${VERIFY_MD5}" -eq 1 && -n "${MD5_COL}" ]]; then
    local expected
    expected="$(awk -F'\t' -v r="${run}" -v m="${mate}" -v rc="${RUN_COL}" -v mc="${MATE_COL}" -v dc="${MD5_COL}" 'NR>1 && $rc==r && $mc==m {print $dc; exit}' "${MANIFEST_PATH}")"
    if [[ -n "${expected}" ]]; then
      local got
      got="$(md5sum "${out}" | awk '{print $1}')"
      if [[ "${got}" != "${expected}" ]]; then
        echo "MD5 mismatch for ${out}: got=${got} expected=${expected}" >&2
        return 11
      fi
    fi
  fi

  if [[ "${VERIFY_GZIP}" -eq 1 ]]; then
    if ! gzip -t "${out}"; then
      echo "GZIP integrity check failed for ${out}" >&2
      return 12
    fi
  fi
}

run_metaphlan_one() {
  local run="$1"
  local fq1="${FASTQ_DIR}/${run}_1.fastq.gz"
  local fq2="${FASTQ_DIR}/${run}_2.fastq.gz"
  local out_tsv="${OUT_DIR}/${run}.metaphlan.tsv"
  local out_log="${OUT_DIR}/${run}.log"
  local bowtie2out="${BOWTIE2_DIR}/${run}.bowtie2.bz2"

  if [[ -s "${out_tsv}" ]]; then
    echo "SKIP (exists): ${out_tsv}"
    return 0
  fi

  download_one "${run}" 1
  download_one "${run}" 2

  echo "Running MetaPhlAn: ${run}"
  (
    set -euo pipefail
    echo "== $(date -Is) =="
    conda run -n hbv-gut-shotgun metaphlan --version
    echo "fq1=${fq1}"
    echo "fq2=${fq2}"
    echo "db=${DB_DIR}"
    echo "bowtie2out=${bowtie2out}"
    echo
    conda run -n hbv-gut-shotgun metaphlan \
      "${fq1},${fq2}" \
      --input_type fastq \
      --bowtie2db "${DB_DIR}" \
      --bowtie2out "${bowtie2out}" \
      --nproc "${NPROC}" \
      -o "${out_tsv}"
    echo
    echo "== done $(date -Is) =="
  ) > "${out_log}" 2>&1
  status=$?

  if [[ "${status}" -ne 0 ]]; then
    return "${status}"
  fi

  if [[ ! -s "${out_tsv}" ]]; then
    echo "MetaPhlAn finished but output missing: ${out_tsv}" >&2
    return 20
  fi

  if [[ "${KEEP_FASTQ}" -eq 0 ]]; then
    rm -f "${fq1}" "${fq2}"
  fi
  if [[ "${KEEP_BOWTIE2}" -eq 0 ]]; then
    rm -f "${bowtie2out}"
  fi
  return 0
}

echo "== Running samples (sequential) =="
failed=0
for run in ${runs}; do
  if [[ ! -f "${PROGRESS_PATH}" ]]; then
    mkdir -p "$(dirname "${PROGRESS_PATH}")"
    echo -e "run_accession\tstatus\tstarted_at\tfinished_at\texit_code" > "${PROGRESS_PATH}"
  fi
  started_at="$(date -Is)"
  set +e
  run_metaphlan_one "${run}"
  status=$?
  set -e
  if [[ "${status}" -ne 0 ]]; then
    echo -e "${run}\tFAIL\t${started_at}\t$(date -Is)\t${status}" >> "${PROGRESS_PATH}"
    echo "FAILED: ${run}" >&2
    failed=1
  else
    echo -e "${run}\tOK\t${started_at}\t$(date -Is)\t0" >> "${PROGRESS_PATH}"
  fi
  df -h "${HOME}" | sed -n '1,2p'
done

echo
echo "== Merge tables =="
mkdir -p "${OUT_DIR}/merged"
shopt -s nullglob
files=("${OUT_DIR}"/*.metaphlan.tsv)
if [[ "${#files[@]}" -eq 0 ]]; then
  echo "No MetaPhlAn outputs found in ${OUT_DIR}" >&2
  exit 5
fi
conda run -n hbv-gut-shotgun merge_metaphlan_tables.py "${files[@]}" > "${OUT_DIR}/merged/merged_metaphlan.tsv"
gzip -f "${OUT_DIR}/merged/merged_metaphlan.tsv"

echo
echo "== Done =="
ls -lah "${OUT_DIR}/merged" | sed -n '1,20p'
exit "${failed}"
