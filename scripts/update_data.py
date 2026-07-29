#!/usr/bin/env python3
"""
GEO 数据增量更新脚本
用于 GitHub Actions 自动更新
"""

import os
import json
import time
import re
import requests
from datetime import datetime, timedelta
from Bio import Entrez

from relevance_filter import assess_relevance, with_relevance_metadata

# 配置
NCBI_EMAIL = os.environ.get('NCBI_EMAIL', '')
NCBI_API_KEY = os.environ.get('NCBI_API_KEY', '')
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_BASE_URL = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com').rstrip('/')
DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-v4-flash')

# Hair Follicle / AGA 搜索配置
SEARCH_CONFIG = {
    "keywords": [
        "hair follicle", "alopecia", "scalp hair", "hair scalp",
        "androgenetic alopecia", "hair loss", "dermal papilla",
        "hair cycle", "hair growth", "baldness"
    ],
    "organisms": ["Homo sapiens", "Mus musculus"],
    "data_types": [
        "Expression profiling by high throughput sequencing",
        "Methylation profiling by array",
        "Methylation profiling by high throughput sequencing",
        "Genome binding/occupancy profiling by high throughput sequencing"
    ],
    "require_keywords": [
        "hair follicle", "hair growth", "hair loss", "hair cycle",
        "hair shaft", "hair bulb", "hair root", "hair stem",
        "alopecia", "baldness", "dermal papilla", "hair keratinocyte",
        "anagen", "catagen", "telogen", "trichocyte", "pilosebaceous",
        "hair greying", "hair graying", "scalp", "androgenetic",
        "outer root sheath", "inner root sheath", "hair matrix"
    ],
    "exclude_keywords": [
        "ovary", "ovarian", "oocyte", "granulosa", "cumulus",
        "antral follicle", "primordial follicle", "follicular fluid",
        "oogenesis", "corpus luteum", "theca cell", "preantral",
        "preovulatory", "ovulation", "IVF", "in vitro fertilization",
        "follicle-stimulating hormone", "FSH",
        "thyroid follicle", "lymphoid follicle", "dental follicle",
        "salivary gland", "lymph node", "germinal center"
    ]
}

DATA_FILE = "data/geo_data.json"
REVIEW_FILE = "data/relevance_review_queue.json"
DECISION_LOG_FILE = "data/relevance_decision_log.json"


def setup_entrez():
    """配置 Entrez"""
    Entrez.email = NCBI_EMAIL
    if NCBI_API_KEY:
        Entrez.api_key = NCBI_API_KEY


def build_query():
    """构建搜索查询"""
    keyword_query = " OR ".join([f'"{kw}"' for kw in SEARCH_CONFIG["keywords"]])
    org_query = " OR ".join([f'"{org}"[Organism]' for org in SEARCH_CONFIG["organisms"]])
    type_query = " OR ".join([f'"{t}"[DataSet Type]' for t in SEARCH_CONFIG["data_types"]])

    return f"({keyword_query}) AND ({org_query}) AND ({type_query})"


