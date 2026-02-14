#!/usr/bin/env bash
set -euo pipefail

# Work around local gcloud Python issues on macOS (CLOUDSDK_PYTHON may point to a broken venv).
: "${CLOUDSDK_PYTHON:=/usr/bin/python3}"
export CLOUDSDK_PYTHON

INSTANCE="${INSTANCE:-hbv-gut-shotgun-1}"
ZONE="${ZONE:-us-west1-c}"

gcloud compute ssh "${INSTANCE}" --zone "${ZONE}" --command "bash -s" <<'BASH'
set -euo pipefail

echo "== TIME =="; date -Is
echo
echo "== progress.tsv (tail) =="
tail -n 30 ~/hbv_gut/results/humann/PRJDB36442/progress.tsv 2>/dev/null || echo "(no progress.tsv yet)"
echo
echo "== humann DB download status =="
if [[ -f ~/humann_dbs/DB_INVENTORY.txt ]]; then
  echo "DB_INVENTORY=present"
  tail -n 20 ~/humann_dbs/DB_INVENTORY.txt || true
else
  echo "DB_INVENTORY=missing"
fi
if [[ -f ~/humann_dbs/full_chocophlan.v201901_v31.tar.gz ]]; then
  ls -lh ~/humann_dbs/full_chocophlan.v201901_v31.tar.gz || true
fi
echo
echo "== outputs (.OK markers) =="
if [[ -d ~/hbv_gut/results/humann/PRJDB36442 ]]; then
  ok_markers="$(find ~/hbv_gut/results/humann/PRJDB36442 -maxdepth 1 -type f -name '*.OK' 2>/dev/null | wc -l | tr -d '[:space:]')"
else
  ok_markers="0"
fi
echo "ok_markers=${ok_markers}"
echo
echo "== running =="
ps aux | grep -E 'humann([[:space:]]|$)|diamond([[:space:]]|$)|bowtie2-align' | grep -v grep | head -n 8 || true
echo
echo "== disk =="
df -h ~ | sed -n "1,2p"
BASH
