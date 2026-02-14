#!/usr/bin/env bash
set -euo pipefail

# Batch HUMAnN run for PRJDB36442.
#
# Notes on paired-end:
# HUMAnN recommends concatenating paired-end reads into a single FASTQ/FASTA.
# We implement this by concatenating the two .fastq.gz streams into one .fastq.gz.

MANIFEST_PATH="${1:-$HOME/PRJDB36442_fastq_manifest.tsv}"

ENV_NAME="${ENV_NAME:-hbv-gut-humann}"
DB_ROOT="${DB_ROOT:-$HOME/humann_dbs}"
METAPHLAN_DB_DIR="${METAPHLAN_DB_DIR:-$HOME/metaphlan_db}"
METAPHLAN_INDEX="${METAPHLAN_INDEX:-}"

FASTQ_DIR="${FASTQ_DIR:-$HOME/hbv_gut/data/PRJDB36442}"
OUT_DIR="${OUT_DIR:-$HOME/hbv_gut/results/humann/PRJDB36442}"
TMP_DIR="${TMP_DIR:-$OUT_DIR/tmp}"

NPROC="${NPROC:-16}"
KEEP_FASTQ="${KEEP_FASTQ:-0}"
VERIFY_MD5="${VERIFY_MD5:-0}"
VERIFY_GZIP="${VERIFY_GZIP:-0}"
BYPASS_TRANSLATED="${BYPASS_TRANSLATED:-1}"
SKIP_FAILED="${SKIP_FAILED:-1}"

PROGRESS_PATH="${PROGRESS_PATH:-$OUT_DIR/progress.tsv}"

mkdir -p "${FASTQ_DIR}" "${OUT_DIR}" "${TMP_DIR}"

if [[ ! -f "${MANIFEST_PATH}" ]]; then
  echo "Missing manifest: ${MANIFEST_PATH}" >&2
  exit 2
fi

if [[ ! -d "${HOME}/miniforge3" ]]; then
  echo "Missing Miniforge at ${HOME}/miniforge3" >&2
  exit 3
fi

source "${HOME}/miniforge3/etc/profile.d/conda.sh"

if ! conda env list | grep -E "^${ENV_NAME}[[:space:]]" >/dev/null 2>&1; then
  echo "Missing conda env: ${ENV_NAME}. Run gcp_bootstrap_humann3.sh first." >&2
  exit 4
fi

NUC_DB="${NUC_DB:-$DB_ROOT/chocophlan}"
PROT_DB="${PROT_DB:-$DB_ROOT/uniref}"

if [[ ! -d "${NUC_DB}" ]]; then
  echo "Missing nucleotide DB directory: ${NUC_DB}" >&2
  echo "Run gcp_download_humann_dbs.sh first." >&2
  exit 5
fi

if [[ "${BYPASS_TRANSLATED}" -eq 0 && ! -d "${PROT_DB}" ]]; then
  echo "Missing protein DB directory: ${PROT_DB}" >&2
  echo "Either download it (DOWNLOAD_PROTEIN_DB=1) or set BYPASS_TRANSLATED=1." >&2
  exit 6
fi

echo "MANIFEST_PATH=${MANIFEST_PATH}"
echo "ENV_NAME=${ENV_NAME}"
echo "DB_ROOT=${DB_ROOT}"
echo "NUC_DB=${NUC_DB}"
echo "PROT_DB=${PROT_DB}"
echo "FASTQ_DIR=${FASTQ_DIR}"
echo "OUT_DIR=${OUT_DIR}"
echo "TMP_DIR=${TMP_DIR}"
echo "NPROC=${NPROC}"
echo "KEEP_FASTQ=${KEEP_FASTQ}"
echo "VERIFY_MD5=${VERIFY_MD5}"
echo "VERIFY_GZIP=${VERIFY_GZIP}"
echo "BYPASS_TRANSLATED=${BYPASS_TRANSLATED}"
echo "SKIP_FAILED=${SKIP_FAILED}"
echo "PROGRESS_PATH=${PROGRESS_PATH}"
echo "METAPHLAN_DB_DIR=${METAPHLAN_DB_DIR}"
echo "METAPHLAN_INDEX=${METAPHLAN_INDEX}"
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
  exit 7
fi

echo "== Building run list from manifest =="
runs="$(awk -F'\t' -v c="${RUN_COL}" 'NR>1 {print $c}' "${MANIFEST_PATH}" | sort -u)"
echo "${runs}" | wc -l | awk '{print "n_runs=" $1}'

