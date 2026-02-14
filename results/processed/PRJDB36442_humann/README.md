# PRJDB36442 HUMAnN outputs (M vs S analysis)

## Contents
- `merged_genefamilies.tsv.gz`: HUMAnN gene family table (merged across samples)
- `merged_pathabundance.tsv.gz`: pathway abundance (merged)
- `merged_pathcoverage.tsv.gz`: pathway coverage (merged)
- `PRJDB36442_logs_slim_20260208T061929Z.tar.gz`: audit bundle (progress table, per-sample logs, OK/FAIL markers, batch log)

## Provenance
- Cohort: PRJDB36442 (CHB gut shotgun)
- Samples: DRR764581–DRR764600 (20 runs)
- Processing: HUMAnN v3.9 (nucleotide search; translated search bypassed)
- Grouping: histology severity M vs S (see `results/feasibility/PRJDB36442_run_groups.tsv`)

## Reproducibility notes
- The audit bundle captures the end-to-end batch log and per-sample HUMAnN logs.
- Merged tables were generated from the per-sample outputs using `humann_join_tables`.
- This directory is the canonical location for downstream analysis notebooks.
