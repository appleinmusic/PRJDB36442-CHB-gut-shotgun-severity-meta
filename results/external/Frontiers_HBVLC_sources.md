# External validation source (HBV-LC vs HC)

## Source file (download on demand)
The original Table 1 Excel file is **not** committed to this repository. It can be reproduced by downloading the
PMC OA package and extracting it (see links below). A helper script is provided:

- `bash scripts/external/fetch_frontiers_hbvlc_table1.sh`

## Source links
- OA API record: https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC12404923
- OA package tarball: https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/b4/f2/PMC12404923.tar.gz
- Article landing page: https://www.frontiersin.org/journals/genetics/articles/10.3389/fgene.2025.1619911/full

## Extraction note
The table was previously extracted from the PMC OA package tarball on 2026-02-08 (UTC). This repo stores only
the derived, analysis-ready TSVs listed below.

## Derived outputs in this project
- `HBVLC_module_stats_conservative.tsv`
- `HBVLC_module_stats_expanded.tsv`
- `module_direction_validation.tsv`
 - `HBVLC_pathway_stats.tsv`
 - `pathway_direction_validation.tsv`
