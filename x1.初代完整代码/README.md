# ESP32 WS2812B 8x8 LED矩阵控制器

基于MicroPython的ESP32 WS2812B LED矩阵控制系统，支持WiFi热点和网页控制。

## 硬件要求

- ESP32开发板
- WS2812B LED灯带（64个灯珠，8x8排列）
- 5V电源（推荐至少2A）

## 接线说明

```
ESP32          WS2812B
GPIO 15  ----> DIN (数据输入)
GND      ----> GND
5V       ----> VCC (外部电源)
```

**注意：** 
- WS2812B需要5V供电，大电流时请使用外部电源
- 数据线默认连接GPIO15，可在代码中修改
- 建议在数据线上串联一个470Ω电阻保护

## 安装步骤

### 1. 安装MicroPython固件

1. 下载MicroPython固件（ESP32）：https://micropython.org/download/esp32/
2. 使用esptool.py刷入固件：

```bash
# 擦除Flash
esptool.py --chip esp32 --port COM3 erase_flash

# 刷入固件
esptool.py --chip esp32 --port COM3 --baud 460800 write_flash -z 0x1000 esp32-xxxxxx.bin
```

### 2. 上传代码

使用Thonny IDE或ampy工具上传文件到ESP32：

#### 使用Thonny IDE
1. 打开Thonny IDE
2. 选择"工具" -> "选项" -> "解释器"
3. 选择"MicroPython (ESP32)"和正确的COM口
4. 在文件浏览器中右键文件，选择"上传到/"

#### 使用ampy
```bash
# 安装ampy
pip install adafruit-ampy

# 上传文件
ampy --port COM3 put boot.py
ampy --port COM3 put main.py
```

### 3. 重启ESP32

重启后程序自动运行。

## 使用说明

### 1. 连接WiFi热点

- SSID: `ESP32_LED_Matrix`
- 密码: `12345678`

### 2. 访问控制界面

在浏览器中访问：`http://192.168.4.1`

### 3. 控制LED

- **选择颜色**：使用颜色选择器或预设颜色
- **点击单个灯珠**：单独设置某个灯珠的颜色
- **设置全部灯珠**：将所有灯珠设置为选定颜色
- **彩虹效果**：显示预设的彩虹渐变效果
- **清除所有**：关闭所有灯珠

## 配置参数

在 `main.py` 中可以修改以下参数：

```python
WIFI_SSID = "ESP32_LED_Matrix"    # WiFi热点名称
WIFI_PASSWORD = "12345678"        # WiFi密码（至少8位）
LED_PIN = 15                      # WS2812B数据引脚
LED_COUNT = 64                    # LED总数
MATRIX_WIDTH = 8                  # 矩阵宽度
MATRIX_HEIGHT = 8                 # 矩阵高度
```

## 功能特性

- ✅ WiFi热点模式（AP模式）
- ✅ Web界面控制
- ✅ 单个LED颜色控制
- ✅ 批量设置所有LED
- ✅ 预设颜色快速选择
- ✅ 彩虹渐变效果
- ✅ 响应式网页设计
- ✅ 美观的用户界面

## 扩展功能

你可以基于此代码添加更多效果：

1. **流水灯效果**
2. **呼吸灯效果**
3. **跑马灯效果**
4. **文字滚动显示**
5. **图案绘制**
6. **动画播放**

## 故障排除

### LED不亮
1. 检查接线是否正确
2. 确认电源供电充足（5V，至少2A）
3. 检查GPIO引脚配置是否正确

### 无法连接WiFi
1. 确认SSID和密码输入正确
2. 检查ESP32串口输出的IP地址
3. 尝试重启ESP32

### 网页无法访问
1. 确保已连接到ESP32的WiFi热点
2. 访问默认IP：192.168.4.1
3. 检查防火墙设置

## 技术栈

- **MicroPython v1.25.0**
- **ESP32**
- **WS2812B (NeoPixel)**
- **HTML5/CSS3/JavaScript**

## 许可证

MIT License

## 作者

ESP32 LED矩阵控制器项目

---

**享受你的LED矩阵编程之旅！** 🎨✨

