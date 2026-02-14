<!--
TEMPLATE (通用科研项目审计) — 建议每个新项目复制后从头执行，不要保留旧项目的勾选状态/报告产物。
本 plan 负责“做什么 + 顺序 + 产物对账”；项目差异（数据集/脚本/手稿/引用来源）通过 inventory + targets.json 适配。
-->

# 🛡️ Project Audit Protocol (Research, Zero-Trust)

**Objective**: 对科研项目进行“证据优先、可复现、可争辩”的地毯式审计：从数据获取/脚本管道到结果表、图板与参考文献，逐条核查，防止后期被质疑学术不端。

**Reviewer Persona**: Zero-Trust Auditor  
**Status**: Completed

> 重要：先读 `conductor/tracks/audit-protocol-v2/audit_rules.md`，并严格执行 Rule 6（Inventory + Coverage Gate）。

## Phase 0: Audit Bootstrap (Scope, Targets, Ground Truth)
*Goal: Prevent wrong-endpoint false negatives and “phantom” claims by defining what must be verified before running checks.*

- [x] **Task 0.0: Generate Inventory (Coverage Gate)**
  - **Script Check**: 运行 inventory 生成全量清单（后续所有逐条审计都必须对账）：
    - `python3 conductor/tracks/audit-protocol-v2/bin/generate_inventory.py`
  - **Output**:
    - `conductor/tracks/audit-protocol-v2/reports/0.0_inventory.json`
    - `conductor/tracks/audit-protocol-v2/reports/0.0_inventory.md`

- [x] **Task 0.1: Identify Project Claims & Critical Artifacts**
  - Read the project’s primary docs (project-dependent): README, any spec/registry/manuscript folders.
  - Extract the **top 10 “manuscript-critical claims”** to audit (dataset IDs, phenotype definitions, N, key effect sizes/AUCs, main figures).
  - **Output**: `conductor/tracks/audit-protocol-v2/reports/0.1_scope_map.md` (claims list + where each claim is stated).

- [x] **Task 0.2: Configure Audit Targets (Datasets / IDs / Keywords)**
  - Update `conductor/tracks/audit-protocol-v2/targets.json` to match the project’s actual dataset IDs and expected concepts.
  - Also configure `entities` checks (tables + organism) so Task 1.2 can run without project-specific hardcoding.
  - Do not rely on “search didn’t find it” as evidence; use canonical accession pages or local metadata.
  - **Output**: `conductor/tracks/audit-protocol-v2/reports/0.2_targets_review.md` (what was added/removed and why).

- [x] **Task 0.3: Define Pass/Fail Semantics for This Audit**
  - Decide (and document) what counts as `BLOCKER` for this specific project type (e.g., wrong dataset ID, phenotype mismatch, leakage, unverifiable DOI).
  - **Output**: `conductor/tracks/audit-protocol-v2/reports/0.3_severity_policy.md`

## Phase 1: Data & Code Forensics (Security & Truth)
*Goal: Ensure data exists, code runs, and biological entities are real.*
*Standard: All checks must adhere to `audit_rules.md`.*

> **Large-file circuit breaker**: For any repo-wide search / secret scan / pattern scan, follow Rule 13 in `audit_rules.md` (limit output, exclude large dirs, write full logs under `reports/`).
> **Figure circuit breaker**: For figure boards, follow Rule 15 in `audit_rules.md` (audit PNG boards; no OCR/base64 dumps; use preview/crop; numbers from `results/tables/*`).

- [x] **Task 1.1: Source Data Verification (Double Checked)**
  - **Script Check**: Run `python3 conductor/tracks/audit-protocol-v2/bin/verify_datasets.py --targets conductor/tracks/audit-protocol-v2/targets.json --out conductor/tracks/audit-protocol-v2/reports/1.1_data_verification_report.md`.
  - **Agent Check（强制双重验证；每条必做）**: 对 `targets.json` 的**每个** dataset 都必须执行：
    - `google_search`（ID + claimed phenotype/trait）→ 选择官方页面 → `jina_reader` 抓取标题/trait/摘要片段
    - 若在线失败：按 Rule 1B 用本地权威元数据做 offline-evidence，否则 INCONCLUSIVE
  - **Coverage Gate**: `targets.json` 的每个 dataset 必须在表格中逐条出现（允许 INCONCLUSIVE，但不允许缺失条目）。
  - **Output**: `conductor/tracks/audit-protocol-v2/reports/1.1_data_verification_report.md`.

- [x] **Task 1.2: Biological Entity Sanity Check (Double Checked)**
  - **Script Check**: Run `python3 conductor/tracks/audit-protocol-v2/bin/verify_entities.py --targets conductor/tracks/audit-protocol-v2/targets.json --out conductor/tracks/audit-protocol-v2/reports/1.2_entity_validation.log` (or pass explicit `--check` entries).
  - **Agent Check**: `google_search` top 5 DEGs to confirm biological plausibility (Tissue/Disease context).
  - **Coverage Gate**: `targets.json` 的每个 entities 检查必须输出对应记录。
  - **Output**: `conductor/tracks/audit-protocol-v2/reports/1.2_entity_validation.log`

- [x] **Task 1.3: Reproducibility Sandbox Test**
  - Attempt to run the full pipeline (`scripts/`) in a clean environment.
  - Detect hardcoded paths, missing dependencies, or non-deterministic logic.
  - Also verify registry/traceability if the project provides a registry/validator (optional).
  - *Output*: `conductor/tracks/audit-protocol-v2/reports/1.3_reproducibility_error_log.md`

