"""
每工具独立提示词，保证生成数据贴合工具语义。
"""

TOOL_PROMPTS = {

    # ========================================
    # 应用管理
    # ========================================
    "list_application": {
        "system": "你是 function call 训练数据生成助手。要求列出已安装的应用。",
        "param_notes": "无参数。arguments 为空对象 {}。",
        "bad_examples": "不要生成\"打开应用列表\"或\"显示桌面\"，那是打开桌面的操作。",
    },

    "open_application": {
        "system": "你是 function call 训练数据生成助手。要求打开某个应用。",
        "param_notes": "application_name（STRING，必选）：应用名称。用常见中文应用名，如微信、支付宝、抖音、淘宝、美团、高德地图、网易云音乐等。",
        "bad_examples": "不要用英文应用名，不要生成打开网页的操作。",
    },

    # ========================================
    # 显示控制
    # ========================================
    "set_brightness": {
        "system": "你是 function call 训练数据生成助手。要求调节屏幕亮度。",
        "param_notes": """至少提供 level 或 direction 之一，两者可同时出现。
- level（STRING，可选）：目标亮度值，如 \"80\"。用户说\"调到80\"时使用。
- direction（STRING，可选）：\"high\"（调高）或 \"low\"（调低）。用户说\"调亮点\"时使用。
同时出现时以 level 为准（如\"调高到80\" → level:\"80\", direction:\"high\"）。""",
        "bad_examples": "不能 level 和 direction 都不提供。",
    },

    # ========================================
    # 通信
    # ========================================
    "send_email": {
        "system": "你是 function call 训练数据生成助手。要求发送邮件。",
        "param_notes": """contact_name（STRING，必选）：可以是姓名（如张伟、李娜）、邮箱地址（如 zhangwei@example.com）或电话号码（如 13812345678）。
subject（STRING，必选）：邮件主题。
message（STRING，可选）：邮件正文。""",
        "bad_examples": "不要用英文名。联系方式值要有真实感。",
    },

    "phone_call": {
        "system": "你是 function call 训练数据生成助手。要求给某人打电话。",
        "param_notes": "contact_name（STRING，必选）：可以是姓名（如张伟）或电话号码（如 13812345678）。",
        "bad_examples": "不要用英文名。",
    },

    "phone_sms": {
        "system": "你是 function call 训练数据生成助手。要求发短信。",
        "param_notes": """contact_name（STRING，必选）：可以是姓名或电话号码。
message（STRING，可选）：短信内容。""",
        "bad_examples": "不要生成彩信、群发。",
    },

    # ========================================
    # 系统信息
    # ========================================
    "battery_status": {
        "system": "你是 function call 训练数据生成助手。想了解电池情况。",
        "param_notes": "无参数。arguments 为空对象 {}。",
        "bad_examples": "不要生成\"充电\"或\"省电模式\"的请求，这属于其他工具的功能。",
    },

    # ========================================
    # 连接与网络
    # ========================================
    "toggle_wifi": {
        "system": "你是 function call 训练数据生成助手。要求开关WiFi。",
        "param_notes": "enable（BOOLEAN，必选）：true 打开，false 关闭。",
        "bad_examples": "不要生成\"连接某个WiFi\"，只能开关。",
    },

    "toggle_bluetooth": {
        "system": "你是 function call 训练数据生成助手。要求开关蓝牙。",
        "param_notes": "enable（BOOLEAN，必选）：true 打开，false 关闭。",
        "bad_examples": "不要生成\"连接某个设备\"，只能开关。",
    },

    "toggle_mobile_data": {
        "system": "你是 function call 训练数据生成助手。要求开关移动数据。",
        "param_notes": "enable（BOOLEAN，必选）：true 打开，false 关闭。",
        "bad_examples": "不要生成\"查看流量用量\"。",
    },

    "toggle_airplane_mode": {
        "system": "你是 function call 训练数据生成助手。要求开关飞行模式。",
        "param_notes": "enable（BOOLEAN，必选）：true 打开，false 关闭。",
        "bad_examples": "不要和其他网络开关混淆。",
    },

    # ========================================
    # 媒体
    # ========================================
    "play_music": {
        "system": "你是 function call 训练数据生成助手。要求播放音乐。",
        "param_notes": """song_name（STRING，可选）：歌曲名，用真实歌曲名如\"晴天\"\"夜曲\"\"平凡之路\"。
artist（STRING，可选）：歌手名，如\"周杰伦\"\"林俊杰\"\"陈奕迅\"。""",
        "bad_examples": "不要生成\"下一首\"、\"暂停\"等，这些是其他工具的功能。",
    },

    "pause_music": {
        "system": "你是 function call 训练数据生成助手。要求暂停音乐。",
        "param_notes": "无参数。arguments 为空对象 {}。",
        "bad_examples": "不要生成\"停止播放\"以外的功能。",
    },

    "take_picture": {
        "system": "你是 function call 训练数据生成助手。要求拍照。",
        "param_notes": "无参数。arguments 为空对象 {}。",
        "bad_examples": "不要生成\"录像\"（这是另一个工具）。",
    },

    "take_screenshot": {
        "system": "你是 function call 训练数据生成助手。要求截图。",
        "param_notes": "无参数。arguments 为空对象 {}。",
        "bad_examples": "不要生成\"拍照\"（这是另一个工具）。",
    },

    # ========================================
    # 硬件控制
    # ========================================
    "set_flashlight": {
        "system": "你是 function call 训练数据生成助手。要求开关手电筒。",
        "param_notes": "enable（BOOLEAN，必选）：true 打开，false 关闭。",
        "bad_examples": "不要生成\"调节亮度\"。",
    },

    # ========================================
    # 地图与定位
    # ========================================
    "show_map": {
        "system": "你是 function call 训练数据生成助手。要求在地图上查看某个位置。",
        "param_notes": "destination（STRING，必选）：位置名称或地址。用真实地名，如\"天安门\"\"陆家嘴\"\"西湖\"\"三里屯\"。",
        "bad_examples": "不要生成\"导航到\"的请求（那是navigate工具）。",
    },

    "get_location": {
        "system": "你是 function call 训练数据生成助手。想查询当前所在位置。",
        "param_notes": "无参数。arguments 为空对象 {}。",
        "bad_examples": "不要生成\"导航\"或\"搜索位置\"的请求。",
    },

    "navigate": {
        "system": "你是 function call 训练数据生成助手。要求导航到某地。",
        "param_notes": "destination（STRING，必选）：目的地名称或地址。用真实地名，如\"北京西站\"\"浦东机场\"\"三里屯太古里\"。",
        "bad_examples": "不要生成\"在地图上看看\"这种只是查看位置的请求。",
    },

    # ========================================
    # 通讯录
    # ========================================
    "create_contact": {
        "system": "你是 function call 训练数据生成助手。要求新建联系人。",
        "param_notes": """contact_name（STRING，必选）：联系人姓名，常见中文名。
email（STRING，可选）：邮箱地址，如 zhangwei@example.com。
phone_number（STRING，可选）：手机号码，如 13812345678。""",
        "bad_examples": "不要用英文名。邮箱和电话号码要看起来真实。",
    },

    "search_contacts": {
        "system": "你是 function call 训练数据生成助手。要在通讯录中搜索联系人。",
        "param_notes": "contact_name（STRING，必选）：要搜索的姓名或电话号码。可以是全名或部分。",
        "bad_examples": "不要生成\"打电话给XX\"（那是phone_call）。",
    },

    # ========================================
    # 提醒与时间
    # ========================================
    "set_alarm": {
        "system": "你是 function call 训练数据生成助手。要求设置闹钟。",
        "param_notes": """datetime（STRING，必选）：日期时间，格式 YYYY-MM-DDTHH:MM:SS。
label（STRING，可选）：闹钟标签，如\"起床\"\"开会\"\"吃药\"。
repeat（STRING，可选）：重复模式，如\"daily\"\"weekly\"\"weekdays\"。""",
        "bad_examples": "不要生成设置倒计时/计时器（这是另一个工具不做）。",
    },

    # ========================================
    # 声音控制
    # ========================================
    "set_volume": {
        "system": "你是 function call 训练数据生成助手。要求调节音量。",
        "param_notes": """至少提供 level 或 direction 之一，两者可同时出现。
- level（STRING，可选）：目标音量值，如 \"80\"。用户说\"调到80\"时使用。
- direction（STRING，可选）：\"high\"（调高）或 \"low\"（调低）。用户说\"调大点\"时使用。
同时出现时以 level 为准。""",
        "bad_examples": "不能 level 和 direction 都不提供。不要说\"静音\"（那是set_mute）。",
    },

    "set_mute": {
        "system": "你是 function call 训练数据生成助手。要求设置静音或取消。",
        "param_notes": "enable（BOOLEAN，必选）：true 静音，false 取消静音。",
        "bad_examples": "不要生成\"音量调到0\"，那是set_volume。",
    },

    # ========================================
    # 浏览与搜索
    # ========================================
    "search_web": {
        "system": "你是 function call 训练数据生成助手。要求搜索信息。",
        "param_notes": "query（STRING，必选）：搜索关键词，用中文自然表达。",
        "bad_examples": "不要生成\"打开网址\"（无此工具）。",
    },

    # ========================================
    # 系统模式
    # ========================================
    "toggle_dnd": {
        "system": "你是 function call 训练数据生成助手。要求开关勿扰模式。",
        "param_notes": "enable（BOOLEAN，必选）：true 开启，false 关闭。",
        "bad_examples": "不要生成\"静音\"（那是set_mute）。",
    },

    "toggle_power_saving_mode": {
        "system": "你是 function call 训练数据生成助手。要求开关省电模式。",
        "param_notes": "enable（BOOLEAN，必选）：true 开启，false 关闭。",
        "bad_examples": "不要生成\"查看电池\"（那是battery_status）。",
    },

    # ========================================
    # 天气服务
    # ========================================
    "get_weather": {
        "system": "你是 function call 训练数据生成助手。想查询天气。",
        "param_notes": """city（STRING，可选）：城市名，如\"北京\"\"上海\"\"杭州\"。不提供则查本地。
datetime（STRING，可选）：日期时间，格式 YYYY-MM-DDTHH:MM:SS。不提供则查今天。""",
        "bad_examples": "不要生成\"设置天气提醒\"。",
    },

    # ========================================
    # 日程管理
    # ========================================
    "create_calendar_event": {
        "system": "你是 function call 训练数据生成助手。要求创建日历事件。",
        "param_notes": """title（STRING，必选）：事件标题，简短。
start_date（STRING，必选）：开始时间 YYYY-MM-DDTHH:MM:SS。
end_date（STRING，必选）：结束时间 YYYY-MM-DDTHH:MM:SS。通常比开始时间晚1-2小时。""",
        "bad_examples": "不要生成\"提醒\"（那是set_alarm）。",
    },

    "search_calendar_events": {
        "system": "你是 function call 训练数据生成助手。想查询日历中的事件。",
        "param_notes": """query（STRING，可选）：搜索关键词。
start_date（STRING，可选）：查询起始日 YYYY-MM-DD。
end_date（STRING，可选）：查询结束日 YYYY-MM-DD。""",
        "bad_examples": "不要生成\"创建事件\"（那是create_calendar_event）。",
    },

    # ========================================
    # 备忘录
    # ========================================
    "create_note": {
        "system": "你是 function call 训练数据生成助手。要求记一条笔记。",
        "param_notes": """title（STRING，必选）：笔记标题，简短。
content（STRING，必选）：笔记正文，可以稍长。""",
        "bad_examples": "不要生成\"设置提醒\"或\"创建日历\"。",
    },

}
