from enum import Enum


class AgentTaskType(Enum):
    LOG_SUMMARIZATION = "summarize"
    LOG_QNA = "log_qna"
    EXTRACT_PATTERNS = "extract_patterns"
    OPTIMIZE_TOPOLOGY = "optimize_topology"
    SYNTHESIZE_TOPOLOGY = "synthesize_topology"
    TOPOLOGY_QNA = "topology_qna"
    ROUTING = "routing"
    VALIDATE_TOPOLOGY = "validate_topology"