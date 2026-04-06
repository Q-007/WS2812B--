import network
import socket
import machine
import neopixel
import time
import ujson

# 配置参数
WIFI_SSID = "ESP32_LED_Matrix"
WIFI_PASSWORD = "12345678"  # 至少8个字符
LED_PIN = 4  # WS2812B数据引脚
LED_COUNT = 64  # 8x8 = 64个灯珠
MATRIX_WIDTH = 8
MATRIX_HEIGHT = 8

# 初始化WS2812B
np = neopixel.NeoPixel(machine.Pin(LED_PIN), LED_COUNT)

# 全局变量存储LED状态
led_colors = [(0, 0, 0)] * LED_COUNT

def setup_ap():
    """配置WiFi热点模式"""
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=WIFI_SSID, password=WIFI_PASSWORD)
    
    while not ap.active():
        time.sleep(0.1)
    
    print('WiFi热点已启动')
    print('SSID:', WIFI_SSID)
    print('密码:', WIFI_PASSWORD)
    print('IP地址:', ap.ifconfig()[0])
    return ap

def set_pixel(index, r, g, b):
    """设置单个灯珠颜色"""
    if 0 <= index < LED_COUNT:
        np[index] = (r, g, b)
        led_colors[index] = (r, g, b)

def set_all_pixels(r, g, b):
    """设置所有灯珠颜色"""
    for i in range(LED_COUNT):
        np[i] = (r, g, b)
        led_colors[i] = (r, g, b)

def clear_all():
    """清除所有灯珠"""
    set_all_pixels(0, 0, 0)
    np.write()

def show_rainbow():
    """显示彩虹效果"""
    colors = [
        (255, 0, 0),    # 红
        (255, 127, 0),  # 橙
        (255, 255, 0),  # 黄
        (0, 255, 0),    # 绿
        (0, 0, 255),    # 蓝
        (75, 0, 130),   # 靛
        (148, 0, 211),  # 紫
        (255, 0, 0),    # 红
    ]
    for i in range(LED_COUNT):
        row = i // MATRIX_WIDTH
        col = i % MATRIX_WIDTH
        color_index = col % len(colors)
        np[i] = colors[color_index]
    np.write()

def get_html_page():
    """生成网页HTML"""
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESP32 LED矩阵控制器</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 20px;
        }
        .controls {
            margin-bottom: 20px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 10px;
        }
        .control-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }
        input[type="color"] {
            width: 100%;
            height: 50px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button {
            width: 100%;
            padding: 12px;
            margin: 5px 0;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5568d3;
        }
        .btn-success {
            background: #48bb78;
            color: white;
        }
        .btn-success:hover {
            background: #38a169;
        }
        .btn-danger {
            background: #f56565;
            color: white;
        }
        .btn-danger:hover {
            background: #e53e3e;
        }
        .led-matrix {
            display: grid;
            grid-template-columns: repeat(8, 1fr);
            gap: 5px;
            margin: 20px 0;
            background: #2d3748;
            padding: 15px;
            border-radius: 10px;
        }
        .led {
            aspect-ratio: 1;
            border-radius: 50%;
            background: #000;
            cursor: pointer;
            transition: all 0.2s;
            border: 2px solid #4a5568;
        }
        .led:hover {
            transform: scale(1.1);
            border-color: #fff;
        }
        .info {
            text-align: center;
            color: #666;
            margin-top: 10px;
            font-size: 14px;
        }
        .preset-colors {
            display: grid;
            grid-template-columns: repeat(8, 1fr);
            gap: 5px;
            margin: 10px 0;
        }
        .preset-color {
            aspect-ratio: 1;
            border-radius: 5px;
            cursor: pointer;
            border: 2px solid #ddd;
            transition: all 0.2s;
        }
        .preset-color:hover {
            transform: scale(1.1);
            border-color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 ESP32 LED矩阵控制器</h1>
        
        <div class="controls">
            <div class="control-group">
                <label>选择颜色：</label>
                <input type="color" id="colorPicker" value="#ff0000">
            </div>
            
            <div class="control-group">
                <label>预设颜色：</label>
                <div class="preset-colors">
                    <div class="preset-color" style="background: #ff0000" onclick="selectPreset('#ff0000')"></div>
                    <div class="preset-color" style="background: #00ff00" onclick="selectPreset('#00ff00')"></div>
                    <div class="preset-color" style="background: #0000ff" onclick="selectPreset('#0000ff')"></div>
                    <div class="preset-color" style="background: #ffff00" onclick="selectPreset('#ffff00')"></div>
                    <div class="preset-color" style="background: #ff00ff" onclick="selectPreset('#ff00ff')"></div>
                    <div class="preset-color" style="background: #00ffff" onclick="selectPreset('#00ffff')"></div>
                    <div class="preset-color" style="background: #ffffff" onclick="selectPreset('#ffffff')"></div>
                    <div class="preset-color" style="background: #ff8800" onclick="selectPreset('#ff8800')"></div>
                </div>
            </div>
            
            <button class="btn-primary" onclick="setAllLeds()">设置全部灯珠</button>
            <button class="btn-success" onclick="showRainbow()">彩虹效果</button>
            <button class="btn-danger" onclick="clearAll()">清除所有</button>
        </div>
        
        <div class="led-matrix" id="ledMatrix"></div>
        
        <div class="info">
            点击单个灯珠可单独设置颜色 | 共64个灯珠(8x8)
        </div>
    </div>

    <script>
        let selectedColor = '#ff0000';
        
        // 创建LED矩阵
        function createMatrix() {
            const matrix = document.getElementById('ledMatrix');
            for (let i = 0; i < 64; i++) {
                const led = document.createElement('div');
                led.className = 'led';
                led.id = 'led-' + i;
                led.onclick = () => setLed(i);
                matrix.appendChild(led);
            }
        }
        
        // 选择预设颜色
        function selectPreset(color) {
            selectedColor = color;
            document.getElementById('colorPicker').value = color;
        }
        
        // 颜色选择器改变
        document.addEventListener('DOMContentLoaded', function() {
            createMatrix();
            document.getElementById('colorPicker').addEventListener('input', function(e) {
                selectedColor = e.target.value;
            });
        });
        
        // 十六进制转RGB
        function hexToRgb(hex) {
            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);
            return {r, g, b};
        }
        
        // 设置单个LED
        function setLed(index) {
            const color = hexToRgb(selectedColor);
            fetch('/set_pixel', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    index: index,
                    r: color.r,
                    g: color.g,
                    b: color.b
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    document.getElementById('led-' + index).style.background = selectedColor;
                }
            });
        }
        
        // 设置所有LED
        function setAllLeds() {
            const color = hexToRgb(selectedColor);
            fetch('/set_all', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    r: color.r,
                    g: color.g,
                    b: color.b
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    for (let i = 0; i < 64; i++) {
                        document.getElementById('led-' + i).style.background = selectedColor;
                    }
                }
            });
        }
        
        // 显示彩虹效果
        function showRainbow() {
            fetch('/rainbow', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    const colors = ['#ff0000', '#ff7f00', '#ffff00', '#00ff00', '#0000ff', '#4b0082', '#9400d3', '#ff0000'];
                    for (let i = 0; i < 64; i++) {
                        const col = i % 8;
                        document.getElementById('led-' + i).style.background = colors[col];
                    }
                }
            });
        }
        
        // 清除所有
        function clearAll() {
            fetch('/clear', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    for (let i = 0; i < 64; i++) {
                        document.getElementById('led-' + i).style.background = '#000000';
                    }
                }
            });
        }
    </script>
