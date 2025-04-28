from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from typing import Dict, Any, List, Optional, Union, Type
from pydantic import BaseModel, Field
import traceback

from ai_agent.src.agents.enums import AgentTaskType

class AgentInputSchema(BaseModel):
    """Base schema for agent inputs."""
    pass

class AgentOutputSchema(BaseModel):
    """Base schema for agent outputs."""
    pass

class AgentTask(BaseModel):
    """Definition of a task that an agent can perform."""
    task_id: AgentTaskType
    description: str
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]
    examples: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    def get_model_description(self) -> str:
        """Generate a description of the input and output models."""
        return f"""
        Task: {self.task_id.value}
        Description: {self.description}
        Input: {self.input_schema.model_json_schema()}
        Output: {self.output_schema.model_json_schema()}
        
        Examples: {self.examples}
        """

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, agent_id: str, description: str):
        print(f"Agent {__class__.__name__} Initialized")
        self.agent_id = agent_id
        self.description = description
        self.tasks = self._register_tasks()
        
    @abstractmethod
    def _register_tasks(self) -> Dict[str, AgentTask]:
        """Register all tasks this agent can perform."""
        pass
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return information about this agent's capabilities."""
        return {
            "agent_id": self.agent_id,
            "description": self.description,
            "tasks": "\n\n".join([f"{task.get_model_description()}" for task_id, task in self.tasks.items()])
        }
    
    def get_task_details(self, task_id: str) -> Optional[AgentTask]:
        """Get detailed information about a specific task."""
        return self.tasks.get(task_id)
    
    @abstractmethod
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message sent directly to this agent."""
        pass
    
    @abstractmethod
    async def run(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task with the given input data."""
        pass
    
    def validate_input(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data against the task's input schema."""
        task = self.get_task_details(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not supported by this agent")
        
        # Validate using Pydantic
        validated = task.input_schema(**input_data)
        return validated.model_dump()
    
    def validate_output(self, task_id: str, output_data: Union[Dict[str, Any], BaseModel]) -> Dict[str, Any]:
        """Validate output data against the task's output schema."""
        task = self.get_task_details(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not supported by this agent")
        
        if isinstance(output_data, BaseModel):
            if not isinstance(output_data, task.output_schema):
                raise Exception(f"output_data is of type {type(output_data)}, expected type ({task.output_schema})")
            else:
                return output_data.model_dump()
        elif isinstance(output_data, dict):
            # Validate using Pydantic
            validated = task.output_schema(**output_data)
            return validated.model_dump()
        else:
            print(f"Unsupported output data type: {type(output_data)}")
            print(f'''
            ===================
            Output Data:
            ===================
            {output_data}
            ===================
            ''')
            traceback.print_exc()
            raise ValueError("Unsupported output data type")