#!/usr/bin/env python3
"""Explainable two-stage relevance filter for the Hair Follicle / AGA GEO corpus.

Stage 1 is intentionally permissive and only asks whether a record contains a
hair/alopecia retrieval term. Stage 2 distinguishes a study's actual omics
subject from incidental mentions such as adverse events, drug indications, or
unrelated clinical phenotypes.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


PatternSpec = Tuple[str, str]


TOPIC_PATTERNS: Sequence[PatternSpec] = (
    ("hair_follicle", r"\bhair[\s-]+follic(?:le|les|ular)\b"),
    ("hair_follicle_stem_cell", r"\b(?:hf[\s-]?scs?|hair[\s-]+follicle[\s-]+stem[\s-]+cells?)\b"),
    ("dermal_papilla", r"\b(?:dermal[\s-]+papilla(?:e|ry)?|dpc[s]?)\b"),
    ("dermal_sheath", r"\bdermal[\s-]+sheath\b"),
    ("root_sheath", r"\b(?:outer|inner)[\s-]+root[\s-]+sheath\b"),
    ("hair_compartment", r"\bhair[\s-]+(?:shaft|bulb|root|matrix|germ|peg|placode)s?\b"),
    ("hair_cycle_stage", r"\b(?:anagen|catagen|telogen|exogen)\b"),
    ("hair_cycle", r"\bhair[\s-]+cycl(?:e|ing)\b"),
    ("hair_growth", r"\bhair[\s-]+(?:growth|regrowth|regeneration)\b"),
    ("hair_loss", r"\bhair[\s-]+(?:loss|thinning|shedding)\b"),
    ("hair_pigmentation", r"\bhair[\s-]+(?:pigmentation|greying|graying)\b"),
    ("alopecia", r"\balopecias?(?:[\s-]+areata|[\s-]+totalis|[\s-]+universalis)?\b"),
    ("androgenetic_alopecia", r"\b(?:androgenetic|androgenic|androgen)[\s-]+alopecia\b"),
    ("balding", r"\b(?:balding|non[\s-]?balding|baldness)\b"),
    ("scalp", r"\bscalp\b"),
    ("follicular_unit", r"\bfollicular[\s-]+unit\b"),
    ("trichogenic", r"\b(?:trichogenic|trichocyte|pilosebaceous)\w*\b"),
    ("hair_eruption", r"\bhair[\s-]+eruption\b"),
)


SAMPLE_PATTERNS: Sequence[PatternSpec] = TOPIC_PATTERNS + (
    ("bulge_cells", r"\bbulge[\s-]+(?:stem[\s-]+)?cells?\b"),
    ("hair_depletion_model", r"\b(?:depilat(?:ion|ed)|plucked[\s-]+hair)\b"),
)


STAGE1_PATTERNS: Sequence[PatternSpec] = TOPIC_PATTERNS + (
    ("hair_generic", r"\bhair\b"),
    ("follicular_epithelium", r"\bfollicular[\s-]+epitheli(?:um|a)\b"),
)


INCIDENTAL_PATTERNS: Sequence[PatternSpec] = (
    (
        "drug_indication",
        r"\b(?:approved|prescribed|indicated|licensed|marketed)"
        r".{0,90}\b(?:alopecia|baldness|hair[\s-]+loss)\b",
    ),
    (
        "adverse_event",
        r"\b(?:adverse[\s-]+events?|side[\s-]+effects?|toxicit(?:y|ies)|complications?)"
        r".{0,120}\b(?:alopecia|baldness|hair[\s-]+loss)\b",
    ),
    (
        "clinical_manifestation",
        r"\b(?:manifestations?|symptoms?|phenotypes?|characteri[sz]ed[\s-]+by)"
        r".{0,140}\b(?:alopecia|baldness|hair[\s-]+loss)\b",
    ),
    (
        "outcome_only",
        r"\b(?:avoid(?:s|ed|ing)?|prevent(?:s|ed|ing)?|less|decreas(?:e|ed|ing)|"
        r"reduc(?:e|ed|ing)|remission[\s-]+of)"
        r".{0,90}\b(?:hair[\s-]+follicle[\s-]+damage|hair[\s-]+loss|alopecia|baldness)\b",
    ),
    (
        "comparison_only",
        r"\b(?:shared[\s-]+with|adjacent[\s-]+to|associated[\s-]+with)"
        r".{0,60}\bhair[\s-]+follicles?\b",
    ),
    (
        "sample_contamination",
        r"\bhair[\s-]+follicles?.{0,100}\b(?:adjacent[\s-]+to|meibomian|"
        r"challenging[\s-]+to[\s-]+isolate)\b",
    ),
    (
        "tumor_origin_background",
        r"\bcomprise\w*.{0,30}\bepidermis[\s-]+and[\s-]+its[\s-]+associated"
        r"[\s-]+hair[\s-]+follicles?\b",
    ),
)


OFF_TOPIC_PATTERNS: Sequence[PatternSpec] = (
    ("renal", r"\b(?:renal|kidney|786[\s-]?o)\b"),
    ("cerebrovascular", r"\b(?:cerebral|brain|stroke|blood[\s-]+brain[\s-]+barrier)\b"),
    ("hepatic", r"\b(?:hepatocellular|hepatic|liver)\b"),
    ("bone_tumor", r"\b(?:osteosarcoma|osteogenic|bone)\b"),
    ("cardiovascular", r"\b(?:atheroscleros\w*|aortic|plasma[\s-]+cholesterol)\b"),
    ("ocular", r"\b(?:lens|cataract|cornea|corneal|limbal|retina|retinal)\b"),
    ("muscle", r"\b(?:myotonic[\s-]+dystrophy|skeletal[\s-]+muscle|myoblast)\b"),
    ("substance_use", r"\b(?:methamphetamine|substance[\s-]+use)\b"),
    ("meibomian", r"\b(?:meibomian|tarsal[\s-]+plates?)\b"),
    ("other_skin_appendage", r"\b(?:eccrine|sweat[\s-]+gland)\w*\b"),
    ("systemic_autoimmune", r"\b(?:polyendocrine|multi[\s-]?organ)\w*\b"),
    ("blood_only", r"\b(?:peripheral[\s-]+blood|pbmcs?|whole[\s-]+blood)\b"),
    (
        "non_hair_epidermal_culture",
        r"\b(?:foreskin|normal[\s-]+human[\s-]+epidermal[\s-]+keratinocytes?|nhek)\b",
    ),
    (
        "skin_carcinogenesis",
        r"\b(?:skin[\s-]+carcinogenesis|cutaneous[\s-]+chemical[\s-]+carcinogenesis|"
        r"chemically[\s-]+induced[\s-]+skin[\s-]+lesions?)\b",
    ),
    (
        "sensory_neuron",
        r"\b(?:mechanosensory|mechanoreceptors?|sensory[\s-]+neurons?|"
        r"c[\s-]?ltmrs?|free[\s-]+nerve[\s-]+endings?|touch[\s-]+sensation)\b",
    ),
)


SKIN_CONTEXT_PATTERN = re.compile(
    r"\b(?:skin|cutaneous|epiderm\w*|derm\w*|keratinocyte|melanocyte|wound)\b",
    re.IGNORECASE,
)
ASSAY_CONTEXT_PATTERN = re.compile(
    r"\b(?:rna[\s-]?seq|single[\s-]+cell|single[\s-]+nucleus|scrna|snrna|"
    r"transcriptom\w*|profil\w*|sequenc\w*|atac[\s-]?seq|methyl\w*|"
    r"sample\w*|isolat\w*|facs|sorted|biops\w*|organoid\w*|model\w*)\b",
    re.IGNORECASE,
)
PRIMARY_QUESTION_PATTERN = re.compile(
    r"\b(?:aim\w*|purpose|goal|investigat\w*|study|studied|examin\w*|"
    r"characteri[sz]\w*|profil\w*|analysis|analy[sz]\w*|reveal\w*|"
    r"regulat\w*|control\w*|develop\w*|regenerat\w*)\b",
    re.IGNORECASE,
)
WEAK_TOPIC_TERMS = {"scalp"}


@dataclass(frozen=True)
class RelevanceAssessment:
    """Serializable result of the two-stage assessment."""

    decision: str
    score: int
    stage1_pass: bool
    reason: str
    title_terms: List[str]
    summary_terms: List[str]
    design_terms: List[str]
    summary_sample_terms: List[str]
    incidental_signals: List[str]
    off_topic_signals: List[str]
    relevant_summary_sentences: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _text(record: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if value is not None:
            return str(value)
    return ""


def _matches(text: str, patterns: Iterable[PatternSpec]) -> List[str]:
    return [
        label
        for label, pattern in patterns
        if re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    ]


def _sentences(text: str) -> List[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+|[\r\n]+", text)
        if sentence.strip()
    ]


def _summary_evidence(summary: str) -> Tuple[List[str], int, List[str]]:
    sample_terms = set()
    central_sentences = 0
    incidental = set()

    for sentence in _sentences(summary):
        topic_terms = _matches(sentence, TOPIC_PATTERNS)
        if not topic_terms:
            continue

        sentence_incidental = _matches(sentence, INCIDENTAL_PATTERNS)
        incidental.update(sentence_incidental)
        if sentence_incidental:
            continue

        has_assay_context = bool(ASSAY_CONTEXT_PATTERN.search(sentence))
        has_primary_context = bool(PRIMARY_QUESTION_PATTERN.search(sentence))
        if has_assay_context:
            sample_terms.update(topic_terms)
        if has_assay_context or has_primary_context or len(topic_terms) >= 2:
            central_sentences += 1

    return sorted(sample_terms), central_sentences, sorted(incidental)


def assess_relevance(record: Mapping[str, Any]) -> RelevanceAssessment:
    """Assess one GEO record using retrieval evidence and subject validation.

    Decisions:
      * include: direct hair/alopecia subject or sample evidence.
      * review: plausible but insufficiently explicit evidence.
      * exclude: only incidental evidence or a contradicted off-topic subject.
    """

    title = _text(record, "Title", "title")
    summary = _text(record, "Summary", "summary")
    design = _text(record, "Overall_Design", "overall_design")
    combined = " ".join((title, summary, design))

    stage1_terms = _matches(combined, STAGE1_PATTERNS)
    stage1_pass = bool(stage1_terms)
    title_terms = _matches(title, TOPIC_PATTERNS)
    summary_terms = _matches(summary, TOPIC_PATTERNS)
    design_terms = _matches(design, SAMPLE_PATTERNS)
    summary_sample_terms, central_sentences, incidental = _summary_evidence(summary)

    off_topic_title = _matches(title, OFF_TOPIC_PATTERNS)
    off_topic_design = _matches(design, OFF_TOPIC_PATTERNS)
    off_topic = sorted(set(off_topic_title + off_topic_design))

    score = 0
    score += min(7, len(title_terms) * 4)
    score += min(9, len(design_terms) * 6)
    score += min(7, len(summary_sample_terms) * 4)
    score += min(4, central_sentences * 2)
    score += min(3, len(summary_terms))
    score -= min(8, len(incidental) * 4)
    score -= min(8, len(off_topic) * 4)

    strong_design_terms = [term for term in design_terms if term not in WEAK_TOPIC_TERMS]
    strong_summary_sample_terms = [
        term for term in summary_sample_terms if term not in WEAK_TOPIC_TERMS
    ]
    strong_summary_terms = [term for term in summary_terms if term not in WEAK_TOPIC_TERMS]
    strong_title_terms = [term for term in title_terms if term not in WEAK_TOPIC_TERMS]
    direct_sample_evidence = bool(strong_design_terms)
    corroborated_summary_sample = bool(strong_summary_sample_terms) and (
        not off_topic or bool(SKIN_CONTEXT_PATTERN.search(design))
    )
    title_evidence = bool(strong_title_terms) or (
        "scalp" in title_terms and bool(re.search(r"\bhair\b", title, re.IGNORECASE))
    )
    contradicted_title = (
        title_evidence
        and bool(off_topic_design)
        and (
            bool(off_topic_title)
            or "non_hair_epidermal_culture" in off_topic_design
        )
        and not direct_sample_evidence
    )
    sensory_neuron_only = (
        "sensory_neuron" in off_topic
        and not direct_sample_evidence
        and not title_evidence
    )
    incidental_only = bool(incidental) and not (
        direct_sample_evidence or title_evidence or summary_sample_terms
    )

    if not stage1_pass:
        decision = "exclude"
        reason = "第一阶段未发现毛囊/毛发/脱发候选词"
    elif direct_sample_evidence:
        decision = "include"
        reason = "实验设计明确包含毛囊、头皮、毛周期或相关细胞/样本"
    elif contradicted_title:
        decision = "exclude"
        reason = "标题虽提及毛发/脱发，但实验设计明确指向无关组织或疾病"
    elif sensory_neuron_only:
        decision = "exclude"
        reason = "组学对象是感觉神经元/触觉亚型，毛囊仅作为神经支配的解剖背景"
    elif title_evidence and not off_topic_title:
        decision = "include"
        reason = "标题以毛囊、毛发生物学或脱发为主要研究主题"
    elif title_evidence and central_sentences >= 1:
        decision = "review"
        reason = "标题含毛发主题，但同时存在其他疾病主题，需人工确认组学样本"
    elif corroborated_summary_sample and central_sentences >= 1:
        decision = "include"
        reason = "摘要明确说明毛囊/脱发相关组学对象，且未被无关实验设计否定"
    elif incidental_only:
        decision = "exclude"
        reason = "毛发/脱发仅作为药物适应证、不良事件、临床表现或次要结局出现"
    elif off_topic and not summary_sample_terms:
        decision = "exclude"
        reason = "研究对象明确属于其他器官/疾病，未发现毛囊相关样本证据"
    elif (
        central_sentences >= 2
        and strong_summary_terms
        and SKIN_CONTEXT_PATTERN.search(combined)
    ):
        decision = "include"
        reason = "摘要中多处以皮肤毛囊/毛发生物学为核心问题"
    else:
        decision = "review"
        reason = "存在毛发相关描述，但缺少足够的研究对象或样本证据"

    return RelevanceAssessment(
        decision=decision,
        score=score,
        stage1_pass=stage1_pass,
        reason=reason,
        title_terms=title_terms,
        summary_terms=summary_terms,
        design_terms=design_terms,
        summary_sample_terms=summary_sample_terms,
        incidental_signals=incidental,
        off_topic_signals=off_topic,
        relevant_summary_sentences=central_sentences,
    )


def with_relevance_metadata(
    record: Mapping[str, Any], assessment: RelevanceAssessment
) -> Dict[str, Any]:
    """Return a copy with compact audit metadata suitable for the public JSON."""

    enriched = dict(record)
    enriched["Relevance_Decision"] = assessment.decision
    enriched["Relevance_Score"] = assessment.score
    enriched["Relevance_Reason"] = assessment.reason
    enriched["Relevance_Evidence"] = {
        "title": assessment.title_terms,
        "summary": assessment.summary_terms,
        "overall_design": assessment.design_terms,
        "summary_sample": assessment.summary_sample_terms,
        "incidental": assessment.incidental_signals,
        "off_topic": assessment.off_topic_signals,
    }
    return enriched
