"""
Step 1.5 — LLM 数据生成 + 多样性增强

31 工具各生成 100 条中文训练数据。
每次 API 调用 1 条，并发运行。
第二阶段由 LLM 审查全量数据，改写表达雷同或实体重复的条目，
提升表达方式、应用名、人名、地名、事件等的多样性。
"""

import json
import os
import random
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from openai import OpenAI

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

GEN_DIR = os.path.join(PROJECT_ROOT, "output", "step1", "gen")

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-6758987f6c594753b747a6e4c2f94268")
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-v4-flash"
DEDUP_MODEL = "deepseek-v4-pro"
CONCURRENCY = 10

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

from scripts.prompts import TIME_TOOLS


def random_datetime_str():
    start = datetime(2026, 1, 1)
    end = datetime(2026, 6, 30)
    days = (end - start).days
    dt = start + timedelta(days=random.randint(0, days))
    dt = dt.replace(hour=random.randint(0, 23), minute=random.randint(0, 59), second=random.randint(0, 59))
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return dt.strftime("%Y-%m-%dT%H:%M:%S"), weekdays[dt.weekday()]

STYLES = [
    "一句简洁的口语指令",
    "一句礼貌的请求",
    "一个疑问句",
    "一句非常口语化、随意的表达",
    "一句带具体细节的描述"
]

