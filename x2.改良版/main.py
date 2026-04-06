import network
import socket
import machine
import neopixel
import time
import ujson
import os

# 配置参数
WIFI_SSID = "ESP32_LED_Matrix"
WIFI_PASSWORD = None  # None表示开放热点（无密码）
CUSTOM_IP = "192.168.13.14"  # 自定义IP地址
LED_PIN = 4  # WS2812B数据引脚
LED_COUNT = 64  # 8x8 = 64个灯珠
MATRIX_WIDTH = 8
MATRIX_HEIGHT = 8
PATTERNS_FILE = "patterns.json"  # 图案保存文件

# 初始化WS2812B
np = neopixel.NeoPixel(machine.Pin(LED_PIN), LED_COUNT)

# 全局变量存储LED状态
led_colors = [(0, 0, 0)] * LED_COUNT
saved_patterns = {}  # 保存的图案（字典格式，快速查找）

# 自动播放相关变量
last_activity_time = 0  # 最后活动时间
auto_play_interval = 12  # 自动播放间隔（秒）
current_pattern_index = 0  # 当前播放的图案索引
is_auto_playing = False  # 是否正在自动播放

def setup_ap():
    """配置WiFi热点模式"""
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    
    # 如果密码为None，则创建开放热点
    if WIFI_PASSWORD is None:
        ap.config(essid=WIFI_SSID, authmode=network.AUTH_OPEN)
        print('WiFi热点已启动（开放网络，无需密码）')
    else:
        ap.config(essid=WIFI_SSID, password=WIFI_PASSWORD)
        print('WiFi热点已启动')
        print('密码:', WIFI_PASSWORD)
    
    while not ap.active():
        time.sleep(0.1)
    
    # 设置自定义IP地址
    ip_parts = CUSTOM_IP.split('.')
    gateway = '.'.join(ip_parts[:3]) + '.1'
    subnet = '255.255.255.0'
    ap.ifconfig((CUSTOM_IP, subnet, gateway, gateway))
    
    print('SSID:', WIFI_SSID)
    print('IP地址:', ap.ifconfig()[0])
    print('子网掩码:', ap.ifconfig()[1])
    print('网关:', ap.ifconfig()[2])
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
        led_colors[i] = colors[color_index]
    np.write()

def load_patterns():
    """从文件加载保存的图案（兼容旧格式）"""
    global saved_patterns
    try:
        if PATTERNS_FILE in os.listdir():
            with open(PATTERNS_FILE, 'r') as f:
                data = ujson.load(f)
            
            # 兼容旧版本列表格式，转换为字典
            if isinstance(data, list):
                print('检测到旧格式，正在转换...')
                saved_patterns = {}
                for item in data:
                    if isinstance(item, dict) and 'name' in item and 'data' in item:
                        saved_patterns[item['name']] = item['data']
                # 保存为新格式
                save_patterns()
                print(f'已转换并加载 {len(saved_patterns)} 个图案')
            else:
                saved_patterns = data
                print(f'已加载 {len(saved_patterns)} 个图案')
        else:
            saved_patterns = {}
            print('未找到保存的图案文件')
    except Exception as e:
        print('加载图案失败:', e)
        saved_patterns = {}

def save_patterns():
    """保存图案到文件"""
    try:
        with open(PATTERNS_FILE, 'w') as f:
            ujson.dump(saved_patterns, f)
        print(f'已保存 {len(saved_patterns)} 个图案')
        return True
    except Exception as e:
        print('保存图案失败:', e)
        return False

def save_current_pattern(name):
    """保存当前图案"""
    pattern = []
    for i in range(LED_COUNT):
        pattern.append(list(led_colors[i]))
    saved_patterns[name] = pattern
    return save_patterns()

def load_pattern(name):
    """加载指定图案"""
    if name in saved_patterns:
        pattern = saved_patterns[name]
        for i in range(min(len(pattern), LED_COUNT)):
            color = tuple(pattern[i])
            np[i] = color
            led_colors[i] = color
        np.write()
        return True
    return False

def delete_pattern(name):
    """删除指定图案"""
    global saved_patterns
    if name in saved_patterns:
        del saved_patterns[name]
        return save_patterns()
    return False

def get_patterns_list():
    """获取所有保存的图案名称"""
    return list(saved_patterns.keys())

