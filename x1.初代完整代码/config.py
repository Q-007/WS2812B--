# 配置文件 - 可以在这里修改参数，然后在main.py中导入使用

# WiFi热点配置
WIFI_CONFIG = {
    'ssid': 'ESP32_LED_Matrix',      # WiFi热点名称
    'password': '12345678',           # WiFi密码（至少8位）
}

# LED配置
LED_CONFIG = {
    'pin': 15,                        # WS2812B数据引脚
    'count': 64,                      # LED总数（8x8=64）
    'width': 8,                       # 矩阵宽度
    'height': 8,                      # 矩阵高度
    'brightness': 255,                # 亮度 (0-255)
}

# 服务器配置
SERVER_CONFIG = {
    'port': 80,                       # Web服务器端口
    'timeout': 10,                    # 连接超时时间（秒）
}

# 预设效果
PRESET_EFFECTS = {
    'rainbow_colors': [
        (255, 0, 0),      # 红
        (255, 127, 0),    # 橙
        (255, 255, 0),    # 黄
        (0, 255, 0),      # 绿
        (0, 0, 255),      # 蓝
        (75, 0, 130),     # 靛
        (148, 0, 211),    # 紫
    ],
}

