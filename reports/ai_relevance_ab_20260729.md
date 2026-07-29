# GEO 相关性判定 AI A/B 回溯报告

- 运行时间：2026-07-29T17:36:55+08:00
- 数据集数：319
- AI 模型：`deepseek-v4-pro`（非思考模式，temperature=0）
- Prompt 版本：`hair-geo-relevance-v1`
- AI 独立重复次数：2
- 参考标签：现有两阶段规则 + 46 条人工边界复核 + 证据裁决 18 条（修正 5 条早期标签）；仍非独立盲法金标准，指标可能偏向现有规则。

## 总体指标

| 策略 | 自动覆盖率 | 决定样本准确率 | 全体有效准确率 | 纳入精确率 | 纳入召回率 | F1 | 错误纳入 | 错误排除 | 转人工 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A：现有两阶段规则 | 85.58% | 100.00% | 85.58% | 100.00% | 100.00% | 100.00% | 0 | 0 | 46 |
| B：AI-only（deepseek-v4-pro） | 100.00% | 95.61% | 95.61% | 96.82% | 98.21% | 97.51% | 9 | 5 | 0 |
| C：规则+AI 高置信共识 | 83.39% | 100.00% | 83.39% | 100.00% | 100.00% | 100.00% | 0 | 0 | 53 |

## 分歧裁决后修正的参考标签

| Accession | 原标签 | 修正标签 | 理由 |
|---|---:|---:|---|
| GSE202075 | include | exclude | 该子系列实际 RNA-seq 样本为新生儿包皮 NHEK 的 IRX siRNA 实验；HFSC 研究属于同一 SuperSeries 的其他子系列，当前 accession 不提供毛囊组学样本。 |
| GSE202086 | include | exclude | 该子系列与 GSE202075 使用相同的新生儿包皮 NHEK IRX siRNA RNA-seq 设计；HFSC 研究属于同一 SuperSeries 的其他子系列，当前 accession 不提供毛囊组学样本。 |
| GSE229111 | include | exclude | Smart-seq 对象是支配有毛/无毛皮肤的机械感觉神经元，科学问题是触觉末梢发育；毛囊仅为神经末梢的解剖靶点。 |
| GSE242128 | include | exclude | 该 GEO 系列的 RNA-seq 对象是化学诱导的皮肤癌病灶和邻近皮肤；毛发生长只出现在总研究标题，当前组学实验未研究毛囊。 |
| GSE64091 | include | exclude | RNA-seq 对象为感觉神经元触觉亚型，科学问题是痛觉与愉悦触觉；毛囊仅用于描述 C-LTMR 的支配位置。 |

## AI 稳定性

- 可比较记录：319
- 两次决定完全一致：319（100.00%）
- 决定发生变化：0
- API 总 tokens：595675

## AI 与参考标签分歧

| Accession | 标题 | 参考 | AI | 置信度 | AI 理由 |
|---|---|---:|---:|---:|---|
| GSE202086 | IRX5 promotes DNA damage repair and activation of hair follicle stem cells [NHEK RNA-Seq] | exclude | include | 0.95 | The study's central question is hair follicle stem cell activation and hair cycle initiation, making it directly relevant to hair biology. |
| GSE243634 | Type 2 cytokine-dependent skin barrier regulation in personalized 2D- and 3D skin models of atopic dermatitis: A pilot study | include | exclude | 0.95 | Hair follicle is used solely as a keratinocyte source for an atopic dermatitis model, with no hair biology or alopecia question. |
| GSE254889 | Hair follicles modulate skin barrier function | include | exclude | 0.95 | The study focuses on epidermal barrier function and gene expression changes in whole epidermis after ABCA12 deletion; hair follicles are not the primary biological subject or assayed sample. |
| GSE94235 | Selective Janus kinase 1 inhibition resolves inflammation and restores hair growth offering a viable treatment option for alopecia areata | include | exclude | 0.95 | The study assays in vitro stimulated healthy donor T-cells to compare JAK inhibitors, with alopecia areata only as a background indication; no hair follicle or alopecia patient samples are profiled. |
| GSE104022 | Molecular consequences of Dlx3 deletion by tamoxifen inducible K14 Cre in adult mouse epidermis (P42-P46) as determined by RNASeq analysis | exclude | include | 0.90 | DLX3 is directly implicated in hair follicle differentiation, and the study examines molecular changes in skin compartments relevant to hair biology. |
| GSE150701 | Specific ectodermal enhancers control the expression of Hoxc genes in developing mammalian teguments [RNA-seq] | exclude | include | 0.90 | The study directly investigates genetic mechanisms required for hair development, with alopecia as a key phenotype, making it relevant to hair biology. |
| GSE164024 | Epidermal PPARγ is a key homeostatic regulator of cutaneous inflammation and barrier function in mouse skin | exclude | include | 0.90 | Alopecia is a primary phenotype of the knockout model, and the study investigates the molecular basis of skin abnormalities including hair loss. |
| GSE171662 | Lgr6 marks epidermal stem cells with a nerve-dependent role in wound re- epithelialization | exclude | include | 0.90 | The study directly involves hair follicle stem cells as a compensatory population in wound re-epithelialization, making it relevant to hair follicle biology. |
| GSE175990 | Single cell transcriptional profile for hidradenitis suppurativa | include | exclude | 0.90 | The study focuses on hidradenitis suppurativa, a skin disease, and while hair follicles are mentioned as part of the anatomical context, the primary subject is the inflammatory skin lesions, not hair follicle biology or alopecia. |
| GSE183831 | mRNA sequencing of skins isolated from B6;129S4-Npytm2Rpa/J homozygous mice and wildtype litter mates reveals transcriptomic changes indicative of skin inflammation associated with Npy overexpression. | exclude | include | 0.90 | The study directly investigates hair graying caused by melanocyte stem cell depletion in hair follicles, making hair biology a central endpoint. |
| GSE197358 | Bead-Jet printing of high-density mesenchymal stem cell-laden Matrigel beads augments skeletal muscle and hair follicle regeneration | exclude | include | 0.90 | The study directly investigates hair follicle regeneration as a primary endpoint. |
| GSE220977 | Sweat gland development requires an eccrine dermal niche and couples two epidermal programs | exclude | include | 0.90 | The study explicitly identifies and analyzes a transcriptome shared with hair follicles, making hair follicle biology a primary subject of the omics experiment. |
| GSE274955 | An mRNA treatment for human skin rejuvenation | include | exclude | 0.90 | Hair follicles are mentioned as one of several cell types in a broad skin aging atlas; the primary subject is skin rejuvenation, not hair biology or alopecia. |
| GSE139272 | Genotoxicity induces epithelial hyperplasia and lineage infidelity via fibroblast IL-1β | exclude | include | 0.85 | The study directly investigates hair follicle biology as a primary subject, examining how genotoxic damage affects hair follicle epithelial cells, which meets inclusion criterion 1. |

## 解释

- `自动覆盖率`：无需人工即可给出 include/exclude 的比例。
- `决定样本准确率`：只在非 review 样本上计算。
- `全体有效准确率`：把 review 视作未完成，因此能体现人工成本。
- 混合策略仅在规则与 AI 同意且 AI 置信度不低于 0.85 时自动处理；其他记录进入人工队列。
