import os
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI

class AgentManager:
    """Manages the lifecycle and coordination of AI agents in the system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agents = {}
        self.api_client = self._initialize_llm()
        
    def _initialize_llm(self):
        """Initialize the language model client."""
        api_key = os.getenv("OPENAI_API_KEY") or self.config.get("api_keys", {}).get("openai")
        try:
            llm = ChatOpenAI(
                model_name=self.config.get("model_name", "gpt-4"),
                temperature=self.config.get("temperature", 0.2),
                api_key=api_key
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize LLM client: {str(e)}")

        return llm
    
    def register_agent(self, agent_id: str, agent_class, **kwargs):
        """Register a new agent in the system."""
        if agent_id in self.agents:
            raise ValueError(f"Agent with ID '{agent_id}' already exists")
            
        agent_instance = agent_class(llm=self.api_client, **kwargs)
        self.agents[agent_id] = agent_instance
        return agent_instance
    
    def get_agent(self, agent_id: str):
        """Retrieve an agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """List all registered agent IDs."""
        return list(self.agents.keys())
    
    def execute_agent(self, agent_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific agent with the given input data."""
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"No agent found with ID '{agent_id}'")
        
        return agent.run(input_data)
    
    def shutdown_agent(self, agent_id: str) -> bool:
        """Shutdown and unregister an agent."""
        if agent_id in self.agents:
            # Clean up resources if needed
            del self.agents[agent_id]
            return True
        return False