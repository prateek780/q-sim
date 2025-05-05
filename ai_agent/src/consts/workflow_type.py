from enum import Enum

class WorkflowType(Enum):
    LOG_SUMMARIZATION = "log_summarization"
    TOPOLOGY_WORKFLOW = "topology"
    ROUTING = "routing"