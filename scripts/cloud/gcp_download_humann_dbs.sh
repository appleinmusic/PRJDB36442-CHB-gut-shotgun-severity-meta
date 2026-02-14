#!/usr/bin/env bash
set -euo pipefail

# Download HUMAnN databases on the VM.
# Default is a *nucleotide-only* setup (ChocoPhlAn) to avoid downloading very large protein DBs.
# Enable protein DB download by setting DOWNLOAD_PROTEIN_DB=1.

if [[ ! -d "${HOME}/miniforge3" ]]; then
  echo "Missing Miniforge at ${HOME}/miniforge3" >&2
  exit 2
fi

source "${HOME}/miniforge3/etc/profile.d/conda.sh"
ENV_NAME="${ENV_NAME:-hbv-gut-humann}"

DB_ROOT="${DB_ROOT:-$HOME/humann_dbs}"
CHOCOPHLAN_BUILD="${CHOCOPHLAN_BUILD:-full}"
DOWNLOAD_PROTEIN_DB="${DOWNLOAD_PROTEIN_DB:-0}"
DOWNLOAD_UTILITY_MAPPING="${DOWNLOAD_UTILITY_MAPPING:-1}"
UNIREF="${UNIREF:-uniref90_diamond}"

mkdir -p "${DB_ROOT}"

echo "ENV_NAME=${ENV_NAME}"
echo "DB_ROOT=${DB_ROOT}"
echo "CHOCOPHLAN_BUILD=${CHOCOPHLAN_BUILD}"
echo "DOWNLOAD_PROTEIN_DB=${DOWNLOAD_PROTEIN_DB}"
echo "DOWNLOAD_UTILITY_MAPPING=${DOWNLOAD_UTILITY_MAPPING}"
echo "UNIREF=${UNIREF}"
echo

conda run -n "${ENV_NAME}" humann --version

echo "== Download ChocoPhlAn (${CHOCOPHLAN_BUILD}) =="
conda run -n "${ENV_NAME}" humann_databases --download chocophlan "${CHOCOPHLAN_BUILD}" "${DB_ROOT}" 

echo "== Optional: Download protein DB (${UNIREF}) =="
if [[ "${DOWNLOAD_PROTEIN_DB}" -eq 1 ]]; then
  conda run -n "${ENV_NAME}" humann_databases --download uniref "${UNIREF}" "${DB_ROOT}"
else
  echo "Skipping protein DB. (Set DOWNLOAD_PROTEIN_DB=1 to enable.)"
fi

echo "== Optional: Download utility mapping (regroup) =="
if [[ "${DOWNLOAD_UTILITY_MAPPING}" -eq 1 ]]; then
  conda run -n "${ENV_NAME}" humann_databases --download utility_mapping full "${DB_ROOT}"
else
  echo "Skipping utility_mapping. (Set DOWNLOAD_UTILITY_MAPPING=1 to enable.)"
fi

echo
echo "== DB inventory =="
{
  echo "time=$(date -Is)"
  echo "db_root=${DB_ROOT}"
  echo "chocophlan_build=${CHOCOPHLAN_BUILD}"
  echo "download_protein_db=${DOWNLOAD_PROTEIN_DB}"
  echo "download_utility_mapping=${DOWNLOAD_UTILITY_MAPPING}"
  echo "uniref=${UNIREF}"
  echo
  du -sh "${DB_ROOT}"/* 2>/dev/null || true
} | tee "${DB_ROOT}/DB_INVENTORY.txt"

echo "== Done =="
