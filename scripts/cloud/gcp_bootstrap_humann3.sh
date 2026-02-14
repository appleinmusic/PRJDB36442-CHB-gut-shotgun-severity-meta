#!/usr/bin/env bash
set -euo pipefail

# Bootstrap HUMAnN3 environment on a running GCP VM.
# Assumes Miniforge is already installed (see gcp_bootstrap_hbv_gut.sh).

if [[ "${EUID}" -eq 0 ]]; then
  echo "Please run as a non-root user (it uses sudo for system packages)." >&2
  exit 1
fi

if [[ ! -d "${HOME}/miniforge3" ]]; then
  echo "Missing Miniforge at ${HOME}/miniforge3. Run scripts/cloud/gcp_bootstrap_hbv_gut.sh first." >&2
  exit 2
fi

source "${HOME}/miniforge3/etc/profile.d/conda.sh"
conda config --set channel_priority strict
conda config --add channels conda-forge >/dev/null 2>&1 || true
conda config --add channels bioconda >/dev/null 2>&1 || true

ENV_NAME="${ENV_NAME:-hbv-gut-humann}"
PY_VER="${PY_VER:-3.12}"
HUMANN_VER="${HUMANN_VER:-3.9}"

echo "== Conda env: ${ENV_NAME} =="
if conda env list | grep -E "^${ENV_NAME}[[:space:]]" >/dev/null 2>&1; then
  echo "Env exists: ${ENV_NAME}"
else
  conda create -y -n "${ENV_NAME}" -c conda-forge -c bioconda --strict-channel-priority \
    "python=${PY_VER}" "humann=${HUMANN_VER}"
fi

echo "== Versions =="
conda run -n "${ENV_NAME}" humann --version
conda run -n "${ENV_NAME}" python -V
conda run -n "${ENV_NAME}" bowtie2 --version | head -n 1 || true
conda run -n "${ENV_NAME}" diamond version | head -n 2 || true

echo "== Done =="
