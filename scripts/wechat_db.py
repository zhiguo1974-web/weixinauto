#!/usr/bin/env python3
"""
macOS 微信数据库读取工具
读取 ~/Library/Containers/com.tencent.xinWeChat/ 下的 SQLite 数据库
自动探索表结构，适配不同版本
"""
import sqlite3
import os
import glob
import json
import sys
from datetime import datetime

def _xwechat_base():
    """获取新 Mac微信 (Electron/AppEx) 用户数据根目录"""
    base = os.path.expanduser(
        '~/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/'
    )
    if not os.path.exists(base):
        return None
    # 找到用户目录（格式: {account}_{hash}）
    for d in sorted(os.listdir(base), reverse=True):
        if d != 'WMPF' and d != 'all_users' and os.path.isdir(os.path.join(base, d)):
            return os.path.join(base, d)
    return None

def _old_macwechat_base():
    """旧版 Mac微信 (Cocoa) 数据库路径"""
    base = os.path.expanduser(
        '~/Library/Containers/com.tencent.xinWeChat/Data/'
        'Library/Application Support/com.tencent.xinWeChat/'
    )
    if os.path.exists(base):
        return base
    return None

def is_encrypted(db_path):
    """检测数据库是否加密（非标准 SQLite 格式）"""
    if not db_path or not os.path.exists(db_path):
        return False
    try:
        with open(db_path, 'rb') as f:
            header = f.read(16)
        # SQLite 标准签名: "SQLite format 3\0"
        return header[:15] != b'SQLite format 3'
    except:
        return True

def find_msg_db():
    """自动查找微信消息数据库路径"""
    # 先找新 Mac微信 (Electron/AppEx) 加密路径
    user_dir = _xwechat_base()
    if user_dir:
        msg_dir = os.path.join(user_dir, 'db_storage', 'message')
        if os.path.exists(msg_dir):
            for f in sorted(os.listdir(msg_dir)):
                if f.endswith('.db') and 'message' in f:
                    path = os.path.join(msg_dir, f)
                    encrypted = is_encrypted(path)
                    return {'path': path, 'encrypted': encrypted, 'version': 'electron'}
        return {'path': msg_dir, 'encrypted': True, 'version': 'electron'}
    
    # 回退：旧 Mac微信 (Cocoa) 未加密路径
    old_base = _old_macwechat_base()
    if old_base:
        for item in sorted(os.listdir(old_base), reverse=True):
            version_dir = os.path.join(old_base, item)
            if not os.path.isdir(version_dir):
                continue
            for root, dirs, files in os.walk(version_dir):
                for f in files:
                    if f.startswith(('MM', 'msg')) and f.endswith(('.sqlite', '.db')):
                        path = os.path.join(root, f)
                        encrypted = is_encrypted(path)
                        return {'path': path, 'encrypted': encrypted, 'version': 'cocoa'}
    return None

def find_contact_db():
    """查找联系人数据库"""
    # 新 Mac微信 (Electron/AppEx)
    user_dir = _xwechat_base()
    if user_dir:
        contact_db = os.path.join(user_dir, 'db_storage', 'contact', 'contact.db')
        if os.path.exists(contact_db):
            encrypted = is_encrypted(contact_db)
            return {'path': contact_db, 'encrypted': encrypted, 'version': 'electron'}
    
    # 旧 Mac微信 (Cocoa)
    old_base = _old_macwechat_base()
    if old_base:
        for item in sorted(os.listdir(old_base), reverse=True):
            version_dir = os.path.join(old_base, item)
            if not os.path.isdir(version_dir):
                continue
            for root, dirs, files in os.walk(version_dir):
                for f in files:
                    if 'contact' in f.lower() and f.endswith(('.db', '.sqlite')):
                        path = os.path.join(root, f)
                        encrypted = is_encrypted(path)
                        return {'path': path, 'encrypted': encrypted, 'version': 'cocoa'}
    return None

def explore_db(db_path):
    """探索数据库表结构"""
    if not db_path:
        return {'error': '未指定数据库路径'}
    
    result = {}
    
    if isinstance(db_path, dict):
        # dict 格式返回的信息
        result = dict(db_path)
        if db_path.get('encrypted'):
            result['note'] = '加密 WCDB 格式，无法用 sqlite3 读取，请使用 GUI 自动化路线'
            return result
        path = db_path.get('path', '')
    else:
        path = db_path
    
    if not path or not os.path.exists(path):
        result['error'] = '数据库文件不存在'
        return result
    
    result['db_path'] = path
    result['size_mb'] = round(os.path.getsize(path) / (1024*1024), 1)
    
    # 检测加密
    encrypted = is_encrypted(path)
    result['encrypted'] = encrypted
    
    if encrypted:
        file_header = open(path, 'rb').read(16).hex()[:32]
        result['header_hex'] = file_header
        result['note'] = '加密 WCDB 格式（非标准 SQLite），无法直接读取'
        return result
    
    # 标准 SQLite 读取
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        
        result['tables'] = {}
        for (table,) in tables:
            cur.execute(f"PRAGMA table_info([{table}])")
            cols = cur.fetchall()
            result['tables'][table] = [
                {'name': col[1], 'type': col[2], 'nullable': not col[3]}
                for col in cols
            ]
        conn.close()
    except Exception as e:
        result['error'] = f'读取失败: {e}'
        result['note'] = '可能是加密格式或损坏'
    
    return result