# 工具特定的多样性要求（用于 LLM 多样性增强）
DIVERSITY_NOTES = {
    "open_application": (
        "2. **应用名多样化**：同一个应用名不应反复出现，同一应用最多出现 2-3 次。\n"
        "   覆盖不同类型——社交（微信、QQ、微博、小红书）、购物（淘宝、京东、拼多多、得物）、\n"
        "   视频（抖音、B站、爱奇艺、腾讯视频）、工具（计算器、日历、备忘录、录音机、指南针）、\n"
        "   办公（钉钉、飞书、WPS、企业微信、腾讯会议）、\n"
        "   生活服务（美团、大众点评、高德地图、滴滴出行、携程、饿了么）等。\n"
    ),
    "send_email": (
        "2. **联系人姓名多样化**：同一姓名不应反复出现，同一姓名最多出现 2-3 次。\n"
        "   使用不同姓氏（张王李赵刘陈杨周吴孙徐朱马胡郑郭何梁宋唐韩冯于），\n"
        "   不同形式——全名（张伟、李娜、王建国）、单名（小明、阿芳）、\n"
        "   头衔+姓（王经理、李医生、赵老师、陈总、刘工）。\n"
        "3. **邮箱域名多样化**：@qq.com @163.com @gmail.com @outlook.com @126.com @sina.com @foxmail.com 等交替使用。\n"
        "4. **邮件主题**：覆盖工作、生活、学习等不同场景，避免同一主题反复出现。\n"
    ),
    "phone_call": (
        "2. **联系人姓名多样化**：同一姓名不应反复出现，同一姓名最多出现 2-3 次。\n"
        "   覆盖不同姓氏、不同称呼方式（全名、单名、昵称、头衔+姓）。\n"
        "   电话号码号段多样化（13x 15x 18x 17x 19x 等不同前缀）。\n"
    ),
    "phone_sms": (
        "2. **联系人姓名多样化**：同一姓名不应反复出现，同一姓名最多出现 2-3 次。\n"
        "   覆盖不同姓氏、不同称呼方式。\n"
        "3. **短信内容多样化**：覆盖通知、问候、确认、提醒、闲聊等不同场景。\n"
    ),
    "show_map": (
        "2. **地名多样化**：同一地点不应反复出现，同一地点最多出现 2-3 次。\n"
        "   覆盖不同城市、不同类型——景点（故宫、西湖、黄山、兵马俑、九寨沟、张家界）、\n"
        "   商圈（陆家嘴、春熙路、三里屯、解放碑、南京路、天河城）、\n"
        "   交通枢纽（虹桥机场、北京南站、白云机场、杭州东站）、\n"
        "   学校医院（清华大学、协和医院、华西医院）、\n"
        "   公园地标（颐和园、洪崖洞、东方明珠、广州塔）等。\n"
    ),
    "navigate": (
        "2. **目的地多样化**：同一目的地不应反复出现，同一目的地最多出现 2-3 次。\n"
        "   覆盖不同城市、不同类型——机场、火车站、商场、餐厅、景点、医院、学校、住宅区、写字楼等。\n"
    ),
    "get_weather": (
        "2. **城市多样化**：同一城市不应反复出现。\n"
        "   覆盖全国不同区域——华北（北京、天津、石家庄）、华东（上海、杭州、南京、苏州、青岛）、\n"
        "   华南（广州、深圳、三亚、厦门、南宁）、西南（成都、重庆、昆明、贵阳、拉萨）、\n"
        "   西北（西安、兰州、乌鲁木齐、银川、西宁）、\n"
        "   东北（哈尔滨、沈阳、大连、长春）、华中（武汉、长沙、郑州、合肥）等。\n"
    ),
    "create_calendar_event": (
        "2. **事件标题多样化**：同一标题不应反复出现。\n"
        "   覆盖工作（项目会议、周报提交、客户拜访、季度评审）、\n"
        "   学习（英语课、考试复习、论文答辩、驾校练车）、\n"
        "   医疗（体检、牙科复查、疫苗接种、中医调理）、\n"
        "   生活（超市采购、交房租、汽车保养、家电维修）、\n"
        "   社交（同学聚会、朋友生日、家庭聚餐、婚礼）、\n"
        "   运动（健身房、晨跑、瑜伽课、游泳）等不同场景。\n"
    ),
    "set_alarm": (
        "2. **闹钟标签多样化**：同一标签不应反复出现。\n"
        "   覆盖起床、午休、会议提醒、运动、吃药、接人、赶航班、直播开始、抢票等不同场景。\n"
        "3. **时间多样化**：早中晚不同时段、工作日和周末均匀分布。\n"
    ),
    "search_calendar_events": (
        "2. **查询关键词多样化**：覆盖工作、生活、医疗、学习、社交等不同主题。\n"
    ),
    "create_note": (
        "2. **笔记标题和内容多样化**：覆盖购物清单、读书笔记、灵感记录、\n"
        "   待办事项、旅行计划、会议纪要、菜谱、日记、账号备忘等不同场景。\n"
    ),
    "play_music": (
        "2. **歌曲和歌手多样化**：同一首歌或同一位歌手不应反复出现。\n"
        "   覆盖不同年代（经典老歌、当下流行）、不同风格（流行、摇滚、民谣、说唱、电子、R&B）、\n"
        "   不同语种（中文、英文、粤语）。\n"
    ),
    "search_web": (
        "2. **搜索关键词多样化**：覆盖新闻、科技、娱乐、健康、教育、财经、体育、旅游、美食等不同领域。\n"
    ),
    "create_contact": (
        "2. **联系人姓名多样化**：同一姓名不应反复出现。\n"
        "   覆盖不同姓氏、不同名字长度（两字名、三字名）。\n"
        "   邮箱域名和电话号码号段多样化。\n"
    ),
    "search_contacts": (
        "2. **搜索姓名多样化**：同一姓名不应反复出现。\n"
        "   可以是全名搜索、部分匹配搜索等不同情况。\n"
    ),
}

# 每个工具需要检查多样性的关键实体字段
ENTITY_KEY = {
    "open_application": "application_name",
    "send_email": "contact_name",
    "phone_call": "contact_name",
    "phone_sms": "contact_name",
    "show_map": "destination",
    "navigate": "destination",
    "get_weather": "city",
    "create_calendar_event": "title",
    "set_alarm": "label",
    "search_calendar_events": "query",
    "create_note": "title",
    "play_music": "song_name",
    "search_web": "query",
    "create_contact": "contact_name",
    "search_contacts": "contact_name",
}


def compute_freq_note(tool_name, items):
    """分析实体频率，生成高频实体提示。"""
    if tool_name not in ENTITY_KEY:
        return ""
    key = ENTITY_KEY[tool_name]
    entities = []
    for item in items:
        val = item.get("arguments", {}).get(key)
        if val:
            entities.append(val)
    if not entities:
        return ""
    freq = Counter(entities)
    overrepr = [(v, c) for v, c in freq.most_common(15) if c >= 3]
    if not overrepr:
        return ""
    lines = ["\n### 当前高频实体（出现 ≥3 次，需要分散）："]
    for v, c in overrepr:
        lines.append(f"- \"{v}\" 出现了 {c} 次，请保留 2-3 条，其余改写为其他内容")
    return "\n".join(lines) + "\n"


