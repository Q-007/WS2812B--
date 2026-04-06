# boot.py -- 在启动时运行
# 这个文件在main.py之前执行

import gc
import esp

# 禁用调试输出
esp.osdebug(None)

# 启用垃圾回收
gc.collect()

print('boot.py 执行完成')