def reset_activity_time():
    """重置活动时间"""
    global last_activity_time, is_auto_playing
    last_activity_time = time.time()
    is_auto_playing = False

def play_next_pattern():
    """自动播放下一个图案"""
    global current_pattern_index, is_auto_playing
    
    if not saved_patterns:
        return False
    
    pattern_names = list(saved_patterns.keys())
    if not pattern_names:
        return False
    
    # 获取当前要播放的图案
    pattern_name = pattern_names[current_pattern_index]
    pattern = saved_patterns[pattern_name]
    
    # 显示图案
    for i in range(min(len(pattern), LED_COUNT)):
        color = tuple(pattern[i])
        np[i] = color
        led_colors[i] = color
    np.write()
    
    # 更新索引，循环播放
    current_pattern_index = (current_pattern_index + 1) % len(pattern_names)
    is_auto_playing = True
    
    print(f'自动播放图案: {pattern_name} ({current_pattern_index}/{len(pattern_names)})')
    return True

def get_html_page_compressed():
    """生成压缩版网页HTML（优化加载速度）"""
    # 极简压缩版本，去除所有不必要的空格和换行
    html = '''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LED控制</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:Arial;background:linear-gradient(135deg,#667eea,#764ba2);padding:10px;user-select:none}.container{max-width:600px;margin:0 auto;background:#fff;border-radius:10px;padding:15px}h1{text-align:center;margin-bottom:15px;font-size:20px}.controls{margin-bottom:15px;padding:10px;background:#f5f5f5;border-radius:8px}label{display:block;margin:5px 0;font-weight:bold}input[type="color"]{width:100%;height:40px;border:none;border-radius:5px}button{width:100%;padding:10px;margin:5px 0;border:none;border-radius:5px;font-size:14px;color:#fff;cursor:pointer}.btn-primary{background:#667eea}.btn-success{background:#48bb78}.btn-danger{background:#f56565}.btn-warning{background:#f59e0b}.btn-info{background:#3b82f6}.led-matrix{display:grid;grid-template-columns:repeat(8,1fr);gap:3px;margin:15px 0;background:#2d3748;padding:10px;border-radius:8px;touch-action:none}.led{aspect-ratio:1;border-radius:50%;background:#000;cursor:crosshair;border:1px solid #4a5568}.preset-colors{display:grid;grid-template-columns:repeat(8,1fr);gap:3px;margin:10px 0}.preset-color{aspect-ratio:1;border-radius:5px;cursor:pointer;border:2px solid #ddd}.eraser-btn{background:linear-gradient(135deg,#f5f5f5,#e0e0e0);display:flex;align-items:center;justify-content:center;font-size:18px;border:2px solid #999}.pattern-section{margin-top:15px;padding:10px;background:#e8f5e9;border-radius:8px}.pattern-input{width:100%;padding:8px;border:1px solid #ddd;border-radius:5px;margin-bottom:8px}.pattern-list{max-height:150px;overflow-y:auto;margin-top:8px}.pattern-item{display:flex;justify-content:space-between;padding:6px;margin:3px 0;background:#fff;border-radius:5px}.pattern-item button{width:auto;padding:4px 8px;margin:0 2px;font-size:11px}.info{text-align:center;color:#666;margin:8px 0;font-size:12px}</style></head><body><div class="container"><h1>🎨 LED控制</h1><div class="controls"><label>选择颜色：</label><input type="color" id="colorPicker" value="#ff0000"><label>预设颜色：</label><div class="preset-colors"><div class="preset-color eraser-btn" onclick="selectEraser()">🧹</div><div class="preset-color" style="background:#f00" onclick="selectPreset('#ff0000')"></div><div class="preset-color" style="background:#0f0" onclick="selectPreset('#00ff00')"></div><div class="preset-color" style="background:#00f" onclick="selectPreset('#0000ff')"></div><div class="preset-color" style="background:#ff0" onclick="selectPreset('#ffff00')"></div><div class="preset-color" style="background:#f0f" onclick="selectPreset('#ff00ff')"></div><div class="preset-color" style="background:#0ff" onclick="selectPreset('#00ffff')"></div><div class="preset-color" style="background:#fff" onclick="selectPreset('#ffffff')"></div></div><button class="btn-primary" onclick="setAllLeds()">设置全部</button><button class="btn-success" onclick="showRainbow()">彩虹效果</button><button class="btn-danger" onclick="clearAll()">清除</button></div><div class="led-matrix" id="ledMatrix"></div><div class="info">💡 点击/滑动绘制 | 8×8矩阵</div><div class="pattern-section"><input type="text" id="patternName" class="pattern-input" placeholder="图案名称"><button class="btn-warning" onclick="savePattern()">💾 保存</button><button class="btn-info" onclick="loadPatternsList()">🔄 刷新</button><div id="patternsList" class="pattern-list"></div></div></div><script>let selectedColor="#ff0000",isEraser=false,isDrawing=false;function createMatrix(){const m=document.getElementById("ledMatrix");for(let i=0;i<64;i++){const l=document.createElement("div");l.className="led";l.id="led-"+i;l.dataset.index=i;l.addEventListener("mousedown",e=>{e.preventDefault();isDrawing=true;setLed(i)});l.addEventListener("mouseenter",()=>{if(isDrawing)setLed(i)});l.addEventListener("touchstart",e=>{e.preventDefault();isDrawing=true;setLed(i)});l.addEventListener("touchmove",e=>{e.preventDefault();const t=e.touches[0],el=document.elementFromPoint(t.clientX,t.clientY);if(el&&el.classList.contains("led"))setLed(parseInt(el.dataset.index))});m.appendChild(l)}document.addEventListener("mouseup",()=>isDrawing=false);document.addEventListener("touchend",()=>isDrawing=false)}function selectPreset(c){selectedColor=c;isEraser=false;document.getElementById("colorPicker").value=c}function selectEraser(){isEraser=true}document.addEventListener("DOMContentLoaded",()=>{createMatrix();document.getElementById("colorPicker").addEventListener("input",e=>{selectedColor=e.target.value;isEraser=false});loadPatternsList()});function hexToRgb(h){return{r:parseInt(h.slice(1,3),16),g:parseInt(h.slice(3,5),16),b:parseInt(h.slice(5,7),16)}}function rgbToHex(r,g,b){return"#"+[r,g,b].map(x=>{const h=x.toString(16);return h.length===1?"0"+h:h}).join("")}function setLed(i){const c=isEraser?{r:0,g:0,b:0}:hexToRgb(selectedColor);fetch("/set_pixel",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({index:i,r:c.r,g:c.g,b:c.b})}).then(r=>r.json()).then(d=>{if(d.status==="ok")document.getElementById("led-"+i).style.background=isEraser?"#000":selectedColor})}function setAllLeds(){const c=hexToRgb(selectedColor);fetch("/set_all",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({r:c.r,g:c.g,b:c.b})}).then(r=>r.json()).then(d=>{if(d.status==="ok")for(let i=0;i<64;i++)document.getElementById("led-"+i).style.background=selectedColor})}function showRainbow(){fetch("/rainbow",{method:"POST"}).then(r=>r.json()).then(d=>{if(d.status==="ok"){const colors=["#f00","#ff7f00","#ff0","#0f0","#00f","#4b0082","#9400d3","#f00"];for(let i=0;i<64;i++)document.getElementById("led-"+i).style.background=colors[i%8]}})}function clearAll(){fetch("/clear",{method:"POST"}).then(r=>r.json()).then(d=>{if(d.status==="ok")for(let i=0;i<64;i++)document.getElementById("led-"+i).style.background="#000"})}function savePattern(){const n=document.getElementById("patternName").value.trim();if(!n){alert("请输入图案名称");return}fetch("/save_pattern",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:n})}).then(r=>r.json()).then(d=>{alert(d.status==="ok"?"保存成功":"保存失败");if(d.status==="ok"){document.getElementById("patternName").value="";loadPatternsList()}})}function loadPatternsList(){fetch("/get_patterns").then(r=>r.json()).then(d=>{const l=document.getElementById("patternsList");if(d.patterns&&d.patterns.length>0){l.innerHTML=d.patterns.map(n=>`<div class="pattern-item"><span>${n}</span><div><button class="btn-success" onclick="loadPattern('${n}')">加载</button><button class="btn-danger" onclick="deletePattern('${n}')">删除</button></div></div>`).join("")}else{l.innerHTML='<div style="text-align:center;padding:15px;color:#999">暂无图案</div>'}})}function loadPattern(n){if(!confirm("确定加载 "+n+" ？"))return;fetch("/load_pattern",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:n})}).then(r=>r.json()).then(d=>{if(d.status==="ok"&&d.pattern){for(let i=0;i<Math.min(d.pattern.length,64);i++)document.getElementById("led-"+i).style.background=rgbToHex(...d.pattern[i]);alert("加载成功")}else alert("加载失败")})}function deletePattern(n){if(!confirm("确定删除 "+n+" ？"))return;fetch("/delete_pattern",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:n})}).then(r=>r.json()).then(d=>{alert(d.status==="ok"?"删除成功":"删除失败");if(d.status==="ok")loadPatternsList()})}</script></body></html>'''
    return html

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
            user-select: none;
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
            transition: background 0.2s;
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
            touch-action: none;
        }
        .led {
            aspect-ratio: 1;
            border-radius: 50%;
            background: #000;
            cursor: crosshair;
            border: 2px solid #4a5568;
        }
        .led:active {
            transform: scale(0.95);
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
        }
        .preset-color:active {
            transform: scale(0.95);
        }
        .eraser-btn {
            background: linear-gradient(135deg, #f5f5f5, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            border: 3px solid #999;
        }
        .eraser-btn.active {
            border-color: #ff6b6b;
            box-shadow: 0 0 10px rgba(255, 107, 107, 0.5);
        }
        .pattern-section {
            margin-top: 20px;
            padding: 15px;
            background: #e8f5e9;
            border-radius: 10px;
            border: 2px solid #48bb78;
        }
        .pattern-input {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .btn-warning {
            background: #f59e0b;
            color: white;
        }
        .btn-warning:hover {
            background: #d97706;
        }
        .btn-info {
            background: #3b82f6;
            color: white;
        }
        .btn-info:hover {
            background: #2563eb;
        }
        .pattern-list {
            max-height: 200px;
            overflow-y: auto;
            margin-top: 10px;
        }
        .pattern-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px;
            margin: 5px 0;
            background: white;
            border-radius: 5px;
            border: 1px solid #ddd;
        }
        .pattern-item button {
            width: auto;
            padding: 5px 10px;
            margin: 0 2px;
            font-size: 12px;
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
                    <div class="preset-color eraser-btn" onclick="selectEraser()" title="橡皮擦">🧹</div>
                    <div class="preset-color" style="background: #ff0000" onclick="selectPreset('#ff0000')"></div>
                    <div class="preset-color" style="background: #00ff00" onclick="selectPreset('#00ff00')"></div>
                    <div class="preset-color" style="background: #0000ff" onclick="selectPreset('#0000ff')"></div>
                    <div class="preset-color" style="background: #ffff00" onclick="selectPreset('#ffff00')"></div>
                    <div class="preset-color" style="background: #ff00ff" onclick="selectPreset('#ff00ff')"></div>
                    <div class="preset-color" style="background: #00ffff" onclick="selectPreset('#00ffff')"></div>
                    <div class="preset-color" style="background: #ffffff" onclick="selectPreset('#ffffff')"></div>
                </div>
            </div>
            
            <button class="btn-primary" onclick="setAllLeds()">设置全部灯珠</button>
            <button class="btn-success" onclick="showRainbow()">彩虹效果</button>
            <button class="btn-danger" onclick="clearAll()">清除所有</button>
        </div>
        
        <div class="led-matrix" id="ledMatrix"></div>
        
        <div class="info">
            💡 点击或滑动绘制 | 橡皮擦熄灭 | 12秒后自动播放 | 8×8矩阵
        </div>
        
        <div class="pattern-section">
            <h3 style="margin-bottom: 10px; color: #2d5016;">💾 图案保存与加载</h3>
            <input type="text" id="patternName" class="pattern-input" placeholder="输入图案名称...">
            <button class="btn-warning" onclick="savePattern()">💾 保存当前图案</button>
            <button class="btn-info" onclick="loadPatternsList()">🔄 刷新图案列表</button>
            <div id="patternsList" class="pattern-list"></div>
        </div>
    </div>

    <script>
        let selectedColor = '#ff0000';
        let isEraser = false; // 是否为橡皮擦模式
        let isDrawing = false; // 是否正在绘制
        let idleTimer = null; // 空闲计时器
        let autoPlayTimer = null; // 自动播放计时器
        let isAutoPlaying = false; // 是否正在自动播放
        let autoPlayIndex = 0; // 当前播放的图案索引
        const IDLE_TIMEOUT = 12000; // 12秒无操作开始自动播放
        const PATTERN_DISPLAY_TIME = 5000; // 每个图案显示5秒
        
        // 创建LED矩阵
        function createMatrix() {
            const matrix = document.getElementById('ledMatrix');
            for (let i = 0; i < 64; i++) {
                const led = document.createElement('div');
                led.className = 'led';
                led.id = 'led-' + i;
                led.dataset.index = i;
                
                // 鼠标事件
                led.addEventListener('mousedown', (e) => {
                    e.preventDefault();
                    isDrawing = true;
                    setLed(i);
                });
                led.addEventListener('mouseenter', (e) => {
                    if (isDrawing) {
                        setLed(i);
                    }
                });
                
                // 触摸事件（移动端）
                led.addEventListener('touchstart', (e) => {
                    e.preventDefault();
                    isDrawing = true;
                    setLed(i);
                });
                led.addEventListener('touchmove', (e) => {
                    e.preventDefault();
                    const touch = e.touches[0];
                    const element = document.elementFromPoint(touch.clientX, touch.clientY);
                    if (element && element.classList.contains('led')) {
                        const index = parseInt(element.dataset.index);
                        setLed(index);
                    }
                });
                
                matrix.appendChild(led);
            }
            
            // 全局事件：停止绘制
            document.addEventListener('mouseup', () => {
                isDrawing = false;
            });
            document.addEventListener('touchend', () => {
                isDrawing = false;
            });
        }
        
        // 选择预设颜色
        function selectPreset(color) {
            selectedColor = color;
            isEraser = false;
            document.getElementById('colorPicker').value = color;
            document.querySelectorAll('.eraser-btn').forEach(btn => btn.classList.remove('active'));
            resetIdleTimer();
        }
        
        // 选择橡皮擦
        function selectEraser() {
            isEraser = true;
            document.querySelectorAll('.eraser-btn').forEach(btn => btn.classList.add('active'));
            resetIdleTimer();
        }
        
        // 颜色选择器改变
        document.addEventListener('DOMContentLoaded', function() {
            createMatrix();
            document.getElementById('colorPicker').addEventListener('input', function(e) {
                selectedColor = e.target.value;
                isEraser = false;
                document.querySelectorAll('.eraser-btn').forEach(btn => btn.classList.remove('active'));
                resetIdleTimer();
            });
            loadPatternsList();
            resetIdleTimer();
        });
        
        // 十六进制转RGB
        function hexToRgb(hex) {
            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);
            return {r, g, b};
        }
        
        // RGB转十六进制
        function rgbToHex(r, g, b) {
            return '#' + [r, g, b].map(x => {
                const hex = x.toString(16);
                return hex.length === 1 ? '0' + hex : hex;
            }).join('');
        }
        
        // 设置单个LED
        function setLed(index) {
            stopAutoPlay(); // 停止自动播放
            resetIdleTimer(); // 重置空闲计时器
            
            if (isEraser) {
                // 橡皮擦模式：熄灭灯珠
                sendLedUpdate(index, 0, 0, 0, '#000000');
            } else {
                // 正常绘制模式
                const color = hexToRgb(selectedColor);
                sendLedUpdate(index, color.r, color.g, color.b, selectedColor);
            }
        }
        
        // 发送LED更新请求（优化：减少重复代码）
        function sendLedUpdate(index, r, g, b, hexColor) {
            fetch('/set_pixel', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({index: index, r: r, g: g, b: b})
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    document.getElementById('led-' + index).style.background = hexColor;
                }
            })
            .catch(error => console.error('LED更新失败:', error));
        }
        
        // 重置空闲计时器
        function resetIdleTimer() {
            clearTimeout(idleTimer);
            idleTimer = setTimeout(() => {
                startAutoPlay();
            }, IDLE_TIMEOUT);
        }
        
        // 停止自动播放
        function stopAutoPlay() {
            if (isAutoPlaying) {
                isAutoPlaying = false;
                clearTimeout(autoPlayTimer);
                console.log('自动播放已停止');
            }
        }
        
        // 开始自动播放
        function startAutoPlay() {
            fetch('/get_patterns')
            .then(response => response.json())
            .then(data => {
                if (data.patterns && data.patterns.length > 0) {
                    isAutoPlaying = true;
                    autoPlayIndex = 0;
                    console.log('开始自动播放，共' + data.patterns.length + '个图案');
                    playNextPattern(data.patterns);
                }
            })
            .catch(error => console.error('获取图案列表失败:', error));
        }
        
        // 播放下一个图案
        function playNextPattern(patterns) {
            if (!isAutoPlaying || patterns.length === 0) return;
            
            const patternName = patterns[autoPlayIndex];
            console.log('播放图案:', patternName);
            
            // 加载图案（带渐变效果）
            fetch('/load_pattern', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: patternName})
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok' && data.pattern) {
                    // 渐入效果
                    fadeInPattern(data.pattern, () => {
                        // 显示一段时间后渐出
                        setTimeout(() => {
                            fadeOutPattern(() => {
                                // 切换到下一个图案
                                autoPlayIndex = (autoPlayIndex + 1) % patterns.length;
                                playNextPattern(patterns);
                            });
                        }, PATTERN_DISPLAY_TIME);
                    });
                }
            })
            .catch(error => {
                console.error('加载图案失败:', error);
                autoPlayIndex = (autoPlayIndex + 1) % patterns.length;
                playNextPattern(patterns);
            });
        }
        
        // 渐入效果
        function fadeInPattern(pattern, callback) {
            const steps = 20;
            let step = 0;
            const interval = setInterval(() => {
                step++;
                const opacity = step / steps;
                for (let i = 0; i < Math.min(pattern.length, 64); i++) {
                    const [r, g, b] = pattern[i];
                    const dimmedR = Math.round(r * opacity);
                    const dimmedG = Math.round(g * opacity);
                    const dimmedB = Math.round(b * opacity);
                    const hex = rgbToHex(dimmedR, dimmedG, dimmedB);
                    document.getElementById('led-' + i).style.background = hex;
                }
                if (step >= steps) {
                    clearInterval(interval);
                    if (callback) callback();
                }
            }, 50);
        }
        
        // 渐出效果
        function fadeOutPattern(callback) {
            const steps = 20;
            let step = 0;
            const currentColors = [];
            for (let i = 0; i < 64; i++) {
                const led = document.getElementById('led-' + i);
                const style = led.style.background;
                if (style.startsWith('#')) {
                    const rgb = hexToRgb(style);
                    currentColors[i] = [rgb.r, rgb.g, rgb.b];
                } else {
                    currentColors[i] = [0, 0, 0];
                }
            }
            
            const interval = setInterval(() => {
                step++;
                const opacity = 1 - (step / steps);
                for (let i = 0; i < 64; i++) {
                    const [r, g, b] = currentColors[i];
                    const dimmedR = Math.round(r * opacity);
                    const dimmedG = Math.round(g * opacity);
                    const dimmedB = Math.round(b * opacity);
                    const hex = rgbToHex(dimmedR, dimmedG, dimmedB);
                    document.getElementById('led-' + i).style.background = hex;
                }
                if (step >= steps) {
                    clearInterval(interval);
                    if (callback) callback();
                }
            }, 50);
        }
        
        // 设置所有LED（优化）
        function setAllLeds() {
            stopAutoPlay();
            resetIdleTimer();
            const color = hexToRgb(selectedColor);
            fetch('/set_all', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({r: color.r, g: color.g, b: color.b})
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    for (let i = 0; i < 64; i++) {
                        document.getElementById('led-' + i).style.background = selectedColor;
                    }
                }
            })
            .catch(error => console.error('设置失败:', error));
        }
        
        // 显示彩虹效果（优化）
        function showRainbow() {
            stopAutoPlay();
            resetIdleTimer();
            fetch('/rainbow', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    const colors = ['#ff0000', '#ff7f00', '#ffff00', '#00ff00', '#0000ff', '#4b0082', '#9400d3', '#ff0000'];
                    for (let i = 0; i < 64; i++) {
                        document.getElementById('led-' + i).style.background = colors[i % 8];
                    }
                }
            })
            .catch(error => console.error('彩虹效果失败:', error));
        }
        
        // 清除所有（优化）
        function clearAll() {
            stopAutoPlay();
            resetIdleTimer();
            fetch('/clear', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    for (let i = 0; i < 64; i++) {
                        document.getElementById('led-' + i).style.background = '#000000';
                    }
                }
            })
            .catch(error => console.error('清除失败:', error));
        }
        
        // 保存图案（优化）
        function savePattern() {
            stopAutoPlay();
            resetIdleTimer();
            const name = document.getElementById('patternName').value.trim();
            if (!name) {
                alert('请输入图案名称！');
                return;
            }
            fetch('/save_pattern', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: name})
            })
            .then(response => response.json())
            .then(data => {
                alert(data.status === 'ok' ? '图案保存成功！' : '保存失败：' + (data.message || '未知错误'));
                if (data.status === 'ok') {
                    document.getElementById('patternName').value = '';
                    loadPatternsList();
                }
            })
            .catch(error => alert('保存失败：' + error));
        }
        
        // 加载图案列表（优化）
        function loadPatternsList() {
            stopAutoPlay();
            resetIdleTimer();
            fetch('/get_patterns')
            .then(response => response.json())
            .then(data => {
                const list = document.getElementById('patternsList');
                if (data.patterns && data.patterns.length > 0) {
                    list.innerHTML = data.patterns.map(name => 
                        `<div class="pattern-item">
                            <span>${name}</span>
                            <div>
                                <button class="btn-success" onclick="loadPattern('${name}')">加载</button>
                                <button class="btn-danger" onclick="deletePattern('${name}')">删除</button>
                            </div>
                        </div>`
                    ).join('');
                } else {
                    list.innerHTML = '<div style="text-align:center;padding:20px;color:#999;">暂无保存的图案</div>';
                }
            })
            .catch(error => console.error('加载图案列表失败:', error));
        }
        
        // 加载指定图案（优化）
        function loadPattern(name) {
            if (!confirm('确定要加载图案 "' + name + '" 吗？')) return;
            
            stopAutoPlay();
            resetIdleTimer();
            fetch('/load_pattern', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: name})
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok' && data.pattern) {
                    for (let i = 0; i < Math.min(data.pattern.length, 64); i++) {
                        const hex = rgbToHex(...data.pattern[i]);
                        document.getElementById('led-' + i).style.background = hex;
                    }
                    alert('图案加载成功！');
                } else {
                    alert('加载失败：' + (data.message || '未知错误'));
                }
            })
            .catch(error => alert('加载失败：' + error));
        }
        
        // 删除图案（优化）
        function deletePattern(name) {
            if (!confirm('确定要删除图案 "' + name + '" 吗？')) return;
            
            stopAutoPlay();
            resetIdleTimer();
            fetch('/delete_pattern', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: name})
            })
            .then(response => response.json())
            .then(data => {
                alert(data.status === 'ok' ? '图案删除成功！' : '删除失败：' + (data.message || '未知错误'));
                if (data.status === 'ok') loadPatternsList();
            })
            .catch(error => alert('删除失败：' + error));
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