## Phase 2: Methodological Rigor (Statistics & Logic)
*Goal: Prevent P-hacking, data leakage, and statistical flaws.*

- [x] **Task 2.1: Statistical Audit**
  - Review `scripts/02_transcriptomics/*.R` for correct FDR/Benjamini-Hochberg application.
  - Check `meta-analysis` weights and heterogeneity handling.
  - *Output*: `conductor/tracks/audit-protocol-v2/reports/2.1_stats_audit.md`

- [x] **Task 2.2: ML Leakage Detection**
  - Inspect `scripts/03_ml_biomarkers/` for Feature Selection vs. Cross-Validation order.
  - Ensure test set is strictly isolated.
  - *Output*: `conductor/tracks/audit-protocol-v2/reports/2.2_ml_leakage_check.md`

- [x] **Task 2.3: Visual Consistency Check**
  - **全量图板审计（强制）**: Audit `figures/final_figures/` for visual/data consistency.
  - *Output*: `conductor/tracks/audit-protocol-v2/reports/2.3_figure_reproduction.md`

- [x] **Task 2.4: MR Analysis Audit (Double Checked)**
  - **Script Check**: Verify GWAS IDs, P-value thresholds, and Clumping params.
  - **Agent Check**: Verify GWAS ID corresponds to the correct target phenotype/trait（避免表型错配/用错终点）.
  - **Output**: `conductor/tracks/audit-protocol-v2/reports/2.4_mr_audit.md`

## Phase 2.5: Pipeline Integrity & Plausibility (The "Glue" Check)
*Goal: Ensure scripts talk to each other correctly and numbers make sense.*

- [ ] **Task 2.5: I/O Handshake Verification (Chain of Custody)**
  - **Logic**: Trace `input_file` vs `output_file` across all scripts. Match column headers (CSV/TSV).
  - **Script Assist（可选但推荐）**：先自动抽取一版草稿，降低遗漏风险：
    - `python3 conductor/tracks/audit-protocol-v2/bin/map_pipeline_io.py --inventory conductor/tracks/audit-protocol-v2/reports/0.0_inventory.json --out conductor/tracks/audit-protocol-v2/reports/2.5_pipeline_io_map.md`
  - **Coverage Gate**: 结合 `0.0_inventory.json`，要求：
    - `inventory.scripts` 中的每个脚本都必须被标注为 in-pipeline 或 orphan；
    - `inventory.in_scope.results/figures` 中的关键产物必须能追溯到脚本或日志。
  - **Output**: `conductor/tracks/audit-protocol-v2/reports/2.5_pipeline_io_map.md`

- [ ] **Task 2.6: Numerical "Smell Test"**
  - **Script Check**: Run `python3 conductor/tracks/audit-protocol-v2/bin/check_numerical_sanity.py --results-dir results --out conductor/tracks/audit-protocol-v2/reports/2.6_numerical_sanity.csv`.
  - **Output**: `conductor/tracks/audit-protocol-v2/reports/2.6_numerical_sanity.csv`

## Phase 3: Writing & Claim Integrity
*Goal: Remove "AI-isms" and ensure logical flow matches expert standards.*

- [x] **Task 3.1: "AI-ism" Text Cleaning**
  - **Note**: Addressed via Reviewer Report.

- [x] **Task 3.2: Logical Flow Stress Test**
  - **Note**: Addressed via Reviewer Report.

- [x] **Task 3.3: Reference Verification (Full Coverage Incremental Audit)**
  - **Requirement**: 每一条参考文献必须核实 DOI/PMID 真实性，每一处文中引用必须核实位置合理性。禁止抽检。
  - **Script Check**: Run `python3 conductor/tracks/audit-protocol-v2/bin/verify_references.py --out conductor/tracks/audit-protocol-v2/reports/3.3_reference_check.csv`.
  - **Manual/Agent Check**: 对所有条目进行双重验证（Rule 5）。
  - **Output**: `conductor/tracks/audit-protocol-v2/reports/3.3_reference_check.csv`

- [x] **Task 3.4: IMRAD Boundary + Terminology Audit**
  - **Note**: Covered in Task 3.9.

- [x] **Task 3.5: Discussion Depth & Negative Results**
  - **Note**: Covered in Task 3.9.

- [x] **Task 3.6: Citation Order, Recency, Retraction Check (Full Coverage)**
  - **Requirement**: 检查引用顺序的一致性、时效性及撤稿风险。
  - **Note**: Covered in Task 3.3/3.9.

- [x] **Task 3.7: Table Style + Dual Manuscript Consistency**

- [x] **Task 3.8: Writing Benchmark (外部相似论文对标)**

- [x] **Task 3.9: Reviewer Report（中科院 2 区 / 纯生信审稿人意见）**
  - **Output**: `conductor/tracks/audit-protocol-v2/reports/3.9_reviewer_report.md`

## Phase 4: Open Source Compliance (Safety)
*Goal: Safe for public GitHub release.*

- [x] **Task 4.1: PII and Secret Scanning** (Skipped per user request)
  - *Output*: `conductor/tracks/audit-protocol-v2/reports/4.1_security_scan.md`

- [x] **Task 4.2: Documentation Completeness**
  - *Output*: `conductor/tracks/audit-protocol-v2/reports/4.2_docs_check.md`
