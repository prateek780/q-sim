import json
import logging
import os
import traceback
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.output_parsers import PydanticOutputParser
from langchain.tools import StructuredTool
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain.callbacks import StdOutCallbackHandler, LangChainTracer

import re

from ai_agent.src.agents.enums import AgentTaskType
from ai_agent.src.agents.examples import EXAMPLES
from ai_agent.src.agents.prompt import get_system_prompt
from ai_agent.src.agents.structures import ExtractPattersInput, LogSummaryOutput, SummarizeInput
from ai_agent.src.exceptions.llm_exception import LLMError
from data.embedding.embedding_util import EmbeddingUtil
from data.embedding.langchain_integration import SimulationLogRetriever
from data.embedding.vector_log import VectorLogEntry
from data.models.simulation.simulation_model import get_simulation
from data.models.topology.world_model import get_topology_from_redis
from .base_agent import BaseAgent, AgentTask



class LogSummarizationAgent(BaseAgent):
    """Agent for summarizing and analyzing system logs."""
    logger = logging.getLogger(__name__)
    
    def __init__(self, llm=None):
        super().__init__(
            agent_id="log_summarizer",
            description="Analyzes and summarizes system logs to extract key insights and patterns",
        )
        self.llm: ChatOpenAI = llm
        self.tools = [
            StructuredTool.from_function(
                func=self._get_relevant_logs,
                name="_get_relevant_logs",
                description="Retrieve relevant logs for analysis",
            ),
            StructuredTool.from_function(
                func=self._get_topology_by_simulation,
                name="_get_topology_by_simulation",
                description="Retrieves the detailed network topology configuration for a given simulation ID.",
            ),
        ]
        self.redis_log = SimulationLogRetriever()
        self.embedding_util = EmbeddingUtil()

    def _register_tasks(self) -> Dict[str, AgentTask]:
        """Register all tasks this agent can perform."""
        return {
            AgentTaskType.LOG_SUMMARIZATION: AgentTask(
                task_id=AgentTaskType.LOG_SUMMARIZATION,
                description="Summarize log entries to identify key issues and patterns",
                input_schema=SummarizeInput,
                output_schema=LogSummaryOutput,
                examples=EXAMPLES,
            ),
        }
    
    def _get_relevant_logs(self, simulation_id: str, query: Optional[str] = '*', limit: int=100):
        """Retrieve logs relevant to a question using vector similarity"""
        if query == "*":
            return VectorLogEntry.get_by_simulation(simulation_id)

        # Generate embedding for query
        query_embedding = self.embedding_util.generate_embedding(query)

        # Search for relevant logs
        return VectorLogEntry.search_similar(
            query_embedding, top_k=limit, filters={"simulation_id": simulation_id}
        )

    def _get_topology_by_simulation(self, simulation_id: str):
        """Retrieve the topology of a simulation using vector similarity"""
        simulation = get_simulation(simulation_id)
        if not simulation:
            return None

        world = get_topology_from_redis(simulation.world_id)
        if not world:
            return None
        return world.model_dump()

    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a direct message to this agent."""
        content = message.get("content", "")

        # Determine appropriate task based on message content
        if "summarize" in content.lower() or "summary" in content.lower():
            task_id = AgentTaskType.LOG_SUMMARIZATION
        elif "pattern" in content.lower() or "anomaly" in content.lower():
            task_id = AgentTaskType.EXTRACT_PATTERNS
        else:
            task_id = AgentTaskType.LOG_SUMMARIZATION  # Default task

        # Extract log entries from message if present
        log_entries = self._extract_logs_from_message(content)

        # Run the appropriate task
        result = await self.run(task_id, {"logs": log_entries})
        return result

    def _extract_logs_from_message(self, content: str) -> List[str]:
        """Extract log entries from message content."""
        # Simple extraction logic - improve as needed
        lines = content.split("\n")
        log_pattern = r"^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}"
        return [line for line in lines if re.match(log_pattern, line)]

    async def run(
        self, task_id: AgentTaskType, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a specific task with the given input data."""
        # Validate input
        validated_input = self.validate_input(task_id, input_data)

        if task_id == AgentTaskType.LOG_SUMMARIZATION:
            result = await self._summarize_logs(validated_input)
        elif task_id == AgentTaskType.EXTRACT_PATTERNS:
            result = await self._extract_patterns(validated_input)
        else:
            raise ValueError(f"Task {task_id} not supported")

        # Validate output
        return self.validate_output(task_id, result)

    async def _summarize_logs(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize log entries."""
        simulation_id = input_data.get("simulation_id")
        if simulation_id:
            logs = self._get_relevant_logs(simulation_id, "*", 5)
        else:
            logs = input_data.get("logs", [])
        max_entries = input_data.get("max_entries", 100)
        focus_components = input_data.get("focus_components")
        user_query = input_data.get("message")

        # Process a limited number of entries
        logs = logs[:max_entries]

        output_parser = PydanticOutputParser(pydantic_object=LogSummaryOutput)

        system_template = get_system_prompt()

        system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )
        human_message_prompt = HumanMessagePromptTemplate.from_template(
            "{input}\n\n{agent_scratchpad}"
        )
        prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )
        prompt = prompt.partial(
            answer_instructions=output_parser.get_format_instructions()
        )

        if self.llm and logs and self.tools:
            llm_with_tools = self.llm.bind_tools(self.tools)
            
            agent = create_structured_chat_agent(llm_with_tools, self.tools, prompt)
            
            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                return_intermediate_steps=True,
                handle_parsing_errors=True,
                max_iterations=5,
                early_stopping_method="force",
            )

            try:
                response = await agent_executor.ainvoke(
                    {
                        "simulation_id": simulation_id,
                        "logs": json.dumps([logs[0], logs[-1]]),
                        'total_logs': len(logs),
                        "input": user_query or f"Summarize logs for simulation ID: {simulation_id}",
                    }
                )
                if "output" in response:
                    return response["output"]
                else:
                    return {"summary": "Failed to generate structured output."}
            except Exception as e:
                traceback.print_exc()
                self.logger.exception(f"Exception during agent execution!")
                raise LLMError(f"Error during agent execution: {e}")
        else:
            raise Exception("LLM not available, logs invalid, or no tools defined")

    async def _extract_patterns(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract recurring patterns from logs."""
        # Similar implementation to summarize but focused on patterns
        # This is a simplified version - expand as needed
        summary_result = await self._summarize_logs(input_data)

        # Add pattern-specific analysis here
        summary_result["summary_text"] = (
            "Pattern analysis: " + summary_result["summary_text"]
        )

        return summary_result
