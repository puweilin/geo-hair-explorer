# GEO Hair Follicle / AGA 两阶段相关性回溯审计

- 审计日期：2026-07-29
- 源数据：`geo_data_raw_20260729.json`
- 总记录数：319
- 自动判定：纳入 245；待人工复核 46；排除 28
- 人工复核后：保留 279；排除 40；未决 0
- 人工复核依据：`relevance_manual_review_20260729.json`
- AI 分歧证据裁决：`relevance_ai_disagreement_adjudication_20260729.json`

## 最终排除记录

| Accession | 标题 | 判定来源 | 排除理由 |
|---|---|---|---|
| GSE280028 | Developing a differentiation-inducing therapeutic strategy for sarcomatoid renal cell carcinoma | 自动规则 | 毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现 |
| GSE303486 | Transcriptome-guided development of a fibrosis-reversal compound reduces skin scarring and allows regeneration via mitochondrial uncoupling [DRUG-seq2] | 自动规则 | 毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现 |
| GSE303487 | Transcriptome-guided development of a fibrosis-reversal compound reduces skin scarring and allows regeneration via mitochondrial uncoupling [RNA-seq] | 自动规则 | 毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现 |
| GSE324041 | HTRA1 Mutation and Expression Regulation in Cerebral Small Vessel Disease | 自动规则 | 毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现 |
| GSE314399 | The human Flower isoform hFWE4 facilitates cornification in cutaneous squamous cell carcinoma | 自动规则 | 毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现 |
| GSE305111 | Rete ridges form via evolutionarily distinct mechanisms in mammalian skin | 人工边界复核 | 主要研究 rete ridge，其摘要明确说明该结构独立于毛囊和汗腺形成。 |
| GSE283674 | Folate receptor β performs a checkpoint function in activated macrophages | 自动规则 | 毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现 |
| GSE216398 | miR-29 is an important driver of aging-related phenotypes | 自动规则 | 毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现 |
| GSE308812 | Single-cell gene expression analysis of ulcerated skin in Has2 transgenic and wild-type mice with scratching-induced ulcerative derm | 自动规则 | 毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现 |
| GSE225460 | The Role of Interferon-γ in Autoimmune Polyendocrine Syndrome Type 1 | 自动规则 | 毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现 |
| GSE274498 | snRNA-seq of murine tarsal plates | 自动规则 | 毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现 |
| GSE250294 | Low fucosylation defines the glycocalyx of progenitor cells and melanocytes in the limbal epithelial stem cell niche | 自动规则 | 毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现 |
| GSE241061 | The IL-33/ST2 axis and tissue Treg maintains epithelial homeostasis in the skin and restrains cancer development | 人工边界复核 | 组学对象是 DMBA 皮肤癌模型的全皮肤；毛囊仅作为 Treg 空间定位背景。 |
| GSE255708 | Finasteride delays atherosclerosis progression in mice and is associated with a reduction in plasma cholesterol in men | 自动规则 | 毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现 |
| GSE254347 | Antiviral drugs prolong survival in murine recessive dystrophic epidermolysis bullosa | 自动规则 | 毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现 |
| GSE243572 | Differential T-cell and monocyte responses in hepatocellular carcinoma treated with regorafenib plus nivolumab: an integrated clinical and biomarker analysis of the phase 2 RENOBATE trial | 自动规则 | 毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现 |
| GSE242128 | MCPIP1 controls effects of myeloid cells on skin carcinogenesis and hair growth | AI 分歧证据裁决 | 该 GEO 系列的 RNA-seq 对象是化学诱导的皮肤癌病灶和邻近皮肤；毛发生长只出现在总研究标题，当前组学实验未研究毛囊。 |
| GSE220977 | Sweat gland development requires an eccrine dermal niche and couples two epidermal programs | AI 分歧证据裁决 | 主要对象是小汗腺发育及其 dermal niche；毛囊仅用于说明一个共享的表皮转录程序。 |
| GSE229111 | Skin-type-dependent development of murine mechanosensory neurons | AI 分歧证据裁决 | Smart-seq 对象是支配有毛/无毛皮肤的机械感觉神经元，科学问题是触觉末梢发育；毛囊仅为神经末梢的解剖靶点。 |
| GSE220948 | Vitamin D inhibition of metastasis and oxidative stress in osteosarcoma | 自动规则 | 研究对象明确属于其他器官/疾病，未发现毛囊相关样本证据 |
| GSE226232 | TNF-α-Activated Adipose–Derived Stem Cells Improve the Angiogenesis of Full-Thickness Skin Grafts Through the TNF-α/NF-κB Signaling Pathway | 人工边界复核 | RNA-seq 对象为 TNF-α 激活的脂肪来源干细胞；毛囊仅列为皮肤移植物需维持的结构。 |
| GSE202086 | IRX5 promotes DNA damage repair and activation of hair follicle stem cells [NHEK RNA-Seq] | AI 分歧证据裁决 | 该子系列与 GSE202075 使用相同的新生儿包皮 NHEK IRX siRNA RNA-seq 设计；HFSC 研究属于同一 SuperSeries 的其他子系列，当前 accession 不提供毛囊组学样本。 |
| GSE202075 | IRX5 promotes DNA damage repair and activation of hair follicle stem cells [nhek_d] | AI 分歧证据裁决 | 该子系列实际 RNA-seq 样本为新生儿包皮 NHEK 的 IRX siRNA 实验；HFSC 研究属于同一 SuperSeries 的其他子系列，当前 accession 不提供毛囊组学样本。 |
| GSE183831 | mRNA sequencing of skins isolated from B6;129S4-Npytm2Rpa/J homozygous mice and wildtype litter mates reveals transcriptomic changes indicative of skin inflammation associated with Npy overexpression. | AI 分歧证据裁决 | 当前全皮肤 RNA-seq 专门研究 NPY 过表达导致的非黑素细胞炎症病理；毛发变灰是既往模型表型背景。 |
| GSE196265 | Expanded CUG repeat RNA alters gene expression profiles in myotonic dystrophy model cells | 自动规则 | 毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现 |
| GSE197358 | Bead-Jet printing of high-density mesenchymal stem cell-laden Matrigel beads augments skeletal muscle and hair follicle regeneration | AI 分歧证据裁决 | SuperSeries 的两个组学子系列分别分析水凝胶中的 MSC 和受损骨骼肌；没有毛囊或毛发再生组学子系列。 |
| GSE197356 | Bead-Jet printing of high-density mesenchymal stem cell-laden Matrigel beads augments skeletal muscle and hair follicle regeneration [skeletal muscle] | 自动规则 | 研究对象明确属于其他器官/疾病，未发现毛囊相关样本证据 |
| GSE197355 | Bead-Jet printing of high-density mesenchymal stem cell-laden Matrigel beads augments skeletal muscle and hair follicle regeneration [MSC] | 自动规则 | 研究对象明确属于其他器官/疾病，未发现毛囊相关样本证据 |
| GSE124121 | RNA-seq of human lens with cataracts, alopecia, & microdontia | 自动规则 | 标题虽提及毛发/脱发，但实验设计明确指向无关组织或疾病 |
| GSE164024 | Epidermal PPARγ is a key homeostatic regulator of cutaneous inflammation and barrier function in mouse skin | AI 分歧证据裁决 | 主要问题是表皮 PPARγ 对炎症、屏障和皮脂腺稳态的调控；alopecia 是多个敲除表型之一。 |
| GSE171662 | Lgr6 marks epidermal stem cells with a nerve-dependent role in wound re- epithelialization | AI 分歧证据裁决 | 组学对象是 Lgr6 表皮干细胞及其神经依赖的创伤修复；毛囊干细胞仅作为失神经后的代偿群体被提及。 |
| GSE161387 | High proliferation and delamination during skin epidermal stratification | 人工边界复核 | 主要研究表皮分层，毛囊停滞只是突变表型之一，组学样本并非毛囊细胞。 |
| GSE139272 | Genotoxicity induces epithelial hyperplasia and lineage infidelity via fibroblast IL-1β | AI 分歧证据裁决 | RNA-seq 对象为顺铂处理的真皮成纤维细胞，主要研究基因毒性后的上皮异常；毛囊只是受影响的多个上皮区室之一。 |
| GSE150701 | Specific ectodermal enhancers control the expression of Hoxc genes in developing mammalian teguments [RNA-seq] | AI 分歧证据裁决 | RNA-seq 取自胚胎远端肢芽外胚层/中胚层，主要解析甲/爪相关 HoxC 调控；脱发是全身遗传表型而非当前组学对象。 |
| GSE132129 | Low-dose quercetin positively regulates mouse healthspan | 自动规则 | 毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现 |
| GSE104022 | Molecular consequences of Dlx3 deletion by tamoxifen inducible K14 Cre in adult mouse epidermis (P42-P46) as determined by RNASeq analysis | AI 分歧证据裁决 | 当前表皮/真皮 RNA-seq 研究 Dlx3 缺失后的 IL17 炎症起始机制；毛囊分化是背景知识。 |
| GSE80082 | Integrin signaling regulates YAP/TAZ to control skin homeostasis | 人工边界复核 | RNA-seq 使用 A431 和 HaCAT 细胞研究 YAP/TAZ；毛发脱落仅为小鼠敲除表型。 |
| GSE77135 | Strong Components of Epigenetic Memory in Cultured Human Fibroblasts Related to Site of Origin and Donor Age (Methylation) | 人工边界复核 | 样本虽来自 scalp 成纤维细胞，但问题是取材部位的表观遗传记忆，不涉及毛囊或脱发。 |
| GSE77131 | Strong Components of Epigenetic Memory in Cultured Human Fibroblasts Related to Site of Origin and Donor Age (RNA-Seq) | 人工边界复核 | 样本虽来自 scalp 成纤维细胞，但问题是取材部位的转录记忆，不涉及毛囊或脱发。 |
| GSE64091 | Transcriptional profiling of cutaneous Mrgprd free nerve endings and C-LTMRs | AI 分歧证据裁决 | RNA-seq 对象为感觉神经元触觉亚型，科学问题是痛觉与愉悦触觉；毛囊仅用于描述 C-LTMR 的支配位置。 |

