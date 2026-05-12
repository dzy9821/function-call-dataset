"""手动补全 17 个差 1-2 条的工具"""
import json, os

GEN_DIR = "/home/ubuntu/project/function-call-dataset/output/step1/gen"

MANUAL = {
    "get_weather": [
        {"user_question": "明天出门需不需要带伞？", "arguments": {"datetime": "2026-03-06T08:00:00"}},
    ],
    "open_application": [
        {"user_question": "帮我打开美团", "arguments": {"application_name": "美团"}},
        {"user_question": "开一下淘宝", "arguments": {"application_name": "淘宝"}},
    ],
    "pause_music": [
        {"user_question": "别放了，先停一下音乐", "arguments": {}},
    ],
    "play_music": [
        {"user_question": "来一首周杰伦的晴天", "arguments": {"song_name": "晴天", "artist": "周杰伦"}},
    ],
    "search_contacts": [
        {"user_question": "帮我在通讯录里找一下刘洋", "arguments": {"contact_name": "刘洋"}},
    ],
    "search_web": [
        {"user_question": "百度一下今天的热搜是什么", "arguments": {"query": "今日热搜"}},
    ],
    "set_brightness": [
        {"user_question": "亮度调到80", "arguments": {"level": "80"}},
    ],
    "set_flashlight": [
        {"user_question": "太黑了，打开手电筒照一下", "arguments": {"enable": True}},
    ],
    "set_mute": [
        {"user_question": "开会了，手机静音", "arguments": {"enable": True}},
    ],
    "set_volume": [
        {"user_question": "音量给我拉到最大", "arguments": {"level": "100"}},
    ],
    "take_picture": [
        {"user_question": "拍张照留个纪念", "arguments": {}},
    ],
    "toggle_airplane_mode": [
        {"user_question": "要起飞了，开飞行模式", "arguments": {"enable": True}},
    ],
    "toggle_bluetooth": [
        {"user_question": "连一下车载蓝牙", "arguments": {"enable": True}},
    ],
    "toggle_dnd": [
        {"user_question": "把勿扰模式打开，我要睡了", "arguments": {"enable": True}},
    ],
    "toggle_mobile_data": [
        {"user_question": "没WiFi了，开流量吧", "arguments": {"enable": True}},
    ],
    "toggle_power_saving_mode": [
        {"user_question": "快没电了，开省电模式撑一下", "arguments": {"enable": True}},
    ],
    "toggle_wifi": [
        {"user_question": "到家了，连上WiFi", "arguments": {"enable": True}},
    ],
}

for tool, items in MANUAL.items():
    path = os.path.join(GEN_DIR, f"{tool}_gen.jsonl")
    seen = set()
    existing = []
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                q = r.get("user_question", "")
                if q not in seen:
                    seen.add(q)
                    existing.append(r)
    new_count = 0
    for item in items:
        item["tool_name"] = tool
        q = item["user_question"]
        if q not in seen:
            seen.add(q)
            existing.append(item)
            new_count += 1
    with open(path, "w") as f:
        for item in existing:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"  {tool:<30s} +{new_count} → {len(existing)} 条")

# Verify
print()
total = 0
done = 0
for f in sorted(os.listdir(GEN_DIR)):
    if f.endswith("_gen.jsonl"):
        with open(os.path.join(GEN_DIR, f)) as fh:
            c = sum(1 for _ in fh)
        total += c
        tool = f.replace("_gen.jsonl", "")
        mark = "✓" if c >= 100 else f"✗ {c}"
        print(f"  {tool:<30s} {c:>3d}  {mark}")
        if c >= 100:
            done += 1
print(f"\n{done}/32 完成, 共 {total} 条")
