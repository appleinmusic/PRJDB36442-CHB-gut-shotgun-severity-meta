# 可行性摸底（Feasibility Scoping）

> 目标：在不自带队列的情况下，先证明“国自然标书级问题”可以用**公开数据 +（必要时）轻量化前瞻队列/外包测序**落地；并定义明确的 stop/pivot 规则，避免陷入“卷烂题 + 数据不够”。

## 现状判断（截至 2026-02-04）
- CHB × 肠道菌群文献不少，但**高质量、可复现、可外部验证**的研究相对少（尤其是长期治疗、纤维化进展、机制链条）。
- 公开数据库中可见 HBV 相关“gut microbiome”项目，但需要严格鉴别：
  - 很多标注为“metagenome”的实际是 **16S/扩增子（AMPLICON）**，不满足本项目“shotgun/宏基因组”主线。
  - 真正的宏基因组项目存在，但“run 数据是否公开/能否直接下载”需要逐项核验。

## 公开数据：已确认/待确认清单（最小集合）

### 已确认可直接落地（shotgun + run 可下载 + 逐样本表型可审计）

- `PRJDB36442`（ENA）/ `PRJCA037061`（NGDC BioProject）  
  - 规模：20 个 run（paired-end），FASTQ 总量约 **58.5 GB**（以 ENA 报告的 `size_bytes` 汇总）  
  - 逐样本表型：NGDC BioSample `Description` 字段包含 **`group M` / `group S`**（mild vs significant histological damage）  
  - 审计材料与对照表：
    - manifest：`results/feasibility/PRJDB36442_fastq_manifest.tsv`（含 URL/size/md5）
    - group 表：`results/feasibility/PRJCA037061_sample_groups.tsv`
    - run↔group join：`results/feasibility/PRJDB36442_run_groups.tsv`

### 已确认存在的项目记录（仍需进一步核验是否为 shotgun + run 可下载）
- ENA: `PRJEB79318`（标题：*Metagenome-based characterization of the gut bacteriome, mycobiome, and virome in patients with chronic hepatitis B-related liver fibrosis*；2024-08-23 公布）
  - 当前通过 ENA API 可查到 study 记录，但 `read_run` 暂未返回（可能是尚未挂载、字段/镜像原因或受限）。后续需要逐项核验下载路径与 run 列表。

### 可作为“对照/预研”的公开项目（目前显示为 amplicon，非 shotgun）
- ENA: `PRJEB64018`（标题：*HBV and gut microbiome*；2025-11-20 公布）
  - ENA 页面可见项目与 accession；但 ENA `read_run` 显示 `library_strategy=AMPLICON`，更像 16S/扩增子数据；可用于先做方法流程/分层分析预研，不作为“shotgun 主分析”。

## 关键落地策略（建议写进标书）

### 策略 1：公开数据 + 轻量化前瞻队列（推荐，更像国自然）
> 你不做湿实验也可以：采样与测序可由合作医院/第三方平台完成，你主要负责方案设计与数据分析。

- 前瞻队列最小设计（可调整）：
  - 样本量：n=120–200（CHB），可加 n=60 健康对照（或用现成健康对照公共队列做匹配）
  - 分层：治疗前/治疗中（不同 NAs）、HBV DNA 不可检出 vs 可检出、纤维化轻 vs 重（LSM/FIB-4）
  - 采集：粪便（shotgun），血清（靶向胆汁酸/关键代谢物，可选），临床指标（ALT/AST/LSM/HBsAg/HBV DNA）
- 好处：能把“功能模块—代谢物—表型”串成机制链条，并能做纵向/疗程相关分析，显著提升新意与说服力。

### 策略 2：纯公开数据（备选，风险更高）
- 前提：必须在 2–3 周内找到 ≥2 个**独立**的 CHB 相关 shotgun 队列，且 run 数据可下载、元数据足够（至少包含纤维化或治疗/病毒学指标之一）。

## Stop / Pivot 规则（必须先写死，防止跑偏）
- **Stop（停止）**：在可行性窗口（建议 2–3 周）内，无法确认至少 1 个可下载的 CHB shotgun 队列 + 无法落实任何采样/测序合作路径。
- **Pivot A（转向）**：若 CHB shotgun 队列不足，则将主线改为“CHB 相关分层 + 功能推断（16S + 代谢通路）+ 外部证据链（胆汁酸/免疫轴文献）”，并把“shotgun”作为后续扩展。
- **Pivot B（收敛结局）**：若缺少 HBsAg 定量/随访，则以“纤维化（LSM/FIB-4）+ ALT 残余炎症”为主结局；把功能性治愈作为展望。
