# Plot Style Guide (PRJDB36442 submission figures)

> Canonical visual specification for **meta** (PRJDB36442 CHB severity manuscript).
> Updated 2026-02-14.

## 1) Scope
Applies to all main and supplementary figures for **meta** (Figures 1–5 + FigureS1).

## 2) Core principles
- Show raw sample-level evidence whenever possible (points/distributions, not bars alone).
- Report **effect size + uncertainty** together for primary claims.
- Keep panel logic monotonic: cohort → primary effect → mechanistic support → external validation.
- Use color only for biological meaning (group/direction), not decoration.
- No "Figure X" titles or full legends inside figures; panel labels `a`, `b`, `c`, `d` only.
- Distinguish **discovery** (exploratory) from **validation** (replication) in panel titles/annotations.

## 3) Typography
| Property | Value |
|---|---|
| Font family | `Arial` (fallback: `Helvetica`, `DejaVu Sans`) |
| Panel label | **bold**, 14 pt, lowercase `a b c d`, positioned top-left outside plot area |
| Axis title | 9–10 pt, sentence case |
| Axis tick labels | 8 pt minimum at final print scale |
| Annotation text | 7–8 pt |
| All text | Editable (Type 42 / TrueType in PDF; `pdf.fonttype=42`) |

## 4) Dimensions & layout
| Target | Width | Height | Notes |
|---|---|---|---|
| Single-column figure | 89 mm (3.5 in) | flexible | Nature/Lancet single-column |
| 1.5-column figure | 120 mm (4.7 in) | flexible | |
| Double-column / full-width | 183 mm (7.2 in) | ≤ 247 mm (9.7 in) | Nature max |
| 4-panel board (2×2) | 183 mm × 183 mm | — | Standard for Figures 2–5 |
| 3-panel row (1×3) | 183 mm × 65 mm | — | Figure 1 |
| Supplementary | flexible | flexible | Same palette/font rules |

## 5) Color palette (color-blind safe, semantic)

### Project-wide semantic colors
| Meaning | Hex | Swatch |
|---|---|---|
| Group M (Mild) | `#4878CF` | 🔵 |
| Group S (Significant) | `#D65F5F` | 🔴 |
| External HC (Healthy control) | `#59A14F` | 🟢 |
| External LC (Liver cirrhosis) | `#B07AA1` | 🟣 |
| Direction match / positive | `#59A14F` | 🟢 |
| Direction mismatch / negative | `#D65F5F` | 🔴 |
| Neutral / non-significant | `#999999` | ⚪ |
| Conservative set | `#4878CF` | 🔵 |
| Expanded set | `#E8853D` | 🟠 |

### Categorical palette (up to 8 categories)
```
#4878CF, #D65F5F, #59A14F, #E8853D, #B07AA1, #76B7B2, #EDC949, #AF7AA1
```
Tableau Colorblind 10 variant — safe for protanopia/deuteranopia/tritanopia.

### Sequential palette for heatmaps
- Diverging: `RdBu_r` (centered at 0) — standard for z-score / log-fold-change
- Sequential: `viridis` (no red-green ambiguity)

## 6) Line weights
| Element | Width (pt) |
|---|---|
| Axes / spines | 0.8 |
| Data lines / curves | 1.2–2.0 |
| Reference / zero lines | 0.8 dashed |
| Threshold lines | 0.7 dotted |
| Error bar caps | 3 pt cap |
| Box / violin outlines | 0.8 |

## 7) Statistical annotation policy
- Main panels show both raw `p` and adjusted `q` where available.
- Primary effect panels show **point estimate + 95% CI** (bootstrap or model-based).
- **n** and/or **ESS** annotated per group on every comparison panel.
- Avoid threshold-only language (no asterisks without accompanying effect size).
- Discovery analyses labelled `exploratory`; validation analyses labelled `replication`.
- Suggestive q values (e.g., q = 0.25) allowed **only** with explicit "exploratory" qualifier.

## 8) Figure-specific visualization rules

### Distribution panels
- **Raincloud plots**: half-violin (kernel density) + jittered swarm points + miniature boxplot (median, IQR).
- Sample size `n=X` annotated below each group.
- Effect size annotation: median difference + bootstrap 95% CI.

### Effect / forest panels
- Horizontal point-range: point = estimate, thick bar = 50% CI, thin bar = 95% CI.
- Zero / null reference as vertical dashed line.
- Each row: feature name (left), q-value + n/ESS (right margin).
- Sort by effect magnitude (ascending or descending, not alphabetic).

### Heatmap panels
- Row-order: hierarchical clustering (Ward linkage) or by effect size.
- Column-order: by group then by sample ID.
- Group annotation bar above heatmap.
- Z-score row-normalized; color bar labelled.
- Limit row labels to top N features (≤ 25) for readability.

### Volcano panels
- X = effect size (delta or log2FC), Y = -log10(p).
- Color: q < FDR threshold → semantic direction color; else neutral grey.
- Label top 8 features by significance; de-clutter with `adjustText`.

### Concordance / bridge panels
- Dumbbell (paired-dot) plot: two points per feature connected by line.
- Line color = direction match/mismatch.
- Annotate q-values on right margin.

## 9) Export rules
| Format | Specs |
|---|---|
| PDF | Vector, fonts embedded (Type 42), `bbox_inches='tight'` |
| PNG | 300 dpi, white background, `bbox_inches='tight'` |
| File naming | `Figure{N}_{ShortTitle}.(pdf\|png)` for main; `FigureS{N}_{ShortTitle}` for supplementary |
| Output dir (meta) | `plots/publication/` |

## 10) Provenance requirements (per figure)
- `{FigureStem}.meta.json` alongside each figure, containing:
  - Input file paths + SHA256 checksums
  - Key columns used
  - Filter / sort rules
  - Statistical parameters (seed, n_boot, alpha, FDR threshold)
  - Software versions (Python, matplotlib, pandas, scipy, numpy)
  - Generation timestamp (UTC ISO 8601)
- `docs/FIGURE_PROVENANCE.tsv` mapping each figure → script → anchor tables.

## 11) Global matplotlib rcParams (applied by all figure scripts)
```python
import matplotlib as mpl
mpl.rcParams.update({
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "axes.grid": False,
    "lines.linewidth": 1.4,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "figure.dpi": 150,
})
```