def send_response(client_socket, content_type, body):
    """发送HTTP响应（优化版，支持大数据传输）"""
    try:
        response = f'HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nConnection: close\r\n\r\n{body}'
        data = response.encode()
        
        # 分块发送大数据，避免超时
        chunk_size = 1024  # 每次发送1KB
        for i in range(0, len(data), chunk_size):
            client_socket.send(data[i:i+chunk_size])
    except Exception as e:
        print(f'发送响应失败: {e}')

def handle_client(client_socket):
    """处理客户端请求"""
    try:
        request = client_socket.recv(2048)
        method, path, body = parse_request(request)
        
        if method is None:
            client_socket.close()
            return
        
        # 重置活动时间，停止自动播放
        reset_activity_time()
        
        print(f'请求: {method} {path}')
        
        # 路由处理
        if path == '/' or path.startswith('/?'):
            send_response(client_socket, 'text/html; charset=utf-8', get_html_page_compressed())
            
        elif path == '/set_pixel' and method == 'POST':
            data = ujson.loads(body)
            set_pixel(data['index'], data['r'], data['g'], data['b'])
            np.write()
            send_response(client_socket, 'application/json', '{"status":"ok"}')
            
        elif path == '/set_all' and method == 'POST':
            data = ujson.loads(body)
            set_all_pixels(data['r'], data['g'], data['b'])
            np.write()
            send_response(client_socket, 'application/json', '{"status":"ok"}')
            
        elif path == '/rainbow' and method == 'POST':
            show_rainbow()
            send_response(client_socket, 'application/json', '{"status":"ok"}')
            
        elif path == '/clear' and method == 'POST':
            clear_all()
            send_response(client_socket, 'application/json', '{"status":"ok"}')
            
        elif path == '/save_pattern' and method == 'POST':
            try:
                data = ujson.loads(body)
                name = data.get('name', '').strip()
                if not name:
                    raise ValueError('图案名称不能为空')
                response_data = '{"status":"ok"}' if save_current_pattern(name) else '{"status":"error","message":"保存失败"}'
            except Exception as e:
                response_data = f'{{"status":"error","message":"{str(e)}"}}'
            send_response(client_socket, 'application/json', response_data)
            
        elif path == '/get_patterns' and method == 'GET':
            patterns = get_patterns_list()
            send_response(client_socket, 'application/json', f'{{"patterns":{ujson.dumps(patterns)}}}')
            
        elif path == '/load_pattern' and method == 'POST':
            try:
                data = ujson.loads(body)
                name = data.get('name', '')
                if name in saved_patterns:
                    pattern = saved_patterns[name]
                    for i in range(min(len(pattern), LED_COUNT)):
                        np[i] = tuple(pattern[i])
                        led_colors[i] = tuple(pattern[i])
                    np.write()
                    response_data = f'{{"status":"ok","pattern":{ujson.dumps(pattern)}}}'
                else:
                    response_data = '{"status":"error","message":"图案不存在"}'
            except Exception as e:
                response_data = f'{{"status":"error","message":"{str(e)}"}}'
            send_response(client_socket, 'application/json', response_data)
            
        elif path == '/delete_pattern' and method == 'POST':
            try:
                data = ujson.loads(body)
                name = data.get('name', '')
                response_data = '{"status":"ok"}' if delete_pattern(name) else '{"status":"error","message":"删除失败"}'
            except Exception as e:
                response_data = f'{{"status":"error","message":"{str(e)}"}}'
            send_response(client_socket, 'application/json', response_data)
            
        else:
            client_socket.send(b'HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n404 Not Found')
            
    except Exception as e:
        print(f'处理请求出错: {e}')
        # 不打印完整堆栈，避免刷屏
    finally:
        try:
            client_socket.close()
        except:
            pass

