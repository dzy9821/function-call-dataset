"""
Step 1.3 — 英文→中文翻译（并发单条）

逐条翻译 _en.jsonl 中的英文问题，使用并发加速。
"""

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEP1_DIR = os.path.join(PROJECT_ROOT, "output", "step1")

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-6758987f6c594753b747a6e4c2f94268")
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-v4-flash"
CONCURRENCY = 5

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# 英文星期→中文星期映射
WEEKDAY_MAP = {
    "Monday": "星期一", "Tuesday": "星期二", "Wednesday": "星期三",
    "Thursday": "星期四", "Friday": "星期五", "Saturday": "星期六", "Sunday": "星期日",
}


def translate_system_en(system_en: str) -> str | None:
    """将英文 system prompt 中的日期时间转为中文格式。
    输入: 'Current date and time given in YYYY-MM-DDTHH:MM:SS format: 2024-08-18T20:15:44\nDay of week is Sunday'
    输出: '当前日期和时间（格式为 YYYY-MM-DDTHH:MM:SS）：2024-08-18T20:15:44  \n星期为: 星期日'
    """
    if not system_en:
        return None
    # 提取日期时间
    dt_match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', system_en)
    # 提取星期
    wd_match = re.search(r'Day of week is (\w+)', system_en)
    if not dt_match or not wd_match:
        return None
    date_str = dt_match.group(1)
    weekday_en = wd_match.group(1)
    weekday_zh = WEEKDAY_MAP.get(weekday_en, weekday_en)
    return f"当前日期和时间（格式为 YYYY-MM-DDTHH:MM:SS）：{date_str}  \n星期为: {weekday_zh}"


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
            # 对时间相关工具，翻译 system_en → system
            if "system_en" in item:
                system_zh = translate_system_en(item["system_en"])
                if system_zh:
                    record["system"] = system_zh
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