def get_recent_messages(limit=20, db_path=None):
    """获取最近消息"""
    if not db_path:
        db_path = find_msg_db()
    
    if not db_path:
        return {'error': '未找到微信数据库，请确认已登录微信'}
    
    print(f'📁 数据库路径: {db_path}', file=sys.stderr)
    
    # 先探索结构
    info = explore_db(db_path)
    tables = info.get('tables', {})
    
    conn = sqlite3.connect(db_path)
    conn.text_factory = str
    cur = conn.cursor()
    
    # 尝试找到消息表
    msg_tables = [t for t in tables if 'chat' in t.lower() or 'msg' in t.lower() or 'message' in t.lower()]
    
    if not msg_tables:
        # 显示所有表名
        print(f'📊 找到以下表: {list(tables.keys())}', file=sys.stderr)
        conn.close()
        return info
    
    table = msg_tables[0]
    cols = [c['name'] for c in tables[table]]
    
    print(f'📋 查询表: {table}', file=sys.stderr)
    print(f'📋 列: {cols}', file=sys.stderr)
    
    # 尝试常用字段名
    time_col = next((c for c in cols if 'time' in c.lower() or 'date' in c.lower()), cols[0])
    msg_col = next((c for c in cols if 'msg' in c.lower() or 'content' in c.lower() or 'text' in c.lower() or 'message' in c.lower()), cols[1] if len(cols) > 1 else cols[0])
    type_col = next((c for c in cols if 'type' in c.lower()), None)
    sender_col = next((c for c in cols if 'sender' in c.lower() or 'from' in c.lower() or 'user' in c.lower()), None)
    
    try:
        query = f'SELECT * FROM [{table}] ORDER BY [{time_col}] DESC LIMIT {limit}'
        cur.execute(query)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            item = dict(zip(cols, row))
            # 时间戳转可读格式
            if time_col in item and isinstance(item[time_col], (int, float)):
                try:
                    item['_time_readable'] = datetime.fromtimestamp(item[time_col]).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            results.append(item)
        
        conn.close()
        return results
    except Exception as e:
        conn.close()
        return {'error': str(e), 'table_info': info}

def get_contacts(db_path=None):
    """获取联系人列表"""
    if not db_path:
        db_path = find_contact_db()
    
    if not db_path:
        return {'error': '未找到联系人数据库'}
    
    info = explore_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.text_factory = str
    cur = conn.cursor()
    
    tables = info.get('tables', {})
    
    # 找联系人表
    contact_tables = [t for t in tables if 'contact' in t.lower() or 'friend' in t.lower()]
    
    if not contact_tables:
        conn.close()
        return info
    
    table = contact_tables[0]
    cols = [c['name'] for c in tables[table]]
    
    try:
        cur.execute(f'SELECT * FROM [{table}] LIMIT 100')
        rows = cur.fetchall()
        results = [dict(zip(cols, row)) for row in rows]
        conn.close()
        return results
    except Exception as e:
        conn.close()
        return {'error': str(e), 'table_info': info}


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'paths'
    
    if action == 'explore':
        db = find_msg_db()
        contact_db = find_contact_db()
        result = {
            'message_db': explore_db(db),
            'contact_db': explore_db(contact_db),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    
    elif action == 'messages':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        db = find_msg_db()
        if db and not db.get('encrypted', True):
            result = get_recent_messages(limit, db.get('path'))
        else:
            result = {'error': '数据库加密或不存在，请使用 GUI 自动化路线（scripts/wechat_gui.py）'}
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    
    elif action == 'contacts':
        db = find_contact_db()
        if db and not db.get('encrypted', True):
            result = get_contacts(db.get('path'))
        else:
            result = {'error': '联系人数据库加密，无法读取'}
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    
    elif action == 'paths':
        msg = find_msg_db()
        contact = find_contact_db()
        user_dir = _xwechat_base()
        print(f'用户数据目录: {user_dir or "(未找到)"}')
        print(f'消息数据库: {msg}')
        print(f'联系人数据库: {contact}')
        if msg and msg.get('encrypted'):
            print(f'\n⚠️  新版 Mac微信 数据库已加密（WCDB 格式）')
            print(f'   无法直接读取，请使用 GUI 自动化方案')
            print(f'   运行: python3 scripts/wechat_gui.py')
