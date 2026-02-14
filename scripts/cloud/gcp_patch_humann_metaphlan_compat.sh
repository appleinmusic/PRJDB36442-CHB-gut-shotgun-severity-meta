#!/usr/bin/env bash
set -euo pipefail

# Patch HUMAnN on the VM for MetaPhlAn CLI compatibility with this project.
#
# Why:
# - HUMAnN v3.9 prescreen calls MetaPhlAn with `--bowtie2out`, but the MetaPhlAn CLI inside our
#   hbv-gut-humann env expects `--mapout`.
# - HUMAnN also validates MetaPhlAn database header markers and only accepts v3 or vJun23; our
#   MetaPhlAn runs use `mpa_vJan25_CHOCOPhlAnSGB_202503`, so we allow `vJan25` for this run.
#
# This is intentionally scripted + backed up for auditability.

# Work around local gcloud Python issues on macOS (CLOUDSDK_PYTHON may point to a broken venv).
: "${CLOUDSDK_PYTHON:=/usr/bin/python3}"
export CLOUDSDK_PYTHON

INSTANCE="${INSTANCE:-hbv-gut-shotgun-1}"
ZONE="${ZONE:-us-west1-c}"
ENV_NAME="${ENV_NAME:-hbv-gut-humann}"

gcloud compute ssh "${INSTANCE}" --zone "${ZONE}" --command "bash -s" <<'BASH'
set -euo pipefail

ENV_NAME="${ENV_NAME:-hbv-gut-humann}"
ROOT="${HOME}/miniforge3/envs/${ENV_NAME}/lib/python3.12/site-packages/humann"
PRESCREEN="${ROOT}/search/prescreen.py"
CFG="${ROOT}/config.py"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
AUDIT_DIR="${HOME}/hbv_gut/results/humann/audit/patches/${TS}_humann_metaphlan_compat"
mkdir -p "${AUDIT_DIR}"

echo "AUDIT_DIR=${AUDIT_DIR}"

cp -f "${PRESCREEN}" "${AUDIT_DIR}/prescreen.py.before"
cp -f "${CFG}" "${AUDIT_DIR}/config.py.before"

python3 - <<'PY'
from pathlib import Path

prescreen = Path("/home/simanan/miniforge3/envs/hbv-gut-humann/lib/python3.12/site-packages/humann/search/prescreen.py")
cfg = Path("/home/simanan/miniforge3/envs/hbv-gut-humann/lib/python3.12/site-packages/humann/config.py")

text = prescreen.read_text()
if "--bowtie2out" not in text:
    raise SystemExit("Expected --bowtie2out not found in prescreen.py")
text = text.replace("--bowtie2out", "--mapout")
prescreen.write_text(text)

cfg_text = cfg.read_text()
old = 'metaphlan_v4_db_version="vJun23"'
new = 'metaphlan_v4_db_version="vJan25"'
if old in cfg_text:
    cfg_text = cfg_text.replace(old, new, 1)
cfg.write_text(cfg_text)
print("patched")
PY

cp -f "${PRESCREEN}" "${AUDIT_DIR}/prescreen.py.after"
cp -f "${CFG}" "${AUDIT_DIR}/config.py.after"

echo "== diff prescreen.py (snippet) =="
diff -u "${AUDIT_DIR}/prescreen.py.before" "${AUDIT_DIR}/prescreen.py.after" | sed -n '1,120p' || true
echo
echo "== diff config.py (snippet) =="
diff -u "${AUDIT_DIR}/config.py.before" "${AUDIT_DIR}/config.py.after" | sed -n '1,120p' || true

echo
echo "== sanity: metaphlan help flags =="
source "${HOME}/miniforge3/etc/profile.d/conda.sh"
conda run -n "${ENV_NAME}" metaphlan --help 2>&1 | head -n 6

echo
echo "== sanity: humann version =="
conda run -n "${ENV_NAME}" humann --version
BASH

echo "Patched HUMAnN MetaPhlAn compatibility on ${INSTANCE} (${ZONE})."

