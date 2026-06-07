#!/usr/bin/env python3
"""
itchat-uos: iPad 微信协议自动回复
基于 UOS/iPad 协议，不需要手机登录，扫二维码即可
支持 macOS 上实时收消息并自动回复
"""
import itchat
from itchat.content import TEXT, PICTURE, VOICE, CARD, SHARING, ATTACHMENT
import sys
import json
import os
import time

# ============ 配置区 ============
# 自动回复的规则
AUTO_REPLY_RULES = {
    '你好': '你好！我是微信机器人，有什么可以帮您的？',
    '在吗': '在的，请问有什么需要？',
    '帮助': '可用指令：\n1. 输入任何问题我会自动回复\n2. 回复"再见"结束对话',
    '再见': '好的，再见！有需要再找我~',
    '你是谁': '我是基于 itchat-uos 的微信机器人，运行在 macOS 上',
}

# 默认回复
DEFAULT_REPLY = '收到您的消息了，我稍后回复您 😊'

# 要忽略的好友名单（不自动回复）
IGNORE_FRIENDS = []

# ============ 消息处理 ============

@itchat.msg_register(TEXT)
def text_reply(msg):
    """文字消息处理"""
    from_user = msg['User']['NickName'] if msg['User'] else 'Unknown'
    content = msg['Text']
    
    # 是群消息吗？
    is_group = msg['Type'] == 'Text' and '@' in str(msg.get('FromUserName', ''))
    
    print(f"\n📩 [{time.strftime('%H:%M:%S')}] {from_user}: {content}")
    
    # 不回复自己
    if msg['FromUserName'] == 'self':
        return None
    
    # 不回复忽略列表
    if from_user in IGNORE_FRIENDS:
        return None
    
    # 检查关键词回复
    for keyword, reply in AUTO_REPLY_RULES.items():
        if keyword in content:
            print(f"🤖 回复 {from_user}: {reply}")
            return reply
    
    # 默认回复
    print(f"🤖 回复 {from_user}: {DEFAULT_REPLY}")
    return DEFAULT_REPLY

@itchat.msg_register([PICTURE, VOICE, CARD, SHARING, ATTACHMENT])
def media_reply(msg):
    """多媒体消息处理"""
    msg_type_map = {
        PICTURE: '图片', VOICE: '语音', CARD: '名片',
        SHARING: '分享', ATTACHMENT: '文件'
    }
    msg_type = msg_type_map.get(msg['Type'], '未知')
    from_user = msg['User']['NickName'] if msg['User'] else 'Unknown'
    
    print(f"\n📎 [{time.strftime('%H:%M:%S')}] {from_user} 发送了{msg_type}")
    
    # 可以回复一条文本
    return f'收到您的{msg_type}消息了 📎'

# ============ 群消息处理（可选） ============

@itchat.msg_register(TEXT, isGroupChat=True)
def group_text_reply(msg):
    """群消息处理（被@时才回复）"""
    content = msg['Text']
    group_name = msg['User']['NickName'] if msg['User'] else 'Unknown'
    sender = msg['ActualNickName'] if msg['ActualNickName'] else 'Unknown'
    
    # 检查是否被@
    is_at = ' @' in content or content.startswith('@')
    
    print(f"\n👥 [{time.strftime('%H:%M:%S')}] {group_name}/{sender}: {content}")
    
    if is_at:
        reply = f'@{sender} 已收到消息！'
        print(f"🤖 回复群 @{sender}: {reply}")
        return reply
    
    return None  # 不回复非@消息


# ============ 好友请求处理 ============

@itchat.msg_register(itchat.content.FRIENDS)
def friend_request(msg):
    """新好友请求自动通过"""
    new_friend = itchat.add_friend(**msg['Text'])
    itchat.send_msg('你好！我是微信机器人，很高兴认识你！', new_friend['UserName'])
    print(f"\n👋 新好友: {msg['Text']['UserName']}")


# ============ 启动 ============

def main():
    print("""
╔════════════════════════════════════╗
║   微信 iPad 协议自动回复机器人      ║
║   itchat-uos (UOS/iPad Protocol)   ║
╚════════════════════════════════════╝
    
使用说明:
1. 运行后会弹出二维码，用微信扫码登录
2. 登录后自动开始监听消息
3. 按 Ctrl+C 退出

协议: iPad/UOS (不需要手机辅助登录)
    """)
    
    # 自动登录（保存会话，下次无需扫码）
    try:
        itchat.auto_login(
            hotReload=True,          # 保存登录状态，下次不用扫码
            enableCmdQR=2,           # 终端二维码（2=彩色的）
            picDir='./qr.png',       # 也保存二维码图片
        )
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        print("首次登录需要扫码，请确保网络通畅")
        sys.exit(1)
    
    print(f"\n✅ 登录成功！开始监听消息...")
    print(f"   好友数: {len(itchat.get_friends())}")
    print(f"   群聊数: {len(itchat.get_chatrooms())}")
    print(f"   公众号: {len(itchat.get_mps())}")
    print(f"\n   按 Ctrl+C 停止\n")
    
    # 开始消息监听循环
    itchat.run()


if __name__ == '__main__':
    main()
