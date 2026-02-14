# Depletion of fermentation-linked functional potential correlates with biopsy-confirmed histological damage in chronic hepatitis B: a transparent reanalysis of a shotgun metagenomic cohort

## Title page (for completion at submission)

**Running title:** CHB histology severity and gut metagenomic modules  
**Keywords:** chronic hepatitis B; gut microbiome; shotgun metagenomics; HUMAnN; MetaPhlAn; histology; reproducibility

## Abstract

**Background:** The gut–liver axis is increasingly implicated in chronic hepatitis B (CHB), yet most microbiome studies emphasize diagnosis-based contrasts and provide limited insight into microbial functional changes associated with biopsy-confirmed disease severity.

**Methods:** We performed a transparent, function-oriented reanalysis of a public CHB shotgun metagenomics cohort (ENA/DDBJ accession `PRJDB36442`, *n*=20). Histological damage severity was recovered from publicly available metadata and used to stratify samples into mild (**group M**) and significant (**group S**) damage. Taxonomic profiling was performed with MetaPhlAn, and metagenome-inferred functional potential was characterized with HUMAnN. We focused on pre-specified, gut–liver-axis-relevant modules of fermentation-linked potential (including acetate and lactate/succinate-related pathways), tryptophan/indole metabolism, and bile acid transformation. Findings were further examined using direction-of-effect triangulation with an independent HBV-related cirrhosis cohort.

**Results:** Compared with group M (9/20), group S (11/20) showed lower microbial diversity (Shannon index, *P*=0.0024). In pre-specified module analysis, acetate and lactate/succinate-associated fermentation modules were lower in group S (median Δ(S−M) −0.00248, *q*=0.059; and −0.00144, *q*=0.083, respectively). While pathway-level associations did not reach conventional FDR thresholds in this small cohort, stratified contribution analyses of top-ranked pathways suggested a shift in microbial drivers, with a larger share of differential signal attributable to *Enterobacteriaceae* (including *Escherichia coli*). Directional triangulation supported partial cross-cohort agreement of fermentation-linked signatures, with 3 of 5 pre-specified modules showing concordant directions of effect between CHB severity and HBV-cirrhosis.

**Conclusions:** Greater histological damage in CHB is associated with lower microbial diversity and a suggestive depletion of fermentation-linked functional potential. By emphasizing transparent phenotype recovery and pre-specified, mechanism-consistent modules, this study provides a reproducible starting point for future validation of microbiome-derived markers of CHB severity.

## Introduction

Chronic hepatitis B (CHB) remains a major global cause of progressive liver injury. The gut microbiome has been implicated as a modulator of hepatic immune tone, with microbial metabolites and microbe-associated molecular patterns (MAMPs) reaching the liver via the portal circulation and potentially shaping necroinflammatory activity.

However, the current CHB microbiome literature is dominated by broad case–control surveys that often lack the functional resolution and granular clinical stratification needed to track disease progression. Furthermore, the value of public metagenomic datasets is frequently hampered by the lack of explicit links between sequencing runs and analysis-ready clinical phenotypes. 

In this study, we addressed these gaps by reanalyzing a public CHB shotgun dataset anchored to biopsy-derived severity labels. We prioritized a small set of pre-specified, gut–liver-axis-relevant functional modules—particularly fermentation-linked potential and tryptophan metabolism—to improve interpretability while limiting post hoc feature selection. We further framed external evidence as directional triangulation rather than strict replication, aiming to identify functional signatures that plausibly track with the spectrum of HBV-related liver damage.

## Methods

### Study design and data integration
This study is an integrated secondary analysis of publicly available shotgun metagenomes deposited under ENA/DDBJ accession `PRJDB36442` (linked to NGDC BioProject `PRJCA037061`). To ensure clinical relevance, we performed a systematic recovery of histological phenotypes from public records, enabling a direct link between microbial profiles and liver injury severity.

### Phenotype recovery and stratification
Samples were stratified into two groups based on biopsy-derived histological damage: **group M** (mild damage) and **group S** (significant damage). The mapping between sequencing accessions and clinical labels was derived from publicly available records and preserved in the project repository to support transparency and reproducibility.

### Taxonomic and functional profiling
Taxonomic profiling was performed using MetaPhlAn, with Shannon diversity computed at the species level. Metagenome-inferred functional potential was characterized using HUMAnN to generate pathway abundance tables. Analyses focused on unstratified pathway features, excluding `UNMAPPED` and `UNINTEGRATED`. To reduce sensitivity to sequencing depth, pathway abundances were normalized to relative proportions within each sample.

