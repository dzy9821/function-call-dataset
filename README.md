# 移动端 Function Call 训练数据集生成

基于 32 款手机助手工具定义，生成中文 function calling 训练数据。

## 工具清单

| 索引 | 工具名称 | 分类 | 描述 | 必选参数 | 可选参数 |
| -- | --- | --- | --- | --- | --- |
| 1 | list_application | 应用管理 | 列出此手机上安装的应用程序。 | 无 | 无 |
| 2 | open_application | 应用管理 | 打开指定应用程序。 | application_name | 无 |
| 3 | set_brightness | 显示控制 | 调节屏幕亮度。 | 无 | level, direction |
| 4 | send_email | 通信 | 发送电子邮件。 | contact_name, subject | message |
| 5 | phone_call | 通信 | 拨打指定联系人的电话。 | contact_name | 无 |
| 6 | phone_sms | 通信 | 发送短信。 | contact_name | message |
| 7 | battery_status | 系统信息 | 提供设备电池的相关信息。 | 无 | 无 |
| 8 | toggle_wifi | 连接与网络 | 开启或关闭Wi-Fi功能。 | enable | 无 |
| 9 | toggle_bluetooth | 连接与网络 | 开启或关闭蓝牙功能。 | enable | 无 |
| 10 | toggle_mobile_data | 连接与网络 | 开启或关闭移动数据网络。 | enable | 无 |
| 11 | toggle_airplane_mode | 连接与网络 | 开启或关闭飞行模式。 | enable | 无 |
| 12 | play_music | 媒体 | 播放音乐或歌曲。 | 无 | song_name, artist |
| 13 | pause_music | 媒体 | 暂停当前播放的音乐。 | 无 | 无 |
| 14 | take_picture | 媒体 | 使用相机拍照。 | 无 | 无 |
| 15 | take_screenshot | 媒体 | 截取当前屏幕内容。 | 无 | 无 |
| 16 | set_flashlight | 硬件控制 | 开启或关闭手电筒。 | enable | 无 |
| 17 | show_map | 地图与定位 | 在地图上显示指定位置。 | destination | 无 |
| 18 | get_location | 地图与定位 | 获取当前设备地理位置。 | 无 | 无 |
| 19 | navigate | 地图与定位 | 启动导航到指定目的地。 | destination | 无 |
| 20 | create_contact | 通讯录 | 创建联系人。 | contact_name | email, phone_number |
| 21 | search_contacts | 通讯录 | 搜索联系人。 | contact_name | 无 |
| 22 | set_alarm | 提醒与时间 | 设置一个闹钟。 | datetime | label, repeat |
| 23 | set_volume | 声音控制 | 调节设备音量。 | 无 | level, direction |
| 24 | set_mute | 声音控制 | 设置设备静音状态。 | enable | 无 |
| 25 | search_web | 浏览与搜索 | 使用搜索引擎进行搜索。 | query | 无 |
| 26 | toggle_dnd | 系统模式 | 开启或关闭勿扰模式。 | enable | 无 |
| 27 | toggle_power_saving_mode | 系统模式 | 开启或关闭省电模式。 | enable | 无 |
| 28 | get_weather | 天气服务 | 获取天气信息。 | 无 | city,datetime |
| 29 | create_calendar_event | 日程管理 | 创建一个新的日历事件。 | title, start_date, end_date | 无 |
| 30 | search_calendar_events | 日程管理 | 查询日历中的事件。 | 无 | query, start_date, end_date |
| 31 | create_note | 备忘录 | 创建一条备忘录或笔记。 | title, content | 无 |

## 整体流程

1. **Step 1** — 单工具数据采集（每工具 100 条中文数据）
2. **Step 2** — 工具关联分析（每工具 top-5 关联工具）
3. **Step 3** — 双工具组合数据生成
4. **Step 4** — 最终训练格式输出

## 进度

### Step 1 — 单工具数据采集

- [x] **1.1 数据盘点** — `scripts/step1_1_inventory.py`
  - 产物：`output/step1/inventory.json`
- [x] **1.2 英文提取+参数匹配** — `scripts/step1_2_extract.py`
  - 三类：✓ 参数匹配 (7)、✗ 同名参数不同 (7 含重叠)、- 无数据 (17)
  - 所有同名工具均提取，参数重叠的保留重叠字段，无重叠的 arguments 为空
  - 产物：`output/step1/en/{tool}_en.jsonl` × 14
- [x] **1.3 英文→中文翻译** — `scripts/step1_3_translate.py`
  - deepseek-v4-flash，并发 5
  - 12 工具 560 条已翻译（部分数据已手动筛选删除）
  - 产物：`output/step1/zh/{tool}_zh.jsonl`（格式 `{zh, en, arguments}`）
- [ ] **1.4 参数生成** — `scripts/step1_4_args.py`
  - 对 zh/ 中中文问题 + 工具定义 → deepseek-v4-flash 生成 arguments
  - 输出：写回 `zh/{tool}_zh.jsonl`
- [ ] **1.5 LLM 补全** — `scripts/step1_5_generate.py`（已简化）
  - 31 工具各生成 100 条，本地去重，不检查已有数据
  - 1.4 生成的 zh/ arguments 需手动审查
  - 用法：`DEEPSEEK_API_KEY=xxx python scripts/step1_5_generate.py [--tools xxx]`
- [ ] **1.6 输出合并** — 待定

### Step 2 — 工具关联分析

- [ ] 待规划

### Step 3 — 双工具组合

- [ ] 待规划

### Step 4 — 最终格式

- [ ] 待规划

## 未来规划

- Step 2: 对 32 个工具分析关联关系（LLM 判断），每工具找 top-5 关联工具，去重得唯一工具对
- Step 3: 关联工具对交叉组合，LLM 合并用户问题为自然中文
- Step 4: 统一下游训练格式 `{data_source, messages, reward_model}`
