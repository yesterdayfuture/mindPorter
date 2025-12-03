"""
定义数据通用格式
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict


@dataclass
class Message:
    """消息数据结构"""
    role: str  # system, user, assistant, tool
    content: str
    timestamp: datetime = None
    metadata: Dict = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()