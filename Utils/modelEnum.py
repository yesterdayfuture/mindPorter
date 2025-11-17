from enum import Enum
from typing import List, Optional


class ModelEnum(Enum):
    Openai: Optional[str] = "openaimodel"
    Ollama: Optional[str] = "ollamamodel"
