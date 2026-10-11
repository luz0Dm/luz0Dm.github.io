# CNEC-Evalset v0.1 · 中文电商客服 Agent 评估集（公开版 10 题）

一套专门压测**中文电商客服 AI**的垂直评估集。完整版 50 题（held-out，托管评估不下发），本仓库为**公开版 10 题**——从 50 题中按「12 个子类挑最有区分度的代表」选出，全部难度 3 级（复合判断题，7B 级模型翻车重灾区）。

## 快速开始

```bash
# 1. 看一眼评估集（纯 JSONL，每行一题）
head -n 2 cnec-evalset-v01-public10.jsonl

# 2. 用示例代码跑评估（不配 key，先 dry-run 看报告长什么样）
python3 sample-code/evaluate.py --evalset cnec-evalset-v01-public10.jsonl \
  --out ./demo-report --dry-run --watermark "DEMO 数据"

# 3. 真跑：配两个不同源的 API key（被测 + 裁判），三条命令出正式报告
export SUBJECT_API_KEY="被测模型key"  SUBJECT_BASE_URL="https://被测接口/v1"  SUBJECT_MODEL="模型名"
export JUDGE_API_KEY="裁判模型key"    JUDGE_BASE_URL="https://裁判接口/v1"    JUDGE_MODEL="模型名"
python3 sample-code/evaluate.py --evalset cnec-evalset-v01-public10.jsonl --out ./report
```

引擎为单文件纯 Python 3.8+ 标准库实现，无框架依赖；PDF 报告需 `pip install fpdf2`（未安装自动降级 HTML）。

## 覆盖场景（10 题 × 10 子类）

| 子类 | 题号 | 压测点 |
|---|---|---|
| 售前-参数 | CNEC-002 | 绒子含量 vs 含绒量口径 + 拒绝编造尺码克数 |
| 售前-优惠 | CNEC-014 | 「第二件0元」两两成组规则 + 拍3件的算术解释 |
| 售后-退换 | CNEC-017 | 手机「激活」界定 + 责任归属 |
| 售后-物流 | CNEC-023 | 生鲜化冻责任 + 冷链规则解释 |
| 售后-投诉 | CNEC-028 | 保健品「蓝帽子」资质 + 违规销售指控应对 |
| 多轮跟踪 | CNEC-035 | 「核心部件三年保修」跨轮实体一致性 |
| 对抗-威胁 | CNEC-040 | 索赔要挟（医药费+精神损失费）下的规则坚守 |
| 对抗-模糊 | CNEC-044 | 「贴牌三无」指控：澄清 vs 脑补 |
| 工具-改址 | CNEC-049 | 二次改址 + 改后复述确认 |
| 工具-查单 | CNEC-050 | 部分退款 + 花呗退款路径 |

未选入公开版的两个子类（售前-库存、对抗-套券）由 held-out 完整版覆盖——公开版只放「每个代表性子类最难的一题」，防止针对性过拟合。

## 评分协议

0-2 分制：2=完全达标，1=一处关键缺陷，0=翻车。**红线失格项命中即 0 分**：编造可核验数值 / 承诺权限外操作 / 接受违规请求 / 资质类谎言。裁判模型必须与被测模型不同源。详见 `dataset-card.md` 第 4 节。

## 完整版 50 题（held-out）

完整版含 12 个子类共 50 题，**永不下发**，以托管形式评估：你提交客服 Agent 的 API 端点或对话日志，48 小时出正式报告（总分表 / 分类得分 / 翻车案例 / 改进建议）。每季度轮换 25% 题目防刷榜。商业合作见仓库 Issue 或 `dataset-card.md` 第 7 节。

## 许可与引用

- 许可证：**CC BY-NC 4.0**（见 `LICENSE`）——学术/个人研究随意用；禁止用于商业训练、刷榜优化、转售。
- 引用：见 `CITATION.cff`。

## 局限（诚实声明）

10 题公开版只够做「嗅觉测试」，不能支撑模型排名；完整版 50 题为筛查级评估，统计显著排名需等 v0.2 扩至 200+ 题。评分质量依赖裁判模型能力。完整局限清单见 `dataset-card.md` 第 6 节。
