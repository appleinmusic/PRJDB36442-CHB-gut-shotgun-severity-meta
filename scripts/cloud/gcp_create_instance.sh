#!/usr/bin/env bash
set -euo pipefail

# Work around local gcloud Python issues on macOS (CLOUDSDK_PYTHON may point to a broken venv).
: "${CLOUDSDK_PYTHON:=/usr/bin/python3}"
export CLOUDSDK_PYTHON

INSTANCE="${INSTANCE:-hbv-gut-shotgun-1}"
ZONE="${ZONE:-us-west1-c}"
MACHINE_TYPE="${MACHINE_TYPE:-e2-standard-16}"
BOOT_SIZE="${BOOT_SIZE:-300GB}"
BOOT_TYPE="${BOOT_TYPE:-pd-balanced}"

gcloud compute instances create "${INSTANCE}" \
  --zone "${ZONE}" \
  --machine-type "${MACHINE_TYPE}" \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size="${BOOT_SIZE}" \
  --boot-disk-type="${BOOT_TYPE}" \
  --tags=hbv-gut,ssh \
  --labels=purpose=hbv_gut_shotgun

gcloud compute instances describe "${INSTANCE}" \
  --zone "${ZONE}" \
  --format='table(name,zone,machineType.basename(),status,networkInterfaces[0].accessConfigs[0].natIP)'
