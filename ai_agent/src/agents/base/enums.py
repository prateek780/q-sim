from enum import Enum


class AgentTaskType(Enum):
    LOG_SUMMARIZATION = "summarize"
    EXTRACT_PATTERNS = "extract_patterns"
    OPTIMIZE_TOPOLOGY = "optimize_topology"
    SYNTHESIZE_TOPOLOGY = "synthesize_topology"
    ROUTING = "routing"