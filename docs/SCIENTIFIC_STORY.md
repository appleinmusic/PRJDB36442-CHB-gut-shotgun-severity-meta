# Scientific story (paper-oriented; public-only start)

## Elevator pitch
Most CHB microbiome papers are “CHB vs healthy differential taxa + classifier”. We instead anchor the analysis to a **clinically meaningful, biopsy-derived severity label** and ask: *which microbes and microbial functions track histological damage within CHB, and what mechanism-consistent modules emerge from shotgun data?*

## What we can defend today (public, auditable)
- Primary public cohort: `PRJDB36442` (20 paired-end shotgun metagenomes).
- Per-sample phenotype: NGDC BioSample `Description` contains **`group M` vs `group S`** (mild vs significant histological damage).
- Reproducibility baseline: per-FASTQ URL/size/MD5 manifest + deterministic commands + cloud run logs.

This is a deliberately conservative starting point: we only claim what can be traced **per sample**.

## Core hypothesis (operational)
Within CHB, the transition from mild to significant histological damage is accompanied by:
1) a **shift in community structure** (species-level) that is reproducible under compositional/statistical robustness checks; and
2) a **coherent functional signal** consistent with gut–liver axis biology (bile acid transformation, endotoxin-related features, tryptophan/indole metabolism), rather than a disconnected “top taxa list”.

## Story arc (how the results will read)
1) **Data credibility first**: show the phenotype provenance and an audit trail from registry → run → FASTQ checksums → tool versions.
2) **Severity-linked taxa (not diagnosis)**: identify taxa associated with `group S` vs `group M` with effect sizes, uncertainty, and sensitivity analyses (depth, rare taxa, alternative transforms).
3) **From taxa to modules**: map taxa shifts to functionally interpretable modules (starting from MetaPhlAn taxonomy; expanding to functional profiling when feasible).
4) **Mechanism-consistent triangulation**: connect modules to known bile-acid / inflammatory pathways using external literature and, when possible, external cohorts (even if not HBV-specific) for directionality checks.
5) **Actionable output**: produce a short list of candidate microbes/modules ranked by robustness + mechanistic plausibility, plus what data would falsify each claim.

## How this differs from “rejected套路”
- **Phenotype is not generic**: we start with biopsy-derived histological severity (`group M/S`) rather than CHB vs healthy.
- **Auditability is built-in**: we can hand reviewers a manifest with URLs + MD5 and a cloud script that reproduces the exact per-sample outputs.
- **Claims are constrained**: no pretending we adjusted for covariates we do not have; we explicitly separate “can conclude now” vs “needs author/controlled metadata”.
- **Mechanism is not a paragraph at the end**: module-level outputs are planned as first-class results, with pre-specified sensitivity checks.

## Known limitations (and how we handle them)
- `PRJDB36442` provides **coarse severity** (`M/S`) and limited covariates publicly.
  - Mitigation: treat it as an internally valid severity-linked cohort; pursue additional metadata (supplementary, author, controlled access) and plan external triangulation rather than overclaiming.
- Single cohort, modest n.
  - Mitigation: (i) emphasize effect sizes + uncertainty; (ii) avoid overfit classifiers; (iii) external checks in adjacent liver-disease shotgun cohorts for mechanistic modules.

