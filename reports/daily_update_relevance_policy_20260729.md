# GEO daily update 相关性策略

## 结论

daily update 只使用可解释的两阶段规则，AI 不参与相关性纳入、排除或复核决定：

- 第二阶段判为 `include`：自动加入。
- 第二阶段判为 `exclude`：不加入，并写入可恢复的决定日志。
- 第二阶段判为 `review`：进入人工复核队列。
- 已存在 accession 只读，不因 daily update 重新判定或自动删除。

DeepSeek API 仅保留原有的中文展示摘要生成功能，不参与选择策略。

## 两阶段规则

第一阶段是高召回候选发现：

- 检索 hair follicle、alopecia、scalp hair、dermal papilla、hair cycle 等主题词。
- 限定人和小鼠，以及 RNA-seq、甲基化、ATAC/结合占位等数据类型。
- 去除 ovarian/thyroid/lymphoid/dental follicle 等稳定词义歧义。

第二阶段验证实际研究对象：

- 标题、摘要或 Overall Design 必须证明毛囊、毛周期、脱发疾病或相关细胞/样本是主要研究问题或可复用组学对象。
- 药物适应证、不良事件、综合征伴随表型、普通 scalp 取材、其他皮肤附属器官的比较，以及标题相关但当前 SubSeries 实际取样无关，不构成单独纳入证据。

## 319 条 A/B 回溯

参考标签经 AI 分歧证据裁决及同类 SubSeries 规则回归后，修正 5 条既有错误纳入：
`GSE242128`、`GSE229111`、`GSE202075`、`GSE202086`、`GSE64091`。
这些记录已转化为可解释的稳定排除规则，不改变 daily update 以规则为准的原则。

| 策略 | 自动覆盖率 | 决定样本准确率 | 错误纳入 | 错误排除 | 转人工 |
|---|---:|---:|---:|---:|---:|
| 当前两阶段规则 | 85.58% | 100.00% | 0 | 0 | 46 |
| AI-only（仅研究对照） | 100.00% | 95.61% | 9 | 5 | 0 |
| 规则 + AI 共识（不用于生产） | 83.39% | 100.00% | 0 | 0 | 53 |

DeepSeek 对 319 条独立运行两次，638 次决定完全一致，但稳定性不等于正确性；
AI-only 仍产生了 14 条经证据裁决确认的错误。

## 数据安全

- `data/geo_data.json`：当前生产数据，使用修正后的 279 条清洗集。
- `data/geo_data_raw_20260729.json`：切换前的 319 条原始快照，可用于恢复和复审。
- `data/geo_data_curated_20260729.json`：带日期的 279 条回溯清洗产物。
- `data/relevance_review_queue.json`：第二阶段无法直接决定的边界记录。
- `data/relevance_decision_log.json`：自动排除记录，保留完整规则证据，便于恢复与复审。
- JSON 使用临时文件加原子替换写入。
- 保存前验证已有 accession 全部仍存在，并拒绝重复 accession。
- GitHub Actions 只提交上述允许的数据文件；API Key 仅从 GitHub Secret 注入。

## 发布状态

网页继续读取 `data/geo_data.json`，该文件已切换为审计后的 279 条数据。
原始 319 条保存在 `data/geo_data_raw_20260729.json`，本次清洗可完整回滚。
