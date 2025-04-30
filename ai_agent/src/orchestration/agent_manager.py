import json
import os
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ai_agent.src.agents.base.base_agent import BaseAgent
from ai_agent.src.consts.agent_type import AgentType
from ai_agent.src.exceptions.llm_exception import LLMError
from ai_agent.src.orchestration.prompt import PROMPT_TEMPLATE
from ai_agent.src.orchestration.structures import RoutingOutput
from config.config import load_config
from server.api.agent.agent_request import AgentRouterRequest

class AgentManager:
    """Manages the lifecycle and coordination of AI agents in the system."""
    
    def __init__(self):
        self.config = load_config()
        self.agents: Dict[AgentType, BaseAgent] = {}
        self.api_client = self._initialize_llm()
        
    def _initialize_llm(self):
        """Initialize the language model client."""
        api_key = os.getenv("OPENAI_API_KEY") or self.config.llm.api_key
        try:
            llm = ChatOpenAI(
                model_name=self.config.llm.model,
                temperature=self.config.llm.temperature,
                api_key=api_key,
                base_url=self.config.llm.base_url
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize LLM client: {str(e)}")

        return llm
    
    def register_agent(self, agent_id: AgentType, agent_class: BaseAgent, **kwargs):
        """Register a new agent in the system."""
        if agent_id in self.agents:
            raise ValueError(f"Agent with ID '{agent_id}' already exists")
            
        agent_instance = agent_class(llm=self.api_client, **kwargs)
        self.agents[agent_id] = agent_instance
        return agent_instance
    
    def get_agent(self, agent_id: AgentType):
        """Retrieve an agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[AgentType]:
        """List all registered agent IDs."""
        return list(self.agents.keys())
    
    def get_agents_and_capabilities(self) -> str:
        """Get a list of all agents and their capabilities."""
        capabilities = "\n\t".join([json.dumps(self.get_agent(agent_id).get_capabilities(), indent=2) for agent_id in self.list_agents()])
        return capabilities

    def execute_agent(self, agent_id: AgentType, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific agent with the given input data."""
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"No agent found with ID '{agent_id}'")
        
        return agent.run(input_data)
    
    def find_best_agent_by_user_query(self, user_query: AgentRouterRequest) -> RoutingOutput:
        """
        Uses an LLM to determine the best agent for a user query based on agent descriptions.

        Args:
        user_query: The query submitted by the user.
        available_agents: A list of AgentInfo objects describing the available agents.
        llm: An initialized LangChain compatible Chat LLM instance.

        Returns:
        A RoutingOutput object containing the routing decision.
        """
        parser = PydanticOutputParser(pydantic_object=RoutingOutput)
        format_instructions = parser.get_format_instructions()
        prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

        chain = prompt | self.api_client | parser

        try:
            routing_input = {
                "agent_details": self.get_agents_and_capabilities(),
                "query": user_query.model_dump_json(indent=2, exclude=['agent_id']),
                "format_instructions": format_instructions,
            }
            result = chain.invoke(routing_input)
            return result

        except Exception as e:
            raise LLMError(f"Error routing query: {e}")
    
    def shutdown_agent(self, agent_id: AgentType) -> bool:
        """Shutdown and unregister an agent."""
        if agent_id in self.agents:
            # Clean up resources if needed
            del self.agents[agent_id]
            return True
        return False