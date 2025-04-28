import traceback
from typing import Any, Dict
from fastapi import APIRouter
from ai_agent.src.consts.agent_type import AgentType
from fastapi import HTTPException

from ai_agent.src.consts.workflow_type import WorkflowType
from ai_agent.src.orchestration.coordinator import Coordinator
from server.api.agent.agent_request import AgentInteractionRequest, AgentRouterRequest
from server.api.agent.summarize import handle_summary_request


agent_router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)


async def handle_routing_request(message_dict: Dict[str, Any]):
    print(message_dict)
    message = AgentRouterRequest(**message_dict)
    agent_coordinator = Coordinator()
    response = await agent_coordinator.execute_workflow(WorkflowType.ROUTING, message)
    return response

agent_to_handler = {
    AgentType.LOG_SUMMARIZER.value: handle_summary_request,
    AgentType.ORCHESTRATOR.value: handle_routing_request
}

@agent_router.post("/message")
async def get_agent_message(message: Dict[str, Any]):
    try:
        return await agent_to_handler[message['agent_id']](message)
    except KeyError  as e:
        raise HTTPException(status_code=400, detail=f"Invalid agent type: {message.get('agent_id', 'INVALID_AGENT_ID')}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
