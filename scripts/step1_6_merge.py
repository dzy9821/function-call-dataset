"""
Step 1.6 — 输出合并

将 zh/（从原始数据集提取翻译的）和 gen/（LLM 生成的）数据
合并为最终训练格式，写入 merged.jsonl。
"""

import json
import os
import random
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

STEP1_DIR = os.path.join(PROJECT_ROOT, "output", "step1")
ZH_DIR = os.path.join(STEP1_DIR, "zh")
GEN_DIR = os.path.join(STEP1_DIR, "gen")
OUTPUT_PATH = os.path.join(STEP1_DIR, "merged.jsonl")

DATA_SOURCE = "td-mobile-action"


def convert(tool_name: str, user_question: str, arguments: dict, system_content: str = "") -> dict:
    """将一条数据转换为最终训练格式。"""
    return {
        "data_source": DATA_SOURCE,
        "messages": [
            {"role": "system", "content": system_content, "tool_calls": None},
            {"role": "user", "content": user_question, "tool_calls": None},
        ],
        "reward_model": {
            "ground_truth": [
                {
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(arguments, ensure_ascii=False),
                    }
                }
            ],
            "style": "rule",
        },
    }


def load_zh(zh_dir: str) -> list[dict]:
    """加载 zh/ 目录的数据。"""
    records = []
    for fname in sorted(os.listdir(zh_dir)):
        if not fname.endswith("_zh.jsonl"):
            continue
        tool_name = fname.replace("_zh.jsonl", "")
        path = os.path.join(zh_dir, fname)
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                records.append(convert(
                    tool_name=tool_name,
                    user_question=item["zh"],
                    arguments=item.get("arguments", {}),
                    system_content=item.get("system", ""),
                ))
    return records


def load_gen(gen_dir: str) -> list[dict]:
    """加载 gen/ 目录的数据。"""
    records = []
    for fname in sorted(os.listdir(gen_dir)):
        if not fname.endswith("_gen.jsonl"):
            continue
        path = os.path.join(gen_dir, fname)
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                records.append(convert(
                    tool_name=item["tool_name"],
                    user_question=item["user_question"],
                    arguments=item.get("arguments", {}),
                    system_content=item.get("system", ""),
                ))
    return records


def print_stats(records: list[dict], label: str):
    """打印工具分布统计。"""
    from collections import Counter
    tools = Counter(
        r["reward_model"]["ground_truth"][0]["function"]["name"]
        for r in records
    )
    print(f"\n{'='*60}")
    print(f"  {label}  —  共 {len(records)} 条")
    print(f"{'='*60}")
    for tool, count in sorted(tools.items()):
        print(f"  {tool:<35s} {count:>4d}")
    print(f"{'─'*60}")
    print(f"  {'TOTAL':<35s} {len(records):>4d}")


def main():
    print("Step 1.6 — 输出合并")

    # 1. 加载
    zh_records = load_zh(ZH_DIR)
    gen_records = load_gen(GEN_DIR)

    print_stats(zh_records, "zh/ 数据")
    print_stats(gen_records, "gen/ 数据")

    # 2. 合并 & 打乱
    all_records = zh_records + gen_records
    random.shuffle(all_records)

    # 3. 写入
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print_stats(all_records, "merged 合计")
    print(f"\n✅ 已写入 {OUTPUT_PATH}  ({len(all_records)} 条)")


if __name__ == "__main__":
    main()
