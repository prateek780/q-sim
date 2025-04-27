from ai_agent.src.agents.enums import AgentTaskType
from ai_agent.src.consts.workflow_type import WorkflowType
from ai_agent.src.orchestration.coordinator import Coordinator
from server.api.agent.agent_request import AgentInteractionRequest


async def handle_summary_request(message: AgentInteractionRequest):
    agent_coordinator = Coordinator()
    
    response = await agent_coordinator.execute_workflow(
        WorkflowType.LOG_SUMMARIZATION,
        {
            "task_data": {
                "task_id": AgentTaskType.LOG_SUMMARIZATION,
                "input_data": {"simulation_id": message.simulation_id},
            }
        },
    )

    return response