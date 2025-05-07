from typing import Any, Dict
from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.consts.workflow_type import WorkflowType
from ai_agent.src.orchestration.coordinator import Coordinator
from data.models.topology.world_model import save_world_to_redis
from server.api.agent.agent_request import SynthesizeTopologyRequest, TopologyOptimizeRequest


async def handle_topology_design(message_dict: Dict[str, Any]):
    if (message_dict.get('task_id') == AgentTaskType.SYNTHESIZE_TOPOLOGY.value):
        message = SynthesizeTopologyRequest(**message_dict)
    else:
        message = TopologyOptimizeRequest(**message_dict)
    
    agent_coordinator = Coordinator()
    
    response = await agent_coordinator.execute_workflow(
        WorkflowType.TOPOLOGY_WORKFLOW,
        {
            "task_data": {
                "task_id": message.task_id or AgentTaskType.OPTIMIZE_TOPOLOGY,
                "input_data": message.model_dump(),
            }
        },
    )

    # if response.get('message_id') and response.get('generated_topology'):
    #     try:
    #         response['generated_topology']['temporary_world'] = True
    #         response['generated_topology'] = save_world_to_redis(response['generated_topology'])
    #     except Exception as e:
    #         print(f"Error saving world to Redis: {e}")

    return response