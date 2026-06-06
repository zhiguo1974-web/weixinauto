---
name: weixinauto
description: "跨平台微信 RPA 工具。Windows 版基于 pywechat/pywinauto，macOS 版基于系统级键盘事件 + pbcopy + AppleScript，支持发消息、搜索、自动化操作。"
---

# 微信自动化 RPA (weixinauto)

## Overview

**跨平台微信 RPA 工具**，根据运行平台自动切换方案：

- **macOS**：系统级键盘事件 + pbcopy + AppleScript（无需 Accessibility 权限）
- **Windows**：基于 [pywechat](https://github.com/zhiguo1974-web/pywechat) 的 `pywinauto`（Windows 专用）

---

## 快速开始 (macOS)

### 脚本路径

```
~/.hermes/skills/autonomous-ai-agents/weixinauto/scripts/wechat_gui.py
```

### 发送消息

```bash
python3 ~/.hermes/skills/autonomous-ai-agents/weixinauto/scripts/wechat_gui.py send "文件传输助手" "你好"
```

### 其他命令

| 命令 | 用法 | 说明 |
|------|------|------|
| `status` | `python3 wechat_gui.py status` | 检查微信运行状态 |
| `focus` | `python3 wechat_gui.py focus` | 激活微信窗口 |
| `launch` | `python3 wechat_gui.py launch` | 打开微信 |
| `send` | `send "好友名" "消息"` | 搜索联系人并发送消息 |
| `send_long` | `send_long "好友名" "长文本"` | 通过剪贴板发送长文本 |
| `search` | `search "好友名"` | 搜索联系人 |
| `type` | `type "文本"` | 在当前焦点输入文字 |
| `key` | `key enter` | 发送键盘按键 |

---

## macOS 实现原理

由于 Mac微信（Electron/WeChatAppEx 版）有以下限制：

- ❌ **Accessibility API** 不支持（Electron 版不暴露 UI 树）
- ❌ **SQLite 数据库** 加密（WCDB 格式，不可直接读取）
- ✅ **系统级键盘事件** 正常工作（无需权限）

所以采用**键盘快捷键模拟**路径：

```
Cmd+F 搜索联系人 → 输入名字 → Enter 选中 → 输入消息 → Enter 发送
```

### 关键技术

| 技术 | 用途 |
|------|------|
| `open -a WeChat` | 激活微信窗口 |
| `System Events keystroke` | 发送键盘输入 |
| `System Events key code` | 发送功能键（Enter等） |
| `pbcopy` | 剪贴板写入（长文本粘贴） |

### 按键映射表

| 名称 | 键码 |
|------|------|
| enter/return | 36 |
| tab | 48 |
| space | 49 |
| up/down/left/right | 126/125/123/124 |
| esc | 53 |
| delete/backspace | 51 |

---

## Windows 版方案

### 仓库路径

```
/Users/zhiguo/www/pywechat/
/Users/zhiguo/www/pywechat/skills/openclaw/pyweixin-rpa/scripts/
```

### 模块导入

```python
import sys
sys.path.insert(0, '/path/to/scripts')
from pyweixin import Messages, Files, Contacts
from pyweixin import AutoReply, Monitor, Moments
from pyweixin import Tools, Navigator
from pyweixin.Config import GlobalConfig
```

### 核心 API

| 模块 | 类 | 功能 |
|------|------|------|
| WeChatAuto | Messages | 发消息、拉取聊天记录、检查新消息 |
| | Files | 发文件、保存文件、转发文件 |
| | Contacts | 联系人/群/公众号信息获取 |
| | FriendSettings | 改备注、标签、拉黑、删除好友 |
| | AutoReply | 自动回复好友/群聊 |
| | Monitor | 消息监听 |
| | Call | 通话、自动接听 |
| | Moments | 朋友圈操作 |
| WeChatTools | Navigator | 打开/关闭微信、搜索 |
| | Tools | 状态检测、路径查询 |

> ⚠️ Windows 版所有方法均为**静态方法**，直接 `ClassName.method()` 调用。
> 详细 API 参见：`/Users/zhiguo/www/pywechat/skills/openclaw/pyweixin-rpa/references/api_reference.md`

---

## 使用场景示例

### 每日定时问候

```python
import subprocess
script = '~/.hermes/skills/.../scripts/wechat_gui.py send "老婆" "早安，今天天气很好！"'
subprocess.run(['python3', '-c', script])
```

### 群发消息

```python
contacts = ['张三', '李四', '王五']
for name in contacts:
    subprocess.run(['python3', script_path, 'send', name, '节日快乐！'])
```

### 收到通知后自动回复

结合 Hermes cronjob：
```bash
# 每5分钟检查并发送
hermes cron create --schedule "*/5 * * * *" --prompt "给文件传输助手发一条'定时心跳消息'"
```

---

## 注意事项

1. **不要同时操作**：键盘模拟时会接管输入，操作期间别动鼠标键盘
2. **延迟等待**：操作间有 1-1.5 秒等待，不要缩短
3. **中文输入**：确保微信输入框处于中文输入法
4. **微信版本**：macOS Electron 版 4.x+
5. **短消息用 `send`，长消息用 `send_long`**（超过 50 字建议用剪贴板）
