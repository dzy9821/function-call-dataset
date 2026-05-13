# 移动端 Function Call 训练数据集生成

为端侧 function call 模型生成中文训练数据，覆盖 31 个手机助手工具。

## 项目结构

```
├── tools_definition.py          # 31 个工具的 function 定义（OpenAI 格式）
├── scripts/
│   ├── prompts.py               # 每工具独立提示词（step1_5 使用）
│   ├── step1_1_inventory.py     # 数据盘点
│   ├── step1_2_extract.py       # 英文提取 + 参数匹配
│   ├── step1_3_translate.py     # 英文→中文翻译
│   ├── step1_4_args.py          # 参数补全（模型生成 arguments）
│   └── step1_5_generate.py      # LLM 批量生成
├── ori-datasets/                # 原始参考数据集（英文, 各约 9500 条）
│   ├── AliRGHZ-Mobile-Actions.jsonl
│   └── google-mobile-actions.jsonl
└── output/
    └── step1/
        ├── inventory.json       # 盘点结果（31 工具）
        ├── en/                  # 提取的英文数据（12 工具, 560 条）
        ├── zh/                  # 翻译+参数补全（12 工具, 272 条，部分已筛选）
        └── gen/                 # LLM 生成（待产出）
```

## 工具清单（31 个）

| # | 名称 | 分类 | 必选 | 可选 |
|---|------|------|------|------|
| 1 | list_application | 应用管理 | — | — |
| 2 | open_application | 应用管理 | application_name | — |
| 3 | set_brightness | 显示控制 | — | level, direction |
| 4 | send_email | 通信 | contact_name, subject | message |
| 5 | phone_call | 通信 | contact_name | — |
| 6 | phone_sms | 通信 | contact_name | message |
| 7 | battery_status | 系统信息 | — | — |
| 8 | toggle_wifi | 连接与网络 | enable | — |
| 9 | toggle_bluetooth | 连接与网络 | enable | — |
| 10 | toggle_mobile_data | 连接与网络 | enable | — |
| 11 | toggle_airplane_mode | 连接与网络 | enable | — |
| 12 | play_music | 媒体 | — | song_name, artist |
| 13 | pause_music | 媒体 | — | — |
| 14 | take_picture | 媒体 | — | — |
| 15 | take_screenshot | 媒体 | — | — |
| 16 | set_flashlight | 硬件控制 | enable | — |
| 17 | show_map | 地图与定位 | destination | — |
| 18 | get_location | 地图与定位 | — | — |
| 19 | navigate | 地图与定位 | destination | — |
| 20 | create_contact | 通讯录 | contact_name | email, phone_number |
| 21 | search_contacts | 通讯录 | contact_name | — |
| 22 | set_alarm | 提醒与时间 | datetime | label, repeat |
| 23 | set_volume | 声音控制 | — | level, direction |
| 24 | set_mute | 声音控制 | enable | — |
| 25 | search_web | 浏览与搜索 | query | — |
| 26 | toggle_dnd | 系统模式 | enable | — |
| 27 | toggle_power_saving_mode | 系统模式 | enable | — |
| 28 | get_weather | 天气服务 | — | city, datetime |
| 29 | create_calendar_event | 日程管理 | title, start_date, end_date | — |
| 30 | search_calendar_events | 日程管理 | — | query, start_date, end_date |
| 31 | create_note | 备忘录 | title, content | — |

## 数据流水线

```
原始数据集 → 1.1盘点 → 1.2提取(参数匹配) → 1.3翻译 → 1.4参数补全 → 1.5 LLM生成 → 1.6 合并
```

### Step 1.1 — 数据盘点
`python scripts/step1_1_inventory.py`

扫描两个原始数据集（共 ~19,000 条），统计每个工具的用户问题数量，与 31 个目标工具做交集。

产物：`output/step1/inventory.json`

### Step 1.2 — 英文提取 + 参数匹配
`python scripts/step1_2_extract.py`

对比原始参数名与目标参数名，分三类：

| 类别 | 数量 | 处理方式 |
|------|------|----------|
| 参数匹配 ✓ | 7 | 提取完整 arguments |
| 同名参数不同 ✗ | 7 | 只提取重叠的参数名 |
| 不在数据集 | 17 | 无数据，靠 1.5 生成 |

产物：`output/step1/en/{tool}_en.jsonl`（12 文件，560 条，去重后，人工审核后，部分已删除，当前剩下272条）

### Step 1.3 — 英文→中文翻译
`python scripts/step1_3_translate.py`

使用 deepseek-v4-flash 逐条翻译，并发 5，保留原文和 arguments。

产物：`output/step1/zh/{tool}_zh.jsonl`（格式 `{zh, en, arguments}`）

### Step 1.4 — 参数补全
`python scripts/step1_4_args.py`

对 zh/ 中 arguments 不完整的条目，发送中文问题 + 完整工具定义 JSON 到 deepseek-v4-flash，让模型提取参数值。

判断"完整"的标准：所有必选参数存在且非空。无参工具的 `{}` 视为完整。

产物：写回 `zh/{tool}_zh.jsonl`

### Step 1.5 — LLM 批量生成（待执行）
`DEEPSEEK_API_KEY=xxx python scripts/step1_5_generate.py [--tools xxx]`

31 工具各生成 100 条中文数据。每次 API 调用生成 1 条，5 并发。

三阶段：
1. 本地精确去重凑满 100 → 自动保存
2. deepseek-v4-pro 语义去重（去掉几乎完全相同的条目）→ 自动保存
3. 去重后有缺口自动补全

有必选参数的工具随机混入反例（模糊请求、arguments 为空）。

产物：`output/step1/gen/{tool}_gen.jsonl`（每文件 100 条）

### Step 1.6 — 输出合并（待规划）

### Step 2-4 — 待规划（工具关联分析、双工具组合、最终格式）

## 进度

- [x] **1.1 数据盘点**
- [x] **1.2 英文提取 + 参数匹配**
- [x] **1.3 英文→中文翻译**（12 工具 272 条，部分已手动筛选）
- [x] **1.4 参数补全**
- [ ] **1.5 LLM 批量生成**
- [ ] **1.6 输出合并**
- [ ] **Step 2 — 工具关联分析**
- [ ] **Step 3 — 双工具组合**
- [ ] **Step 4 — 最终格式**
