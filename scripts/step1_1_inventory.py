"""
Step 1.1 — 数据盘点

扫描两个原始数据集，统计每个工具的用户问题数量，
与 32 个目标工具做交集，输出盘点表。
"""

import json
import ast
import os
from collections import Counter

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "step1")
ALI_PATH = os.path.join(PROJECT_ROOT, "ori-datasets", "AliRGHZ-Mobile-Actions.jsonl")
GOOGLE_PATH = os.path.join(PROJECT_ROOT, "ori-datasets", "google-mobile-actions.jsonl")


def load_our_tools():
    """加载 32 个目标工具名称。"""
    sys.path.insert(0, PROJECT_ROOT)
    from tools_definition import TOOLS
    return [t["function"]["name"] for t in TOOLS]


def scan_ali(path: str) -> Counter:
    """扫描 AliRGHZ 数据集，统计每工具用户问题数。"""
    counter = Counter()
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            msgs = ast.literal_eval(obj.get("messages", "[]"))
            tool_name = None
            for m in msgs:
                if m.get("role") == "assistant" and "tool_calls" in m:
                    tc = m["tool_calls"][0]["function"]
                    tool_name = tc["name"]
                    break
            if tool_name:
                counter[tool_name] += 1
    return counter


def scan_google(path: str) -> Counter:
    """扫描 Google 数据集，统计每工具用户问题数。"""
    counter = Counter()
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            for m in obj.get("messages", []):
                if m.get("role") == "assistant":
                    tc = m.get("tool_calls")
                    if tc and len(tc) > 0:
                        tool_name = tc[0]["function"]["name"]
                        counter[tool_name] += 1
                        break
    return counter


def main():
    our_tools = load_our_tools()
    print(f"目标工具数: {len(our_tools)}")

    print("\n扫描 AliRGHZ ...")
    ali = scan_ali(ALI_PATH)
    print(f"  总条数: {ali.total():,}, 工具种类: {len(ali)}")

    print("扫描 Google ...")
    google = scan_google(GOOGLE_PATH)
    print(f"  总条数: {google.total():,}, 工具种类: {len(google)}")

    # 合并
    combined = Counter()
    for c in [ali, google]:
        combined.update(c)
    print(f"\n合并总数: {combined.total():,}, 工具种类: {len(combined)}")

    # 交集分析
    our_set = set(our_tools)
    existing_set = set(combined.keys())
    hit = our_set & existing_set
    miss = our_set - existing_set

    print(f"\n{'='*60}")
    print(f"命中工具 (有现成数据): {len(hit)}")
    print(f"缺失工具 (需 LLM 生成): {len(miss)}")
    print(f"{'='*60}")

    # 详细盘点表
    inventory = []
    for name in sorted(hit):
        count = combined[name]
        need_gen = max(0, 100 - count)
        inventory.append({
            "tool": name,
            "source_count": count,
            "need_translate": min(count, 100),
            "need_generate": need_gen,
            "source": "dataset",
        })
        print(f"  ✓ {name:<30s} 现有 {count:>5d} 条, 需翻译 {min(count,100):>3d} 条, 需生成 {need_gen:>3d} 条")

    for name in sorted(miss):
        inventory.append({
            "tool": name,
            "source_count": 0,
            "need_translate": 0,
            "need_generate": 100,
            "source": "llm",
        })
        print(f"  ✗ {name:<30s} 现有    0 条, 需翻译   0 条, 需生成 100 条")

    total_translate = sum(i["need_translate"] for i in inventory)
    total_generate = sum(i["need_generate"] for i in inventory)
    print(f"\n合计: 需翻译 {total_translate} 条, 需生成 {total_generate} 条")

    # 保存盘点表
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "inventory.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, ensure_ascii=False, indent=2)
    print(f"\n盘点表已保存: {out_path}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, PROJECT_ROOT)
    main()
