# Cloud scripts (GCP)

These scripts assume you have `gcloud` configured locally and a Ubuntu VM on GCP.

Recommended pattern:

1) Create VM: `scripts/cloud/gcp_create_instance.sh`
2) Bootstrap VM: `scripts/cloud/gcp_bootstrap_hbv_gut.sh`
3) Download MetaPhlAn DB: `scripts/cloud/gcp_download_metaphlan_db.sh` and `scripts/cloud/gcp_download_metaphlan_aux.sh`
4) Submit batch job: `scripts/cloud/gcp_submit_prjdb36442_batch.sh`
5) Check status: `scripts/cloud/gcp_status_prjdb36442.sh`
6) Fetch results: `scripts/cloud/gcp_fetch_prjdb36442_results.sh`
7) Stop VM to save cost: `scripts/cloud/gcp_stop_instance.sh`

All scripts support `INSTANCE` and `ZONE` environment variables.

