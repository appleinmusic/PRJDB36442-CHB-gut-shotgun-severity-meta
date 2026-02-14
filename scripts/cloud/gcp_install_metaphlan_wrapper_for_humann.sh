#!/usr/bin/env bash
set -euo pipefail

# Work around local gcloud Python issues on macOS (CLOUDSDK_PYTHON may point to a broken venv).
: "${CLOUDSDK_PYTHON:=/usr/bin/python3}"
export CLOUDSDK_PYTHON

INSTANCE="${INSTANCE:-hbv-gut-shotgun-1}"
ZONE="${ZONE:-us-west1-c}"

REMOTE_DIR="${REMOTE_DIR:-~/humann_bin}"
WRAPPER_LOCAL="${WRAPPER_LOCAL:-scripts/cloud/metaphlan_wrapper_for_humann.sh}"

if [[ ! -f "${WRAPPER_LOCAL}" ]]; then
  echo "Missing wrapper: ${WRAPPER_LOCAL}" >&2
  exit 2
fi

chmod +x "${WRAPPER_LOCAL}"

gcloud compute ssh "${INSTANCE}" --zone "${ZONE}" --command "bash -lc 'set -euo pipefail; mkdir -p ${REMOTE_DIR}'"
gcloud compute scp --zone "${ZONE}" "${WRAPPER_LOCAL}" "${INSTANCE}":${REMOTE_DIR}/metaphlan
gcloud compute ssh "${INSTANCE}" --zone "${ZONE}" --command "bash -lc 'set -euo pipefail; chmod +x ${REMOTE_DIR}/metaphlan; ${REMOTE_DIR}/metaphlan --version'"

echo "Installed: ${INSTANCE}:${REMOTE_DIR}/metaphlan"

