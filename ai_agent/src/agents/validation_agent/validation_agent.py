from logging import getLogger
import traceback
from typing import Any, Dict, Union

from langchain_openai import ChatOpenAI
from ai_agent.src.agents.base.base_agent import AgentTask, BaseAgent
from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.agents.topology_agent.structure import SynthesisTopologyOutput
from ai_agent.src.agents.validation_agent.prompt import TOPOLOGY_VALIDATION_AGENT_PROMPT
from ai_agent.src.agents.validation_agent.structures import TopologyValidationResult, ValidationStatus
from ai_agent.src.agents.validation_agent.world_validation import validate_world_topology_static_logic
from ai_agent.src.consts.agent_type import AgentType
from langchain_core.output_parsers import PydanticOutputParser
from ai_agent.src.exceptions.llm_exception import LLMError
from data.models.topology.world_model import WorldModal

from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.agents import create_structured_chat_agent, AgentExecutor

class ValidationAgent(BaseAgent):
    logger = getLogger(__name__)

    def __init__(self, llm: ChatOpenAI = None):
        super().__init__(
            agent_id=AgentType.VALIDATION_AGENT,
            description=f"""
                A validation agent that helps in validating network topologies.
                This can check if a topology meets certain criteria or is valid.
                """,
        )
        self.llm = llm

    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        pass


    def _register_tasks(self):
        return {
            AgentTaskType.VALIDATE_TOPOLOGY: AgentTask(
                task_id=AgentTaskType.VALIDATE_TOPOLOGY,
                description="Validate an existing network topology based on specific criteria or instructions.",
                input_schema=SynthesisTopologyOutput,
                output_schema=TopologyValidationResult,
                examples=[],
            ),
        }

    async def run(
        self, task_id: AgentTaskType, input_data: Dict[str, Any]
    ):
        if task_id == AgentTaskType.VALIDATE_TOPOLOGY:
            # Implement the logic to validate the topology
            result = self.validate_generated_topology(input_data["generate_response"])
        else:
            raise ValueError(f"Unsupported task type: {task_id}")
        
        # Validate output
        validated_output =  self.validate_output(task_id, result)

        return validated_output
        

    def validate_generated_topology(self, generate_response: Union[SynthesisTopologyOutput, Dict[str, Any]]) -> TopologyValidationResult:
        if isinstance(generate_response, Dict):
            generate_response = SynthesisTopologyOutput(**generate_response)

        errors = validate_world_topology_static_logic(generate_response.generated_topology)
        if errors:
            return TopologyValidationResult(errors=errors, static_errors=ValidationStatus.FAILED)
        

        parser = PydanticOutputParser(pydantic_object=TopologyValidationResult)
        format_instructions = parser.get_format_instructions()

        system_message_prompt = SystemMessagePromptTemplate.from_template(
            TOPOLOGY_VALIDATION_AGENT_PROMPT
        )

        human_message_prompt = HumanMessagePromptTemplate.from_template(
            "{input}\n\n{agent_scratchpad}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        if self.llm:
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
                agent_input = {
                    'world_instructions': WorldModal.schema_for_fields(),
                    "original_user_query": generate_response.input_query,
                    "generated_topology_json": generate_response.generated_topology.model_dump_json(),
                    "generating_agent_thought_process": generate_response.thought_process,
                    'answer_instructions':format_instructions,
                    'input': f'Validate the topology and provide feedback for the generating agent.',
                }
                result = agent_executor.invoke(agent_input)
                final_output_data = result.get("output")

                if isinstance(final_output_data, dict):
                    # Parse the dictionary into the Pydantic model for validation
                    parsed_output = TopologyValidationResult.model_validate(
                        final_output_data
                    )
                    print("--- Synthesis Topology Proposal Generated ---")
                    return parsed_output
                else:
                    print(
                        f"ERROR: Agent returned unexpected final output format: {type(final_output_data)}"
                    )
                    print(f"Raw output: {final_output_data}")
                    # Attempt to parse if it's a string containing JSON (shouldn't happen with correct prompt)
                    if isinstance(final_output_data, str):
                        try:
                            parsed_output = TopologyValidationResult.model_validate_json(
                                final_output_data
                            )
                            print(
                                "--- Optimization Proposal Generated (Parsed from String) ---"
                            )
                            return parsed_output
                        except Exception as e_parse:
                            print(
                                f"ERROR: Failed to parse string output as JSON: {e_parse}"
                            )

                    return None  # Failed
            except Exception as e:
                traceback.print_exc()
                self.logger.exception(f"Exception during agent execution!")
                raise LLMError(f"Error during agent execution: {e}")