# 微信 RPA 自动化 (weixinauto)

> **跨平台微信 RPA 工具** — 支持 macOS（键盘事件模拟）和 Windows（pywinauto）

## 功能

### macOS 版
- ✅ 搜索联系人 & 发送消息
- ✅ 通过剪贴板发送长文本
- ✅ 键盘按键模拟（Enter、Tab、方向键等）
- ✅ 无需 Accessibility 权限（系统级键盘事件）
- ✅ 兼容 Electron 新版本微信（WeChatAppEx）

### Windows 版
- ✅ 消息发送（单/多人）
- ✅ 文件传输（单/多文件）
- ✅ 联系人管理（备注、标签、拉黑）
- ✅ 朋友圈操作（发布、导出）
- ✅ 自动回复（好友/群聊）
- ✅ 消息监听
- ✅ 通话控制
- ✅ 基于 [pywechat](https://github.com/zhiguo1974-web/pywechat) 项目（pywinauto 纯 UI 自动化）

## 快速开始（macOS）

```bash
# 检查微信运行状态
python3 scripts/wechat_gui.py status

# 给联系人发消息
python3 scripts/wechat_gui.py send "文件传输助手" "你好"

# 发送长文本
python3 scripts/wechat_gui.py send_long "文件传输助手" "长消息内容..."

# 搜索联系人
python3 scripts/wechat_gui.py search "张三"
```

## 安装

### macOS
```bash
# 克隆仓库
git clone https://github.com/zhiguo1974-web/weixinauto.git
cd weixinauto
```

### Windows
```bash
git clone https://github.com/zhiguo1974-web/weixinauto.git
pip install -r windows/requirements.txt
```

## 技术原理

### macOS
Electron 版 Mac微信 有以下限制：
- ❌ Accessibility API 不暴露 UI 树
- ❌ SQLite 数据库使用 WCDB 加密

**解决方案**：系统级键盘事件模拟
```
Cmd+F 搜索联系人 → 输入名字 → Enter 选中 → 输入消息 → Enter 发送
```

### Windows
基于 `pywinauto` 的纯 UI 自动化（无 Hook 注入），详情参见 [pywechat](https://github.com/zhiguo1974-web/pywechat)。

## 脚本说明

| 文件 | 说明 |
|------|------|
| `SKILL.md` | Hermes Agent 技能定义（完整 API 文档） |
| `scripts/wechat_gui.py` | macOS GUI 自动化主脚本 |
| `scripts/wechat_db.py` | macOS 微信数据库探针工具（WCDB 加密版暂不可读） |

## 注意事项

- macOS 版操作时会接管键盘，期间请勿操作鼠标键盘
- 操作间有 1-1.5s 延迟等待
- 确保微信处于前台并登录状态
- Windows 版仅支持 Windows 7/10/11
- 请勿用于非法用途

## 许可证

MIT
