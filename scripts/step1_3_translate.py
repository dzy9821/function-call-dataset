"""
Step 1.3 — 英文→中文翻译（并发单条）

逐条翻译 _en.jsonl 中的英文问题，使用并发加速。
每次 LLM 调用只翻译一条，确保质量。
"""

import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEP1_DIR = os.path.join(PROJECT_ROOT, "output", "step1")
LLM_URL = "http://182.150.59.81:31845/v1/chat/completions"
LLM_MODEL = "Qwen3-30B-A3B-Instruct-2507"
CONCURRENCY = 5  # 并发数


def translate_one(en_text: str) -> str:
    """翻译单条英文为中文。"""
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是翻译助手。将用户输入的英文翻译为自然口语化的中文，只输出翻译结果，不要解释。",
            },
            {
                "role": "user",
                "content": en_text,
            },
        ],
        "temperature": 0.3,
        "max_tokens": 512,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        LLM_URL, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"    [ERROR] {e}")
        return en_text  # 失败时返回原文


def process_tool(tool: str):
    """处理单个工具的翻译。"""
    src_path = os.path.join(STEP1_DIR, f"{tool}_en.jsonl")
    dst_path = os.path.join(STEP1_DIR, f"{tool}_zh.jsonl")

    items = []
    with open(src_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))

    total = len(items)
    print(f"  {tool}: {total} 条, 并发 {CONCURRENCY}")

    results = [None] * total

    def translate_item(idx):
        zh = translate_one(items[idx]["en"])
        return idx, zh

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = {pool.submit(translate_item, i): i for i in range(total)}
        done = 0
        for future in as_completed(futures):
            idx, zh = future.result()
            results[idx] = zh
            done += 1
            if done % 10 == 0 or done == total:
                print(f"    {done}/{total}")

    # 写入
    with open(dst_path, "w", encoding="utf-8") as f:
        for item, zh in zip(items, results):
            record = {"zh": zh, "en": item["en"], "arguments": item["arguments"]}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"    → {os.path.basename(dst_path)}")
    return total


def main():
    # 收集所有 _en.jsonl 文件
    files = sorted(f for f in os.listdir(STEP1_DIR) if f.endswith("_en.jsonl"))
    if not files:
        print("没有 _en.jsonl 文件需要翻译")
        return

    tools = [f.replace("_en.jsonl", "") for f in files]
    print(f"待翻译工具: {len(tools)} 个\n")

    grand_total = 0
    for tool in tools:
        grand_total += process_tool(tool)
        print()

    print(f"1.3 翻译完成, 共 {grand_total} 条")


if __name__ == "__main__":
    main()
