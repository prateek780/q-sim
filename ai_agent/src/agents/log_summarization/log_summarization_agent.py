import json
import logging
import traceback
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from langchain_openai import ChatOpenAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_structured_chat_agent, AgentExecutor

import re

from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.agents.log_summarization.examples import LOG_SUMMARY_EXAMPLES
from ai_agent.src.agents.log_summarization.prompt import get_system_prompt
from ai_agent.src.agents.log_summarization.structures import LogSummaryOutput, SummarizeInput
from ai_agent.src.consts.agent_type import AgentType
from ai_agent.src.exceptions.llm_exception import LLMError
from data.embedding.embedding_util import EmbeddingUtil
from data.embedding.langchain_integration import SimulationLogRetriever
from ai_agent.src.agents.base.base_agent import BaseAgent, AgentTask



class LogSummarizationAgent(BaseAgent):
    """Agent for summarizing and analyzing system logs."""
    logger = logging.getLogger(__name__)
    
    def __init__(self, llm=None):
        super().__init__(
            agent_id=AgentType.LOG_SUMMARIZER,
            description="Analyzes and summarizes system logs to extract key insights and patterns",
        )
        self.llm: ChatOpenAI = llm

    def _register_tasks(self) -> Dict[str, AgentTask]:
        """Register all tasks this agent can perform."""
        return {
            AgentTaskType.LOG_SUMMARIZATION: AgentTask(
                task_id=AgentTaskType.LOG_SUMMARIZATION,
                description="Summarize log entries to identify key issues and patterns",
                input_schema=SummarizeInput,
                output_schema=LogSummaryOutput,
                examples=LOG_SUMMARY_EXAMPLES,
            ),
        }

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
            logs = self._get_relevant_logs(simulation_id, "*")
        else:
            logs = input_data.get("logs", [])

        if not logs:
            raise HTTPException(status_code=400, detail={"message": "No logs provided", 'simulation_id': simulation_id})

        focus_components = input_data.get("focus_components")
        user_query = input_data.get("message")

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

        if self.llm and self.tools:
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
