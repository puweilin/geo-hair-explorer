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
from datetime import datetime
from Bio import Entrez

# 配置
NCBI_EMAIL = os.environ.get('NCBI_EMAIL', '')
NCBI_API_KEY = os.environ.get('NCBI_API_KEY', '')
MINIMAX_API_KEY = os.environ.get('MINIMAX_API_KEY', '')

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
        "embryo", "blastocyst", "uterus", "uterine", "endometrium",
        "placenta", "follicle-stimulating hormone", "FSH",
        "thyroid follicle", "lymphoid follicle", "dental follicle",
        "salivary gland", "lymph node", "germinal center"
    ]
}

DATA_FILE = "data/geo_data.json"


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

    # 只搜索最近30天的数据
    date_query = "0030[MDAT]"

    return f"({keyword_query}) AND ({org_query}) AND ({type_query}) AND {date_query}"


def search_geo():
    """搜索 GEO 数据库"""
    query = build_query()
    print(f"搜索查询: {query[:100]}...")

    handle = Entrez.esearch(db="gds", term=query, retmax=500, usehistory="y")
    results = Entrez.read(handle)
    handle.close()

    return results.get("IdList", [])


def fetch_summaries(id_list):
    """获取数据集摘要"""
    if not id_list:
        return []

    handle = Entrez.esummary(db="gds", id=",".join(id_list))
    records = Entrez.read(handle)
    handle.close()

    return records


def passes_filter(record):
    """检查记录是否通过过滤器"""
    title = record.get("title", "").lower()
    summary = record.get("summary", "").lower()
    combined = title + " " + summary

    # 必须包含至少一个必要关键词
    has_required = any(kw in combined for kw in SEARCH_CONFIG["require_keywords"])
    if not has_required:
        return False

    # 不能包含排除关键词
    has_excluded = any(kw in combined for kw in SEARCH_CONFIG["exclude_keywords"])
    if has_excluded:
        return False

    return True


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


def generate_ai_summary(title, summary, data_type):
    """生成 AI 摘要"""
    if not MINIMAX_API_KEY:
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

    try:
        response = requests.post(
            'https://api.minimaxi.com/v1/chat/completions',
            headers={
                "Authorization": f'Bearer {MINIMAX_API_KEY}',
                "Content-Type": "application/json"
            },
            json={
                "model": "MiniMax-M2.1",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1500,
                "temperature": 0.7
            },
            timeout=60
        )
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            # 清理思考标签
            return re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    except Exception as e:
        print(f"AI 摘要生成失败: {e}")

    return ""


def parse_record(record):
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

    ai_summary = generate_ai_summary(title, summary, data_type)
    if ai_summary:
        time.sleep(1)  # API 速率限制

    return {
        "Accession": accession,
        "Title": title,
        "Organism": record.get("taxon", ""),
        "Data_Type": data_type,
        "Sample_Count": record.get("n_samples", 0),
        "Platform": record.get("GPL", ""),
        "Country": "",
        "Lab": "",
        "Institute": "",
        "Contributors": "",
        "PubMed_IDs": pubmed_str,
        "Supplementary_Size": "N/A",
        "Summary": summary,
        "Overall_Design": "",
        "AI_Summary_CN": ai_summary,
        "AI_Summary": ai_summary,
        "GEO_Link": f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}",
        "Submission_Date": record.get("PDAT", ""),
    }


def load_existing_data():
    """加载现有数据"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_data(data):
    """保存数据"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    print(f"开始更新数据 - {datetime.now()}")

    if not NCBI_EMAIL:
        print("错误: 未设置 NCBI_EMAIL")
        return

    setup_entrez()

    # 加载现有数据
    existing_data = load_existing_data()
    existing_accessions = {d["Accession"] for d in existing_data}
    print(f"现有数据集: {len(existing_data)}")

    # 搜索新数据
    id_list = search_geo()
    print(f"搜索到: {len(id_list)} 条记录")

    if not id_list:
        print("没有新数据")
        return

    # 获取摘要
    summaries = fetch_summaries(id_list)

    # 过滤和解析
    new_count = 0
    for record in summaries:
        accession = record.get("Accession", "")

        # 跳过已存在的
        if accession in existing_accessions:
            continue

        # 只处理 GSE
        if not accession.startswith("GSE"):
            continue

        # 过滤
        if not passes_filter(record):
            continue

        # 解析
        parsed = parse_record(record)
        if parsed:
            existing_data.insert(0, parsed)  # 新数据放在开头
            existing_accessions.add(accession)
            new_count += 1
            print(f"  新增: {accession}")

    if new_count > 0:
        save_data(existing_data)
        print(f"完成! 新增 {new_count} 条数据，总计 {len(existing_data)} 条")
    else:
        print("没有新数据需要添加")


if __name__ == "__main__":
    main()
