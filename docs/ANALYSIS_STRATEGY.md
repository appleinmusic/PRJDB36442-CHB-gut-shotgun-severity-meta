# Analysis strategy (CHB gut shotgun; public-only)

## Goal

Avoid low-novelty “CHB vs healthy differential taxa” and instead target clinically meaningful phenotypes and mechanisms using shotgun metagenomics.

## Primary dataset constraint

Current feasibility scan suggests a single HBV gut shotgun candidate (`PRJDB36442`). This drives the design: maximize internal validity + multiple orthogonal readouts; then validate externally where possible (even if not HBV-specific cohorts).

## Primary questions (within-CHB)

1. **Histological damage stratification (biopsy-derived)**: Which microbial taxa/functions track liver injury severity *within CHB*, not just diagnosis.  
   - In the currently confirmed public dataset (`PRJDB36442`), the available per-sample label is **`group M` vs `group S`** (mild vs significant histological damage; see `docs/metadata/PRJDB36442_phenotypes.md`).
2. **Mechanism-oriented functions**: Are bile acid, SCFA, tryptophan/indole, and LPS-related modules associated with histological damage after adjusting for confounders (as available).
3. **Ecological states**: Are there discrete community states (enterotype-like) linked to severity and specific functional capacities.

## Statistical approach (publishable defaults)

- Prefer **within-cohort modeling** with covariates over binary case-control contrasts.
- Compositionality-aware analyses:
  - CLR/Aitchison geometry for continuous modeling
  - ANCOM-BC2 / ALDEx2-style methods for differential abundance where appropriate
- Multiple testing control: FDR with pre-registered feature families (taxa vs functions vs modules).
- Robustness: sensitivity to read depth, removal of rare taxa, alternative normalizations.

## Outputs that reviewers expect

- A reproducible pipeline with exact database versions, download manifests, and deterministic commands.
- Figures that link features to clinical gradients (not only heatmaps): partial dependence, adjusted effect sizes, calibration.
- External triangulation:
  - If HBV shotgun is single-cohort, validate “fibrosis module” in other liver disease shotgun cohorts; interpret HBV-specificity cautiously.

## Immediate next steps (after HUMAnN finishes)

1. **Fetch merged functional tables (small)**: `merged_pathabundance.tsv.gz`, `merged_genefamilies.tsv.gz`, `merged_pathcoverage.tsv.gz` + batch logs.
2. **Define “mechanism modules” up front** (not post-hoc):
   - bile acid transformation / secondary bile acids
   - tryptophan → indole derivatives
   - SCFA-related carbohydrate fermentation (as proxy)
   - LPS/peptidoglycan biosynthesis / endotoxin-associated pathways
3. **Score modules per sample** from pathway tables (normalize → transform → sum/aggregate with a fixed mapping), then compare `M` vs `S` with effect sizes + uncertainty.
4. **Taxa ↔ function triangulation**:
   - check whether severity-linked taxa plausibly drive the same functional direction (avoid “taxa list + unrelated pathway list”).
5. **One notebook, one script**:
   - Jupyter notebook for exploratory QC + figure drafts.
   - Scripted analysis (deterministic) for final outputs reviewers can reproduce headlessly.

## Stop/pivot criteria

If `PRJDB36442` lacks usable per-sample severity labels beyond `group M/S` (e.g., fibrosis stage, ALT, treatment variables), pivot to:

- multi-cohort **16S** meta-analysis (CHB vs controls + fibrosis where available), or
- shotgun cohorts in adjacent liver phenotypes (cirrhosis/NASH) to establish a method paper before HBV-specific expansion.