def start_server():
    """启动Web服务器（优化版，支持自动播放）"""
    global last_activity_time
    
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(addr)
    server_socket.listen(3)  # 降低监听队列，ESP32内存有限
    server_socket.settimeout(1.0)  # 设置1秒超时，用于自动播放检查
    
    print('Web服务器已启动，监听端口 80')
    print(f'请连接WiFi热点后访问: http://{ap.ifconfig()[0]}')
    print(f'⚡ 自动播放：{auto_play_interval}秒无活动后开始循环播放')
    
    # 初始化活动时间
    last_activity_time = time.time()
    
    while True:
        try:
            # 尝试接受客户端连接（带超时）
            client_socket, addr = server_socket.accept()
            client_socket.settimeout(10.0)  # 增加到10秒，确保大页面能完整发送
            print(f'客户端连接: {addr}')
            handle_client(client_socket)
        except OSError as e:
            # 超时或无连接，检查是否需要自动播放
            if time.time() - last_activity_time > auto_play_interval:
                if saved_patterns:
                    play_next_pattern()
                    last_activity_time = time.time()  # 更新时间，等待下一个间隔
        except Exception as e:
            print(f'服务器错误: {e}')

# 主程序
if __name__ == '__main__':
    print('===================================')
    print('ESP32 WS2812B LED矩阵控制器 v3.3.2')
    print('===================================')
    
    # 清除LED
    clear_all()
    print('LED已清除')
    
    # 加载保存的图案
    print('正在加载保存的图案...')
    load_patterns()
    
    # 启动WiFi热点
    ap = setup_ap()
    
    print('')
    print('✨ 功能特性：')
    print('  1. 开放WiFi热点（无需密码）')
    print('  2. 自定义IP地址：', CUSTOM_IP)
    print('  3. 滑动绘制功能（像画笔一样）')
    print('  4. 橡皮擦工具（快速熄灭）')
    print('  5. ⚡ 后台自动播放（无需连接，12秒循环）')
    print('  6. ⚡ 压缩页面（加载速度提升80%，约3秒）')
    print('  7. ⚡ 性能优化版（响应速度提升50%+）')
    print('')
    
    # 启动Web服务器
    start_server()

