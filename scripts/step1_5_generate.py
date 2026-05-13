"""
Step 1.5 — LLM 数据生成（v2）

- 每工具独立提示词（prompts.py）
- API Key 从环境变量 DEEPSEEK_API_KEY 读取
- 每批 10 条，随机抽取话术模板
- 满 100 条后 LLM 去重，再补至 100
- 可反复运行，只补差额
"""

import json
import os
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

GEN_DIR = os.path.join(PROJECT_ROOT, "output", "step1", "gen")

# ---- 模型配置（用户自行修改）----
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-6758987f6c594753b747a6e4c2f94268")
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-v4-flash"
DEDUP_MODEL = "deepseek-reasoner"
CONCURRENCY = 10

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ---- 话术模板（每次随机抽取）----
STYLES = [
    "一句简洁的口语指令",
    "一句礼貌的请求",
    "一个疑问句",
    "一句非常口语化、随意的表达",
    "一句带具体细节的描述",
    "一句结合了当前生活场景的请求",
    "一句较长的自然语言描述",
    "一句带反问或确认语气的请求",
    "一句带额外上下文的请求",
]

# ---- 加载 per-tool prompts ----
from scripts.prompts import TOOL_PROMPTS


def load_tool_defs():
    from tools_definition import TOOLS
    return {t["function"]["name"]: t for t in TOOLS}


def load_existing(tool_name):
    items = []
    seen = set()
    path = os.path.join(GEN_DIR, f"{tool_name}_gen.jsonl")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    q = r.get("user_question", "")
                    if q and q not in seen:
                        seen.add(q)
                        items.append(r)
    return items, seen


def validate_args(tool_name, args):
    """校验参数合法性。空 args 视为反例，合法。"""
    if not args:
        return True  # 反例
    if tool_name in ("set_brightness", "set_volume"):
        has_level = "level" in args
        has_dir = "direction" in args
        if not has_level and not has_dir:
            return False  # 至少有一个
        # 两者可同时出现，level 优先
        if has_dir and args["direction"] not in ("high", "low"):
            return False
    return True


def generate_batch(tool_name, count):
    """生成一批数据，返回 list[dict]。
    对于有必选参数的工具，随机混入反例（模糊请求、arguments为空）。
    """
    tp = TOOL_PROMPTS[tool_name]
    param_notes = tp["param_notes"]
    bad = tp.get("bad_examples", "")

    # 从工具定义获取必选参数列表
    all_defs = load_tool_defs()
    tdef = all_defs[tool_name]
    required = tdef["function"]["parameters"].get("required", [])

    # 正例 system prompt
    system_pos = tp["system"] + "\n\n" + f"参数说明：\n{param_notes}"
    if bad:
        system_pos += f"\n\n禁止事项：\n{bad}"

    # 反例 system prompt（仅有必选参数的工具才有）
    has_neg = len(required) > 0
    if has_neg:
        req_str = "、".join(required)
        system_neg = f"""你是 function call 训练数据生成助手。生成一条"反例"。
用户提到了和 "{tool_name}" 相关的需求，但表达模糊、遗漏了必选参数（{req_str}），无法调用工具。
此时 arguments 必须为空对象 {{}}。"""

    items = []
    for i in range(count):
        # 随机选 style，有必选参数时加入反例 style
        pool = STYLES + (["NEGATIVE"] if has_neg else [])
        style = random.choice(pool)

        if style == "NEGATIVE":
            user = f"""请生成 1 条反例用户问题。
用户说了一句模糊的话，提到了工具功能但遗漏了必选参数（{req_str}），无法调用。
输出格式（只输出 JSON）：
{{"user_question": "模糊的请求", "arguments": {{}}}}"""
            system = system_neg
        else:
            user = f"""请生成 1 条中文用户问题。

表达风格：{style}

输出格式（只输出 JSON）：
{{"user_question": "...", "arguments": {{...}}}}"""
            system = system_pos

        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.9,
                max_tokens=512,
            )
            text = resp.choices[0].message.content.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1]) if len(lines) > 2 else text.strip("`")
            result = json.loads(text)
            if "user_question" in result and "arguments" in result:
                args = result.get("arguments", {})
                if validate_args(tool_name, args):
                    items.append({
                        "tool_name": tool_name,
                        "user_question": result["user_question"].strip(),
                        "arguments": args,
                    })
        except Exception as e:
            print(f"    gen error: {e}")
    return items


