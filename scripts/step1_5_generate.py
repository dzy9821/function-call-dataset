"""
Step 1.5 — LLM 数据生成

31 工具各生成 100 条中文训练数据。
每次 API 调用 1 条，并发运行，本地去重 + LLM 去重。
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

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-6758987f6c594753b747a6e4c2f94268")
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-v4-flash"
DEDUP_MODEL = "deepseek-v4-pro"
CONCURRENCY = 5

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

STYLES = [
    "一句简洁的口语指令",
    "一句礼貌的请求",
    "一个疑问句",
    "一句非常口语化、随意的表达",
    "一句带具体细节的描述",
    "一句结合了当前生活场景的请求",
    "一句较长的自然语言描述",
    "一句带额外上下文的请求",
]

from scripts.prompts import TOOL_PROMPTS


def load_tool_defs():
    from tools_definition import TOOLS
    return {t["function"]["name"]: t for t in TOOLS}


def validate_args(tool_name, args):
    if not args:
        return True
    if tool_name in ("set_brightness", "set_volume"):
        has_level = "level" in args
        has_dir = "direction" in args
        if not has_level and not has_dir:
            return False
        if has_dir and args["direction"] not in ("high", "low"):
            return False
    return True


def generate_one(tool_name):
    tp = TOOL_PROMPTS[tool_name]
    param_notes = tp["param_notes"]
    tdef = load_tool_defs()[tool_name]
    required = tdef["function"]["parameters"].get("required", [])
    tool_json = json.dumps(tdef, ensure_ascii=False, indent=2)

    system_pos = tp["system"] + "\n\n" + f"参数说明：\n{param_notes}" + "\n\n" + f"工具定义：\n{tool_json}"

    has_neg = len(required) > 0
    if has_neg:
        req_str = "、".join(required)
        system_neg = (
            f"你是 function call 训练数据生成助手。生成一条\"反例\"。\n"
            f"用户提到了和 \"{tool_name}\" 相关的需求，但表达模糊、遗漏了必选参数（{req_str}），无法调用工具。\n"
            f"此时 arguments 必须为空对象 {{}}。"
        )

    pool = STYLES + (["NEGATIVE"] if has_neg else [])
    style = random.choice(pool)

    if style == "NEGATIVE":
        user = (
            f"请生成 1 条反例用户问题。\n"
            f"用户说了一句模糊的话，提到了工具功能但遗漏了必选参数（{req_str}），无法调用。\n"
            f"输出格式（只输出 JSON）：\n"
            f'{{"user_question": "模糊的请求", "arguments": {{}}}}'
        )
        system = system_neg
    else:
        user = (
            f"请生成 1 条中文用户问题。\n\n"
            f"表达风格：{style}\n\n"
            f"输出格式（只输出 JSON）：\n"
            f'{{"user_question": "...", "arguments": {{...}}}}'
        )
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
                return {
                    "tool_name": tool_name,
                    "user_question": result["user_question"].strip(),
                    "arguments": args,
                }
    except Exception as e:
        print(f"  gen error: {e}")
    return None


def dedup_via_llm(tool_name, items):
    """LLM 语义去重。"""
    if not items:
        return items
    print(f"    LLM 去重开始 ({tool_name}, {len(items)} 条) ...")
    numbered = "\n".join(f"{i}: {item['user_question']}" for i, item in enumerate(items))
    prompt = (
        f"以下是 \"{tool_name}\" 工具的训练数据。因为是同一个工具，语义相近是正常的，"
        f"只需要去掉表达几乎完全相同的条目。\n\n"
        f"{numbered}\n\n"
        f"找出表达几乎完全相同的条目，用 JSON 输出要删除的索引：\n"
        f'{{"remove": [1, 5, 8]}}\n\n'
        f"只输出 JSON，不要任何其他内容。"
    )

    text = ""
    try:
        resp = client.chat.completions.create(
            model=DEDUP_MODEL,
            messages=[
                {"role": "system", "content": "你是数据清洗专家，只输出 JSON。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=32768,
        )
        choice = resp.choices[0]
        msg = choice.message
        text = (msg.content or "").strip()
        if not text and hasattr(msg, "reasoning_content"):
            text = (msg.reasoning_content or "").strip()
        if not text:
            print("    LLM 去重: 无输出，跳过")
            return items

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        else:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start : end + 1]

        result = json.loads(text)
        remove = set(result.get("remove", []))
        if not remove:
            print("    LLM 去重: 无需删除")
            return items

        kept = [item for i, item in enumerate(items) if i not in remove]
        print(f"    LLM 去重: {len(items)} → {len(kept)} (删除 {len(remove)})")
        for idx in sorted(remove)[:3]:
            if idx < len(items):
                print(f"      删[{idx}]: {items[idx]['user_question'][:50]}")
        return kept

    except json.JSONDecodeError as e:
        print(f"    LLM 去重 JSON 解析失败: {e}")
        print(f"    原始文本: {repr(text[:200])}")
        return items
    except Exception as e:
        print(f"    LLM 去重 error: {e}")
        return items


def process_tool(tool_name):
    """生成 100 条数据。"""
    path = os.path.join(GEN_DIR, f"{tool_name}_gen.jsonl")
    seen = set()
    results = []

    print(f"  {tool_name}: 生成 100 条 ...")

    def save():
        with open(path, "w", encoding="utf-8") as f:
            for item in results[:100]:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # 第一阶段：本地去重凑满 100
    max_rounds = 5
    for round_num in range(max_rounds):
        need = 100 - len(results)
        if need == 0:
            break

        print(f"    第 {round_num + 1} 轮: 并发 {CONCURRENCY} 生成 {need} 条 ...")

        batch = [None] * need

        def gen_item(i):
            return i, generate_one(tool_name)

        with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
            futures = {pool.submit(gen_item, i): i for i in range(need)}
            done = 0
            ok = 0
            for future in as_completed(futures):
                i, result = future.result()
                batch[i] = result
                done += 1
                if result is not None:
                    ok += 1
                if done % max(1, need // 5) == 0 or done == need:
                    print(f"    [{done}/{need}] 成功 {ok}")

        for item in batch:
            if item is None:
                continue
            q = item["user_question"]
            if q not in seen:
                seen.add(q)
                results.append(item)

        save()
        print(f"    累计 {len(results)} 条 → 已保存")

        if len(results) >= 100:
            break

    # 第二阶段：满 100 后 LLM 去重
    before = len(results)
    results = dedup_via_llm(tool_name, results[:100])
    seen = {item["user_question"] for item in results}
    save()

    # 第三阶段：去重后不足补全
    need = 100 - len(results)
    if need > 0:
        print(f"    LLM 去重后缺 {need} 条，补全 ...")
        for round_num in range(5):
            if need == 0:
                break
            batch = [generate_one(tool_name) for _ in range(need)]
            for item in batch:
                if item is None:
                    continue
                q = item["user_question"]
                if q not in seen:
                    seen.add(q)
                    results.append(item)
            results = results[:100]
            need = 100 - len(results)
            save()

    print(f"  → {min(len(results), 100)} 条\n")
    return min(len(results), 100)


def main(tools_filter=None):
    all_tools = load_tool_defs()
    if tools_filter:
        all_tools = {k: v for k, v in all_tools.items() if k in tools_filter}

    os.makedirs(GEN_DIR, exist_ok=True)
    print(f"生成 {len(all_tools)} 个工具, 各 100 条\n")

    total = 0
    for tool_name in all_tools:
        total += process_tool(tool_name)

    print(f"完成: {total} 条")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tools", type=str, default="", help="指定工具名，逗号分隔")
    args = parser.parse_args()

    tool_list = [t.strip() for t in args.tools.split(",") if t.strip()] if args.tools else None
    main(tools_filter=tool_list)
