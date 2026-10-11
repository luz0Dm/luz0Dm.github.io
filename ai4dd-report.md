# AI 药物发现（AI4DD）领域文献计量公开报告 · 2026 版

> **免费公开版** · 由 WS2 OpenAlex 文献计量管线自动生成 + 人工解读
> 数据源：OpenAlex API（polite pool，mailto 已注册）
> 本版数据：**示例数据（2026 年 2 月管线试跑快照，n=2000，按引用量排序抽样）**——正式发布前将实跑全量管线填充。

---

## 一、执行摘要

- 近 5 年（2021–2026）AI 药物发现主题在 OpenAlex 可检索文献总量超过 **26 万篇**（全文搜索命中数，含交叉主题），领域仍处高速产出期。
- 本报告基于管线试跑的 **2000 篇高引样本**（按引用量降序抽样）：总被引 **760,883 次**，中位被引 **257 次**——头部效应极强，Top 1% 论文拿走绝大多数引用。
- 机构格局：**Harvard 一家独大（117 篇）**，Stanford / MIT / UCL / Oxford / Cambridge 组成第二梯队；**四川大学（44 篇）与法国 Inserm（44 篇）并列第 8**，中国与美国是仅有的两个第一梯队国家（US 788 vs CN 503 篇次）。
- 主题重心正从「通用深度学习综述」转向 **可解释 AI（XAI）、计算药物发现方法、AI 医疗伦理** 三大落地方向。

> **本报告不覆盖的部分，恰是决策最需要的部分**——竞争格局深度分析（谁在收缩、谁在加注）、管线成功率（AI 发现分子的临床通过率 vs 传统路径）、未被满足需求（哪些适应症/靶点类型 AI 渗透率为零）。**这三块仅在定制版提供**（见末节）。

---

## 二、发文趋势（近 5 年）

| 年份 | 高引样本文数 |
|---|---|
| 2021 | 641 |
| 2022 | 504 |
| 2023 | 501 |
| 2024 | 297 |
| 2025 | 56 |
| 2026 | 1 |

**读法**（重要）：本表为**按引用量排序抽样的样本分布**，2021 年占比最高反映的是「引用积累需要时间」这一计量学规律，**不能读成「领域在萎缩」**。全量年度趋势（含零引论文）需按 publication_date 排序重跑，定制版交付该口径数据。

![年度发文趋势](out_ai4dd_demo/chart_yearly_trend.png)

*示例图表，正式发布前需实跑管线填充。*

---

## 三、机构格局 Top 20

| # | 机构 | 样本内文数 | 类型 |
|---|---|---|---|
| 1 | Harvard University | 117 | 学术 |
| 2 | Stanford University | 62 | 学术 |
| 3 | MIT | 57 | 学术 |
| 4 | University College London | 55 | 学术 |
| 5 | University of Oxford | 51 | 学术 |
| 6 | University of Cambridge | 49 | 学术 |
| 7 | Massachusetts General Hospital | 45 | 医院/学术 |
| 8 | Sichuan University | 44 | 学术（中国） |
| 8 | Inserm | 44 | 国立研究（法国） |
| 10 | University of Toronto | 44 | 学术 |
| 11 | University of Pennsylvania | 43 | 学术 |
| 12 | UC San Diego | 42 | 学术 |

（13–20 名详见随附 `top_institutions.csv`。）

**值得注意**：Top 20 全部由**学术机构与大学医院**构成，**无一企业主体**——AI 药企（如英矽智能、Recursion、Exscientia 等）的产出以管线公告/专利而非论文为主，**论文计量看不到的真实商业竞争格局，见定制版**。

国家分布（样本次数）：US 788 / CN 503 / GB 318 / IN 187 / DE 181。

![Top 机构](out_ai4dd_demo/chart_top_institutions.png)

*示例图表，正式发布前需实跑管线填充。*

---

## 四、高引论文 Top 15

| # | 论文 | 年 | 被引 |
|---|---|---|---|
| 1 | The STRING database in 2023 (Nucleic Acids Res) | 2022 | 9,403 |
| 2 | Review of deep learning: concepts, CNN architectures… (J Big Data) | 2021 | 7,882 |
| 3 | Machine Learning: Algorithms, Real-World Applications… (SN Comp Sci) | 2021 | 5,546 |
| 4 | Global burden of diabetes 1990–2021 (GBD, Lancet 系) | 2023 | ~4,600 |
| 5 | UCSF ChimeraX: structure building & analysis (Protein Sci) | 2023 | 4,518 |
| 6 | Performance of ChatGPT on USMLE (PLOS Digital Health) | 2023 | 4,085 |
| 7 | WHO Classification of Haematolymphoid Tumours 5th ed (Leukemia) | 2022 | 3,997 |
| 8 | PubChem 2023 update (Nucleic Acids Res) | 2022 | 3,390 |
| 9 | PROTAC targeted protein degraders (Nat Rev Drug Discov) | 2022 | 3,221 |
| 10 | 2023 Alzheimer's disease facts and figures | 2023 | 3,182 |
| 11 | Revolutionizing healthcare: AI in clinical practice (BMC Med Educ) | 2023 | 3,102 |
| 12 | ChatGPT Utility in Healthcare: Systematic Review (Healthcare) | 2023 | 3,080 |
| 13 | A Survey on Knowledge Graphs (IEEE TNNLS) | 2021 | 2,921 |
| 14 | Global burden of 88 risk factors, 204 countries (GBD) | 2023 | ~2,800 |
| 15 | Physics-Informed Neural Networks survey (J Sci Comput) | 2022 | 2,763 |