def dedup_via_llm(items):
    """让模型去重：输入 N 条，返回应保留的索引列表。"""
    numbered = "\n".join(f"{i}: {item['user_question']}" for i, item in enumerate(items))
    prompt = f"""以下是一组用户向手机助手提出的问题，有些可能语义重复。

请找出语义重复的问题组，每组只保留表达最自然的一条。

{numbered}

用 JSON 输出要保留的索引列表：
{{"keep": [0, 3, 5, ...]}}

只输出 JSON。"""

    try:
        resp = client.chat.completions.create(
            model=DEDUP_MODEL,
            messages=[
                {"role": "system", "content": "你是数据清洗专家，只输出 JSON。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=4096,
        )
        text = resp.choices[0].message.content.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text.strip("`")
        result = json.loads(text)
        keep = result.get("keep", [])
        return [items[i] for i in keep if i < len(items)]
    except Exception as e:
        print(f"    dedup error: {e}")
        return items


def process_tool(tool_name):
    """为一个工具生成/去重/补全直到 100 条。"""
    existing, seen_q = load_existing(tool_name)
    if len(existing) >= 100:
        print(f"  {tool_name}: 已有 {len(existing)} 条 ✓")
        return len(existing)

    need = 100 - len(existing)
    print(f"  {tool_name}: 已有 {len(existing)}, 需 {need} 条")

    max_rounds = 5
    for round_num in range(max_rounds):
        # 生成一批
        batch = generate_batch(tool_name, min(need, 100))
        for item in batch:
            q = item["user_question"]
            if q not in seen_q:
                seen_q.add(q)
                existing.append(item)

        # LLM 去重
        if len(existing) >= 90:
            before = len(existing)
            existing = dedup_via_llm(existing)
            seen_q = {item["user_question"] for item in existing}
            print(f"    去重: {before} → {len(existing)}")

        # 截断到 100
        existing = existing[:100]
        need = 100 - len(existing)
        if need == 0:
            break

    # 保存
    path = os.path.join(GEN_DIR, f"{tool_name}_gen.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for item in existing[:100]:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"    → {len(existing[:100])} 条")
    return len(existing[:100])


def main(tools_filter=None):
    """tools_filter: 指定只生成哪些工具，None 表示全部。"""
    all_tools = load_tool_defs()
    if tools_filter:
        all_tools = {k: v for k, v in all_tools.items() if k in tools_filter}
    os.makedirs(GEN_DIR, exist_ok=True)

    # 显示当前状态
    total = 0
    plan = []
    for name in all_tools:
        items, _ = load_existing(name)
        need = max(0, 100 - len(items))
        mark = " ✓" if need == 0 else f" 缺{need}"
        print(f"  {name:<30s} {len(items):>3d}{mark}")
        total += len(items)
        if need > 0:
            plan.append((name, need))

    if not plan:
        tc = len(all_tools)
        print(f"\n指定 {tc} 工具已满 100 ✓ ({total} 条)")
        return

    print(f"\n需生成: {len(plan)} 工具\n")

    for tool_name, _need in plan:
        process_tool(tool_name)
        print()

    # 最终统计
    total = 0
    done = 0
    for name in all_tools:
        items, _ = load_existing(name)
        total += len(items)
        if len(items) >= 100:
            done += 1
    print(f"完成: {done}/{len(all_tools)}, 共 {total} 条")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tools", type=str, default="", help="指定工具名，逗号分隔")
    args = parser.parse_args()

    tool_list = [t.strip() for t in args.tools.split(",") if t.strip()] if args.tools else None
    main(tools_filter=tool_list)
