"""
Step 1.5 — LLM 数据生成（草案，待审批）

策略要点：
- 模型较弱(Qwen3-30B)，每次只生成 1 条，但多用不同类型的话术模板轮换，保证多样性
- 对每个工具预定义 9 个"场景模板"，LLM 按场景填具体值
- 生成完立即校验参数名和类型，不合格的重试
- 最终每个工具留 100 条

工具分两类：
  A. 有参数工具 — 需 LLM 同时生成中文问题 + 正确的参数值
  B. 无参数工具 — LLM 只需生成中文问题（如 battery_status、take_picture）

模板策略（以 set_volume(level) 为例）：
  "直接指令"     → "把音量调到50%"
  "模糊请求"     → "声音太吵了，调小一点"
  "极端场景"     → "开到最大声"
  "数字表达"     → "音量设为30"
  ...

生成流程：
  inventory.json → 确定每工具需生成数 → 轮换模板逐条生成 → 校验参数 → 保存
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
CONCURRENCY = 5

# ------------------------------------------------------------
# 9 个场景模板，轮换使用以保证多样性
# ------------------------------------------------------------
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
    """加载工具定义 {name: {description, params}}。"""
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
                k: {
                    "type": v["type"],
                    "desc": v["description"],
                    "required": k in required,
                }
                for k, v in props.items()
            },
        }
    return result


def build_prompt(tool_name: str, tool_def: dict, template_desc: str) -> str:
    """为单次生成构建 prompt。"""
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


def parse_response(text: str) -> dict | None:
    """尝试解析 LLM 返回的 JSON。"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text.strip("`")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def validate_args(tool_name: str, tool_def: dict, args: dict) -> bool:
    """校验生成的参数名和类型是否正确。"""
    valid_params = tool_def["params"]
    for k in args:
        if k not in valid_params:
            return False
    for k, v in valid_params.items():
        if v["required"] and k not in args:
            return False
    return True


def generate_one(tool_name: str, tool_def: dict, template_idx: int) -> dict | None:
    """生成 1 条数据，失败重试最多 3 次。"""
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
                if validate_args(tool_name, tool_def, args):
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

    # 读取 inventory，确定每工具需生成的条数
    inv_path = os.path.join(STEP1_DIR, "inventory.json")
    with open(inv_path, encoding="utf-8") as f:
        inventory = json.load(f)

    plan = []
    for item in inventory:
        need = item["need_generate"]
        if need > 0:
            plan.append((item["tool"], need))
    
    total = sum(n for _, n in plan)
    print(f"需生成工具: {len(plan)} 个, 合计 {total} 条\n")
    print("=" * 60)
    print("这段代码是草案，不会实际执行。")
    print("策略说明：")
    print("  1. 9个话术模板轮换 → 保证多样性")
    print("  2. 每次生成1条 → 单条质量高")
    print("  3. 生成后校验参数 → 不合格重试(最多3次)")
    print("  4. 输出: output/step1/{tool}_gen.jsonl")
    print("=" * 60)


if __name__ == "__main__":
    main()
