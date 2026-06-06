#!/usr/bin/env python3
"""
macOS 微信 GUI 自动化工具 (Electron版兼容)
基于系统级键盘事件 + AppleScript + pbcopy，无需 Accessibility 权限
"""
import subprocess
import time
import sys
import json

def run_osa(script):
    """执行 AppleScript，不指定 process，使用全局键盘事件"""
    result = subprocess.run(['osascript', '-e', script],
                          capture_output=True, text=True, timeout=15)
    return result.stdout.strip(), result.stderr.strip()

def focus_wechat():
    """激活微信窗口（使用应用级 activate）"""
    subprocess.run(['open', '-a', 'WeChat'])
    time.sleep(1.5)
    return True

def launch_wechat():
    """打开微信"""
    subprocess.run(['open', '-a', 'WeChat'])
    time.sleep(3)
    return True

def search_contact(name):
    """Cmd+F 搜索联系人"""
    focus_wechat()
    time.sleep(0.5)
    run_osa('tell application "System Events" to keystroke "f" using command down')
    time.sleep(0.5)
    run_osa(f'tell application "System Events" to keystroke "{name}"')
    time.sleep(1.5)
    run_osa('tell application "System Events" to key code 36')
    time.sleep(1.5)

def send_key(key_name):
    """发送键盘按键"""
    key_map = {
        'enter': 36, 'return': 36, 'tab': 48, 'space': 49,
        'up': 126, 'down': 125, 'left': 123, 'right': 124,
        'esc': 53, 'escape': 53, 'delete': 51, 'backspace': 51,
        'cmd': 55, 'shift': 56, 'ctrl': 59, 'option': 58, 'alt': 58
    }
    code = key_map.get(key_name.lower())
    if code:
        run_osa(f'tell application "System Events" to key code {code}')

def type_text(text):
    """输入文本"""
    escaped = text.replace('"', '\\"').replace('\n', '\\return')
    run_osa(f'tell application "System Events" to keystroke "{escaped}"')

def paste_from_clipboard(text):
    """写入剪贴板并粘贴"""
    subprocess.run(['pbcopy'], input=text.encode('utf-8'))
    time.sleep(0.3)
    run_osa('tell application "System Events" to keystroke "v" using command down')

def send_message(name, text):
    """给指定联系人发消息（通过 Cmd+F 搜索 -> 输入 -> Enter 发送）"""
    search_contact(name)
    type_text(text)
    time.sleep(0.3)
    send_key('enter')
    return True

def send_message_long(name, text):
    """给指定联系人发长消息（通过剪贴板粘贴避免键盘输入限制）"""
    search_contact(name)
    paste_from_clipboard(text)
    time.sleep(0.3)
    send_key('enter')
    return True

def check_wechat_running():
    """检查微信是否在运行"""
    script = 'tell application "System Events" to return exists (processes where name is "WeChat")'
    out, _ = run_osa(script)
    # 也检查 WeChatAppEx
    script2 = 'tell application "System Events" to return exists (processes where name is "WeChatAppEx")'
    out2, _ = run_osa(script2)
    return 'true' in out.lower() or 'true' in out2.lower()

def get_screen_info():
    """获取屏幕信息"""
    result = subprocess.run(['osascript', '-e',
        'tell application "Finder" to get bounds of window of desktop'],
        capture_output=True, text=True)
    return result.stdout.strip()

def click_at(x, y):
    """通过 AppleScript 在指定坐标点击"""
    run_osa(f'''
    tell application "System Events"
        set mousePosition to {{{x}, {y}}}
        perform action "AXPress" of (first element of (every process) whose position is mousePosition)
    end tell
    ''')


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'status'

    if action == 'status':
        running = check_wechat_running()
        screen = get_screen_info()
        print(json.dumps({
            'running': running,
            'screen': screen,
            '注': 'Mac微信(Electron版)需用键盘快捷键控制'
        }, ensure_ascii=False, indent=2))

    elif action == 'focus':
        focus_wechat()
        print('OK')

    elif action == 'launch':
        launch_wechat()
        print('OK')

    elif action == 'send':
        name = sys.argv[2] if len(sys.argv) > 2 else '文件传输助手'
        text = sys.argv[3] if len(sys.argv) > 3 else '测试消息'
        send_message(name, text)
        print('OK')

    elif action == 'send_long':
        name = sys.argv[2] if len(sys.argv) > 2 else '文件传输助手'
        text = sys.argv[3] if len(sys.argv) > 3 else '长文本通过剪贴板粘贴'
        send_message_long(name, text)
        print('OK')

    elif action == 'search':
        name = sys.argv[2] if len(sys.argv) > 2 else '文件传输助手'
        search_contact(name)
        print('OK')

    elif action == 'type':
        text = sys.argv[2] if len(sys.argv) > 2 else 'hello'
        type_text(text)
        print('OK')

    elif action == 'key':
        send_key(sys.argv[2] if len(sys.argv) > 2 else 'enter')
        print('OK')

    else:
        print(f'''
用法: {sys.argv[0]} <命令> [参数]

命令:
  status           检查微信运行状态
  focus            激活微信窗口
  launch           打开微信
  send <名称> <消息>  给联系人发消息
  send_long <名称> <文本>  通过剪贴板发长文本
  search <名称>    搜索联系人
  key <键名>       发送键盘按键
  type <文本>      在当前位置输入文字
''')
