TOOLS = [
    # === 应用管理 ===
    {
        "function": {
            "name": "list_application",
            "description": "列出此手机上安装的应用程序。",
            "parameters": {
                "type": "OBJECT",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "function": {
            "name": "open_application",
            "description": "打开指定应用程序。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "application_name": {
                        "type": "STRING",
                        "description": "要打开的应用程序名称。"
                    }
                },
                "required": ["application_name"]
            }
        }
    },

    # === 显示控制 ===
    {
        "function": {
            "name": "set_brightness",
            "description": "调节屏幕亮度。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "level": {
                        "type": "STRING",
                        "description": "目标亮度数值，范围 0 到 100。"
                    },
                    "direction": {
                        "type": "STRING",
                        "description": "调节方向，'high' 为调高，'low' 为调低。"
                    }
                },
                "required": []
            }
        }
    },

    # === 通信 ===
    {
        "function": {
            "name": "send_email",
            "description": "发送电子邮件。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "contact_name": {
                        "type": "STRING",
                        "description": "收件人姓名、邮箱地址或电话号码。"
                    },
                    "subject": {
                        "type": "STRING",
                        "description": "邮件主题。"
                    },
                    "message": {
                        "type": "STRING",
                        "description": "邮件正文内容。"
                    }
                },
                "required": ["contact_name", "subject"]
            }
        }
    },
    {
        "function": {
            "name": "phone_call",
            "description": "拨打指定联系人的电话。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "contact_name": {
                        "type": "STRING",
                        "description": "联系人姓名或电话号码。"
                    }
                },
                "required": ["contact_name"]
            }
        }
    },
    {
        "function": {
            "name": "phone_sms",
            "description": "发送短信。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "contact_name": {
                        "type": "STRING",
                        "description": "收件人姓名或电话号码。"
                    },
                    "message": {
                        "type": "STRING",
                        "description": "短信内容。"
                    }
                },
                "required": ["contact_name"]
            }
        }
    },

    # === 系统信息 ===
    {
        "function": {
            "name": "battery_status",
            "description": "提供设备电池的相关信息。",
            "parameters": {
                "type": "OBJECT",
                "properties": {},
                "required": []
            }
        }
    },

    # === 连接与网络 ===
    {
        "function": {
            "name": "toggle_wifi",
            "description": "开启或关闭Wi-Fi功能。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "enable": {
                        "type": "BOOLEAN",
                        "description": "true 为开启 Wi-Fi，false 为关闭 Wi-Fi。"
                    }
                },
                "required": ["enable"]
            }
        }
    },
    {
        "function": {
            "name": "toggle_bluetooth",
            "description": "开启或关闭蓝牙功能。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "enable": {
                        "type": "BOOLEAN",
                        "description": "true 为开启蓝牙，false 为关闭蓝牙。"
                    }
                },
                "required": ["enable"]
            }
        }
    },
    {
        "function": {
            "name": "toggle_mobile_data",
            "description": "开启或关闭移动数据网络。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "enable": {
                        "type": "BOOLEAN",
                        "description": "true 为开启移动数据，false 为关闭移动数据。"
                    }
                },
                "required": ["enable"]
            }
        }
    },
    {
        "function": {
            "name": "toggle_airplane_mode",
            "description": "开启或关闭飞行模式。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "enable": {
                        "type": "BOOLEAN",
                        "description": "true 为开启飞行模式，false 为关闭飞行模式。"
                    }
                },
                "required": ["enable"]
            }
        }
    },

    # === 媒体 ===
    {
        "function": {
            "name": "play_music",
            "description": "播放音乐或歌曲。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "song_name": {
                        "type": "STRING",
                        "description": "要播放的歌曲名称。"
                    },
                    "artist": {
                        "type": "STRING",
                        "description": "歌手名称。"
                    }
                },
                "required": []
            }
        }
    },
    {
        "function": {
            "name": "pause_music",
            "description": "暂停当前播放的音乐。",
            "parameters": {
                "type": "OBJECT",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "function": {
            "name": "take_picture",
            "description": "使用相机拍照。",
            "parameters": {
                "type": "OBJECT",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "function": {
            "name": "take_screenshot",
            "description": "截取当前屏幕内容。",
            "parameters": {
                "type": "OBJECT",
                "properties": {},
                "required": []
            }
        }
    },

    # === 硬件控制 ===
    {
        "function": {
            "name": "set_flashlight",
            "description": "开启或关闭手电筒。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "enable": {
                        "type": "BOOLEAN",
                        "description": "true 为打开手电筒，false 为关闭手电筒。"
                    }
                },
                "required": ["enable"]
            }
        }
    },

    # === 地图与定位 ===
    {
        "function": {
            "name": "show_map",
            "description": "在地图上显示指定位置。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "destination": {
                        "type": "STRING",
                        "description": "要显示的位置，可以是地址、地点名称或坐标。"
                    }
                },
                "required": ["destination"]
            }
        }
    },
    {
        "function": {
            "name": "get_location",
            "description": "获取当前设备地理位置。",
            "parameters": {
                "type": "OBJECT",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "function": {
            "name": "navigate",
            "description": "启动导航到指定目的地。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "destination": {
                        "type": "STRING",
                        "description": "导航目的地，可以是地址、地点名称或坐标。"
                    }
                },
                "required": ["destination"]
            }
        }
    },

    # === 通讯录 ===
    {
        "function": {
            "name": "create_contact",
            "description": "创建联系人。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "contact_name": {
                        "type": "STRING",
                        "description": "联系人姓名。"
                    },
                    "email": {
                        "type": "STRING",
                        "description": "联系人的电子邮件地址。"
                    },
                    "phone_number": {
                        "type": "STRING",
                        "description": "联系人的电话号码。"
                    }
                },
                "required": ["contact_name"]
            }
        }
    },
    {
        "function": {
            "name": "search_contacts",
            "description": "搜索联系人。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "contact_name": {
                        "type": "STRING",
                        "description": "要搜索的联系人姓名或电话号码。"
                    }
                },
                "required": ["contact_name"]
            }
        }
    },

    # === 提醒与时间 ===
    {
        "function": {
            "name": "set_alarm",
            "description": "设置一个闹钟。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "datetime": {
                        "type": "STRING",
                        "description": "闹钟的日期和时间，格式为 YYYY-MM-DDTHH:MM:SS。"
                    },
                    "label": {
                        "type": "STRING",
                        "description": "闹钟标签/备注。"
                    },
                    "repeat": {
                        "type": "STRING",
                        "description": "重复模式，如 'daily'、'weekly'、'weekdays' 等。"
                    }
                },
                "required": ["datetime"]
            }
        }
    },

    # === 声音控制 ===
    {
        "function": {
            "name": "set_volume",
            "description": "调节设备音量。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "level": {
                        "type": "STRING",
                        "description": "目标音量数值，范围 0 到 100。"
                    },
                    "direction": {
                        "type": "STRING",
                        "description": "调节方向，'high' 为调高，'low' 为调低。"
                    }
                },
                "required": []
            }
        }
    },
    {
        "function": {
            "name": "set_mute",
            "description": "设置设备静音状态。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "enable": {
                        "type": "BOOLEAN",
                        "description": "true 为静音，false 为取消静音。"
                    }
                },
                "required": ["enable"]
            }
        }
    },

    # === 浏览与搜索 ===
    {
        "function": {
            "name": "search_web",
            "description": "使用搜索引擎进行搜索。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "query": {
                        "type": "STRING",
                        "description": "搜索关键词。"
                    }
                },
                "required": ["query"]
            }
        }
    },

    # === 系统模式 ===
    {
        "function": {
            "name": "toggle_dnd",
            "description": "开启或关闭勿扰模式。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "enable": {
                        "type": "BOOLEAN",
                        "description": "true 为开启勿扰模式，false 为关闭勿扰模式。"
                    }
                },
                "required": ["enable"]
            }
        }
    },
    {
        "function": {
            "name": "toggle_power_saving_mode",
            "description": "开启或关闭省电模式。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "enable": {
                        "type": "BOOLEAN",
                        "description": "true 为开启省电模式，false 为关闭省电模式。"
                    }
                },
                "required": ["enable"]
            }
        }
    },

    # === 天气服务 ===
    {
        "function": {
            "name": "get_weather",
            "description": "获取天气信息。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "city": {
                        "type": "STRING",
                        "description": "要查询天气的城市名称。不提供则查询当前位置天气。"
                    },
                    "datetime": {
                        "type": "STRING",
                        "description": "要查询天气的日期和时间，格式为 YYYY-MM-DDTHH:MM:SS。不提供则查询当前天气。"
                    }
                },
                "required": []
            }
        }
    },

    # === 日程管理 ===
    {
        "function": {
            "name": "create_calendar_event",
            "description": "创建一个新的日历事件。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "title": {
                        "type": "STRING",
                        "description": "事件标题。"
                    },
                    "start_date": {
                        "type": "STRING",
                        "description": "事件开始日期和时间，格式为 YYYY-MM-DDTHH:MM:SS。"
                    },
                    "end_date": {
                        "type": "STRING",
                        "description": "如果没有提到结束时间，则结束时间为开始时间后一小时，格式为 YYYY-MM-DDTHH:MM:SS。"
                    }
                },
                "required": ["title", "start_date", "end_date"]
            }
        }
    },
    {
        "function": {
            "name": "search_calendar_events",
            "description": "查询日历中的事件。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "query": {
                        "type": "STRING",
                        "description": "搜索关键词，按事件标题匹配。不提供则返回最近的事件列表。"
                    },
                    "start_date": {
                        "type": "STRING",
                        "description": "查询起始日期，格式为 YYYY-MM-DDTHH:MM:SS。"
                    },
                    "end_date": {
                        "type": "STRING",
                        "description": "查询结束日期，格式为 YYYY-MM-DDTHH:MM:SS。"
                    }
                },
                "required": []
            }
        }
    },

    # === 备忘录 ===
    {
        "function": {
            "name": "create_note",
            "description": "创建一条备忘录或笔记。",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "title": {
                        "type": "STRING",
                        "description": "备忘录标题。"
                    },
                    "content": {
                        "type": "STRING",
                        "description": "备忘录内容。"
                    }
                },
                "required": ["title", "content"]
            }
        }
    },
]


def get_tool_by_name(name: str) -> dict | None:
    """按名称获取单个工具定义。"""
    for tool in TOOLS:
        if tool["function"]["name"] == name:
            return tool
    return None


def get_tool_names() -> list[str]:
    """获取所有工具名称列表。"""
    return [t["function"]["name"] for t in TOOLS]
