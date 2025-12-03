"""
用户对话历史记录，存储到 本地 sqlite 数据库中
"""
import sqlite3
import json
from Utils.Messages.messageStruct.userInput import Message
from typing import List
from datetime import datetime


class MemorySystem:
    """记忆系统 - 存储对话历史和上下文"""

    def __init__(self, db_path: str = "agent_memory.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT,
                metadata TEXT
            )"""
        )
        conn.commit()
        conn.close()

    def store_message(self, session_id: str, message: Message):
        """存储消息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO conversations (session_id, role, content, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_id,
            message.role,
            message.content,
            message.timestamp.isoformat(),
            json.dumps(message.metadata) if message.metadata else None
        ))
        conn.commit()
        conn.close()

    def get_recent_context(self, session_id: str, limit: int = 10) -> List[Message]:
        """获取最近的对话上下文"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content, timestamp, metadata 
            FROM conversations 
            WHERE session_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (session_id, limit))

        rows = cursor.fetchall()
        conn.close()

        messages = []
        for row in reversed(rows):  # 按时间顺序排列
            role, content, timestamp, metadata = row
            msg = Message(
                role=role,
                content=content,
                timestamp=datetime.fromisoformat(timestamp),
                metadata=json.loads(metadata) if metadata else None
            )
            messages.append(msg)

        return messages