## 自动规则未直接决定、经人工确认保留的记录

| Accession | 标题 | 保留理由 |
|---|---|---|
| GSE300342 | H3K9me3 controls epidermis development by repressing RNA Pol II activity on key promoters and enhancers [bulk RNA-Seq] | 胚胎表皮基底细胞组学直接研究毛囊形成缺陷。 |
| GSE300343 | H3K9me3 controls epidermis development by repressing RNA Pol II activity on key promoters and enhancers [CUT&Run] | 胚胎表皮染色质数据直接研究毛囊形成缺陷。 |
| GSE300346 | H3K9me3 controls epidermis development by repressing RNA Pol II initiation on key promoters and enhancers [scRNA-seq] | 单细胞数据覆盖毛囊形成相关的胚胎表皮谱系。 |
| GSE318406 | H3K9me3 controls epidermis development by repressing RNA Pol II activity on key promoters and enhancers [CUT&Run - Temporal] | 时间序列表皮染色质数据用于解释毛囊形成过程。 |
| GSE294435 | Transcription Elongation Factor SPT6 Maintains Epidermal Homeostasis and Suppresses Skin Inflammation in Mice | 单细胞表皮研究明确将毛囊发育作为主要生物学表型之一。 |
| GSE279813 | Gene expression changes in skin of dihydrotestosterone-induced mice after treatment of a newly-developed traditional Chinese medicine formula, Hanlianxiang. | DHT 诱导的雄激素性脱发模型及治疗干预。 |
| GSE273335 | Identification of unique mesenchymal subpopulations for regenerating follicular and interfollicular epithelia after devastating necrosis in the skin graft | 研究皮肤移植后滤泡上皮再生和 dermal papilla 相关间充质群体。 |
| GSE294233 | RNA seq on murine basal keratinocytes and murine Lrig1 positive sorted keratinocytes | 研究 Lrig1 阳性角质形成细胞对毛囊干细胞激活的 niche 信号。 |
| GSE274955 | An mRNA treatment for human skin rejuvenation | 人皮肤单细胞图谱明确分析 hair follicle 细胞更新，属于可复用的毛囊细胞群数据。 |
| GSE273649 | HNRNPU is essential for proper murine skin development | 表皮 Hnrnpu 缺失导致毛囊发育失败，组学对象与发育表型直接相关。 |
| GSE272815 | Helminth protein enhances wound healing by inhibiting fibrosis and promoting tissue regeneration | 全层创伤模型直接研究毛囊再生及其免疫细胞机制。 |
| GSE252889 | Smart-seq analysis comparing melanocytes from Spry1flox/flox mice tail epidermis to the melanocytes derived from Spry1 epidermis specific knockout mice tail and back epidermis | 研究 Spry1 缺失后毛囊 melanocyte stem cells 的迁移与命运。 |
| GSE224433 | An ERK-dependent molecular switch antagonizes fibrosis and promotes regeneration in spiny mice (Acomys) | 再生性伤口模型以毛囊新生作为核心再生结局。 |
| GSE195657 | Single nucelus RNA sequencing of 14 week EGA fetal skin | 胎儿皮肤单核数据比较形成毛囊与形成皮纹的皮肤区域。 |
| GSE193920 | Local IL-17 orchestrates skin aging | 皮肤衰老单细胞研究明确分析毛囊干细胞激活和毛干再生。 |
| GSE181390 | Chromatin remodeling governs postnatal maturation in dermal fibroblasts [scRNA-Seq] | 新生皮肤多细胞数据用于解释能够恢复功能性毛囊的再生性成纤维细胞状态。 |
| GSE201447 | ScRNA-seq Analysis of Whole Skin Cells from Irradiated and Naïve Mice | 研究目标明确包括放射诱导性脱发，组学样本来自照射后全皮肤。 |
| GSE165314 | Stem cells expand potency and alter tissue fitness by accumulating diverse epigenetic memories (scRNA-seq) | 直接追踪毛囊干细胞在损伤修复中的命运和表观遗传记忆。 |
| GSE189210 | Parallel single cell multi-omics analysis of neonatal skin reveals transitional fibroblast states that restrict differentiation into distinct fates | 多组学分析直接解析 dermal papilla 与脂肪细胞命运分化。 |
| GSE175990 | Single cell transcriptional profile for hidradenitis suppurativa | 化脓性汗腺炎是毛囊单位相关的炎症性疾病，病灶皮肤单细胞数据可用于研究毛囊单位病理。 |
| GSE180405 | Single-cell transcriptomic profiles of CD45-positive cells from Mx1-Cre x Adam10f/f Rag2KO mice | 炎症性脱发模型的皮肤免疫细胞单细胞数据。 |
| GSE147298 | BMP signaling: at the gate between activated melanocyte stem cells and differentiation [SMART-Seq2 single cell RNA-seq] | 研究与毛周期同步的 melanocyte stem cells 激活、分化和毛发变灰。 |
| GSE131600 | Single-cell ATAC-Seq of cells recruited to regenerative portions of large skin wounds. | 大创面单细胞 ATAC 直接研究 wound-induced hair follicle neogenesis。 |
| GSE108677 | Single-cell transcriptomics of Hic1 lineage cells recruited during regenerative and scar-forming skin wound healing. | 再生性大创面间充质细胞数据用于解释新毛囊诱导状态。 |
| GSE132383 | Validation of small molecule activators and identification of altered signaling pathways underlying the age-related decline in proliferative capacity in human dermal progenitors | 比较年轻和衰老的人毛囊 dermal progenitor cells 转录组。 |
| GSE102086 | Single Cell and Open Chromatin Analysis Reveals Molecular Origin of Epidermal Cells of the Skin | 早期表皮单细胞数据研究毛囊等皮肤附属器的细胞起源。 |
| GSE97213 | Single Cell and Open Chromatin Analysis Reveals Molecular Origin of Epidermal Cells of the Skin | 早期表皮 RNA-seq/ATAC-seq 研究毛囊等皮肤附属器的细胞起源。 |
| GSE112671 | Single cell RNA-seq analysis in dermis of SM22rtTA; tetO-Cre; R26-Tomato (SM22-Tomato, control) and SM22rtTA; tetO-Cre; R26-SmoM2/Tomato (SM22-SmoM2/Tomato, forced Hh activation in wound dermis) at 3 days after complete reepithelialization | 伤口真皮 Hh 激活模型直接研究毛囊新生。 |
| GSE94893 | RNA-seq analysis in dermis and epidermis of WT (control), LSL-Shh (Shh overexpression in epidermis), and E14.5d skin | Shh 诱导伤口毛囊新生的真皮和表皮 RNA-seq。 |
| GSE110459 | Identification of transcriptional targets of FGF20. | FGF20 靶基因实验直接研究毛囊 placode 和 dermal condensate 发育。 |
| GSE89928 | Wounds That Never Heal? Stem Cell Lineage Infidelity at the Crossroads of Wound-Repair and Cancer | 直接比较表皮与毛囊干细胞在稳态、损伤和肿瘤中的谱系可塑性。 |
| GSE88989 | Cell type-specific chromatin states differentially prime squamous cell carcinoma tumor-initiating cells for epithelial to mesenchymal transition [RNA-seq] | 直接比较毛囊干细胞来源与表皮来源的 SCC 起始细胞。 |
| GSE74283 | Epithelial cell RNA-seq in aged skin | 明确比较年轻与衰老皮肤中的毛囊干细胞和表皮细胞。 |
| GSE71621 | Cell type-specific chromatin states differentially prime squamous cell carcinoma tumor-initiating cells for epithelial to mesenchymal transition | 系列研究直接比较毛囊干细胞来源与表皮来源的肿瘤起始细胞。 |

## 判定口径

第一阶段保持高召回，只负责发现候选记录。第二阶段要求标题、摘要或实验设计能够证明毛囊、毛周期、头皮、脱发疾病或相关细胞/样本是主要研究对象。药物适应证、不良事件、综合征伴随症状、普通 scalp 取材和与其他皮肤附属器官的比较，不再单独构成纳入证据。