from scripts.prompts import TOOL_PROMPTS


def load_tool_defs():
    from tools_definition import TOOLS
    return {t["function"]["name"]: t for t in TOOLS}


def validate_args(tool_name, args, required=None):
    """校验生成的 arguments 是否合法。
    - set_brightness / set_volume：level 和 direction 必须至少有一个
    - 其他有必选参数的工具：所有必选参数必须存在且非空
    """
    if args is None:
        return False
    if tool_name in ("set_brightness", "set_volume"):
        has_level = "level" in args
        has_dir = "direction" in args
        if not has_level and not has_dir:
            return False
        if has_dir and args["direction"] not in ("high", "low"):
            return False
        return True
    # 通用必选参数校验（反例的 arguments={} 豁免）
    if required:
        if args == {}:  # 反例，豁免
            return True
        for r in required:
            if r not in args or args[r] is None or args[r] == "":
                return False
    return True


def generate_one(tool_name):
    tp = TOOL_PROMPTS[tool_name]
    param_notes = tp["param_notes"]
    tdef = load_tool_defs()[tool_name]
    required = tdef["function"]["parameters"].get("required", [])
    tool_json = json.dumps(tdef, ensure_ascii=False, indent=2)

    system_pos = tp["system"] + "\n\n" + f"参数说明：\n{param_notes}" + "\n\n" + f"工具定义：\n{tool_json}"

    # 对时间相关工具，生成随机日期时间上下文
    system_prompt_field = None
    if tool_name in TIME_TOOLS:
        date_str, weekday_str = random_datetime_str()
        system_prompt_field = f"当前日期和时间（格式为 YYYY-MM-DDTHH:MM:SS）：{date_str}  \n星期为: {weekday_str}"
        system_pos += f"\n\n当前日期上下文：{system_prompt_field}\n用户问题中的时间应使用相对表述（如“明天”“下周一”“后天下午”），而 arguments 中的时间则是基于当前日期计算后的绝对时间。"

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
            if validate_args(tool_name, args, required=required):
                record = {
                    "tool_name": tool_name,
                    "user_question": result["user_question"].strip(),
                    "arguments": args,
                }
                if system_prompt_field:
                    record["system"] = system_prompt_field
                return record
    except Exception as e:
        print(f"  gen error: {e}")
    return None


