#!/usr/bin/env bash
set -euo pipefail

# Work around local gcloud Python issues on macOS (CLOUDSDK_PYTHON may point to a broken venv).
: "${CLOUDSDK_PYTHON:=/usr/bin/python3}"
export CLOUDSDK_PYTHON

INSTANCE="${INSTANCE:-hbv-gut-shotgun-1}"
ZONE="${ZONE:-us-west1-c}"

gcloud compute ssh "${INSTANCE}" --zone "${ZONE}" --command "bash -lc 'set -euo pipefail
echo \"== TIME ==\"; date -Is
echo
echo \"== progress.tsv (tail) ==\"
tail -n 30 ~/hbv_gut/results/metaphlan/PRJDB36442/progress.tsv 2>/dev/null || echo \"(no progress.tsv yet)\"
echo
echo \"== outputs ==\"
ls -1 ~/hbv_gut/results/metaphlan/PRJDB36442/*.metaphlan.tsv 2>/dev/null | wc -l | tr -d \"[:space:]\" | sed \"s/^/metaphlan_tsv=/\"
echo
echo \"== running ==\"
ps aux | grep -E \"metaphlan .*DRR|bowtie2-align\" | grep -v grep | head -n 5 || true
echo
echo \"== disk ==\"
df -h ~ | sed -n \"1,2p\"
'"