</body>
</html>
"""
    return html

def parse_request(request):
    """解析HTTP请求"""
    try:
        lines = request.split(b'\r\n')
        method_line = lines[0].decode()
        parts = method_line.split(' ')
        method = parts[0]
        path = parts[1]
        
        body = None
        if b'\r\n\r\n' in request:
            body_start = request.index(b'\r\n\r\n') + 4
            body = request[body_start:].decode()
        
        return method, path, body
    except:
        return None, None, None

def handle_client(client_socket):
    """处理客户端请求"""
    try:
        request = client_socket.recv(2048)
        method, path, body = parse_request(request)
        
        if method is None:
            client_socket.close()
            return
        
        print(f'请求: {method} {path}')
        
        # 路由处理
        if path == '/' or path.startswith('/?'):
            # 返回主页
            response = 'HTTP/1.1 200 OK\r\n'
            response += 'Content-Type: text/html; charset=utf-8\r\n'
            response += 'Connection: close\r\n\r\n'
            response += get_html_page()
            client_socket.send(response.encode())
            
        elif path == '/set_pixel' and method == 'POST':
            # 设置单个灯珠
            data = ujson.loads(body)
            set_pixel(data['index'], data['r'], data['g'], data['b'])
            np.write()
            response = 'HTTP/1.1 200 OK\r\n'
            response += 'Content-Type: application/json\r\n'
            response += 'Connection: close\r\n\r\n'
            response += '{"status":"ok"}'
            client_socket.send(response.encode())
            
        elif path == '/set_all' and method == 'POST':
            # 设置所有灯珠
            data = ujson.loads(body)
            set_all_pixels(data['r'], data['g'], data['b'])
            np.write()
            response = 'HTTP/1.1 200 OK\r\n'
            response += 'Content-Type: application/json\r\n'
            response += 'Connection: close\r\n\r\n'
            response += '{"status":"ok"}'
            client_socket.send(response.encode())
            
        elif path == '/rainbow' and method == 'POST':
            # 显示彩虹效果
            show_rainbow()
            response = 'HTTP/1.1 200 OK\r\n'
            response += 'Content-Type: application/json\r\n'
            response += 'Connection: close\r\n\r\n'
            response += '{"status":"ok"}'
            client_socket.send(response.encode())
            
        elif path == '/clear' and method == 'POST':
            # 清除所有
            clear_all()
            response = 'HTTP/1.1 200 OK\r\n'
            response += 'Content-Type: application/json\r\n'
            response += 'Connection: close\r\n\r\n'
            response += '{"status":"ok"}'
            client_socket.send(response.encode())
            
        else:
            # 404
            response = 'HTTP/1.1 404 Not Found\r\n'
            response += 'Connection: close\r\n\r\n'
            response += '404 Not Found'
            client_socket.send(response.encode())
            
    except Exception as e:
        print('处理请求出错:', e)
    finally:
        client_socket.close()

def start_server():
    """启动Web服务器"""
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(addr)
    server_socket.listen(5)
    
    print('Web服务器已启动，监听端口 80')
    print('请连接WiFi热点后访问: http://' + ap.ifconfig()[0])
    
    while True:
        try:
            client_socket, addr = server_socket.accept()
            print('客户端连接:', addr)
            handle_client(client_socket)
        except Exception as e:
            print('服务器错误:', e)

# 主程序
if __name__ == '__main__':
    print('=================================')
    print('ESP32 WS2812B LED矩阵控制器')
    print('=================================')
    
    # 清除LED
    clear_all()
    print('LED已清除')
    
    # 启动WiFi热点
    ap = setup_ap()
    
    # 启动Web服务器
    start_server()

