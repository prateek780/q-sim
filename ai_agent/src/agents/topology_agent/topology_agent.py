from logging import getLogger
import traceback
from typing import Any, Dict, Union

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_structured_chat_agent, AgentExecutor

from ai_agent.src.agents.base.base_agent import AgentTask, BaseAgent
from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.agents.topology_agent.prompt import TOPOLOGY_OPTIMIZER_PROMPT
from ai_agent.src.agents.topology_agent.structure import OptimizeTopologyOutput, OptimizeTopologyRequest
from ai_agent.src.consts.agent_type import AgentType
from ai_agent.src.exceptions.llm_exception import LLMError
from data.models.topology.world_model import WorldModal


class TopologyAgent(BaseAgent):
    logger = getLogger(__name__)

    def __init__(self, llm=None):
        super().__init__(
            agent_id=AgentType.TOPOLOGY_DESIGNER,
            description=f"""
                A topology designer agent that helps in designing and optimizing network topologies.
                This can either synthesize a new topology or optimize an existing one.
            """
        )

        self.llm: ChatOpenAI = llm
    
    def _register_tasks(self):
        return {
            AgentTaskType.OPTIMIZE_TOPOLOGY: AgentTask(
                task_id=AgentTaskType.OPTIMIZE_TOPOLOGY,
                description="Optimize an existing network topology based on generic principles or optional instructions.",
                input_schema=OptimizeTopologyRequest,
                output_schema=OptimizeTopologyOutput,
                examples=EXAMPLES,
            ),
        }

    async def update_topology(self, input_data: Union[Dict[str, Any], OptimizeTopologyRequest]):
        if isinstance(input_data, Dict):
            # Implement the logic to optimize the topology based on the provided instructions
            input_data = OptimizeTopologyRequest(input_data)
        
        
        
        parser = PydanticOutputParser(pydantic_object=OptimizeTopologyOutput)
        format_instructions = parser.get_format_instructions()

        
        prompt = ChatPromptTemplate.from_template(TOPOLOGY_OPTIMIZER_PROMPT)

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
                agent_input = {
                    "world_id": input_data.world_id,
                    "optional_instructions": input_data.optional_instructions or "None provided. Apply general optimization principles.", # Provide default text if None
                    "format_instructions": format_instructions,
                    "world_instructions": WorldModal.schema_for_fields(),
                    "input": f"Optimize topology for world {input_data.world_id} with instructions: {input_data.optional_instructions or 'default principles'}"
                }
                result = agent_executor.invoke(agent_input)
                final_output_data = result.get("output")


                if isinstance(final_output_data, dict):
                    # Parse the dictionary into the Pydantic model for validation
                    parsed_output = OptimizeTopologyOutput.model_validate(final_output_data)
                    print("--- Optimization Proposal Generated ---")
                    return parsed_output
                else:
                    print(f"ERROR: Agent returned unexpected final output format: {type(final_output_data)}")
                    print(f"Raw output: {final_output_data}")
                    # Attempt to parse if it's a string containing JSON (shouldn't happen with correct prompt)
                    if isinstance(final_output_data, str):
                        try:
                            parsed_output = OptimizeTopologyOutput.model_validate_json(final_output_data)
                            print("--- Optimization Proposal Generated (Parsed from String) ---")
                            return parsed_output
                        except Exception as e_parse:
                            print(f"ERROR: Failed to parse string output as JSON: {e_parse}")

                    return None # Failed
            except Exception as e:
                traceback.print_exc()
                self.logger.exception(f"Exception during agent execution!")
                raise LLMError(f"Error during agent execution: {e}")
        else:
            raise Exception("LLM not available, logs invalid, or no tools defined")