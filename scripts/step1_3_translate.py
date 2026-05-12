"""
Step 1.3 — 英文→中文翻译

读取 step1 的 _en.jsonl 文件，批量调 LLM 将英文问题翻译为中文。
保留 arguments 不变。每批最多 20 条减少请求次数。
"""

import json
import os
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEP1_DIR = os.path.join(PROJECT_ROOT, "output", "step1")
LLM_URL = "http://182.150.59.81:31845/v1/chat/completions"
LLM_MODEL = "Qwen3-30B-A3B-Instruct-2507"
BATCH_SIZE = 20


def load_en_files(directory: str) -> dict:
    """加载所有 _en.jsonl 文件，返回 {tool_name: [items]}。"""
    results = {}
    for fname in sorted(os.listdir(directory)):
        if not fname.endswith("_en.jsonl"):
            continue
        tool = fname.replace("_en.jsonl", "")
        path = os.path.join(directory, fname)
        items = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        results[tool] = items
    return results


def build_batches(items: list[dict], batch_size: int) -> list[list[dict]]:
    """将 items 切分为批次。"""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def translate_batch(batch: list[dict]) -> list[str]:
    """单批翻译，调 LLM 返回中文列表。"""
    # 构建英文列表
    en_list = [item["en"] for item in batch]
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(en_list))

    import urllib.request

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你将一组英文用户问题翻译为中文。要求：\n"
                    "1. 中文表达自然口语化，符合中文用户的说话习惯\n"
                    "2. 准确翻译语义，不增减信息\n"
                    "3. 输出一个 JSON 数组，每个元素是一条翻译结果\n"
                    "4. 只输出 JSON 数组，不要任何其他内容"
                ),
            },
            {
                "role": "user",
                "content": f"请翻译以下 {len(en_list)} 条英文问题：\n\n{numbered}",
            },
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        LLM_URL,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        text = body["choices"][0]["message"]["content"].strip()

        # 解析 JSON 数组
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text.strip("`")

        translations = json.loads(text)
        if not isinstance(translations, list):
            translations = [translations]
        # 确保每条是纯字符串
        result = []
        for t in translations:
            if isinstance(t, str):
                result.append(t)
            elif isinstance(t, dict):
                # 兜底：取第一个值
                result.append(list(t.values())[0] if t.values() else str(t))
            else:
                result.append(str(t))
        return result
    except Exception as e:
        print(f"    [ERROR] {e}")
        # 失败时原样返回英文
        return en_list


def main():
    en_data = load_en_files(STEP1_DIR)
    tool_count = len(en_data)
    total_items = sum(len(v) for v in en_data.values())
    print(f"待翻译工具: {tool_count} 个, 合计 {total_items} 条\n")

    for idx, (tool, items) in enumerate(en_data.items()):
        batches = build_batches(items, BATCH_SIZE)
        print(f"[{idx+1}/{tool_count}] {tool} ({len(items)} 条, {len(batches)} 批)")

        translated = []
        for bi, batch in enumerate(batches):
            zhs = translate_batch(batch)
            for item, zh in zip(batch, zhs):
                translated.append({"zh": zh, "en": item["en"], "arguments": item["arguments"]})
            print(f"  批 {bi+1}/{len(batches)} 完成")
            if bi < len(batches) - 1:
                time.sleep(0.5)  # 避免速率过快

        # 写入 _zh.jsonl
        out_path = os.path.join(STEP1_DIR, f"{tool}_zh.jsonl")
        with open(out_path, "w", encoding="utf-8") as f:
            for item in translated:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"  → 已保存 {out_path} ({len(translated)} 条)\n")

    print("1.3 翻译完成")


if __name__ == "__main__":
    main()
