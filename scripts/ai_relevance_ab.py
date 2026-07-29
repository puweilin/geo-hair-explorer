#!/usr/bin/env python3
"""Compare rule-only, DeepSeek-only, and rule+AI relevance strategies.

The script is deliberately read-only with respect to ``data/geo_data.json``.
API responses are cached so an interrupted evaluation can be resumed without
paying for completed records again.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

import requests

from relevance_filter import assess_relevance


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "geo_data_raw_20260729.json"
DEFAULT_REFERENCE = REPO_ROOT / "reports" / "relevance_audit_20260729.json"
DEFAULT_ADJUDICATION = (
    REPO_ROOT / "reports" / "relevance_ai_disagreement_adjudication_20260729.json"
)
DEFAULT_CACHE = REPO_ROOT / "reports" / "cache" / "deepseek_relevance_ab.json"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "reports"
DEFAULT_MODEL = "deepseek-v4-pro"
DEFAULT_BASE_URL = "https://api.deepseek.com"
PROMPT_VERSION = "hair-geo-relevance-v1"
VALID_DECISIONS = {"include", "exclude", "review"}


SYSTEM_PROMPT = """You are a biomedical omics dataset curator.

Judge whether a GEO SERIES belongs in a Hair Follicle / Hair Biology / Alopecia
omics collection. Evaluate the study's actual scientific question and assayed
samples, not keyword presence alone.

INCLUDE when at least one of these is true:
1. Hair follicle, hair cycle, hair shaft/pigmentation, follicular stem cells,
   dermal papilla/sheath, root sheath, hair matrix, or closely related cells
   are a primary biological subject or directly assayed sample.
2. Alopecia or another hair-loss disorder is the primary disease under study,
   even if the profiled sample is blood, immune cells, or whole skin.
3. Hair-follicle development, regeneration/neogenesis, cycling, degeneration,
   pigmentation/greying, or treatment response is a central study endpoint and
   the omics experiment is designed to explain it.
4. A broader skin dataset contains explicit, reusable hair-follicle cell
   populations or compartments central to the analysis.

EXCLUDE when hair/alopecia is only:
1. A drug indication (for example, minoxidil is described as an alopecia drug)
   in a study whose real subject is cancer or another unrelated disease.
2. An adverse event, clinical-history detail, syndrome manifestation, or
   secondary phenotype while the assayed tissue addresses another organ.
3. Background knowledge, an anatomical comparison, or one incidental structure
   in a general skin study whose omics samples do not address hair biology.
4. A sampling location such as scalp, without a hair-follicle or hair-disease
   question.

Use REVIEW only when the supplied metadata is genuinely insufficient or the
study is a borderline broad-skin dataset. Do not use REVIEW merely because the
study is complex.

Return one JSON object only, with exactly this shape:
{
  "decision": "include | exclude | review",
  "confidence": 0.0,
  "primary_subject": "short description",
  "evidence": ["specific metadata evidence"],
  "reason": "one concise reason"
}

