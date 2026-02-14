#!/usr/bin/env bash
set -euo pipefail

ACC="${1:-CRA023641}"
OUT="${2:-data/metadata/ngdc/${ACC}.xlsx}"

mkdir -p "$(dirname "${OUT}")"

url="https://ngdc.cncb.ac.cn/gsa/file/exportExcelFile"

tmp="${OUT}.download"
curl -fL --retry 10 --retry-all-errors --retry-delay 2 \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data "type=3&dlAcession=${ACC}" \
  -o "${tmp}" \
  "${url}"

mv -f "${tmp}" "${OUT}"
echo "${OUT}"