def diversify_via_llm(tool_name, items):
    """LLM 多样性增强：改写表达雷同或实体重复的条目。"""
    if len(items) < 2:
        return items

    print(f"    LLM 多样性增强 ({tool_name}, {len(items)} 条) ...")

    # 构建带 index 的条目列表
    lines = []
    for i, item in enumerate(items):
        obj = {"user_question": item["user_question"], "arguments": item["arguments"]}
        lines.append(f"{i}: {json.dumps(obj, ensure_ascii=False)}")
    numbered = "\n".join(lines)

    # 工具特定的多样性说明
    diversity_note = DIVERSITY_NOTES.get(tool_name, "")

    # 高频实体统计
    freq_note = compute_freq_note(tool_name, items)

    tdef = load_tool_defs()[tool_name]
    required = tdef["function"]["parameters"].get("required", [])
    req_note = f"必选参数：{', '.join(required)}" if required else "无必选参数"

    prompt = (
        f"你是 function call 训练数据多样化专家。以下是 \"{tool_name}\" 工具的 {len(items)} 条训练数据"
        f"（每行 JSON 包含 user_question 和 arguments）。\n\n"
        f"{numbered}\n\n"
        f"请检查并提升数据多样性，重点关注：\n\n"
        f"### 1. 表达方式多样化\n"
        f"同一功能的条目应使用不同的句式、语气、用词，例如：\n"
        f"- 简短口语指令（\"开下微信\"）\n"
        f"- 礼貌请求（\"请帮我打开微信\"）\n"
        f"- 疑问句（\"能帮我把微信打开吗\"）\n"
        f"- 带场景描述（\"我想回个消息，帮我打开微信\"）\n"
        f"如果多条条目使用了高度相似的表达方式，请改写其中一部分，保留 1-2 条即可。\n\n"
        f"{diversity_note}"
        f"{freq_note}\n"
        f"### 要求\n"
        f"- 只改写确实需要多样化的条目，已经足够多样化的条目不要改动\n"
        f"- **arguments 的值必须从 user_question 中原样提取，不能自行推断或构造**。\n"
        f"  例如 user_question 中写的是\"小李\"，arguments 就不能写\"李磊\"，只能写\"小李\"。\n"
        f"  改名时两边同步改：user_question 写\"李磊\"，arguments 才能写\"李磊\"。\n"
        f"- arguments 中字段的键和类型必须正确（{req_note}）\n"
        f"- 改写后的条目之间也要保持多样性，不要引入新的雷同\n\n"
        f"### 输出格式\n"
        f"用 JSON 列出要修改的条目：\n"
        f'{{"modify": [{{"index": 0, "user_question": "改写后", "arguments": {{...}}}}, ...]}}\n\n'
        f"只输出 JSON，不要任何其他内容。"
    )

    text = ""
    try:
        resp = client.chat.completions.create(
            model=DEDUP_MODEL,
            messages=[
                {"role": "system", "content": "你是训练数据多样化专家。只输出 JSON。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=32768,
        )
        choice = resp.choices[0]
        msg = choice.message
        text = (msg.content or "").strip()
        if not text and hasattr(msg, "reasoning_content"):
            text = (msg.reasoning_content or "").strip()
        if not text:
            print("    LLM 多样性增强: 无输出，跳过")
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
        modifications = result.get("modify", [])
        if not modifications:
            print("    LLM 多样性增强: 无需修改")
            return items

        # 应用修改
        modified = 0
        for mod in modifications:
            idx = mod.get("index")
            new_q = mod.get("user_question")
            new_args = mod.get("arguments")
            if idx is None or not new_q or new_args is None:
                continue
            if idx < 0 or idx >= len(items) or not isinstance(idx, int):
                continue
            if not validate_args(tool_name, new_args, required=required):
                continue
            items[idx]["user_question"] = new_q.strip()
            items[idx]["arguments"] = new_args
            modified += 1

        if modified > 0:
            print(f"    LLM 多样性增强: 修改了 {modified} 条")
            for mod in modifications[:3]:
                if mod.get("index") is not None:
                    i = mod["index"]
                    print(f"      改[{i}]: {items[i]['user_question'][:60]}")
        else:
            print("    LLM 多样性增强: 所有修改未通过校验，跳过")
        return items

    except json.JSONDecodeError as e:
        print(f"    LLM 多样性增强 JSON 解析失败: {e}")
        print(f"    原始文本: {repr(text[:200])}")
        return items
    except Exception as e:
        print(f"    LLM 多样性增强 error: {e}")
        return items


def diversify_and_fill(tool_name, results):
    """一次多样性增强 + 补全。返回 (results, modified_count)。"""
    path = os.path.join(GEN_DIR, f"{tool_name}_gen.jsonl")
    before_snapshot = {i: (item["user_question"], json.dumps(item["arguments"], sort_keys=True, ensure_ascii=False))
                       for i, item in enumerate(results)}
    results = diversify_via_llm(tool_name, results[:100])
    seen = {item["user_question"] for item in results}
    modified = sum(1 for i, item in enumerate(results)
                   if i in before_snapshot and before_snapshot[i] != (item["user_question"], json.dumps(item["arguments"], sort_keys=True, ensure_ascii=False)))

    def save():
        with open(path, "w", encoding="utf-8") as f:
            for item in results[:100]:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
    save()

    need = 100 - len(results)
    if need > 0:
        for _ in range(5):
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

    return results[:100], modified


def process_tool_generate(tool_name):
    """生成 100 条数据，不做 LLM 去重。支持续跑。
    返回 (results, generated): generated 表示本轮是否有新数据生成。
    """
    path = os.path.join(GEN_DIR, f"{tool_name}_gen.jsonl")
    results = []
    seen = set()

    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    results.append(item)
                    seen.add(item["user_question"])
        if len(results) >= 100:
            print(f"  {tool_name}: 已有 {len(results)} 条，跳过 ✓")
            return results[:100], False
        print(f"  {tool_name}: 已有 {len(results)} 条，继续补全至 100 ...")
    else:
        print(f"  {tool_name}: 生成 100 条 ...")

    before_count = len(results)

    def save():
        with open(path, "w", encoding="utf-8") as f:
            for item in results[:100]:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

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

    generated = len(results) > before_count
    print(f"  → {min(len(results), 100)} 条\n")
    return results[:100], generated


def main(tools_filter=None):
    all_tools = load_tool_defs()
    if tools_filter:
        all_tools = {k: v for k, v in all_tools.items() if k in tools_filter}

    os.makedirs(GEN_DIR, exist_ok=True)
    print(f"工具: {len(all_tools)} 个, 各 100 条\n")

    # ---- 第一阶段：生成（不 LLM 去重），顺序处理每个工具 ----
    gen_results = {}  # {tool_name: results_list}
    gen_flags = {}    # {tool_name: bool}  本轮是否有新数据生成
    for tool_name in all_tools:
        results, generated = process_tool_generate(tool_name)
        gen_results[tool_name] = results
        gen_flags[tool_name] = generated

    # ---- 第二阶段：LLM 多样性增强，只处理本轮有新数据的工具 ----
    DEDUP_CONCURRENCY = 10
    pending = {k: v for k, v in gen_results.items() if v and gen_flags.get(k)}

    if pending:
        print(f"\nLLM 多样性增强: {len(pending)} 个工具, 并发 {DEDUP_CONCURRENCY}\n")

        with ThreadPoolExecutor(max_workers=DEDUP_CONCURRENCY) as pool:
            futures = {}
            for tool_name, results in pending.items():
                f = pool.submit(diversify_and_fill, tool_name, results)
                futures[f] = tool_name
            for future in as_completed(futures):
                tool_name = futures[future]
                results, modified = future.result()
                mark = f" (改 {modified})" if modified > 0 else ""
                print(f"  {tool_name}: {len(results)} 条{mark}")

    total = sum(len(v[:100]) for v in gen_results.values())
    print(f"\n完成: {total} 条")


def run_dedup_loop(tools_filter=None):
    """反复 LLM 多样性增强，直到所有工具无改动或达到最大轮次。"""
    all_tools = load_tool_defs()
    if tools_filter:
        all_tools = {k: v for k, v in all_tools.items() if k in tools_filter}

    DEDUP_CONCURRENCY = 5
    MAX_ROUNDS = 1

    def load_results(tool_name):
        path = os.path.join(GEN_DIR, f"{tool_name}_gen.jsonl")
        results = []
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        results.append(json.loads(line))
        return results[:100]

    tool_data = {}
    for name in all_tools:
        data = load_results(name)
        if data:
            tool_data[name] = data

    if not tool_data:
        print("没有 gen 文件，请先运行生成")
        return

    print(f"LLM 多样性增强循环: {len(tool_data)} 个工具, 并发 {DEDUP_CONCURRENCY}, 最多 {MAX_ROUNDS} 轮\n")

    for round_num in range(MAX_ROUNDS):
        pending = list(tool_data.keys())
        if not pending:
            break

        print(f"--- 第 {round_num + 1} 轮 ---")
        total_modified = 0

        with ThreadPoolExecutor(max_workers=DEDUP_CONCURRENCY) as pool:
            futures = {}
            for name in pending:
                f = pool.submit(diversify_and_fill, name, tool_data[name])
                futures[f] = name
            for future in as_completed(futures):
                name = futures[future]
                results, modified = future.result()
                tool_data[name] = results
                total_modified += modified
                mark = " ✓ 无需修改" if modified == 0 else f" (改 {modified})"
                print(f"  {name}: {len(results)} 条{mark}")

        if total_modified == 0:
            print(f"\n全部工具无需修改，退出")
            break
        print()

    print(f"完成")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tools", type=str, default="", help="指定工具名，逗号分隔")
    parser.add_argument("--dedup-only", action="store_true", help="只运行 LLM 多样性增强（反复增强直到无改动）")
    args = parser.parse_args()

    tool_list = [t.strip() for t in args.tools.split(",") if t.strip()] if args.tools else None

    if args.dedup_only:
        run_dedup_loop(tools_filter=tool_list)
    else:
        main(tools_filter=tool_list)