### Mechanism-oriented functional modules
To enhance biological interpretability, we defined metabolic modules *a priori* as fixed sets of pathways capturing fermentation-linked potential (acetate and lactate/succinate-associated pathways), tryptophan/indole metabolism, and bile acid transformation. Module scores were computed per sample as the sum of member pathway relative abundances. We additionally evaluated robustness to alternative module definitions (conservative vs expanded membership).

### Statistical analysis and external triangulation
Differences between groups were evaluated using two-sided Mann–Whitney U tests. We controlled for multiple testing within feature families using the Benjamini–Hochberg false discovery rate (FDR). Given the cohort size (*n*=20), bootstrap confidence intervals (5,000 resamples) were used to quantify uncertainty in median deltas. For external triangulation, we compared the direction of effect against an independent HBV-related cirrhosis cohort (LC vs healthy). Concordance was defined as agreement in the sign of the median delta between CHB severity (S−M) and the external cirrhosis comparison.

## Results

### Significant liver damage is linked to microbial diversity loss
Group S exhibited lower Shannon diversity than group M (median 3.16 vs 3.79; *P*=0.0024; Fig. 1), consistent with a contraction in within-sample diversity with more severe histological damage.

### Depletion of fermentation-linked potential in severe CHB
In pre-specified module analysis, modules associated with acetate and lactate/succinate fermentation were lower in group S (median Δ(S−M) −0.00248, *q*=0.059; and −0.00144, *q*=0.083, respectively; Fig. 2). These directions were preserved under alternative module definitions, supporting robustness of the directional signal in this cohort.

### Shifting taxonomic drivers of selected pathways
While pathway-level testing did not yield FDR-significant features, exploratory ranking highlighted amino-acid biosynthesis and membrane lipid-related pathways among the top signals. Stratified contribution summaries for selected pathways suggested that the taxonomic sources of these signals differed between groups, with a larger share attributable to *Enterobacteriaceae* (including *Escherichia coli*) in group S (Fig. 3).

### Cross-cohort consistency supports partial directional concordance
Triangulation with an independent HBV-cirrhosis cohort showed partial directional concordance. Three of the five pre-specified modules showed the same direction of effect in both CHB severity and cirrhosis progression, including the depletion of fermentation-linked modules (Fig. 4). Overall, 54% of pathways exhibited directional concordance, rising to 62% among pathways significant in the external cohort.

## Discussion

By re-evaluating a biopsy-labeled CHB cohort through a transparent and function-oriented lens, we identified associations between histological damage severity and reduced fermentation-linked functional potential. Unlike broad case–control studies, an intra-disease histology contrast offers a more direct view of microbial shifts that may accompany hepatic necroinflammation.

The observed depletion of fermentation-linked modules is biologically plausible in the gut–liver axis context. SCFAs contribute to epithelial barrier maintenance and immune modulation; reduced fermentation potential may therefore coincide with increased exposure to pro-inflammatory microbial products. Notably, the stratified contribution patterns in severe cases suggested a larger share attributable to *Enterobacteriaceae*, consistent with a shift toward taxa often enriched in inflammatory states. Because these inferences are based on metagenome-derived functional potential rather than metabolite measurements, mechanistic claims should be tested in cohorts with paired metabolomics and clinical covariates.

While this cohort is small and lacks detailed covariates, the observed direction-of-effect agreement across independent HBV-related cohorts suggests that fermentation-linked signatures merit further study. These results also underscore the value—and the limitations—of public metagenomic reanalysis when phenotype provenance is explicit and interpretability is prioritized through pre-specification.

## Conclusions

In a biopsy-stratified CHB cohort, greater histological damage is associated with reduced microbial diversity and a depletion of fermentation-linked functional modules. This study provides a reproducible foundation for future prospective work aimed at validating the gut microbiome as a non-invasive indicator of disease progression in chronic hepatitis B.

## Declarations

**Ethics approval and consent:** Not applicable (secondary analysis of public, de-identified data).  
**Availability of data and materials:** Raw sequencing data are available from ENA/DDBJ (`PRJDB36442`) and NGDC (`PRJCA037061`). Analysis scripts, module definitions, and figure-generation code are available in the associated repository.  
**Competing interests:** The authors declare no competing interests.  
**Funding:** [to be completed].  
**Author contributions:** [to be completed].  
