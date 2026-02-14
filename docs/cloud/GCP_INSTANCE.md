# GCP compute (HBV gut shotgun)

## Instance

Keep any live instance identifiers and external IP addresses out of Git history.
Store your current values in `docs/cloud/GCP_INSTANCE.local.md` (gitignored).

Template (fill locally):

- Project: `<your-gcp-project>`
- Instance: `<instance-name>`
- Zone: `<zone>`
- External IP: `<external-ip>`

Connect:

```bash
gcloud compute ssh <instance-name> --zone <zone>
```

Stop/start:

```bash
gcloud compute instances stop <instance-name> --zone <zone>
gcloud compute instances start <instance-name> --zone <zone>
```

Delete (irreversible):

```bash
gcloud compute instances delete <instance-name> --zone <zone>
```

## On-VM layout

- MetaPhlAn DB: `~/metaphlan_db/`
- Raw fastq: `~/hbv_gut/data/PRJDB36442/`
- Results: `~/hbv_gut/results/`

## Background jobs

Two detached `tmux` sessions are used for long downloads:

- `metaphlan-db`: downloads/extracts MetaPhlAn DB
- `ena-fastq`: downloads `DRR764597` fastqs
- `prjdb36442-metaphlan`: batch MetaPhlAn for all runs (optional)

Useful commands:

```bash
tmux ls
tmux attach -t metaphlan-db
tmux attach -t ena-fastq
```
