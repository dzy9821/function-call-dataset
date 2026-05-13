"""
Step 1.2 — 英文数据提取（含参数匹配检查）

扫描两个原始数据集，对每个工具做参数名对比：
- 参数完全一致的：提取英文用户问题 + 参数
- 参数不一致的：跳过，归入需 LLM 生成
"""

import json
import ast
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALI_PATH = os.path.join(PROJECT_ROOT, "ori-datasets", "AliRGHZ-Mobile-Actions.jsonl")
GOOGLE_PATH = os.path.join(PROJECT_ROOT, "ori-datasets", "google-mobile-actions.jsonl")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "step1")

MAX_PER_TOOL = 120


def load_our_params():
    """返回 {tool_name: {param_name: type}}。"""
    import sys
    sys.path.insert(0, PROJECT_ROOT)
    from tools_definition import TOOLS
    return {
        t["function"]["name"]: {
            k: v["type"]
            for k, v in t["function"]["parameters"]["properties"].items()
        }
        for t in TOOLS
    }


def get_source_params():
    """从两个数据集中提取每个工具实际使用的参数名集合。
    返回 {tool_name: set_of_param_names}."""
    result = {}

    # AliRGHZ
    with open(ALI_PATH, encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            msgs = ast.literal_eval(obj.get("messages", "[]"))
            for m in msgs:
                if m.get("role") == "assistant" and "tool_calls" in m:
                    tc = m["tool_calls"][0]["function"]
                    raw_name = tc["name"]
                    mapped = raw_name
                    args = tc.get("arguments", {})
                    param_set = set(args.keys())
                    if mapped not in result:
                        result[mapped] = param_set
                    else:
                        result[mapped] |= param_set

    # Google
    with open(GOOGLE_PATH, encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            for m in obj.get("messages", []):
                if m.get("role") == "assistant":
                    tc = m.get("tool_calls")
                    if tc and len(tc) > 0:
                        raw_name = tc[0]["function"]["name"]
                        mapped = raw_name
                        args = tc[0]["function"].get("arguments", {})
                        param_set = {k for k, v in args.items() if v is not None}
                        if mapped not in result:
                            result[mapped] = param_set
                        else:
                            result[mapped] |= param_set
    return result


def extract_matching():
    """提取参数匹配的工具数据，返回 {tool_name: [{en, arguments}]}。"""
    our = load_our_params()
    src = get_source_params()

    # 找出参数匹配的工具
    matching = set()
    for name in our:
        our_set = set(our[name].keys())
        src_set = src.get(name, set())
        if our_set == src_set:
            matching.add(name)

    print(f"参数匹配的工具: {len(matching)} 个\n")

    # 提取这些工具的数据
    results = {t: [] for t in matching}

    # 从 AliRGHZ 提取
    with open(ALI_PATH, encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            msgs = ast.literal_eval(obj.get("messages", "[]"))
            user_q = None
            tool_name = None
            tool_args = {}
            for m in msgs:
                if m.get("role") == "user":
                    user_q = m.get("content", "").strip()
                if m.get("role") == "assistant" and "tool_calls" in m:
                    tc = m["tool_calls"][0]["function"]
                    raw_name = tc["name"]
                    mapped = raw_name
                    if mapped in matching:
                        tool_name = mapped
                        tool_args = tc.get("arguments", {})
            if user_q and tool_name and len(results[tool_name]) < MAX_PER_TOOL:
                results[tool_name].append({"en": user_q, "arguments": tool_args})

    # 从 Google 提取
    with open(GOOGLE_PATH, encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            user_q = None
            tool_name = None
            tool_args = {}
            for m in obj.get("messages", []):
                if m.get("role") == "user":
                    user_q = m.get("content", "").strip()
                if m.get("role") == "assistant":
                    tc = m.get("tool_calls")
                    if tc and len(tc) > 0:
                        raw_name = tc[0]["function"]["name"]
                        mapped = raw_name
                        if mapped in matching:
                            tool_name = mapped
                            raw_args = tc[0]["function"].get("arguments", {})
                            tool_args = {k: v for k, v in raw_args.items() if v is not None}
            if user_q and tool_name and len(results[tool_name]) < MAX_PER_TOOL:
                results[tool_name].append({"en": user_q, "arguments": tool_args})

    return results


def main():
    our = load_our_params()
    src = get_source_params()

    # 分组
    matching = []
    name_match_but_params_differ = []
    not_in_dataset = []

    for name in sorted(our.keys()):
        our_set = set(our[name].keys())
        src_set = src.get(name, set())
        src_str = ", ".join(sorted(src_set)) if src_set else "(无)"
        our_str = ", ".join(sorted(our_set)) if our_set else "(无)"

        if our_set == src_set:
            matching.append((name, src_str, our_str))
        elif name in src:
            name_match_but_params_differ.append((name, src_str, our_str))
        else:
            not_in_dataset.append((name, src_str, our_str))

    print(f"{'工具':<30s} {'原始参数':<40s} {'我们的参数':<40s} {'匹配':>5s}")
    print("-" * 120)
    for name, src_str, our_str in matching:
        print(f"{name:<30s} {src_str:<40s} {our_str:<40s} {'✓':>5s}")
    print()
    for name, src_str, our_str in name_match_but_params_differ:
        print(f"{name:<30s} {src_str:<40s} {our_str:<40s} {'✗':>5s}")
    print()
    for name, src_str, our_str in not_in_dataset:
        print(f"{name:<30s} {src_str:<40s} {our_str:<40s} {'-':>5s}")

    print(f"\n参数匹配: {len(matching)} 个")
    print(f"同名参数不同: {len(name_match_but_params_differ)} 个")
    print(f"不在数据集中: {len(not_in_dataset)} 个\n")

    # 提取
    results = extract_matching()

    # 去重 + 保存
    total = 0
    dedup_counts = {}  # {tool_name: deduplicated_count}
    for tool in sorted(results.keys()):
        items = results[tool]
        seen = set()
        unique = []
        for item in items:
            key = item["en"]
            if key not in seen:
                seen.add(key)
                unique.append(item)
        items = unique
        dedup_counts[tool] = len(items)

        if len(items) == 0:
            print(f"  {tool:<30s}   0 条 → 跳过")
            continue

        path = os.path.join(OUTPUT_DIR, "en", f"{tool}_en.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"  {tool:<30s} {len(items):>3d} 条 → {os.path.basename(path)}")
        total += len(items)

    # 更新 inventory（仅标记实际有数据的工具为 dataset）
    inv_path = os.path.join(OUTPUT_DIR, "inventory.json")
    with open(inv_path, encoding="utf-8") as f:
        inventory = json.load(f)

    for item in inventory:
        tool = item["tool"]
        count = dedup_counts.get(tool, 0)
        if count > 0:
            item["source"] = "dataset"
            item["source_count"] = count
            item["need_translate"] = count
            item["need_generate"] = max(0, 100 - count)
        else:
            item["source"] = "llm"
            item["source_count"] = 0
            item["need_translate"] = 0
            item["need_generate"] = 100

    with open(inv_path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, ensure_ascii=False, indent=2)

    print(f"\n合计提取 {total} 条（参数匹配的 6 个工具）")
    print(f"inventory.json 已更新")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, PROJECT_ROOT)
    main()
