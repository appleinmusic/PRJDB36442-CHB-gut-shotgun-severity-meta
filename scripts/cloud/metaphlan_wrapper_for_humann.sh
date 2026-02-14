#!/usr/bin/env bash
set -euo pipefail

# HUMAnN uses MetaPhlAn for prescreen and also calls `metaphlan --version` to enforce a minimum version.
# Some MetaPhlAn installs emit non-version lines after `--version` (e.g., database warnings), and HUMAnN
# parses the *last* line as the version string. This wrapper guarantees the version line is last.
#
# Install on the VM as: ~/humann_bin/metaphlan (name MUST be `metaphlan` for HUMAnN to resolve it).
#
# The real MetaPhlAn binary can be overridden with REAL_METAPHLAN, but we default to the working
# hbv-gut-shotgun env path used in this project.

REAL_METAPHLAN="${REAL_METAPHLAN:-/home/simanan/miniforge3/envs/hbv-gut-shotgun/bin/metaphlan}"

if [[ "${1:-}" == "--version" ]]; then
  out="$("${REAL_METAPHLAN}" --version 2>&1 || true)"
  printf '%s\n' "${out}" | awk '/MetaPhlAn version/{print; found=1; exit} END{if(!found){exit 1}}'
  exit 0
fi

exec "${REAL_METAPHLAN}" "$@"