The response must be valid JSON. Do not reveal chain-of-thought."""


@dataclass(frozen=True)
class Metrics:
    total: int
    include: int
    exclude: int
    review: int
    coverage: float
    accuracy_on_decided: float
    effective_accuracy: float
    precision_include: float
    recall_include: float
    f1_include: float
    false_include: int
    false_exclude: int


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    temporary.replace(path)


def record_payload(record: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "Accession": str(record.get("Accession", "")),
        "Title": str(record.get("Title", "")),
        "Organism": str(record.get("Organism", "")),
        "Data_Type": str(record.get("Data_Type", "")),
        "Summary": str(record.get("Summary", "")),
        "Overall_Design": str(record.get("Overall_Design", "")),
    }


def content_hash(record: Mapping[str, Any], model: str) -> str:
    payload = {
        "prompt_version": PROMPT_VERSION,
        "model": model,
        "record": record_payload(record),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def normalize_assessment(raw: Mapping[str, Any]) -> Dict[str, Any]:
    decision = str(raw.get("decision", "")).strip().lower()
    if decision not in VALID_DECISIONS:
        raise ValueError(f"invalid decision: {decision!r}")

    confidence = float(raw.get("confidence"))
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(f"confidence outside [0, 1]: {confidence}")

    evidence_raw = raw.get("evidence", [])
    if isinstance(evidence_raw, str):
        evidence = [evidence_raw]
    elif isinstance(evidence_raw, Sequence):
        evidence = [str(item).strip() for item in evidence_raw if str(item).strip()]
    else:
        raise ValueError("evidence must be a string or array")

    return {
        "decision": decision,
        "confidence": round(confidence, 4),
        "primary_subject": str(raw.get("primary_subject", "")).strip(),
        "evidence": evidence[:6],
        "reason": str(raw.get("reason", "")).strip(),
    }


def call_deepseek(
    record: Mapping[str, Any],
    *,
    api_key: str,
    base_url: str,
    model: str,
    timeout: int,
    max_retries: int,
) -> Dict[str, Any]:
    user_prompt = (
        "Classify this GEO record. Return valid JSON only.\n\n"
        + json.dumps(record_payload(record), ensure_ascii=False, indent=2)
    )
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "thinking": {"type": "disabled"},
                    "temperature": 0,
                    "max_tokens": 500,
                    "response_format": {"type": "json_object"},
                    "stream": False,
                },
                timeout=timeout,
            )
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            if not content:
                raise ValueError("DeepSeek returned empty content")
            assessment = normalize_assessment(json.loads(content))
            usage = body.get("usage") or {}
            return {
                "assessment": assessment,
                "usage": {
                    "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
                    "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
                    "total_tokens": int(usage.get("total_tokens", 0) or 0),
                },
                "response_model": str(body.get("model", model)),
            }
        except (
            requests.RequestException,
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            last_error = error
            status = getattr(getattr(error, "response", None), "status_code", None)
            retryable = status is None or status in {408, 409, 429} or status >= 500
            if attempt + 1 >= max_retries or not retryable:
                break
            time.sleep(min(20, 2 ** attempt))

    raise RuntimeError(f"DeepSeek classification failed: {last_error}") from last_error


def reference_labels(rows: Iterable[Mapping[str, Any]]) -> Dict[str, str]:
    labels: Dict[str, str] = {}
    for row in rows:
        accession = str(row.get("Accession", ""))
        decision = str(row.get("Final_Decision", "")).lower()
        if not accession or decision not in {"include", "exclude"}:
            raise ValueError(f"invalid reference row: {accession!r} / {decision!r}")
        labels[accession] = decision
    return labels


def apply_adjudication(
    labels: Mapping[str, str],
    path: Path | None,
) -> tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
    corrected = dict(labels)
    changes: Dict[str, Dict[str, str]] = {}
    if path is None or not path.exists():
        return corrected, changes

    raw = load_json(path)
    for accession, item in raw.get("decisions", {}).items():
        if accession not in corrected:
            raise ValueError(f"adjudication contains unknown accession: {accession}")
        decision = str(item.get("decision", "")).lower()
        if decision not in {"include", "exclude"}:
            raise ValueError(f"invalid adjudicated decision for {accession}: {decision}")
        original = corrected[accession]
        corrected[accession] = decision
        if original != decision:
            changes[accession] = {
                "from": original,
                "to": decision,
                "reason": str(item.get("reason", "")),
            }
    return corrected, changes


def calculate_metrics(
    predictions: Mapping[str, str],
    references: Mapping[str, str],
) -> Metrics:
    total = len(references)
    counts = Counter(predictions[accession] for accession in references)
    decided = counts["include"] + counts["exclude"]
    correct = sum(
        predictions[accession] == reference
        for accession, reference in references.items()
        if predictions[accession] != "review"
    )
    tp = sum(
        predictions[accession] == "include" and reference == "include"
        for accession, reference in references.items()
    )
    fp = sum(
        predictions[accession] == "include" and reference == "exclude"
        for accession, reference in references.items()
    )
    fn = sum(
        predictions[accession] == "exclude" and reference == "include"
        for accession, reference in references.items()
    )
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return Metrics(
        total=total,
        include=counts["include"],
        exclude=counts["exclude"],
        review=counts["review"],
        coverage=decided / total if total else 0.0,
        accuracy_on_decided=correct / decided if decided else 0.0,
        effective_accuracy=correct / total if total else 0.0,
        precision_include=precision,
        recall_include=recall,
        f1_include=f1,
        false_include=fp,
        false_exclude=fn,
    )


def hybrid_decision(rule_decision: str, ai: Mapping[str, Any]) -> str:
    """Auto-decide only high-confidence rule/AI consensus; otherwise review."""

    ai_decision = str(ai["decision"])
    confidence = float(ai["confidence"])
    if (
        rule_decision in {"include", "exclude"}
        and ai_decision == rule_decision
        and confidence >= 0.85
    ):
        return rule_decision
    return "review"


def percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def markdown_report(
    *,
    records: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
    metrics_by_strategy: Mapping[str, Metrics],
    model: str,
    repeat: int,
    stability: Mapping[str, Any],
    token_usage: Mapping[str, int],
    documented_label_corrections: Mapping[str, Mapping[str, str]],
    adjudication_count: int,
    manual_review_count: int,
) -> str:
    title_by_accession = {
        str(record.get("Accession", "")): str(record.get("Title", ""))
        for record in records
    }
    strategy_names = {
        "rule": "A：现有两阶段规则",
        "ai": f"B：AI-only（{model}）",
        "hybrid": "C：规则+AI 高置信共识",
    }
    lines = [
        "# GEO 相关性判定 AI A/B 回溯报告",
        "",
        f"- 运行时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- 数据集数：{len(records)}",
        f"- AI 模型：`{model}`（非思考模式，temperature=0）",
        f"- Prompt 版本：`{PROMPT_VERSION}`",
        f"- AI 独立重复次数：{repeat}",
        (
            f"- 参考标签：现有两阶段规则 + {manual_review_count} 条人工边界复核 + "
            f"证据裁决 {adjudication_count} 条"
            f"（修正 {len(documented_label_corrections)} 条早期标签）；"
            "仍非独立盲法金标准，指标可能偏向现有规则。"
        ),
        "",
        "## 总体指标",
        "",
        "| 策略 | 自动覆盖率 | 决定样本准确率 | 全体有效准确率 | 纳入精确率 | 纳入召回率 | F1 | 错误纳入 | 错误排除 | 转人工 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key in ("rule", "ai", "hybrid"):
        metric = metrics_by_strategy[key]
        lines.append(
            f"| {strategy_names[key]} | {percent(metric.coverage)} | "
            f"{percent(metric.accuracy_on_decided)} | "
            f"{percent(metric.effective_accuracy)} | "
            f"{percent(metric.precision_include)} | "
            f"{percent(metric.recall_include)} | "
            f"{percent(metric.f1_include)} | {metric.false_include} | "
            f"{metric.false_exclude} | {metric.review} |"
        )

    lines.extend([
        "",
        "## 分歧裁决后修正的参考标签",
        "",
        "| Accession | 原标签 | 修正标签 | 理由 |",
        "|---|---:|---:|---|",
    ])
    for accession, change in sorted(documented_label_corrections.items()):
        reason = str(change["reason"]).replace("|", r"\|")
        lines.append(
            f"| {accession} | {change['from']} | {change['to']} | {reason} |"
        )

    lines.extend([
        "",
        "## AI 稳定性",
        "",
        f"- 可比较记录：{stability['comparable']}",
        f"- 两次决定完全一致：{stability['same']}（{percent(stability['agreement'])}）",
        f"- 决定发生变化：{stability['changed']}",
        f"- API 总 tokens：{token_usage['total_tokens']}",
        "",
        "## AI 与参考标签分歧",
        "",
        "| Accession | 标题 | 参考 | AI | 置信度 | AI 理由 |",
        "|---|---|---:|---:|---:|---|",
    ])
    disagreements = [
        row
        for row in rows
        if row["AI_Decision"] != "review"
        and row["AI_Decision"] != row["Reference_Decision"]
    ]
    disagreements.sort(
        key=lambda row: (-float(row["AI_Confidence"]), str(row["Accession"]))
    )
    for row in disagreements:
        accession = str(row["Accession"])
        title = title_by_accession[accession].replace("|", r"\|")
        reason = str(row["AI_Reason"]).replace("|", r"\|")
        lines.append(
            f"| {accession} | {title} | {row['Reference_Decision']} | "
            f"{row['AI_Decision']} | {row['AI_Confidence']:.2f} | {reason} |"
        )

    lines.extend([
        "",
        "## 解释",
        "",
        "- `自动覆盖率`：无需人工即可给出 include/exclude 的比例。",
        "- `决定样本准确率`：只在非 review 样本上计算。",
        "- `全体有效准确率`：把 review 视作未完成，因此能体现人工成本。",
        "- 混合策略仅在规则与 AI 同意且 AI 置信度不低于 0.85 时自动处理；其他记录进入人工队列。",
        "",
    ])
    return "\n".join(lines)


def save_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument(
        "--adjudication",
        type=Path,
        default=DEFAULT_ADJUDICATION,
        help="可选的分歧证据裁决文件；其中 decisions 会覆盖参考标签",
    )
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--label", default="20260729")
    parser.add_argument("--model", default=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL))
    parser.add_argument(
        "--base-url",
        default=os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL),
    )
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise SystemExit("DEEPSEEK_API_KEY is not set")
    if args.repeat < 1:
        raise SystemExit("--repeat must be at least 1")

    records = load_json(args.input)
    reference_rows = load_json(args.reference)
    if not isinstance(records, list) or not isinstance(reference_rows, list):
        raise ValueError("input and reference files must contain JSON arrays")

    original_references = reference_labels(reference_rows)
    references, label_changes = apply_adjudication(
        original_references,
        args.adjudication,
    )
    adjudication_raw = (
        load_json(args.adjudication)
        if args.adjudication.exists()
        else {"decisions": {}, "label_corrections": []}
    )
    adjudication_decisions = adjudication_raw.get("decisions", {})
    documented_label_corrections = {}
    for accession in adjudication_raw.get("label_corrections", []):
        item = adjudication_decisions[accession]
        documented_label_corrections[accession] = {
            "from": "include",
            "to": str(item["decision"]),
            "reason": str(item.get("reason", "")),
        }
    record_by_accession = {
        str(record.get("Accession", "")): record for record in records
    }
    if set(record_by_accession) != set(references):
        missing_reference = set(record_by_accession) - set(references)
        missing_record = set(references) - set(record_by_accession)
        raise ValueError(
            f"accession mismatch; no reference={sorted(missing_reference)}, "
            f"no record={sorted(missing_record)}"
        )

    cache: Dict[str, Any]
    if args.cache.exists() and not args.force:
        cache = load_json(args.cache)
    else:
        cache = {"meta": {}, "entries": {}}
    cache.setdefault("entries", {})
    cache["meta"] = {
        "prompt_version": PROMPT_VERSION,
        "model": args.model,
        "base_url": args.base_url,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    cache_lock = threading.Lock()

    def classify_one(repeat_index: int, record: Mapping[str, Any]) -> tuple[str, Dict[str, Any]]:
        accession = str(record.get("Accession", ""))
        key = f"{args.label}:repeat-{repeat_index}:{accession}"
        expected_hash = content_hash(record, args.model)
        cached = cache["entries"].get(key)
        if (
            cached
            and not args.force
            and cached.get("content_hash") == expected_hash
        ):
            return key, cached

        result = call_deepseek(
            record,
            api_key=api_key,
            base_url=args.base_url,
            model=args.model,
            timeout=args.timeout,
            max_retries=args.max_retries,
        )
        entry = {
            "accession": accession,
            "repeat": repeat_index,
            "content_hash": expected_hash,
            "assessment": result["assessment"],
            "usage": result["usage"],
            "response_model": result["response_model"],
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        with cache_lock:
            cache["entries"][key] = entry
            cache["meta"]["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_json_atomic(args.cache, cache)
        return key, entry

    tasks = []
    results: Dict[int, Dict[str, Dict[str, Any]]] = {
        index: {} for index in range(1, args.repeat + 1)
    }
    total_calls = len(records) * args.repeat
    completed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for repeat_index in range(1, args.repeat + 1):
            for record in records:
                tasks.append(executor.submit(classify_one, repeat_index, record))
        for future in as_completed(tasks):
            _, entry = future.result()
            results[int(entry["repeat"])][str(entry["accession"])] = entry
            completed += 1
            if completed % 25 == 0 or completed == total_calls:
                print(f"AI 回溯进度: {completed}/{total_calls}", flush=True)

    first_run = results[1]
    rule_predictions: Dict[str, str] = {}
    ai_predictions: Dict[str, str] = {}
    hybrid_predictions: Dict[str, str] = {}
    output_rows = []
    for record in records:
        accession = str(record.get("Accession", ""))
        rule = assess_relevance(record)
        ai = first_run[accession]["assessment"]
        rule_predictions[accession] = rule.decision
        ai_predictions[accession] = str(ai["decision"])
        hybrid_predictions[accession] = hybrid_decision(rule.decision, ai)
        repeat_decisions = [
            results[index][accession]["assessment"]["decision"]
            for index in range(1, args.repeat + 1)
        ]
        output_rows.append({
            "Accession": accession,
            "Title": str(record.get("Title", "")),
            "Reference_Decision": references[accession],
            "Rule_Decision": rule.decision,
            "Rule_Reason": rule.reason,
            "AI_Decision": ai["decision"],
            "AI_Confidence": ai["confidence"],
            "AI_Primary_Subject": ai["primary_subject"],
            "AI_Reason": ai["reason"],
            "AI_Evidence": " || ".join(ai["evidence"]),
            "AI_Repeat_Decisions": " || ".join(repeat_decisions),
            "Hybrid_Decision": hybrid_predictions[accession],
        })

    metrics_by_strategy = {
        "rule": calculate_metrics(rule_predictions, references),
        "ai": calculate_metrics(ai_predictions, references),
        "hybrid": calculate_metrics(hybrid_predictions, references),
    }
    if args.repeat >= 2:
        decision_vectors = {
            accession: [
                results[index][accession]["assessment"]["decision"]
                for index in range(1, args.repeat + 1)
            ]
            for accession in references
        }
        same = sum(len(set(vector)) == 1 for vector in decision_vectors.values())
        stability = {
            "comparable": len(decision_vectors),
            "same": same,
            "changed": len(decision_vectors) - same,
            "agreement": same / len(decision_vectors) if decision_vectors else 0.0,
        }
    else:
        stability = {
            "comparable": 0,
            "same": 0,
            "changed": 0,
            "agreement": 0.0,
        }

    token_usage = Counter()
    for run_results in results.values():
        for entry in run_results.values():
            token_usage.update(entry.get("usage", {}))

    report_payload = {
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": args.model,
            "prompt_version": PROMPT_VERSION,
            "repeat": args.repeat,
            "reference_warning": (
                "Reference labels combine rule output, 48 manual reviews, and "
                "evidence adjudication of AI disagreements; they are not an "
                "independent blinded gold standard."
            ),
            "label_changes_on_current_reference": label_changes,
            "documented_label_corrections": documented_label_corrections,
        },
        "metrics": {
            key: asdict(metric) for key, metric in metrics_by_strategy.items()
        },
        "stability": stability,
        "token_usage": dict(token_usage),
        "rows": output_rows,
    }
    json_path = args.output_dir / f"ai_relevance_ab_{args.label}.json"
    csv_path = args.output_dir / f"ai_relevance_ab_{args.label}.csv"
    markdown_path = args.output_dir / f"ai_relevance_ab_{args.label}.md"
    save_json_atomic(json_path, report_payload)
    save_csv(csv_path, output_rows)
    markdown_path.write_text(
        markdown_report(
            records=records,
            rows=output_rows,
            metrics_by_strategy=metrics_by_strategy,
            model=args.model,
            repeat=args.repeat,
            stability=stability,
            token_usage=token_usage,
            documented_label_corrections=documented_label_corrections,
            adjudication_count=len(adjudication_decisions),
            manual_review_count=sum(
                bool(row.get("Manual_Review")) for row in reference_rows
            ),
        ),
        encoding="utf-8",
    )
    print(f"JSON: {json_path}")
    print(f"CSV: {csv_path}")
    print(f"Markdown: {markdown_path}")


if __name__ == "__main__":
    main()
