"""
Step 1.3 — 英文→中文翻译（并发单条）

逐条翻译 _en.jsonl 中的英文问题，使用并发加速。
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEP1_DIR = os.path.join(PROJECT_ROOT, "output", "step1")

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-6758987f6c594753b747a6e4c2f94268")
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-v4-flash"
CONCURRENCY = 5

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def translate_one(en_text: str) -> str:
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "将英文翻译为自然口语化的中文，只输出翻译结果。"},
                {"role": "user", "content": en_text},
            ],
            temperature=0.3,
            max_tokens=256,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"    [ERROR] {e}")
        return en_text


def process_tool(tool: str):
    src_path = os.path.join(STEP1_DIR, "en", f"{tool}_en.jsonl")
    dst_path = os.path.join(STEP1_DIR, "zh", f"{tool}_zh.jsonl")

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

    with open(dst_path, "w", encoding="utf-8") as f:
        for item, zh in zip(items, results):
            record = {"zh": zh, "en": item["en"], "arguments": item["arguments"]}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"    → {os.path.basename(dst_path)}")
    return total


def main():
    en_dir = os.path.join(STEP1_DIR, "en")
    files = sorted(f for f in os.listdir(en_dir) if f.endswith("_en.jsonl"))
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
