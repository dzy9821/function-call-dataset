"""
Step 1.4 — 参数生成

对 zh/ 中每个工具的中文问题，带工具定义调 deepseek-v4-flash，
让模型返回正确的 function call arguments。
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEP1_DIR = os.path.join(PROJECT_ROOT, "output", "step1")
ZH_DIR = os.path.join(STEP1_DIR, "zh")
GEN_DIR = os.path.join(STEP1_DIR, "gen")

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-6758987f6c594753b747a6e4c2f94268")
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-v4-flash"
CONCURRENCY = 5

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def load_tool_defs():
    import sys
    sys.path.insert(0, PROJECT_ROOT)
    from tools_definition import TOOLS
    return {t["function"]["name"]: t for t in TOOLS}


def generate_args(tool_name: str, user_question: str, tool_def: dict) -> dict | None:
    """让模型生成 arguments。"""
    tool_json = json.dumps(tool_def, ensure_ascii=False, indent=2)
    system = f"""你是 function call 参数提取助手。根据用户的中文问题和工具定义，提取正确的参数值。

工具定义：
{tool_json}

规则：
- 参数值必须真实合理（联系人用常见中文名，地名用真实地点，数值在合理范围）
- 严格遵守参数类型和必选/可选要求
- 只输出 JSON 对象，不要其他内容"""

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"用户说：「{user_question}」\n\n请提取参数："},
            ],
            temperature=0.1,
            max_tokens=512,
        )
        text = (resp.choices[0].message.content or "").strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text.strip("`")
        return json.loads(text)
    except Exception as e:
        print(f"      [ERR] {e}")
        return None


def process_tool(tool_name: str, tool_def: dict):
    """处理单个工具。"""
    zh_path = os.path.join(ZH_DIR, f"{tool_name}_zh.jsonl")
    if not os.path.exists(zh_path):
        return

    items = []
    with open(zh_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))

    total = len(items)
    # 统计已有完整 arguments 的
    has_args = sum(1 for i in items if i.get("arguments"))
    need = total - has_args
    if need == 0:
        print(f"  {tool_name}: {total} 条, arguments 全部已完整 ✓")
        return

    print(f"  {tool_name}: {total} 条, {need} 条需生成 arguments")

    results = [None] * total

    def gen_one(idx):
        item = items[idx]
        if item.get("arguments"):
            return idx, item["arguments"]
        args = generate_args(tool_name, item["zh"], tool_def)
        return idx, args if args else {}

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = {pool.submit(gen_one, i): i for i in range(total)}
        done = 0
        ok = 0
        for future in as_completed(futures):
            idx, args = future.result()
            results[idx] = args
            done += 1
            if args:
                ok += 1
            if done % max(1, total // 5) == 0 or done == total:
                print(f"    [{done}/{total}]")

    # 写回 zh/
    for item, args in zip(items, results):
        if args:
            item["arguments"] = args

    with open(zh_path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    filled = sum(1 for i in items if i.get("arguments"))
    print(f"    → {os.path.basename(zh_path)} ({filled}/{total} 有参数)")


def main():
    tools = load_tool_defs()

    for tool_name in sorted(tools.keys()):
        if os.path.exists(os.path.join(ZH_DIR, f"{tool_name}_zh.jsonl")):
            process_tool(tool_name, tools[tool_name])
            print()

    print("1.4 完成")


if __name__ == "__main__":
    main()
