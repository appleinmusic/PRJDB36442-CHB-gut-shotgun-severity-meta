#!/usr/bin/env bash
set -euo pipefail

DB_URL_BASE="http://cmprod1.cibio.unitn.it/biobakery4/metaphlan_databases/bowtie2_indexes"
TAR_NAME="mpa_vJan25_CHOCOPhlAnSGB_202503_bt2.tar"
MD5_NAME="${TAR_NAME%.tar}.md5"

DB_DIR="${1:-$HOME/metaphlan_db}"
mkdir -p "${DB_DIR}"

echo "DB_DIR=${DB_DIR}"
cd "${DB_DIR}"

echo "== Fetch expected MD5 =="
curl -fsSL "${DB_URL_BASE}/${MD5_NAME}" -o "${MD5_NAME}"
expected="$(awk '{print $1}' "${MD5_NAME}")"
if [[ -z "${expected}" ]]; then
  echo "Failed to parse expected MD5 from ${MD5_NAME}" >&2
  exit 2
fi
echo "expected_md5=${expected}"

echo "== Download tar (resume-capable) =="
curl -fL --retry 20 --retry-all-errors --retry-delay 10 --continue-at - \
  -o "${TAR_NAME}.download" "${DB_URL_BASE}/${TAR_NAME}"

echo "== Verify MD5 =="
got="$(md5sum "${TAR_NAME}.download" | awk '{print $1}')"
echo "got_md5=${got}"
if [[ "${got}" != "${expected}" ]]; then
  echo "MD5 mismatch. Keep ${TAR_NAME}.download for inspection/retry." >&2
  exit 3
fi

mv -f "${TAR_NAME}.download" "${TAR_NAME}"

echo "== Extract =="
tar -xf "${TAR_NAME}"

index_base="${TAR_NAME%_bt2.tar}"
echo "${index_base}" > mpa_latest

echo "== Smoke test (files) =="
ls -lah mpa_latest "${MD5_NAME}" "${TAR_NAME}" | sed -n '1,10p'
ls -1 | grep -E "^${index_base}\\..*bt2" | head -n 5 || true

echo "== Done =="
