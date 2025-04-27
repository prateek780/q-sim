import traceback
from fastapi import APIRouter
from ai_agent.src.consts.agent_type import AgentType
from fastapi import HTTPException

from server.api.agent.agent_request import AgentInteractionRequest
from server.api.agent.summarize import handle_summary_request


agent_router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)


agent_to_handler = {
    AgentType.LOG_SUMMARIZER: handle_summary_request
}

@agent_router.post("/message")
async def get_agent_message(message: AgentInteractionRequest):
    
    try:
        return await agent_to_handler[message.agent_id](message)
    except KeyError  as e:
        raise HTTPException(status_code=400, detail=f"Invalid agent type: {message.agent_id}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
