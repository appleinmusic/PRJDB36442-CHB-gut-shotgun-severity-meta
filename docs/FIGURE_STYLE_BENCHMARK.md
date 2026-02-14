# Figure Style Benchmark (2024-2026 reconnaissance)

> **Purpose**: anchor each planned figure type to ≥ 3 recent high-quality exemplars.
> Reviewed 2026-02-14; covers Nature/Nat Comms/Microbiome/Frontiers 2024-2026.

## Planned main figure types

| Type | Figure(s) | Core visual |
|------|-----------|-------------|
| 1. Study design + CONSORT-style audit | Figure 1, FigureS1 | Alluvial / Sankey flow + summary lollipop |
| 2. Distribution + raw points + effect size | Figure 1 (panels), Figure 2a | Raincloud (half-violin + swarm + box median) |
| 3. Effect size forest / point-range | Figure 2b, Figure 4a | Forest with CI bars, n/ESS annotation |
| 4. Pathway landscape overview | Figure 3 | Enhanced volcano + heatmap with clustered rows |
| 5. Cross-cohort concordance | Figure 4 | Paired-dot (dumbbell) + quadrant scatter |
| 6. Evidence-chain / triangulation | Figure 5 | Bridge plot + driver bar + logic matrix + workflow |

---

## Exemplar set

### Type 1: Study design + audit trace
| Exemplar | Identifier | Style notes to adopt |
|---|---|---|
| Nature Research Figure Guide 2025 | URL: https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/ | Panel hierarchy clear; vector-first export; no embedded legends. |
| CONSORT 2010 flow diagram standard | DOI: 10.1136/bmj.c332 | Structured left-to-right alluvial with sample counts at each stage. |
| Microbiome integrated meta-omics (2025) | DOI: 10.1186/s40168-025-02291-8 | Registry→processing→results chain in a single board row; pipeline steps as labelled nodes. |
| Nat Comms gut-liver axis multi-omics (2025) | DOI: 10.1038/s41467-025-64914-w | Cohort overview panels adjacent to first-pass QC; consistent palette from first figure onward. |

### Type 2: Distribution + raw points
| Exemplar | Identifier | Style notes to adopt |
|---|---|---|
| Jambor HK "Nature Cell Biology" editorial (2025) | DOI: 10.1038/s41556-025-01684-z | Replace bars with distributions; show individual data points for n < 50. |
| Frontiers Genetics HBV-LC study (2025) | DOI: 10.3389/fgene.2025.1619911 | In multi-group microbiome contrasts, raw spread + group overlap visible; raincloud preferred. |
| Microbiome integrated meta-omics (2025) | DOI: 10.1186/s40168-025-02291-8 | High-information panels: sample-level distributions + median + IQR markers; n annotated per group. |
| Allen et al. Nature 2024 (raincloud reference) | DOI: 10.1038/s41593-024-01624-4 | Half-violin + jittered points + miniature boxplot; compact vertical encoding. |

### Type 3: Effect size + uncertainty (forest / point-range)
| Exemplar | Identifier | Style notes to adopt |
|---|---|---|
| Nature Research Figure Guide 2025 | URL: https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/ | Point-range/forest for interpretable magnitude; zero-reference dashed line. |
| Jambor HK 2025 | DOI: 10.1038/s41556-025-01684-z | Pair effect magnitude with uncertainty, not significance-only symbols. |
| Nat Comms gut metagenome study (2025) | DOI: 10.1038/s41467-025-64914-w | Cross-cohort effect summaries reveal heterogeneity; annotate n/ESS per row. |

### Type 4: Pathway landscape (volcano + heatmap + drivers)
| Exemplar | Identifier | Style notes to adopt |
|---|---|---|
| Frontiers Genetics HBV-LC study (2025) | DOI: 10.3389/fgene.2025.1619911 | Couple pathway overview with biologically interpretable sets; dual-color volcano. |
| Nat Comms gut metagenome study (2025) | DOI: 10.1038/s41467-025-64914-w | High-dimensional panels readable by limiting labels to top-ranked features. |
| Microbiome integrated meta-omics (2025) | DOI: 10.1186/s40168-025-02291-8 | Overview panel + focused mechanism panels within one figure board; dendrogram optional. |
| Qin et al. Nature 2024 (cirrhosis metagenome) | DOI: 10.1038/s41586-024-07531-1 | Row-clustered heatmap with marginal annotation tracks (q-value, direction). |

### Type 5: External concordance (cross-cohort direction)
| Exemplar | Identifier | Style notes to adopt |
|---|---|---|
| Nat Comms gut metagenome study (2025) | DOI: 10.1038/s41467-025-64914-w | Per-cohort effects directly before summary consistency statements; show both concordant/discordant. |
| Microbiome integrated meta-omics (2025) | DOI: 10.1186/s40168-025-02291-8 | Highlight heterogeneity explicitly; do not hide discordant cohorts. |
| Frontiers Genetics HBV-LC study (2025) | DOI: 10.3389/fgene.2025.1619911 | For HBV-related external support, report direction + context limitations clearly. |

### Type 6: Evidence chain / triangulation (Figure 5)
| Exemplar | Identifier | Style notes to adopt |
|---|---|---|
| Bradford-Hill evidence synthesis diagrams (modern redraw) | DOI: 10.1093/ije/dyh313 | Structured criteria grid; each criterion gets explicit pass/fail/NA. |
| Nat Comms multi-omics triangulation (2025) | DOI: 10.1038/s41467-025-64914-w | Layer evidence from multiple sources into a single summary panel; use icons + arrows. |
| Lancet Digital Health TTE workflow (2024) | DOI: 10.1016/S2589-7500(24)00120-4 | Minimalist flow diagram; boxes + arrows with judgment criteria at decision nodes. |

---

## Adoption checklist for this project
- [ ] Raincloud (half-violin + swarm + box) for all within-cohort comparisons.
- [ ] Forest/point-range with CI + n/ESS for all primary effects.
- [ ] Enhanced volcano with q-value color threshold (not just p).
- [ ] Paired-dot / dumbbell for cross-cohort concordance.
- [ ] Evidence-chain panels with explicit pass/fail criteria in meta.json.
- [ ] Export every figure in both PDF (vector) and PNG (300 dpi).
- [ ] No embedded "Figure X" titles; panel labels a–d only.
