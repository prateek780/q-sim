from typing import Dict, Any, List, Optional
import asyncio
import logging
from .agent_manager import AgentManager

class Coordinator:
    """Central coordinator for the AI agent system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agent_manager = AgentManager(config)
        self.active_workflows = {}
        self.logger = logging.getLogger("coordinator")
        
    async def initialize_system(self):
        """Initialize all required agents and resources."""
        self.logger.info("Initializing agent system")
        # Register core agents
        self._register_core_agents()
        # Initialize shared resources
        # Setup communication channels, TODO: Plan this
        
    def _register_core_agents(self):
        """Register the core agents required by the system."""
        from ..agents.log_summarization_agent import LogSummarization

        self.agent_manager.register_agent("log_summarization", LogSummarization)
        
    async def execute_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]):
        """Execute a multi-agent workflow."""
        self.active_workflows[workflow_id] = {"status": "running", "data": {}}
        
        try:
            if workflow_id == "log_summarization":
                # Example of a specific workflow
                agent_id = "log_summarization"
                task_data = workflow_data.get("task_data")
                
                self.logger.info(f"Executing workflow {workflow_id} with agent {agent_id}")
                
                # Execute the agent task
                result = await self._run_agent_task(agent_id, task_data)
                
                # Update workflow status
                self.active_workflows[workflow_id]["status"] = "completed"
                self.active_workflows[workflow_id]["result"] = result
                
        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            self.active_workflows[workflow_id]["status"] = "failed"
            self.active_workflows[workflow_id]["error"] = str(e)
            raise
            
    async def _run_agent_task(self, agent_id: str, task_data: Dict[str, Any]):
        """Execute a task with a specific agent."""
        agent = self.agent_manager.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
            
        # Execute agent task
        result = await asyncio.to_thread(agent.run, task_data)
        return result
        
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a workflow."""
        if workflow_id not in self.active_workflows:
            return {"status": "not_found"}
        return self.active_workflows[workflow_id]