"""
Step 1.5 — LLM 数据生成

每次运行：读取已有 gen 文件 → 计算差额 → 只生成不足部分 → 追加去重。
可反复运行直到所有工具满 100 条。
"""

import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEP1_DIR = os.path.join(PROJECT_ROOT, "output", "step1")
GEN_DIR = os.path.join(STEP1_DIR, "gen")
LLM_URL = "http://182.150.59.81:31845/v1/chat/completions"
LLM_MODEL = "Qwen3-30B-A3B-Instruct-2507"
CONCURRENCY = 10

TEMPLATES = [
    "用户用简洁的指令式语句提出请求。",
    "用户用礼貌的请求句式提出请求。",
    "用户用疑问句形式提出请求。",
    "用户用口语化、随意的表达提出请求。",
    "用户用包含具体数值/名称的表达提出请求。",
    "用户结合当前场景提出请求（如刚做完一件事紧接着做另一件）。",
    "用户用较长的自然语言描述需求。",
    "用户用反问或确认语气提出请求。",
    "用户用带有额外上下文信息的句子提出请求。",
]


def load_tool_defs():
    import sys
    sys.path.insert(0, PROJECT_ROOT)
    from tools_definition import TOOLS
    result = {}
    for t in TOOLS:
        fn = t["function"]
        props = fn["parameters"]["properties"]
        required = fn["parameters"].get("required", [])
        result[fn["name"]] = {
            "description": fn["description"],
            "params": {
                k: {"type": v["type"], "desc": v["description"], "required": k in required}
                for k, v in props.items()
            },
        }
    return result


def load_existing(tool_name: str) -> tuple[list[dict], set]:
    """加载已有生成数据，返回 (items, seen_questions)。"""
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


def build_prompt(tool_name, tool_def, template_desc):
    desc = tool_def["description"]
    params = tool_def["params"]
    param_lines = []
    for k, v in params.items():
        req = "必选" if v["required"] else "可选"
        param_lines.append(f"  {k} ({v['type']}, {req}): {v['desc']}")
    param_section = "\n".join(param_lines) if param_lines else "  无参数"
    return f"""你是一个手机助手训练数据生成器。为以下工具生成 1 条中文用户问题。

工具名称: {tool_name}
功能描述: {desc}
参数定义:
{param_section}

要求:
1. 生成一个用户会用中文口语说出的手机操作请求
2. 风格: {template_desc}
3. 参数值必须是真实合理的（如联系人姓名用常见中文名，地名用真实地点，网址用真实域名，数值在合理范围内），禁止使用占位符或编造的值
4. 输出一个 JSON 对象:
   {{"user_question": "用户的中文请求",
     "arguments": {{参数名: 参数值}}}}（无参数时 arguments 为空对象 {{}}）

只输出 JSON，不要其他内容。"""


def parse_response(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text.strip("`")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def validate_args(tool_def, args):
    valid_params = tool_def["params"]
    for k in args:
        if k not in valid_params:
            return False
    for k, v in valid_params.items():
        if v["required"] and k not in args:
            return False
    return True


def generate_one(tool_name, tool_def, template_idx):
    template = TEMPLATES[template_idx % len(TEMPLATES)]
    prompt = build_prompt(tool_name, tool_def, template)
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "你是训练数据生成器，只输出 JSON。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.9,
        "max_tokens": 1024,
    }
    for attempt in range(3):
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                LLM_URL, data=data, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            text = body["choices"][0]["message"]["content"]
            result = parse_response(text)
            if result and "user_question" in result and "arguments" in result:
                args = result.get("arguments", {})
                if not isinstance(args, dict):
                    continue
                if validate_args(tool_def, args):
                    return {
                        "tool_name": tool_name,
                        "user_question": result["user_question"].strip(),
                        "arguments": args,
                    }
        except Exception:
            pass
    return None


def main():
    tools = load_tool_defs()
    os.makedirs(GEN_DIR, exist_ok=True)

    # 算每个工具的差额
    plan = []
    for tool_name in tools:
        items, _ = load_existing(tool_name)
        need = max(0, 100 - len(items))
        plan.append((tool_name, need))

    # 打印状态
    for tool_name, need in plan:
        marker = " ← 需补" if need > 0 else " ✓"
        print(f"  {tool_name:<30s} 已有 {100-need:>3d}, 差额 {need:>3d}{marker}")

    total = sum(n for _, n in plan)
    if total == 0:
        print(f"\n全部 32 工具已满 100 ✓")
        return

    print(f"\n需补全: {sum(1 for _, n in plan if n > 0)} 个工具, {total} 条\n")

    for tool_idx, (tool_name, need) in enumerate(plan):
        if need == 0:
            continue

        tool_def = tools[tool_name]
        existing, seen_q = load_existing(tool_name)
        print(f"[{tool_idx+1}/32] {tool_name}: 补 {need} 条")

        results = [None] * need

        def gen_item(i):
            return i, generate_one(tool_name, tool_def, i)

        with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
            futures = {pool.submit(gen_item, i): i for i in range(need)}
            done = 0
            for future in as_completed(futures):
                i, result = future.result()
                results[i] = result
                done += 1
                ok = sum(1 for r in results[:done] if r is not None)
                if done % 50 == 0 or done == need:
                    print(f"  {done}/{need} (成功 {ok})")

        # 去重合并
        for r in results:
            if r is None:
                continue
            q = r["user_question"]
            if q not in seen_q:
                seen_q.add(q)
                existing.append(r)

        existing = existing[:100]
        path = os.path.join(GEN_DIR, f"{tool_name}_gen.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for item in existing:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"  → 总计 {len(existing)} 条\n")

    print("1.5 完成")


if __name__ == "__main__":
    main()
