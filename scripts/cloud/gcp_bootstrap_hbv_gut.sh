#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -eq 0 ]]; then
  echo "Please run as a non-root user (it uses sudo for system packages)." >&2
  exit 1
fi

echo "== System packages =="
sudo apt-get update -y
sudo apt-get install -y --no-install-recommends \
  curl wget ca-certificates bzip2 tar pigz tmux git build-essential unzip htop

echo "== SSH hardening (no password auth) =="
if [[ -f /etc/ssh/sshd_config ]]; then
  sudo sed -i.bak -E 's/^#?PasswordAuthentication\s+.*/PasswordAuthentication no/' /etc/ssh/sshd_config || true
  sudo sed -i -E 's/^#?PermitRootLogin\s+.*/PermitRootLogin no/' /etc/ssh/sshd_config || true
  sudo systemctl restart ssh 2>/dev/null || sudo systemctl restart sshd 2>/dev/null || true
fi

echo "== Miniforge =="
if [[ -d "${HOME}/miniforge3" ]]; then
  echo "Found: ${HOME}/miniforge3"
else
  arch="$(uname -m)"
  if [[ "${arch}" != "x86_64" ]]; then
    echo "Unsupported arch: ${arch}" >&2
    exit 1
  fi
  installer="Miniforge3-Linux-x86_64.sh"
  url="https://github.com/conda-forge/miniforge/releases/latest/download/${installer}"
  curl -fsSL "${url}" -o "/tmp/${installer}"
  bash "/tmp/${installer}" -b -p "${HOME}/miniforge3"
fi

source "${HOME}/miniforge3/etc/profile.d/conda.sh"
conda config --set channel_priority strict
conda config --add channels conda-forge >/dev/null 2>&1 || true
conda config --add channels bioconda >/dev/null 2>&1 || true

echo "== Conda env: hbv-gut-shotgun =="
if conda env list | grep -E '^hbv-gut-shotgun[[:space:]]' >/dev/null 2>&1; then
  echo "Env exists."
else
  conda create -y -n hbv-gut-shotgun -c conda-forge -c bioconda --strict-channel-priority \
    python=3.10 metaphlan=4.0.6
fi

conda run -n hbv-gut-shotgun metaphlan --version

echo "== Done =="
