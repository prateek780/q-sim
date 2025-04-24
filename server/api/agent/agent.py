from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from ai_agent.src.consts.agent_type import AgentType
from ai_agent.src.consts.workflow_type import WorkflowType
from ai_agent.src.orchestration.coordinator import Coordinator
from data.embedding.embedding_util import EmbeddingUtil
from data.embedding.vector_log import VectorLogEntry


agent_router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)


class AgentInteractionRequest(BaseModel):
    agent_id: AgentType
    message: str
    tags: Optional[List[str]] = None


@agent_router.post("/message")
async def get_agent_message(message: AgentInteractionRequest):
    agent_coordinator = Coordinator()
    simulation_id = "01JSCW7XRM53FRRV4JKSSPMEPE"
    # embedding_util = EmbeddingUtil()
    # query_embedding = embedding_util.generate_embedding('')
        
    # Search for relevant logs
    logs = VectorLogEntry.get_by_simulation(
        simulation_id
    )
    # agent_coordinator.execute_workflow(WorkflowType.LOG_SUMMARIZATION, {
    #     'task_data': {
    #         ''
    #     }
    # })
    return logs