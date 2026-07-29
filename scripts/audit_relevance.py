#!/usr/bin/env python3
"""Backtest the two-stage relevance policy against an existing GEO JSON corpus."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Dict, Mapping

from relevance_filter import assess_relevance, with_relevance_metadata


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "geo_data_raw_20260729.json"
DEFAULT_MANUAL_REVIEW = (
    REPO_ROOT / "reports" / "relevance_manual_review_20260729.json"
)
DEFAULT_ADJUDICATION = (
    REPO_ROOT / "reports" / "relevance_ai_disagreement_adjudication_20260729.json"
)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def load_manual_decisions(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {}

    raw = load_json(path)
    decisions: Dict[str, Dict[str, str]] = {}
    for decision in ("include", "exclude"):
        for accession, reason in raw.get(decision, {}).items():
            decisions[accession] = {"decision": decision, "reason": reason}
    return decisions


def load_adjudicated_decisions(path: Path) -> Dict[str, Dict[str, str]]:
    """Load evidence-based overrides that may correct any automated decision."""

    if not path.exists():
        return {}
    raw = load_json(path)
    decisions: Dict[str, Dict[str, str]] = {}
    for accession, item in raw.get("decisions", {}).items():
        decision = str(item.get("decision", "")).lower()
        if decision not in {"include", "exclude"}:
            raise ValueError(
                f"证据裁决包含无效决定: {accession}={decision!r}"
            )
        decisions[accession] = {
            "decision": decision,
            "reason": str(item.get("reason", "")),
        }
    return decisions


def audit_record(
    record: Mapping[str, Any],
    manual_decisions: Mapping[str, Mapping[str, str]],
    adjudicated_decisions: Mapping[str, Mapping[str, str]],
) -> Dict[str, Any]:
    assessment = assess_relevance(record)
    accession = str(record.get("Accession", ""))
    manual = manual_decisions.get(accession)
    adjudicated = adjudicated_decisions.get(accession)
    if adjudicated:
        final_decision = adjudicated["decision"]
        final_reason = adjudicated["reason"]
        decision_source = "evidence_adjudication"
    elif manual:
        final_decision = manual["decision"]
        final_reason = manual["reason"]
        decision_source = "manual_boundary_review"
    else:
        final_decision = assessment.decision
        final_reason = assessment.reason
        decision_source = "automated_rule"

    return {
        "Accession": accession,
        "Title": record.get("Title", ""),
        "Automated_Decision": assessment.decision,
        "Automated_Score": assessment.score,
        "Automated_Reason": assessment.reason,
        "Final_Decision": final_decision,
        "Final_Reason": final_reason,
        "Decision_Source": decision_source,
        "Manual_Review": bool(manual),
        "Evidence_Adjudication": bool(adjudicated),
        "Title_Terms": assessment.title_terms,
        "Summary_Terms": assessment.summary_terms,
        "Overall_Design_Terms": assessment.design_terms,
        "Summary_Sample_Terms": assessment.summary_sample_terms,
        "Incidental_Signals": assessment.incidental_signals,
        "Off_Topic_Signals": assessment.off_topic_signals,
        "Relevant_Summary_Sentences": assessment.relevant_summary_sentences,
        "GEO_Link": record.get("GEO_Link", ""),
    }


def save_csv(path: Path, rows: list[Mapping[str, Any]]) -> None:
    list_fields = {
        "Title_Terms",
        "Summary_Terms",
        "Overall_Design_Terms",
        "Summary_Sample_Terms",
        "Incidental_Signals",
        "Off_Topic_Signals",
    }
    fieldnames = list(rows[0].keys()) if rows else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            flattened = dict(row)
            for field in list_fields:
                flattened[field] = "; ".join(flattened[field])
            writer.writerow(flattened)


def markdown_report(
    rows: list[Mapping[str, Any]],
    source_path: Path,
    manual_path: Path,
    adjudication_path: Path,
) -> str:
    automated_counts = Counter(row["Automated_Decision"] for row in rows)
    final_counts = Counter(row["Final_Decision"] for row in rows)
    excluded = [row for row in rows if row["Final_Decision"] == "exclude"]
    retained_reviews = [
        row
        for row in rows
        if row["Manual_Review"] and row["Final_Decision"] == "include"
    ]

    lines = [
        "# GEO Hair Follicle / AGA 两阶段相关性回溯审计",
        "",
        f"- 审计日期：{date.today().isoformat()}",
        f"- 源数据：`{source_path.name}`",
        f"- 总记录数：{len(rows)}",
        (
            "- 自动判定："
            f"纳入 {automated_counts['include']}；"
            f"待人工复核 {automated_counts['review']}；"
            f"排除 {automated_counts['exclude']}"
        ),
        (
            "- 人工复核后："
            f"保留 {final_counts['include']}；"
            f"排除 {final_counts['exclude']}；"
            f"未决 {final_counts['review']}"
        ),
        f"- 人工复核依据：`{manual_path.name}`",
        f"- AI 分歧证据裁决：`{adjudication_path.name}`",
        "",
        "## 最终排除记录",
        "",
        "| Accession | 标题 | 判定来源 | 排除理由 |",
        "|---|---|---|---|",
    ]
    for row in excluded:
        source = {
            "evidence_adjudication": "AI 分歧证据裁决",
            "manual_boundary_review": "人工边界复核",
            "automated_rule": "自动规则",
        }[str(row["Decision_Source"])]
        title = str(row["Title"]).replace("|", r"\|")
        reason = str(row["Final_Reason"]).replace("|", r"\|")
        lines.append(
            f"| {row['Accession']} | {title} | {source} | {reason} |"
        )

    lines.extend([
        "",
        "## 自动规则未直接决定、经人工确认保留的记录",
        "",
        "| Accession | 标题 | 保留理由 |",
        "|---|---|---|",
    ])
    for row in retained_reviews:
        title = str(row["Title"]).replace("|", r"\|")
        reason = str(row["Final_Reason"]).replace("|", r"\|")
        lines.append(f"| {row['Accession']} | {title} | {reason} |")

    lines.extend([
        "",
        "## 判定口径",
        "",
        "第一阶段保持高召回，只负责发现候选记录。第二阶段要求标题、摘要或实验设计能够证明毛囊、毛周期、头皮、脱发疾病或相关细胞/样本是主要研究对象。药物适应证、不良事件、综合征伴随症状、普通 scalp 取材和与其他皮肤附属器官的比较，不再单独构成纳入证据。",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--manual-review", type=Path, default=DEFAULT_MANUAL_REVIEW)
    parser.add_argument(
        "--adjudication",
        type=Path,
        default=DEFAULT_ADJUDICATION,
    )
    parser.add_argument(
        "--label",
        default="20260729",
        help="输出文件标签，默认使用本次回溯日期",
    )
    args = parser.parse_args()

    records = load_json(args.input)
    if not isinstance(records, list):
        raise ValueError("输入 JSON 必须是记录数组")

    accessions = [record.get("Accession") for record in records]
    if len(accessions) != len(set(accessions)):
        raise ValueError("输入数据包含重复 Accession")

    manual_decisions = load_manual_decisions(args.manual_review)
    adjudicated_decisions = load_adjudicated_decisions(args.adjudication)
    unknown_adjudications = set(adjudicated_decisions) - set(accessions)
    if unknown_adjudications:
        raise ValueError(
            "证据裁决包含源数据中不存在的记录: "
            + ", ".join(sorted(unknown_adjudications))
        )
    rows = [
        audit_record(record, manual_decisions, adjudicated_decisions)
        for record in records
    ]

    auto_review_accessions = {
        row["Accession"] for row in rows if row["Automated_Decision"] == "review"
    }
    missing_reviews = auto_review_accessions - set(manual_decisions)
    unexpected_reviews = set(manual_decisions) - auto_review_accessions
    if missing_reviews:
        raise ValueError(
            "人工复核文件未覆盖以下待复核记录: "
            + ", ".join(sorted(missing_reviews))
        )
    if unexpected_reviews:
        raise ValueError(
            "人工复核文件包含当前非 review 记录: "
            + ", ".join(sorted(unexpected_reviews))
        )

    reports_dir = REPO_ROOT / "reports"
    json_path = reports_dir / f"relevance_audit_{args.label}.json"
    csv_path = reports_dir / f"relevance_audit_{args.label}.csv"
    md_path = reports_dir / f"relevance_audit_{args.label}.md"
    excluded_path = reports_dir / f"relevance_excluded_{args.label}.json"
    curated_path = REPO_ROOT / "data" / f"geo_data_curated_{args.label}.json"

    save_json(json_path, rows)
    save_csv(csv_path, rows)
    save_json(
        excluded_path,
        [row for row in rows if row["Final_Decision"] == "exclude"],
    )

    row_by_accession = {row["Accession"]: row for row in rows}
    curated = []
    for record in records:
        row = row_by_accession[record["Accession"]]
        if row["Final_Decision"] != "include":
            continue
        assessment = assess_relevance(record)
        enriched = with_relevance_metadata(record, assessment)
        enriched["Relevance_Final_Decision"] = "include"
        enriched["Relevance_Final_Source"] = row["Decision_Source"]
        if row["Manual_Review"]:
            enriched["Relevance_Manual_Reason"] = row["Final_Reason"]
        if row["Evidence_Adjudication"]:
            enriched["Relevance_Adjudication_Reason"] = row["Final_Reason"]
        curated.append(enriched)
    save_json(curated_path, curated)

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(
        markdown_report(
            rows,
            args.input,
            args.manual_review,
            args.adjudication,
        ),
        encoding="utf-8",
    )

    counts = Counter(row["Final_Decision"] for row in rows)
    print(
        f"审计完成: 总计 {len(rows)}，保留 {counts['include']}，"
        f"排除 {counts['exclude']}，未决 {counts['review']}"
    )
    print(f"报告: {md_path}")
    print(f"候选清洗集: {curated_path}")


if __name__ == "__main__":
    main()
