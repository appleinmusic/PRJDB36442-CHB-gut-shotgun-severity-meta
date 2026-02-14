#!/usr/bin/env bash
set -euo pipefail

# Fetch the PMC OA package for the Frontiers Genetics HBV-LC article and extract Table 1 as Excel.
#
# Outputs:
#   results/external/Frontiers_HBVLC_Table1.xlsx
#
# Source (PMC OA record):
#   https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC12404923

OUT="results/external/Frontiers_HBVLC_Table1.xlsx"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

mkdir -p "$(dirname "${OUT}")"

TARBALL_URL="https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/b4/f2/PMC12404923.tar.gz"
TARBALL="${TMP_DIR}/PMC12404923.tar.gz"

curl -fL --retry 10 --retry-all-errors --retry-delay 2 -o "${TARBALL}" "${TARBALL_URL}"
tar -xzf "${TARBALL}" -C "${TMP_DIR}"

# Find the Table 1 xlsx inside the extracted package.
TABLE="$(find "${TMP_DIR}" -type f -iname '*table*1*.xlsx' -o -type f -iname 'table1.xlsx' | head -n 1 || true)"
if [[ -z "${TABLE}" ]]; then
  echo "ERROR: could not locate a Table 1 .xlsx in the PMC OA package." >&2
  echo "Inspect extracted files under: ${TMP_DIR}" >&2
  exit 1
fi

cp -f "${TABLE}" "${OUT}"
echo "${OUT}"

