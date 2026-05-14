"""
每工具独立提示词，保证生成数据贴合工具语义。
"""

TOOL_PROMPTS = {

    # ========================================
    # 应用管理
    # ========================================
    "list_application": {
        "system": "你是 function call 训练数据生成助手。要求列出已安装的应用。表达多样化、覆盖不同场景和角度。",
        "param_notes": "无参数。arguments 为空对象 {}。" 
    },

    "open_application": {
        "system": "你是 function call 训练数据生成助手。要求打开某个应用。表达多样化、覆盖不同场景和角度。",
        "param_notes": "application_name（STRING，必选）：应用名称。覆盖系统应用、英文名称应用、常用中文名应用等不同类型。" 
    },

    # ========================================
    # 显示控制
    # ========================================
    "set_brightness": {
        "system": "你是 function call 训练数据生成助手。要求调节屏幕亮度。表达多样化、覆盖不同场景和角度。",
        "param_notes": """至少提供 level 或 direction 之一，两者可同时出现。
- level（STRING，可选）：目标亮度值，如 \"80\"。用户说\"调到80\"时使用。
- direction（STRING，可选）：\"high\"（调高）或 \"low\"（调低）。用户说\"调亮点\"时使用。
同时出现时以 level 为准（如\"调高到80\" → level:\"80\", direction:\"high\"）。""" 
    },

    # ========================================
    # 通信
    # ========================================
    "send_email": {
        "system": "你是 function call 训练数据生成助手。要求发送邮件。表达多样化、覆盖不同场景和角度。",
        "param_notes": """contact_name（STRING，必选）：姓名/邮箱/电话。使用多元化的中文名（不同姓氏如张王李赵刘陈杨周吴孙），邮箱用不同域名（@qq.com @163.com @gmail.com），电话号段多样化。
subject（STRING，必选）：邮件主题，覆盖工作、生活、学习等场景。
message（STRING，可选）：邮件正文。"""
    },

    "phone_call": {
        "system": "你是 function call 训练数据生成助手。要求给某人打电话。表达多样化、覆盖不同场景和角度。",
        "param_notes": "contact_name（STRING，必选）：姓名或电话号码。使用多元化的中文名（不同姓氏），电话号段多样化。" 
    },

    "phone_sms": {
        "system": "你是 function call 训练数据生成助手。要求发短信。表达多样化、覆盖不同场景和角度。",
        "param_notes": """contact_name（STRING，必选）：姓名或电话号码，多元化。
message（STRING，可选）：短信内容，覆盖通知、问候、确认等场景。"""
    },

    # ========================================
    # 系统信息
    # ========================================
    "battery_status": {
        "system": "你是 function call 训练数据生成助手。想了解电池情况。表达多样化、覆盖不同场景和角度。",
        "param_notes": "无参数。arguments 为空对象 {}。" 
    },

    # ========================================
    # 连接与网络
    # ========================================
    "toggle_wifi": {
        "system": "你是 function call 训练数据生成助手。要求开关WiFi。表达多样化、覆盖不同场景和角度。",
        "param_notes": "enable（BOOLEAN，必选）：true 打开，false 关闭。" 
    },

    "toggle_bluetooth": {
        "system": "你是 function call 训练数据生成助手。要求开关蓝牙。表达多样化、覆盖不同场景和角度。",
        "param_notes": "enable（BOOLEAN，必选）：true 打开，false 关闭。" 
    },

    "toggle_mobile_data": {
        "system": "你是 function call 训练数据生成助手。要求开关移动数据。表达多样化、覆盖不同场景和角度。",
        "param_notes": "enable（BOOLEAN，必选）：true 打开，false 关闭。" 
    },

    "toggle_airplane_mode": {
        "system": "你是 function call 训练数据生成助手。要求开关飞行模式。表达多样化、覆盖不同场景和角度。",
        "param_notes": "enable（BOOLEAN，必选）：true 打开，false 关闭。" 
    },

    # ========================================
    # 媒体
    # ========================================
    "play_music": {
        "system": "你是 function call 训练数据生成助手。要求播放音乐。表达多样化、覆盖不同场景和角度。",
        "param_notes": """song_name（STRING，可选）：歌曲名，覆盖不同年代、风格（流行、摇滚、民谣、说唱等）。
artist（STRING，可选）：歌手名，覆盖不同地区、年代的艺人。"""
    },

    "pause_music": {
        "system": "你是 function call 训练数据生成助手。要求暂停音乐。表达多样化、覆盖不同场景和角度。",
        "param_notes": "无参数。arguments 为空对象 {}。" 
    },

    "take_picture": {
        "system": "你是 function call 训练数据生成助手。要求拍照。表达多样化、覆盖不同场景和角度。",
        "param_notes": "无参数。arguments 为空对象 {}。" 
    },

    "take_screenshot": {
        "system": "你是 function call 训练数据生成助手。要求截图。表达多样化、覆盖不同场景和角度。",
        "param_notes": "无参数。arguments 为空对象 {}。" 
    },

    # ========================================
    # 硬件控制
    # ========================================
    "set_flashlight": {
        "system": "你是 function call 训练数据生成助手。要求开关手电筒。表达多样化、覆盖不同场景和角度。",
        "param_notes": "enable（BOOLEAN，必选）：true 打开，false 关闭。" 
    },

    # ========================================
    # 地图与定位
    # ========================================
    "show_map": {
        "system": "你是 function call 训练数据生成助手。要求在地图上查看某个位置。表达多样化、覆盖不同场景和角度。",
        "param_notes": "destination（STRING，必选）：位置名称或地址。覆盖不同城市、不同类型（景点、商圈、交通枢纽、学校、医院等），如\"故宫\"\"陆家嘴\"\"春熙路\"\"广州塔\"\"武汉大学\"。" 
    },

    "get_location": {
        "system": "你是 function call 训练数据生成助手。想查询当前所在位置。表达多样化、覆盖不同场景和角度。",
        "param_notes": "无参数。arguments 为空对象 {}。" 
    },

    "navigate": {
        "system": "你是 function call 训练数据生成助手。要求导航到某地。表达多样化、覆盖不同场景和角度。",
        "param_notes": "destination（STRING，必选）：目的地。覆盖不同城市、不同类型（机场、火车站、商场、餐厅、景点、住宅区等）。" 
    },

    # ========================================
    # 通讯录
    # ========================================
    "create_contact": {
        "system": "你是 function call 训练数据生成助手。要求新建联系人。表达多样化、覆盖不同场景和角度。",
        "param_notes": """contact_name（STRING，必选）：联系人姓名，使用多元化的中文名（不同姓氏、不同字辈）。
email（STRING，可选）：邮箱，不同域名。
phone_number（STRING，可选）：手机号，不同号段。""" 
    },

    "search_contacts": {
        "system": "你是 function call 训练数据生成助手。要在通讯录中搜索联系人。表达多样化、覆盖不同场景和角度。",
        "param_notes": "contact_name（STRING，必选）：要搜索的姓名或电话号码。可以是全名或部分。" 
    },

    # ========================================
    # 提醒与时间
    # ========================================
    "set_alarm": {
        "system": "你是 function call 训练数据生成助手。要求设置闹钟。表达多样化、覆盖不同场景和角度。",
        "param_notes": """datetime（STRING，必选）：日期时间 YYYY-MM-DDTHH:MM:SS，时间多样化（早中晚不同时段）。
label（STRING，可选）：闹钟标签，覆盖起床、会议、运动、学习、吃药、接人等场景。
repeat（STRING，可选）：\"daily\"\"weekly\"\"weekdays\" 等。"""
    },

    # ========================================
    # 声音控制
    # ========================================
    "set_volume": {
        "system": "你是 function call 训练数据生成助手。要求调节音量。表达多样化、覆盖不同场景和角度。",
        "param_notes": """至少提供 level 或 direction 之一，两者可同时出现。
- level（STRING，可选）：目标音量值，如 \"80\"。用户说\"调到80\"时使用。
- direction（STRING，可选）：\"high\"（调高）或 \"low\"（调低）。用户说\"调大点\"时使用。
同时出现时以 level 为准。""" 
    },

    "set_mute": {
        "system": "你是 function call 训练数据生成助手。要求设置静音或取消。表达多样化、覆盖不同场景和角度。",
        "param_notes": "enable（BOOLEAN，必选）：true 静音，false 取消静音。" 
    },

    # ========================================
    # 浏览与搜索
    # ========================================
    "search_web": {
        "system": "你是 function call 训练数据生成助手。要求搜索信息。表达多样化、覆盖不同场景和角度。",
        "param_notes": "query（STRING，必选）：搜索关键词。覆盖新闻、生活、科技、娱乐、健康、教育等不同领域。" 
    },

    # ========================================
    # 系统模式
    # ========================================
    "toggle_dnd": {
        "system": "你是 function call 训练数据生成助手。要求开关勿扰模式。表达多样化、覆盖不同场景和角度。",
        "param_notes": "enable（BOOLEAN，必选）：true 开启，false 关闭。" 
    },

    "toggle_power_saving_mode": {
        "system": "你是 function call 训练数据生成助手。要求开关省电模式。表达多样化、覆盖不同场景和角度。",
        "param_notes": "enable（BOOLEAN，必选）：true 开启，false 关闭。" 
    },

    # ========================================
    # 天气服务
    # ========================================
    "get_weather": {
        "system": "你是 function call 训练数据生成助手。想查询天气。表达多样化、覆盖不同场景和角度。",
        "param_notes": """city（STRING，可选）：城市名，覆盖全国不同区域（华北、华东、华南、西南、西北等），如\"哈尔滨\"\"成都\"\"昆明\"\"拉萨\"\"三亚\"。不提供则查本地。
datetime（STRING，可选）：日期时间 YYYY-MM-DDTHH:MM:SS。不提供则查今天。""" 
    },

    # ========================================
    # 日程管理
    # ========================================
    "create_calendar_event": {
        "system": "你是 function call 训练数据生成助手。要求创建日历事件。表达多样化、覆盖不同场景和角度。",
        "param_notes": """title（STRING，必选）：事件标题，覆盖工作、生活、学习、医疗、社交等场景。
start_date（STRING，必选）：开始时间 YYYY-MM-DDTHH:MM:SS。
end_date（STRING，必选）：结束时间 YYYY-MM-DDTHH:MM:SS。时长多样化（30分钟到全天）。""" 
    },

    "search_calendar_events": {
        "system": "你是 function call 训练数据生成助手。想查询日历中的事件。表达多样化、覆盖不同场景和角度。",
        "param_notes": """query（STRING，可选）：搜索关键词，覆盖工作、生活、医疗等主题。
start_date（STRING，可选）：查询起始日 YYYY-MM-DD。
end_date（STRING，可选）：查询结束日 YYYY-MM-DD。""" 
    },

    # ========================================
    # 备忘录
    # ========================================
    "create_note": {
        "system": "你是 function call 训练数据生成助手。要求记一条笔记。表达多样化、覆盖不同场景和角度。",
        "param_notes": """title（STRING，必选）：笔记标题，覆盖生活、工作、学习、灵感等场景。
content（STRING，必选）：笔记正文，内容和标题匹配。"""
    },

}

# 含时间参数的工具，需要 system prompt 中包含日期时间
TIME_TOOLS = {"set_alarm", "get_weather", "create_calendar_event", "search_calendar_events"}