_download_one() {
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

_run_one() {
  local run="$1"

  local fq1="${FASTQ_DIR}/${run}_1.fastq.gz"
  local fq2="${FASTQ_DIR}/${run}_2.fastq.gz"
  local combined="${FASTQ_DIR}/${run}.combined.fastq.gz"

  local out_log="${OUT_DIR}/${run}.log"
  local marker_ok="${OUT_DIR}/${run}.OK"
  local marker_fail="${OUT_DIR}/${run}.FAIL"

  # HUMAnN outputs are multiple files per sample. Use .OK marker for idempotency.
  if [[ -f "${marker_ok}" ]]; then
    echo "SKIP (exists): ${marker_ok}"
    return 0
  fi
  if [[ "${SKIP_FAILED}" -eq 1 && -f "${marker_fail}" ]]; then
    echo "SKIP (previous FAIL): ${marker_fail} (set SKIP_FAILED=0 to re-run)"
    return 0
  fi

  _cleanup_inputs() {
    if [[ "${KEEP_FASTQ}" -eq 0 ]]; then
      rm -f "${fq1}" "${fq2}" "${combined}"
    fi
  }

  _download_one "${run}" 1
  _download_one "${run}" 2

  echo "Concatenating paired-end reads: ${run}"
  cat "${fq1}" "${fq2}" > "${combined}"
  if [[ "${KEEP_FASTQ}" -eq 0 ]]; then
    rm -f "${fq1}" "${fq2}"
  fi

  if [[ "${VERIFY_GZIP}" -eq 1 ]]; then
    gzip -t "${combined}"
  fi

  echo "Running HUMAnN: ${run}"
  humann_exit=0
  (
    set -euo pipefail
    echo "== $(date -Is) =="
    conda run -n "${ENV_NAME}" humann --version
    echo "input=${combined}"
    echo "nuc_db=${NUC_DB}"
    echo "prot_db=${PROT_DB}"
    echo "threads=${NPROC}"
    echo "bypass_translated=${BYPASS_TRANSLATED}"
    echo "metaphlan_db_dir=${METAPHLAN_DB_DIR}"
    echo "metaphlan_index=${METAPHLAN_INDEX}"
    echo

    # HUMAnN3 does not expose a --tmp-dir flag; direct temp files via TMPDIR.
    export TMPDIR="${TMP_DIR}"

    if [[ -z "${METAPHLAN_INDEX}" && -f "${METAPHLAN_DB_DIR}/mpa_latest" ]]; then
      METAPHLAN_INDEX="$(cat "${METAPHLAN_DB_DIR}/mpa_latest" | tr -d '\r\n')"
    fi
    # Note: the MetaPhlAn CLI used inside the HUMAnN env on this VM expects --db_dir and -x,
    # not --bowtie2db/--bowtie2out.
    metaphlan_opts="--db_dir ${METAPHLAN_DB_DIR}"
    if [[ -n "${METAPHLAN_INDEX}" ]]; then
      metaphlan_opts="${metaphlan_opts} -x ${METAPHLAN_INDEX}"
    fi

    args=(
      --input "${combined}"
      --output "${OUT_DIR}"
      --output-basename "${run}"
      --threads "${NPROC}"
      --nucleotide-database "${NUC_DB}"
      --metaphlan-options "${metaphlan_opts}"
      --remove-temp-output
    )
    if [[ "${BYPASS_TRANSLATED}" -eq 1 ]]; then
      args+=(--bypass-translated-search)
    else
      args+=(--protein-database "${PROT_DB}")
    fi

    conda run -n "${ENV_NAME}" humann "${args[@]}"
    echo
    echo "== done $(date -Is) =="
  ) > "${out_log}" 2>&1 || humann_exit=$?

  # Always remove HUMAnN temp directories if they were left behind (can be huge on failures).
  rm -rf "${OUT_DIR}/${run}_humann_temp_"* 2>/dev/null || true

  if [[ "${humann_exit}" -ne 0 ]]; then
    echo "HUMAnN failed for ${run} (exit=${humann_exit}). See ${out_log}" >&2
    printf "time=%s\texit_code=%s\tlog=%s\n" "$(date -Is)" "${humann_exit}" "${out_log}" > "${marker_fail}" || true
    _cleanup_inputs
    return "${humann_exit}"
  fi

  # check key outputs
  if [[ ! -s "${OUT_DIR}/${run}_pathabundance.tsv" ]]; then
    echo "Missing output: ${OUT_DIR}/${run}_pathabundance.tsv" >&2
    printf "time=%s\texit_code=%s\treason=missing_pathabundance\tlog=%s\n" "$(date -Is)" "20" "${out_log}" > "${marker_fail}" || true
    _cleanup_inputs
    return 20
  fi
  if [[ ! -s "${OUT_DIR}/${run}_genefamilies.tsv" ]]; then
    echo "Missing output: ${OUT_DIR}/${run}_genefamilies.tsv" >&2
    printf "time=%s\texit_code=%s\treason=missing_genefamilies\tlog=%s\n" "$(date -Is)" "21" "${out_log}" > "${marker_fail}" || true
    _cleanup_inputs
    return 21
  fi

  touch "${marker_ok}"
  rm -f "${marker_fail}" 2>/dev/null || true

  if [[ "${KEEP_FASTQ}" -eq 0 ]]; then
    rm -f "${fq1}" "${fq2}" "${combined}"
  fi

  return 0
}

failed=0
for run in ${runs}; do
  if [[ ! -f "${PROGRESS_PATH}" ]]; then
    mkdir -p "$(dirname "${PROGRESS_PATH}")"
    echo -e "run_accession\tstatus\tstarted_at\tfinished_at\texit_code" > "${PROGRESS_PATH}"
  fi

  started_at="$(date -Is)"
  set +e
  _run_one "${run}"
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

conda run -n "${ENV_NAME}" humann_join_tables --input "${OUT_DIR}" --output "${OUT_DIR}/merged/merged_genefamilies.tsv" --file_name genefamilies
conda run -n "${ENV_NAME}" humann_join_tables --input "${OUT_DIR}" --output "${OUT_DIR}/merged/merged_pathabundance.tsv" --file_name pathabundance
conda run -n "${ENV_NAME}" humann_join_tables --input "${OUT_DIR}" --output "${OUT_DIR}/merged/merged_pathcoverage.tsv" --file_name pathcoverage

gzip -f "${OUT_DIR}/merged/merged_genefamilies.tsv"
gzip -f "${OUT_DIR}/merged/merged_pathabundance.tsv"
gzip -f "${OUT_DIR}/merged/merged_pathcoverage.tsv"

echo "== Done =="
ls -lah "${OUT_DIR}/merged" | sed -n '1,50p'

exit "${failed}"
