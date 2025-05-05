from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.agents.router.structure import RoutingInput, RoutingOutput
from ai_agent.src.consts.agent_type import AgentType


ROUTING_AGENT_INPUT_EXAMPLE = RoutingInput(
    conversation_id="12345",
    agent_details=["This is an example of agent details."],
    user_query={"query": "Summarize my simulation logs"}
)

ROUTER_AGENT_OUTPUT_EXAMPLE = RoutingOutput(
    agent_id=AgentType.LOG_SUMMARIZER,
    task_id=AgentTaskType.LOG_SUMMARIZATION.value,
    input_data=ROUTING_AGENT_INPUT_EXAMPLE.user_query,
    reason="The user query is related to summarizing logs, which is the task of the LOG_SUMMARIZER agent.",
)



ROUTER_AGENT_EXAMPLES = [
    {
        "input": ROUTING_AGENT_INPUT_EXAMPLE.model_dump_json(),
        "output": ROUTER_AGENT_OUTPUT_EXAMPLE.model_dump_json(),
    }
]