def search_geo(max_retries=3):
    """搜索 GEO 数据库（带重试机制）"""
    query = build_query()
    end_date = datetime.now().strftime("%Y/%m/%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y/%m/%d")
    print(f"搜索查询: {query[:100]}...")
    print(f"日期范围: {start_date} - {end_date}")

    for attempt in range(max_retries):
        try:
            handle = Entrez.esearch(
                db="gds", term=query, retmax=500, usehistory="y",
                mindate=start_date, maxdate=end_date, datetype="pdat"
            )
            results = Entrez.read(handle)
            handle.close()
            return results.get("IdList", [])
        except Exception as e:
            print(f"搜索失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(10)  # 等待10秒后重试
            else:
                print("所有重试都失败了")
                return []


def fetch_summaries(id_list, max_retries=3):
    """获取数据集摘要（带重试机制）"""
    if not id_list:
        return []

    for attempt in range(max_retries):
        try:
            handle = Entrez.esummary(db="gds", id=",".join(id_list))
            records = Entrez.read(handle)
            handle.close()
            return records
        except Exception as e:
            print(f"获取摘要失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(10)
            else:
                return []


def passes_stage1_filter(record):
    """第一阶段高召回过滤：保留候选词命中，同时去除已知同名歧义。"""
    title = record.get("title", "").lower()
    summary = record.get("summary", "").lower()
    combined = title + " " + summary

    # 候选记录至少命中一个宽泛检索词。
    has_required = any(
        kw.lower() in combined for kw in SEARCH_CONFIG["require_keywords"]
    )
    if not has_required:
        return False

    # 去除 ovarian/thyroid/lymphoid follicle 等稳定的词义歧义。
    has_excluded = any(
        kw.lower() in combined for kw in SEARCH_CONFIG["exclude_keywords"]
    )
    if has_excluded:
        return False

    return True


def passes_filter(record):
    """向后兼容旧调用；最终纳入仍须执行第二阶段主题评估。"""
    return passes_stage1_filter(record)


def clean_pubmed_ids(pubmed_str):
    """清理 PubMed ID 格式"""
    if not pubmed_str:
        return ""
    numbers = re.findall(r'IntegerElement\((\d+)', str(pubmed_str))
    if numbers:
        return "; ".join(numbers)
    numbers = re.findall(r'\d+', str(pubmed_str))
    if numbers:
        return "; ".join(numbers)
    return str(pubmed_str)


def generate_ai_summary(title, summary, data_type, max_retries=3):
    """使用 DeepSeek 生成 AI 摘要。"""
    if not DEEPSEEK_API_KEY:
        print("    跳过 AI 摘要：未设置 DEEPSEEK_API_KEY")
        return ""

    prompt = f"""请用中文为以下GEO数据集生成一个精炼的科研摘要（80-120字）：

标题: {title}
数据类型: {data_type}
研究摘要: {summary[:800]}

要求：
1. 概述研究目的和科学问题
2. 说明使用的技术方法
3. 总结主要发现或研究价值
4. 使用专业但易懂的中文表达

请直接输出中文摘要："""

    for attempt in range(max_retries):
        try:
            response = requests.post(
                f'{DEEPSEEK_BASE_URL}/chat/completions',
                headers={
                    "Authorization": f'Bearer {DEEPSEEK_API_KEY}',
                    "Content-Type": "application/json"
                },
                json={
                    "model": DEEPSEEK_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一名严谨的生物医学数据策展编辑。只输出最终中文摘要，不展示推理过程。"
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "thinking": {"type": "disabled"},
                    "max_tokens": 400,
                    "temperature": 0.3,
                    "stream": False
                },
                timeout=90
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        except (requests.RequestException, KeyError, TypeError, ValueError) as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            status_text = f"HTTP {status}" if status else type(e).__name__
            print(f"    DeepSeek 摘要生成失败 ({attempt + 1}/{max_retries}, {status_text}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    return ""


def backfill_missing_ai_summaries(data):
    """补齐历史记录中缺失的 AI 摘要，并统一两个摘要字段。"""
    updated_count = 0
    for record in data:
        existing_summary = record.get("AI_Summary_CN") or record.get("AI_Summary")
        if existing_summary and (
            record.get("AI_Summary_CN") != existing_summary
            or record.get("AI_Summary") != existing_summary
        ):
            record["AI_Summary_CN"] = existing_summary
            record["AI_Summary"] = existing_summary
            updated_count += 1

    if not DEEPSEEK_API_KEY:
        missing_count = sum(
            not (record.get("AI_Summary_CN") or record.get("AI_Summary"))
            for record in data
        )
        if missing_count:
            print(f"待补齐 AI 摘要: {missing_count} 条（未设置 DEEPSEEK_API_KEY，本次跳过）")
        return updated_count

    missing_records = [
        record for record in data
        if not (record.get("AI_Summary_CN") or record.get("AI_Summary"))
    ]
    print(f"待补齐 AI 摘要: {len(missing_records)} 条")

    for index, record in enumerate(missing_records, 1):
        accession = record.get("Accession", "")
        print(f"  [{index}/{len(missing_records)}] 生成摘要: {accession}")
        ai_summary = generate_ai_summary(
            record.get("Title", ""),
            record.get("Summary", ""),
            record.get("Data_Type", "")
        )
        if ai_summary:
            record["AI_Summary_CN"] = ai_summary
            record["AI_Summary"] = ai_summary
            updated_count += 1
            time.sleep(1)

    return updated_count


def fetch_geo_soft(accession):
    """获取GEO SOFT格式的详细信息（Country, Lab, Institute等）"""
    url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}&targ=self&form=text&view=full"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return {}

        info = {
            "overall_design": "",
            "contributors": [],
            "lab": "",
            "institute": "",
            "country": "",
        }

        for line in response.text.split('\n'):
            line = line.strip()
            if line.startswith('!Series_overall_design'):
                info["overall_design"] = line.split('=', 1)[1].strip()
            elif line.startswith('!Series_contributor'):
                contributor = line.split('=', 1)[1].strip()
                parts = contributor.split(',')
                if len(parts) >= 2:
                    name = f"{parts[-1]} {parts[0]}".strip()
                    if name and name not in info["contributors"]:
                        info["contributors"].append(name)
            elif line.startswith('!Series_contact_laboratory'):
                info["lab"] = line.split('=', 1)[1].strip()
            elif line.startswith('!Series_contact_institute'):
                info["institute"] = line.split('=', 1)[1].strip()
            elif line.startswith('!Series_contact_country'):
                info["country"] = line.split('=', 1)[1].strip()

        return info
    except Exception as e:
        print(f"    获取SOFT信息失败: {e}")
        return {}


def parse_record(record, soft_info=None, assessment=None):
    """解析单条记录"""
    accession = record.get("Accession", "")
    if not accession.startswith("GSE"):
        return None

    pubmed_ids = record.get("PubMedIds", [])
    pubmed_str = "; ".join(str(p) for p in pubmed_ids) if pubmed_ids else ""
    pubmed_str = clean_pubmed_ids(pubmed_str)

    data_type = "bulk RNA-seq"  # 简化处理
    title = record.get("title", "")
    summary = record.get("summary", "")

    if soft_info is None:
        soft_info = fetch_geo_soft(accession)
        time.sleep(0.3)

    parsed = {
        "Accession": accession,
        "Title": title,
        "Organism": record.get("taxon", ""),
        "Data_Type": data_type,
        "Sample_Count": record.get("n_samples", 0),
        "Platform": record.get("GPL", ""),
        "Country": soft_info.get("country", ""),
        "Lab": soft_info.get("lab", ""),
        "Institute": soft_info.get("institute", ""),
        "Contributors": "; ".join(soft_info.get("contributors", [])),
        "PubMed_IDs": pubmed_str,
        "Supplementary_Size": "N/A",
        "Summary": summary,
        "Overall_Design": soft_info.get("overall_design", ""),
        "AI_Summary_CN": "",
        "AI_Summary": "",
        "GEO_Link": f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}",
        "Submission_Date": record.get("PDAT", ""),
    }
    if assessment is not None:
        parsed = with_relevance_metadata(parsed, assessment)
    return parsed


def load_existing_data():
    """加载现有数据"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_data(data):
    """原子保存数据，避免任务中断留下半写入 JSON。"""
    save_json_atomic(DATA_FILE, data)


def save_json_atomic(path, payload):
    """Write JSON through a sibling temporary file and atomically replace it."""

    temporary = f"{path}.tmp"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(temporary, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(temporary, path)


def load_review_queue():
    """加载待人工复核的第二阶段边界记录。"""
    if os.path.exists(REVIEW_FILE):
        with open(REVIEW_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_review_queue(queue):
    """保存待人工复核记录，并按提交日期倒序排列。"""
    queue.sort(key=lambda item: item.get("Submission_Date", ""), reverse=True)
    save_json_atomic(REVIEW_FILE, queue)


def load_decision_log():
    """加载可恢复的自动排除日志。"""

    if os.path.exists(DECISION_LOG_FILE):
        with open(DECISION_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_decision_log(entries):
    """保存自动排除日志；不删除历史决定。"""

    entries.sort(key=lambda item: item.get("Decided_At", ""), reverse=True)
    save_json_atomic(DECISION_LOG_FILE, entries)


def main():
    print(f"开始更新数据 - {datetime.now()}")

    if not NCBI_EMAIL:
        print("错误: 未设置 NCBI_EMAIL")
        return

    setup_entrez()

    # 加载现有数据
    existing_data = load_existing_data()
    existing_accessions = {d["Accession"] for d in existing_data}
    original_accessions = set(existing_accessions)
    review_queue = load_review_queue()
    queued_by_accession = {
        item["Accession"]: item for item in review_queue if item.get("Accession")
    }
    decision_log = load_decision_log()
    logged_by_accession = {
        item["Accession"]: item for item in decision_log if item.get("Accession")
    }
    print(f"现有数据集: {len(existing_data)}")
    print(f"待人工复核: {len(queued_by_accession)}")
    print(f"已记录自动排除: {len(logged_by_accession)}")

    # 搜索新数据
    id_list = search_geo()
    print(f"搜索到: {len(id_list)} 条记录")

    # 获取摘要
    summaries = fetch_summaries(id_list)

    # 过滤和解析
    new_count = 0
    review_count = 0
    excluded_count = 0
    for record in summaries:
        accession = record.get("Accession", "")

        # 跳过已存在的
        if (
            accession in existing_accessions
            or accession in queued_by_accession
            or accession in logged_by_accession
        ):
            continue

        # 只处理 GSE
        if not accession.startswith("GSE"):
            continue

        # 第一阶段：宽泛关键词候选召回。
        if not passes_stage1_filter(record):
            continue

        # 第二阶段：读取实验设计，以研究对象/样本证据验证主题相关性。
        soft_info = fetch_geo_soft(accession)
        time.sleep(0.3)
        assessment = assess_relevance({
            "Title": record.get("title", ""),
            "Summary": record.get("summary", ""),
            "Overall_Design": soft_info.get("overall_design", ""),
        })
        final_decision = assessment.decision
        decision_source = "two_stage_rule"

        if final_decision == "exclude":
            excluded_count += 1
            logged_by_accession[accession] = {
                "Accession": accession,
                "Title": record.get("title", ""),
                "Summary": record.get("summary", ""),
                "Overall_Design": soft_info.get("overall_design", ""),
                "Submission_Date": record.get("PDAT", ""),
                "Final_Decision": "exclude",
                "Decision_Source": decision_source,
                "Rule_Assessment": assessment.to_dict(),
                "Decided_At": datetime.now().isoformat(timespec="seconds"),
                "GEO_Link": f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}",
            }
            print(f"  排除并记录: {accession} ({decision_source})")
            continue

        if final_decision == "review":
            queued_by_accession[accession] = {
                "Accession": accession,
                "Title": record.get("title", ""),
                "Summary": record.get("summary", ""),
                "Overall_Design": soft_info.get("overall_design", ""),
                "Submission_Date": record.get("PDAT", ""),
                "Assessment": assessment.to_dict(),
                "Rule_Assessment": assessment.to_dict(),
                "Decision_Source": decision_source,
                "GEO_Link": f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}",
            }
            review_count += 1
            print(f"  待复核: {accession} ({decision_source})")
            continue

        # 只为第二阶段确认纳入的记录生成/补齐展示数据。
        parsed = parse_record(record, soft_info=soft_info, assessment=assessment)
        if parsed:
            parsed["Relevance_Final_Source"] = decision_source
            existing_data.insert(0, parsed)  # 新数据放在开头
            existing_accessions.add(accession)
            new_count += 1
            print(f"  新增: {accession}")

    final_accession_list = [
        item.get("Accession", "") for item in existing_data
    ]
    final_accessions = set(final_accession_list)
    if len(final_accession_list) != len(final_accessions):
        raise RuntimeError("安全检查失败：daily update 产生了重复 accession")
    if not original_accessions.issubset(final_accessions):
        removed = sorted(original_accessions - final_accessions)
        raise RuntimeError(
            "安全检查失败：daily update 不得删除已有 accession: "
            + ", ".join(removed)
        )

    save_review_queue(list(queued_by_accession.values()))
    save_decision_log(list(logged_by_accession.values()))
    if review_count > 0:
        print(f"新增/更新 {review_count} 条待人工复核记录")

    summary_count = backfill_missing_ai_summaries(existing_data)

    if new_count > 0 or summary_count > 0:
        save_data(existing_data)
        print(
            f"完成! 新增 {new_count} 条数据，自动排除 {excluded_count} 条，"
            f"补齐 {summary_count} 条摘要，"
            f"总计 {len(existing_data)} 条"
        )
    else:
        print(f"没有新数据或摘要需要更新；自动排除 {excluded_count} 条")


if __name__ == "__main__":
    main()
