from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import re
import asyncio
from .base_agent import BaseAgent, AgentTask


class LogEntry(BaseModel):
    """Schema for a log entry."""

    # TODO: This will evolve according to log format
    timestamp: str
    level: str
    component: str
    message: str
    metadata: Optional[Dict[str, Any]] = None


class LogInput(BaseModel):
    """Input schema for log summarization tasks."""

    # TODO: This will evolve according to log format and requirement
    logs: List[str]
    max_entries: Optional[int] = 100
    focus_components: Optional[List[str]] = None
    time_range: Optional[Dict[str, str]] = None


class SummaryOutput(BaseModel):
    """Output schema for log summary."""

    error_count: int
    warning_count: int
    key_issues: List[str]
    component_summary: Dict[str, Dict[str, int]]
    summary_text: str


class LogSummarizationAgent(BaseAgent):
    """Agent for summarizing and analyzing system logs."""

    def __init__(self, llm=None):
        super().__init__(
            agent_id="log_summarizer",
            description="Analyzes and summarizes system logs to extract key insights and patterns",
        )
        self.llm = llm
        print("LogSummarizationAgent initialized with LLM:", llm)

    def _register_tasks(self) -> Dict[str, AgentTask]:
        """Register all tasks this agent can perform."""
        return {
            "summarize": AgentTask(
                task_id="summarize",
                description="Summarize log entries to identify key issues and patterns",
                input_schema=LogInput,
                output_schema=SummaryOutput,
                # TODO: Update this example, I picked these logs from internet
                examples=[
                    {
                        "input": {
                            "logs": [
                                "2023-10-01 14:23:05 ERROR topology_designer Failed to analyze network: Invalid format",
                                "2023-10-01 14:23:10 WARN congestion_monitor High packet loss detected in node N7",
                            ],
                            "max_entries": 50,
                        },
                        "output": {
                            "error_count": 1,
                            "warning_count": 1,
                            "key_issues": [
                                "Topology designer failed due to format issues",
                                "High packet loss in node N7",
                            ],
                            "component_summary": {
                                "topology_designer": {"ERROR": 1},
                                "congestion_monitor": {"WARN": 1},
                            },
                            "summary_text": "The system encountered format issues in the topology designer and packet loss in node N7.",
                        },
                    }
                ],
            ),
            "extract_patterns": AgentTask(
                task_id="extract_patterns",
                description="Extract recurring patterns and anomalies from logs",
                input_schema=LogInput,
                output_schema=SummaryOutput,
                examples=[],
            ),
        }

    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a direct message to this agent."""
        content = message.get("content", "")

        # Determine appropriate task based on message content
        if "summarize" in content.lower() or "summary" in content.lower():
            task_id = "summarize"
        elif "pattern" in content.lower() or "anomaly" in content.lower():
            task_id = "extract_patterns"
        else:
            task_id = "summarize"  # Default task

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

    async def run(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task with the given input data."""
        # Validate input
        validated_input = self.validate_input(task_id, input_data)

        if task_id == "summarize":
            result = await self._summarize_logs(validated_input)
        elif task_id == "extract_patterns":
            result = await self._extract_patterns(validated_input)
        else:
            raise ValueError(f"Task {task_id} not supported")

        # Validate output
        return self.validate_output(task_id, result)

    async def _summarize_logs(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize log entries."""
        logs = input_data.get("logs", [])
        max_entries = input_data.get("max_entries", 100)
        focus_components = input_data.get("focus_components")

        # Process a limited number of entries
        logs = logs[:max_entries]

        # Parse logs into structured format
        parsed_logs = []
        for log in logs:
            try:
                parts = log.split(" ", 3)
                if len(parts) >= 4:
                    date, time, level, rest = parts
                    component_msg = rest.split(" ", 1)
                    component = component_msg[0]
                    message = component_msg[1] if len(component_msg) > 1 else ""

                    parsed_logs.append(
                        {
                            "timestamp": f"{date} {time}",
                            "level": level,
                            "component": component,
                            "message": message,
                        }
                    )
            except Exception:
                # Skip entries that don't match expected format
                continue

        # Filter by components if specified
        if focus_components:
            parsed_logs = [
                log for log in parsed_logs if log["component"] in focus_components
            ]

        # Count errors and warnings
        error_count = sum(1 for log in parsed_logs if log["level"] == "ERROR")
        warning_count = sum(1 for log in parsed_logs if log["level"] == "WARN")

        # Analyze by component
        component_summary = {}
        for log in parsed_logs:
            component = log["component"]
            level = log["level"]

            if component not in component_summary:
                component_summary[component] = {}

            if level not in component_summary[component]:
                component_summary[component][level] = 0

            component_summary[component][level] += 1

        # Extract key issues with LLM if available
        key_issues = []
        summary_text = ""

        if self.llm and parsed_logs:
            # Use LLM to extract key issues
            error_logs = [
                f"{log['timestamp']} {log['level']} {log['component']} {log['message']}\n"
                for log in parsed_logs
                if log["level"] in ["ERROR", "WARN"]
            ]
            if error_logs:
                prompt = f"""
                Analyze these log entries and identify the key issues:
                
                {error_logs}
                
                Extract up to 5 key issues from these logs. Be concise.
                """

                try:
                    print("Prompt for LLM:", prompt)
                    response = await self.llm.agenerate([prompt])
                    issues_text = response.generations[0][0].text
                    key_issues = [
                        issue.strip()
                        for issue in issues_text.split("\n")
                        if issue.strip()
                    ]

                    # Also generate summary text
                    summary_prompt = f"""
                    Provide a one-sentence summary of these system logs:
                    
                    - {error_count} errors and {warning_count} warnings
                    - Components with issues: {', '.join(component_summary.keys())}
                    - Key issues: {', '.join(key_issues[:3])}
                    """

                    summary_response = await self.llm.agenerate([summary_prompt])
                    summary_text = summary_response.generations[0][0].text.strip()

                except Exception as e:
                    # Fallback if LLM fails
                    key_issues = [
                        f"{log['component']}: {log['message']}"
                        for log in parsed_logs[:5]
                        if log["level"] in ["ERROR", "WARN"]
                    ]
                    summary_text = f"Found {error_count} errors and {warning_count} warnings across {len(component_summary)} components."
        else:
            # Manual extraction without LLM
            key_issues = [
                f"{log['component']}: {log['message']}"
                for log in parsed_logs[:5]
                if log["level"] in ["ERROR", "WARN"]
            ]
            summary_text = f"Found {error_count} errors and {warning_count} warnings across {len(component_summary)} components."

        return {
            "error_count": error_count,
            "warning_count": warning_count,
            "key_issues": key_issues[:5],  # Limit to top 5 issues
            "component_summary": component_summary,
            "summary_text": summary_text,
        }

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
