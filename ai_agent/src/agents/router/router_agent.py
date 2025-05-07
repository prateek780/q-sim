import logging
import traceback
from typing import Any, Dict
from ai_agent.src.agents.base.base_agent import AgentTask, BaseAgent
from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.agents.router.examples import ROUTER_AGENT_EXAMPLES
from ai_agent.src.agents.router.prompt import PROMPT_TEMPLATE
from ai_agent.src.agents.router.structure import RoutingInput, RoutingOutput
from ai_agent.src.consts.agent_type import AgentType
from ai_agent.src.exceptions.llm_exception import LLMError

from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_structured_chat_agent, AgentExecutor

from data.models.conversation.conversation_ops import get_conversation_history


class RouterAgent(BaseAgent):
    logger = logging.getLogger(__name__)

    def __init__(self, llm=None):
        super().__init__(
            agent_id=AgentType.ORCHESTRATOR,
            description="Routes messages to the appropriate agent based on content",
        )
        self.llm = llm

    def _register_tasks(self) -> Dict[str, AgentTask]:
        return {
            AgentTaskType.ROUTING: AgentTask(
                name="Route Message",
                task_id=AgentTaskType.ROUTING,
                description="Routes messages to the appropriate agent based on content",
                input_schema=RoutingInput,
                output_schema=RoutingOutput,
                examples=ROUTER_AGENT_EXAMPLES,
            )
        }

    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        pass

    async def run(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        print(list(input_data.keys()))
        validated_input = self.validate_input(task_id, input_data)

        if task_id == AgentTaskType.ROUTING:
            result = await self.route_message(validated_input)
        else:
            raise ValueError(f"Invalid task ID: {task_id}")

        return self.validate_output(task_id, result)

    async def route_message(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Route the message to the appropriate agent based on its content."""

        user_query = input_data.get("user_query")
        agent_details = input_data.get("agent_details", {})
        conversation_id = user_query.get("conversation_id")
        if not user_query or not agent_details or not conversation_id:
            raise ValueError(f"User query and agent details are required. {input_data}")

        last_5_messages = get_conversation_history(conversation_id, limit=5)

        output_parser = PydanticOutputParser(pydantic_object=RoutingOutput)

        system_message_prompt = SystemMessagePromptTemplate.from_template(
            PROMPT_TEMPLATE
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
                        "query": user_query,
                        "agent_details": agent_details,
                        "input": user_query,
                        "last_5_messages": "\n".join(
                            map(lambda x: x.model_dump_json(), last_5_messages)
                        ),
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
            raise Exception("LLM not available or no tools defined")
