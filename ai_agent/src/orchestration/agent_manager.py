import os
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI

from ai_agent.src.agents.base_agent import BaseAgent
from ai_agent.src.consts.agent_type import AgentType
from config.config import load_config

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
    
    def execute_agent(self, agent_id: AgentType, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific agent with the given input data."""
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"No agent found with ID '{agent_id}'")
        
        return agent.run(input_data)
    
    def shutdown_agent(self, agent_id: AgentType) -> bool:
        """Shutdown and unregister an agent."""
        if agent_id in self.agents:
            # Clean up resources if needed
            del self.agents[agent_id]
            return True
        return False