**结构解读**：高引头部被三类论文占据——**基础数据资源**（STRING / PubChem / ChimeraX）、**通用 ML/DL 综述**、**通用对话接口医疗评测**（上表 #6/#12 两篇，标题见表）。真正「AI 设计出分子并推进临床」的原创研究**无一进入 Top 15**——这一落差本身就是领域最大的认知套利空间，定制版将逐篇拆解。

---

## 五、技术主题聚类

基于 OpenAlex topics 字段对样本聚类（主题名称为 OpenAlex 自动标注）：

| 聚类 | 样本次数 | 判断 |
|---|---|---|
| AI in Healthcare & Education | 221 | 最大簇，偏应用综述 |
| Computational Drug Discovery Methods | 189 | **核心方法簇**：分子生成/对接/性质预测 |
| ML in Materials Science | 112 | 交叉溢出 |
| AI Applications（通用） | 96 | 泛化 |
| Cancer Immunotherapy & Biomarkers | 74 | 疾病热点 |
| Nanoparticle-Based Drug Delivery | 67 | 递送系统 |
| Ethics & Social Impacts of AI | 64 | 监管/伦理升温 |
| Explainable AI (XAI) | 61 | **增长最快的工程需求**：监管申报要求可解释 |
| Ferroptosis & cancer prognosis | 58 | 靶点机制热点 |
| Alzheimer's research | 56 | 神经退行持续高热 |

![引用分布](out_ai4dd_demo/chart_citation_dist.png)

*示例图表，正式发布前需实跑管线填充。*

---

## 六、巨头 vs 学术对比

论文计量口径下，**学术界占据绝对主导**（Top 20 机构全为学术主体）；产业界（AI 药企 + 大药企 AI 部门）的成果出口主要是**临床管线、授权交易与专利**，而非论文。

- **学术侧信号**：可解释性、伦理、基准数据集论文量上升 → 领域在为「接受监管审视」做准备。
- **产业侧信号**（本报告论文数据无法覆盖）：哪家 AI 药企的管线进入 II/III 期、哪些大药企在买 vs 自建、单笔授权金额分布——**定制版以交易与管线数据库交叉补齐**。

---

## 【本版故意缺失 · 定制版提供】

以下三块是免费版**刻意留白**的部分，也是 BD/投资决策真正付费的部分：

1. **竞争格局深度分析**：AI 药企分赛道（小分子生成 / 大分子 / 递送 / 临床试验设计）逐个画像，含融资-管线-授权三轴交叉验证；谁在收缩、谁在加注、谁的论文产出与管线进度背离。
2. **管线成功率**：AI 发现分子进入临床后的 I/II/III 期通过率 vs 行业基线（传统发现路径）的实证对比，含失败案例归因。
3. **未被满足需求**：按适应症 × 靶点类型扫描 AI 渗透率，定位「论文很热但管线为零」与「管线拥挤但论文过剩」的错配区间。

---

## 七、方法论与数据源

- **数据源**：OpenAlex API（https://api.openalex.org，开放获取，2.5 亿+ works 记录），使用 polite pool（mailto 参数注册），限速 8 req/s（低于官方 10 req/s 上限）。
- **管线**：`openalex_pipeline.py`（开源，随报告附带）：主题关键词 → 近 5 年文献 → 年度趋势 / Top 20 机构·作者·期刊 / 引用分布 / 机构合作网络边列表 / 高引清单 → CSV + matplotlib 图表，全自动。
- **本版口径声明**：n=2000，按被引量降序抽样（保证高引清单质量）；年度趋势受引用积累偏差影响，已在对应章节标注。正式版默认全量拉取（上限可配）双口径交付。
- **局限**：① OpenAlex 全文搜索存在主题交叉噪声（如 GBD 疾病负担、材料科学 ML 混入）；② 论文计量看不到非论文成果（管线、专利、交易）；③ 被引数为抓取时点快照。

---

## 八、定制服务说明

同样的管线 + 人工分析，按你的主题与决策问题定制：

| 档位 | 价格 | 交付物 | 适合 |
|---|---|---|---|
| **快照定制** | **$500**（一次性，个人卡可刷） | ① 你的主题全量管线实跑（CSV + 图表全套）② 10 页定制报告：趋势/机构/主题/高引 + 一节定向分析（你指定一个问题）③ 合作网络边列表（Gephi 可直接导入） | 中小 biotech 分析师、咨询师做快速尽调底稿 |
| **决策定制** | **$2,000**（一次性） | ① 快照定制全部内容 ② **竞争格局深度分析 + 管线成功率实证 + 未被满足需求扫描**（免费版留白三块全填）③ 20+ 页报告 + 一次 45 分钟电话解读 ④ 30 天内一次数据刷新 | VC 分析师投决支持、biotech BD 立项评估 |

- **交付周期**：5 个工作日（自需求确认起）。
- **里程碑**：需求确认 → 数据快照预览（第 3 个工作日，可调整口径）→ 终稿交付。以交付物验收，不以页数/字数承诺。
- **下单方式**：回复本报告注明「定制 + 主题 + 决策问题」，24 小时内给需求确认函。

---

*本报告为免费公开版。文中标注「示例数据」处为管线试跑快照，正式发布版将以全量实跑数据填充。定制咨询：通过报告分发渠道回复即可。*
