from enum import Enum


class AgentTaskType(Enum):
    LOG_SUMMARIZATION = "summarize"
    EXTRACT_PATTERNS = "extract_patterns"