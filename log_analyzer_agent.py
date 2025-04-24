#!/usr/bin/env python3
"""
Quantum-Classical Network Log Analyzer Agent

This script analyzes structured log files to trace message paths and
component activities through a quantum-classical network simulation.
"""

import json
import re
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union

# Try to import Groq or fallback to local implementation
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    print("Warning: Groq package not found. Using LangChain fallback.")
    GROQ_AVAILABLE = False
    try:
        from langchain_groq import ChatGroq
        from langchain.agents import Tool, initialize_agent, AgentType
        from langchain.memory import ConversationBufferMemory
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        print("Error: Neither groq nor langchain_groq found. Please install with:")
        print("pip install groq")
        print("or")
        print("pip install langchain-groq")
        LANGCHAIN_AVAILABLE = False

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Simple fallback for dotenv
    def simple_load_dotenv():
        """Simple implementation to load .env file"""
        if not os.path.exists('.env'):
            return
        
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    simple_load_dotenv()

# Get Groq API key from environment variables
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY not found in environment variables or .env file.")


class LogAnalyzer:
    """Analyzes structured logs from a quantum-classical network simulation"""
    
    def __init__(self, log_file_path: str = "json_validation_output/corrected_logs.json"):
        """
        Initialize the log analyzer
        
        Args:
            log_file_path: Path to the structured logs JSON file
        """
        # Always use corrected_logs.json for consistency
        self.log_file_path = "json_validation_output/corrected_logs.json"
        if log_file_path != "json_validation_output/corrected_logs.json":
            print(f"Note: Using 'json_validation_output/corrected_logs.json' instead of '{log_file_path}' for consistency")
            
        self.logs = []
        self.components = set()
        self.event_types = set()
        self.load_logs()
    
    def load_logs(self) -> bool:
        """
        Load and parse the structured logs file
        
        Returns:
            True if logs were successfully loaded, False otherwise
        """
        try:
            with open(self.log_file_path, 'r') as f:
                data = json.load(f)
                
            if 'logs' in data and isinstance(data['logs'], list):
                self.logs = data['logs']
                
                # Extract component names and event types
                for log in self.logs:
                    if 'component' in log:
                        self.components.add(log['component'])
                    if 'event_type' in log:
                        self.event_types.add(log['event_type'])
                        
                print(f"Loaded {len(self.logs)} log entries.")
                return True
            else:
                print("Error: Invalid log format. Expected 'logs' array.")
                return False
                
        except FileNotFoundError:
            print(f"Error: Log file '{self.log_file_path}' not found.")
            return False
        except json.JSONDecodeError:
            print(f"Error: Log file '{self.log_file_path}' is not valid JSON.")
            return False
    
    def get_logs_by_component(self, component_name: str) -> List[Dict[str, Any]]:
        """
        Get all logs for a specific component
        
        Args:
            component_name: Name of the component to filter by
            
        Returns:
            List of log entries for the specified component
        """
        return [log for log in self.logs if log.get('component') == component_name]
    
    def get_logs_by_event_type(self, event_type: str) -> List[Dict[str, Any]]:
        """
        Get all logs with a specific event type
        
        Args:
            event_type: Event type to filter by
            
        Returns:
            List of log entries with the specified event type
        """
        return [log for log in self.logs if log.get('event_type') == event_type]
    
    def get_logs_by_time_range(self, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """
        Get logs within a specific time range
        
        Args:
            start_time: Start time in format HH:MM:SS
            end_time: End time in format HH:MM:SS
            
        Returns:
            List of log entries within the specified time range
        """
        try:
            start = datetime.strptime(start_time, "%H:%M:%S")
            end = datetime.strptime(end_time, "%H:%M:%S")
            
            return [
                log for log in self.logs 
                if 'time' in log and datetime.strptime(log['time'], "%H:%M:%S") >= start 
                and datetime.strptime(log['time'], "%H:%M:%S") <= end
            ]
        except ValueError:
            print("Error: Invalid time format. Please use HH:MM:SS format.")
            return []
    
    def search_logs(self, query: str) -> List[Dict[str, Any]]:
        """
        Search logs for a specific query string
        
        Args:
            query: Query string to search for
            
        Returns:
            List of log entries containing the query string
        """
        return [
            log for log in self.logs 
            if query.lower() in json.dumps(log).lower()
        ]
    
    def trace_message(self, message_content: str, source: Optional[str] = None, 
                      destination: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Trace a message through the network
        
        Args:
            message_content: Content of the message to trace
            source: Optional source component
            destination: Optional destination component
            
        Returns:
            List of log entries related to the message path
        """
        # Clean up message content for better matching
        message_content = message_content.strip()
        message_pattern = re.escape(message_content)
        
        # Find initial send event with the message content
        send_logs = [log for log in self.logs if 
                   ('send' in log.get('event_type', '').lower() or 'sent' in log.get('event', '').lower()) and
                   re.search(f"['\"]\\s*{message_pattern}\\s*['\"]", log.get('event', '').lower())]
        
        # If no exact match, try broader search
        if not send_logs:
            send_logs = [log for log in self.logs if 
                       ('send' in log.get('event_type', '').lower() or 'sent' in log.get('event', '').lower()) and
                       message_pattern in log.get('event', '').lower()]
        
        # Filter by source if provided
        if source and send_logs:
            send_logs = [log for log in send_logs if source.lower() in log.get('component', '').lower()]
        
        # If no send events found, try searching all logs
        if not send_logs:
            return self.search_logs(message_content)
        
        # Start with the initial send event
        initial_log = send_logs[0]
        
        # Determine sender and intended receiver
        sender = initial_log.get('component')
        receiver = None
        
        # Try to extract the intended receiver from the event
        event_text = initial_log.get('event', '')
        receiver_match = re.search(r'to ([A-Za-z0-9_-]+)', event_text)
        if receiver_match:
            receiver = receiver_match.group(1)
        
        # Create a key events list to track important log entries
        key_events = {
            'send': initial_log,
            'quantum_initiate': None,
            'encrypt': None,
            'qkd_complete': None,
            'decrypt': None,
            'receive': None
        }
        
        # Track components that have handled the message
        handled_components = {sender}
        component_sequence = [sender]
        
        # Find all logs related to this message
        # Sort logs by time to ensure chronological order
        sorted_logs = sorted(self.logs, key=lambda x: x.get('time', '00:00:00'))
        
        # Find the index of the initial log
        start_index = 0
        for i, log in enumerate(sorted_logs):
            if log.get('log_id') == initial_log.get('log_id'):
                start_index = i
                break
        
        # Start with the initial log
        relevant_logs = [initial_log]
        
        # First pass: get all logs that mention message encryption/decryption
        encryption_logs = []
        decryption_logs = []
        quantum_initiation_logs = []
        qkd_completion_logs = []
        
        # Look for specific log patterns for encryption/decryption
        for log in sorted_logs[start_index+1:]:
            event = log.get('event', '').lower()
            
            # Check for encryption events
            if ('encrypt' in event):
                if message_pattern in event or 'bytearray' in event:
                    encryption_logs.append(log)
                    if not key_events['encrypt']:
                        key_events['encrypt'] = log
                
            # Check for decryption events
            elif ('decrypt' in event):
                if message_pattern in event or 'bytearray' in event:
                    decryption_logs.append(log)
                    if not key_events['decrypt']:
                        key_events['decrypt'] = log
                
            # Check for QKD initiation
            elif ('initiating qkd' in event or 'initiating quantum key' in event):
                quantum_initiation_logs.append(log)
                if not key_events['quantum_initiate']:
                    key_events['quantum_initiate'] = log
                
            # Check for QKD completion
            elif ('completed qkd' in event or 'completed quantum key' in event or 
                  'established a shared key' in event):
                qkd_completion_logs.append(log)
                if not key_events['qkd_complete']:
                    key_events['qkd_complete'] = log
        
        # Keep track of receiver logs for determining the final destination
        receiver_logs = []
        if receiver:
            receiver_logs = [log for log in sorted_logs if 
                           log.get('component') == receiver and 
                           ('received data' in log.get('event', '').lower() or 'received message' in log.get('event', '').lower()) and
                           message_pattern in log.get('event', '').lower()]
            if receiver_logs:
                key_events['receive'] = receiver_logs[0]
                
        # Process logs after the initial send
        for current_log in sorted_logs[start_index+1:]:
            current_component = current_log.get('component')
            current_event = current_log.get('event', '').lower()
            
            # Check if this log is related to our message
            is_relevant = False
            
            # Exact message content appears in the event
            if re.search(f"['\"]\\s*{message_pattern}\\s*['\"]", current_event):
                is_relevant = True
            
            # Message is referenced in this event
            elif message_pattern in current_event:
                is_relevant = True
            
            # Encryption and decryption logs are always relevant
            elif current_log in encryption_logs or current_log in decryption_logs:
                is_relevant = True
                
            # Quantum key distribution is relevant
            elif current_log in quantum_initiation_logs or current_log in qkd_completion_logs:
                is_relevant = True
            
            # Log explicitly mentions handling a packet related to our message path
            elif ('packet' in current_event and 
                  (('from ' + sender.lower()) in current_event or
                   (receiver and ('to ' + receiver.lower()) in current_event) or
                   any(comp.lower() in current_event for comp in component_sequence))):
                is_relevant = True
            
            # Component is part of the quantum network and previous component was quantum
            elif (current_component.startswith(('Quantum', 'QC_Router')) and 
                  any(comp.startswith(('Quantum', 'QC_Router')) for comp in component_sequence[-1:])):
                is_relevant = True
            
            # Routers involved in the message path
            elif (current_component.startswith('ClassicalRouter') and 
                  ('routing' in current_event or 'received packet' in current_event) and
                  (receiver and receiver.lower() in current_event.lower())):
                is_relevant = True
                
            # QKD operations associated with adapters in our path
            elif ('qkd' in current_event.lower() or 'quantum key' in current_event.lower()) and (
                  current_component in component_sequence or 
                  any(comp.startswith(('Quantum', 'QC_Router')) for comp in component_sequence)):
                is_relevant = True
            
            # Component is our intended receiver and receives data
            elif (receiver and current_component == receiver and 
                  ('received' in current_event and ('data' in current_event or message_pattern in current_event))):
                is_relevant = True
                key_events['receive'] = current_log
            
            if is_relevant and current_component not in handled_components:
                relevant_logs.append(current_log)
                handled_components.add(current_component)
                component_sequence.append(current_component)
                
                # Check if we've reached the final destination component receiving the message
                if (destination and current_component == destination and 
                    'received data' in current_event and message_pattern in current_event):
                    key_events['receive'] = current_log
                    break
                    
                # Or if we've reached the originally intended receiver
                if (receiver and current_component == receiver and 
                    'received data' in current_event and message_pattern in current_event):
                    key_events['receive'] = current_log
                    break
        
        # Make sure we include all key events in our trace
        for event_type, log in key_events.items():
            if log and log not in relevant_logs:
                relevant_logs.append(log)
                
        # Add any encryption/decryption logs we might have missed
        for log in encryption_logs + decryption_logs:
            if log not in relevant_logs:
                relevant_logs.append(log)
        
        # Sort the relevant logs by time to ensure chronological order
        relevant_logs = sorted(relevant_logs, key=lambda x: x.get('time', '00:00:00'))
        
        return relevant_logs
    
    def format_message_trace(self, logs: List[Dict[str, Any]]) -> str:
        """
        Format the message trace logs into a human-readable format
        
        Args:
            logs: List of log entries to format
            
        Returns:
            Formatted string with the message trace
        """
        if not logs:
            return "No logs found for this message trace."
        
        result = []
        
        for i, log in enumerate(logs, 1):
            log_id = log.get('log_id', f"LOG_{i}")
            component = log.get('component', 'Unknown')
            time = log.get('time', 'Unknown')
            event = log.get('event', 'Unknown')
            event_type = log.get('event_type', 'Unknown')
            
            # Create a short description based on the event and component
            description = self._get_event_description(event, component, event_type)
            
            result.append(f"{i}. [{log_id}] {time} - {component}: {description}")
        
        return "\n".join(result)
    
    def _get_event_description(self, event: str, component: str, event_type: str) -> str:
        """
        Generate a short description of an event
        
        Args:
            event: Full event text
            component: Component name
            event_type: Event type
            
        Returns:
            Short description of the event
        """
        # Creation events
        if event_type == 'creation':
            return "Component created"
        
        # Send events
        if event_type == 'send' or 'sent data' in event.lower() or 'sending' in event.lower():
            # Try to extract destination and message
            dest_match = re.search(r'to ([A-Za-z0-9_-]+)', event)
            message_match = re.search(r"['\"](.*?)['\"]", event)
            next_hop_match = re.search(r'next hop: ([A-Za-z0-9_-]+)', event)
            
            # Build a descriptive message
            if message_match:
                # Get the full message or limit it to first 40 chars if too long
                message = message_match.group(1)
                message = message if len(message) <= 40 else message[:37] + "..."
                
                if dest_match and next_hop_match:
                    return f"Sends message '{message}' to {dest_match.group(1)} via {next_hop_match.group(1)}"
                elif dest_match:
                    return f"Sends message '{message}' to {dest_match.group(1)}"
                else:
                    return f"Sends message '{message}'"
            elif dest_match:
                return f"Sends data to {dest_match.group(1)}"
            else:
                return "Sends data"
        
        # Receive events
        if event_type == 'receive' or 'received' in event.lower():
            if 'received packet' in event.lower():
                # Extract source, destination, and data
                src_match = re.search(r'from ([A-Za-z0-9_-]+)', event)
                dest_match = re.search(r'to ([A-Za-z0-9_-]+)', event)
                data_match = re.search(r"data ['\"](.{1,30})['\"]", event) or re.search(r"data '(.{1,30})'", event)
                
                description = "Receives packet"
                if src_match:
                    description += f" from {src_match.group(1)}"
                if dest_match:
                    description += f" to {dest_match.group(1)}"
                if data_match:
                    data = data_match.group(1)
                    if len(data) > 30:
                        data = data[:27] + "..."
                    description += f" with data '{data}'"
                
                return description
            
            if 'received data' in event.lower():
                # Try to extract message
                message_match = re.search(r"['\"](.*?)['\"]", event)
                if message_match:
                    message = message_match.group(1)
                    if len(message) > 40:
                        message = message[:37] + "..."
                    return f"Receives message '{message}'"
                else:
                    return "Receives data"
                    
            if 'received event' in event.lower():
                event_data_match = re.search(r'\{(.*?)\}', event)
                if event_data_match:
                    data = event_data_match.group(1)
                    if len(data) > 40:
                        data = data[:37] + "..."
                    return f"Receives event with data: {data}"
                return "Receives event"
            
            return "Receives data"
        
        # Routing events
        if event_type == 'routing' or 'routing' in event.lower():
            if 'routing packet' in event.lower() and 'to' in event.lower():
                # Try to extract destination
                dest_match = re.search(r'to ([A-Za-z0-9_-]+)', event)
                if dest_match:
                    return f"Routes packet to {dest_match.group(1)}"
                else:
                    return "Routes packet"
            
            return "Routes packet"
        
        # Forwarding events
        if 'forwarding' in event.lower():
            src_match = re.search(r'from ([A-Za-z0-9_-]+)', event)
            dest_match = re.search(r'to ([A-Za-z0-9_-]+)', event)
            next_hop_match = re.search(r'next hop ([A-Za-z0-9_-]+)', event) or re.search(r'via ([A-Za-z0-9_-]+)', event)
            
            description = "Forwards packet"
            if src_match:
                description += f" from {src_match.group(1)}"
            if dest_match:
                description += f" to {dest_match.group(1)}"
            if next_hop_match:
                description += f" via {next_hop_match.group(1)}"
                
            return description
        
        # QKD events
        if 'quantum' in component.lower() or 'qkd' in event.lower():
            if 'initiating' in event.lower() and 'qkd' in event.lower():
                adapter_match = re.search(r'with ([A-Za-z0-9_-]+)', event)
                if adapter_match:
                    return f"Initiates QKD with {adapter_match.group(1)}"
                return "Initiates quantum key distribution"
                
            if 'sending qubit' in event.lower():
                dest_match = re.search(r'to ([A-Za-z0-9_-]+)', event)
                if dest_match:
                    return f"Sends qubit to {dest_match.group(1)}"
                return "Sends qubit for quantum key distribution"
                
            if 'transmitting qubit' in event.lower():
                src_match = re.search(r'from ([A-Za-z0-9_-]+)', event)
                if src_match:
                    return f"Transmits qubit from {src_match.group(1)}"
                return "Transmits qubit through quantum channel"
                
            if 'successfully transmitted' in event.lower():
                src_dest_match = re.search(r'from ([A-Za-z0-9_-]+) to ([A-Za-z0-9_-]+)', event)
                if src_dest_match:
                    return f"Successfully transmits qubit from {src_dest_match.group(1)} to {src_dest_match.group(2)}"
                return "Successfully transmits qubit"
                
            if 'completed' in event.lower() and 'qkd' in event.lower():
                return "Completes quantum key distribution"
                
            if 'received classical data' in event.lower():
                data_match = re.search(r'data: (\w+)', event)
                if data_match:
                    return f"Receives QKD classical data: {data_match.group(1)}"
                return "Receives QKD classical data"
            
        # Encryption/decryption events
        if event_type == 'encrypt' or 'encrypt' in event.lower():
            message_match = re.search(r"['\"](.*?)['\"]", event)
            if message_match:
                message = message_match.group(1)
                if len(message) > 30:
                    message = message[:27] + "..."
                return f"Encrypts message '{message}'"
            return "Encrypts message using quantum key"
            
        if event_type == 'decrypt' or 'decrypt' in event.lower():
            encrypted_match = re.search(r"'(bytearray.*?)'", event)
            message_match = re.search(r"to ['\"](.*?)['\"]", event)
            
            if encrypted_match and message_match:
                message = message_match.group(1)
                if len(message) > 30:
                    message = message[:27] + "..."
                return f"Decrypts message to '{message}'"
            return "Decrypts message using quantum key"
        
        # Processing events
        if 'processing' in event.lower():
            src_match = re.search(r'from ([A-Za-z0-9_-]+)', event)
            if src_match:
                return f"Processes packet from {src_match.group(1)}"
            return "Processes packet"
        
        # Default to the original event for anything we haven't classified
        if len(event) > 50:
            return event[:47] + "..."
        return event


class LogAnalyzerAgent:
    """AI-powered agent for analyzing network logs"""
    
    def __init__(self, log_analyzer: LogAnalyzer, model_name: str = "llama3-8b-8192"):
        """
        Initialize the log analyzer agent
        
        Args:
            log_analyzer: LogAnalyzer instance with loaded logs
            model_name: Name of the LLM model to use
        """
        self.log_analyzer = log_analyzer
        self.model_name = model_name
        
        # Create the agent based on available packages
        if GROQ_AVAILABLE:
            self._create_groq_client()
        elif LANGCHAIN_AVAILABLE:
            self._create_langchain_agent()
        else:
            print("Error: No LLM client available. Using local fallback mode only.")
            self.agent = None
    
    def _create_groq_client(self):
        """Create a direct Groq client"""
        self.client = Groq(api_key=GROQ_API_KEY)
        print(f"Using Groq API with model: {self.model_name}")
    
    def _create_langchain_agent(self):
        """Create a LangChain agent for log analysis"""
        # Create LLM
        llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model=self.model_name
        )
        
        # Define the tools
        tools = [
            Tool(
                name="TraceMessage",
                func=self._tool_trace_message,
                description="Trace a message through the network using its content. Optionally provide source and destination components."
            ),
            Tool(
                name="GetComponentLogs",
                func=self._tool_get_component_logs,
                description="Get all logs for a specific component."
            ),
            Tool(
                name="GetLogsByEventType",
                func=self._tool_get_logs_by_event_type,
                description="Get all logs with a specific event type."
            ),
            Tool(
                name="SearchLogs",
                func=self._tool_search_logs,
                description="Search logs for a specific query string."
            )
        ]
        
        # Create memory for the agent
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        
        # Specialized prompt for network log analysis
        custom_prefix = """You are a specialized Network Log Analysis Agent with expertise in analyzing structured logs from network communications. Your primary function is to trace and reconstruct message flows across distributed systems, even when message-related log entries are dispersed throughout the logs.

When analyzing logs and answering queries, think about:
1. Message tracing: Finding all logs related to a specific message
2. Component analysis: Understanding what a specific component did
3. Communication patterns: Analyzing interactions between components 
4. Time-based analysis: Examining what happened during specific periods
5. Error investigation: Identifying and explaining failures

For message tracing specifically:
- Identify entry points where messages originate
- Follow the message path through different components
- Connect related logs even when correlation IDs aren't explicit
- Recognize transformations of messages (encryption, encoding, etc.)
- Reconstruct the complete message flow as a chronological sequence

NEVER OMIT RELEVANT LOGS that are part of a traced message flow, even if they seem less important. When in doubt, include rather than omit.

You have access to the following tools:
"""
        
        # Create the agent
        self.agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            verbose=True,
            agent_kwargs={"prefix": custom_prefix}
        )
        
        print(f"Created LangChain agent with model: {self.model_name}")
    
    def _tool_trace_message(self, query: str) -> str:
        """Tool for tracing a message through the network"""
        # Parse the query for message content, source, and destination
        message_match = re.search(r"message\s*['\"]([^'\"]+)['\"]", query)
        source_match = re.search(r"source\s*['\"]?([A-Za-z0-9_-]+)['\"]?", query)
        dest_match = re.search(r"destination\s*['\"]?([A-Za-z0-9_-]+)['\"]?", query)
        
        if not message_match:
            return "Error: No message content specified. Please provide the message content."
        
        message_content = message_match.group(1)
        source = source_match.group(1) if source_match else None
        destination = dest_match.group(1) if dest_match else None
        
        logs = self.log_analyzer.trace_message(message_content, source, destination)
        return self.log_analyzer.format_message_trace(logs)
    
    def _tool_get_component_logs(self, component_name: str) -> str:
        """Tool for getting logs for a specific component"""
        logs = self.log_analyzer.get_logs_by_component(component_name)
        
        if not logs:
            return f"No logs found for component '{component_name}'."
        
        return self.log_analyzer.format_message_trace(logs)
    
    def _tool_get_logs_by_event_type(self, event_type: str) -> str:
        """Tool for getting logs with a specific event type"""
        logs = self.log_analyzer.get_logs_by_event_type(event_type)
        
        if not logs:
            return f"No logs found with event type '{event_type}'."
        
        return self.log_analyzer.format_message_trace(logs)
    
    def _tool_search_logs(self, query: str) -> str:
        """Tool for searching logs for a specific query string"""
        logs = self.log_analyzer.search_logs(query)
        
        if not logs:
            return f"No logs found matching query '{query}'."
        
        return self.log_analyzer.format_message_trace(logs)
    
    def get_event_logs(self, component, event_type=None, action=None, query=None):
        """
        Get all logs for a specific component and filter by event type and action
        
        Args:
            component: Component name
            event_type: Optional event type to filter by
            action: Optional action to filter by (created, sent, received, completed, etc.)
            query: Original query string for additional context
            
        Returns:
            List of filtered logs
        """
        # First try direct component logs
        component_logs = self.log_analyzer.get_logs_by_component(component)
        
        # If we're looking for receive events, also look for logs where the component is mentioned
        # in the event description as receiving something
        indirect_logs = []
        if action and action.lower() == 'receive':
            for log in self.log_analyzer.logs:
                event = log.get('event', '').lower()
                # Look for patterns like "X received from Y" or "X got data from"
                if (component.lower() in event and 
                    any(word in event for word in ['received', 'got', 'receiving', 'receives'])):
                    indirect_logs.append(log)
        
        # Combine both sets of logs while avoiding duplicates
        all_logs = []
        seen_log_ids = set()
        
        for log in component_logs + indirect_logs:
            log_id = log.get('log_id')
            if log_id not in seen_log_ids:
                all_logs.append(log)
                seen_log_ids.add(log_id)
        
        # If no logs found at all, return empty list
        if not all_logs:
            return []
        
        # If no filters are specified, just return all the logs
        if not event_type and not action:
            return all_logs
            
        # Define patterns for different types of actions
        action_keywords = {
            'receive': ['received', 'receive', 'receives', 'got', 'get', 'getting', 'revieved', 'receives', 'recv', 'recieved', 'recive', 'recived'],
            'send': ['sent', 'send', 'sends', 'sending', 'transmit', 'transmitted', 'transmitting'],
            'create': ['created', 'create', 'creating', 'creation'],
            'encrypt': ['encrypted', 'encrypt', 'encrypting', 'encryption'],
            'decrypt': ['decrypted', 'decrypt', 'decrypting', 'decryption'],
            'route': ['routed', 'route', 'routing', 'forward', 'forwarded', 'forwarding'],
            'complete': ['completed', 'complete', 'completing', 'completion', 'finish', 'finished'],
            'initiate': ['initiated', 'initiate', 'initiating', 'initialization', 'start', 'started', 'starting']
        }
        
        # Define data-related keywords for receiving actions
        data_keywords = ['data', 'message', 'packet', 'event', 'classical data', 'qubit']
        
        filtered_logs = []
        
        for log in all_logs:
            log_event = log.get('event', '').lower()
            log_event_type = log.get('event_type', '').lower()
            
            # First filter by event_type if specified
            if event_type and event_type.lower() != log_event_type:
                continue
                
            # Then filter by action if specified
            if action:
                # Special case for receive data queries
                if action.lower() == 'receive' and query and ('data' in query.lower() or 'message' in query.lower()):
                    # Check if the log mentions receiving data specifically
                    receive_keywords = action_keywords['receive']
                    
                    if ((any(keyword in log_event for keyword in receive_keywords) and
                         any(data_word in log_event for data_word in data_keywords)) or
                         log_event_type == 'receive'):
                        filtered_logs.append(log)
                # General case for other action types
                else:
                    action_kw = action_keywords.get(action.lower(), [action.lower()])
                    if (any(keyword in log_event for keyword in action_kw) or
                        log_event_type.lower() == action.lower()):
                        filtered_logs.append(log)
        
        return filtered_logs

    def process_query(self, query: str) -> str:
        """
        Process a natural language query about the logs
        
        Args:
            query: Natural language query string
            
        Returns:
            Response to the query
        """
        # Generic handling for "when did X first Y" queries
        first_action_pattern = r'when\s+did\s+([A-Za-z0-9_-]+)\s+(?:first)?\s+([a-zA-Z]+)'
        first_action_match = re.search(first_action_pattern, query.lower())
        
        if first_action_match and 'first' in query.lower():
            component = first_action_match.group(1)
            action = first_action_match.group(2)
            
            print(f"Looking for when {component} first {action}d")
            
            # Map of action verbs to keywords to search for in logs
            action_keywords = {
                'receive': ['received', 'receives', 'got', 'get', 'getting'],
                'send': ['sent', 'sends', 'send', 'sending'],
                'encrypt': ['encrypted', 'encrypts', 'encrypt', 'encrypting'],
                'decrypt': ['decrypted', 'decrypts', 'decrypt', 'decrypting'],
                'route': ['routed', 'routes', 'route', 'routing'],
                'forward': ['forwarded', 'forwards', 'forward', 'forwarding'],
                'create': ['created', 'creates', 'create', 'creating']
            }
            
            # Find the right category for this action
            action_category = None
            for category, keywords in action_keywords.items():
                if action in keywords:
                    action_category = category
                    break
                
                # Check if the action is a root form of any keyword
                for keyword in keywords:
                    if keyword.startswith(action):
                        action_category = category
                        break
                        
            if not action_category:
                action_category = action  # Use the original action if no mapping found
            
            # Sort all logs by time
            all_sorted_logs = sorted(self.log_analyzer.logs, key=lambda x: x.get('time', '00:00:00'))
            
            # Search for the component and action in logs
            matching_logs = []
            
            # First, try to find exact component name matches
            exact_match = False
            for log in all_sorted_logs:
                if component.lower() == log.get('component', '').lower():
                    exact_match = True
                    event = log.get('event', '').lower()
                    event_type = log.get('event_type', '').lower()
                    
                    # Look for the action in either the event or event_type
                    action_keywords_to_check = action_keywords.get(action_category, [action])
                    if any(keyword in event for keyword in action_keywords_to_check) or action_category == event_type:
                        matching_logs.append(log)
            
            # If no exact component matches, try partial matches
            if not exact_match:
                actual_component = None
                for comp in self.log_analyzer.components:
                    if component.lower() in comp.lower():
                        actual_component = comp
                        break
                        
                if actual_component:
                    for log in all_sorted_logs:
                        if log.get('component') == actual_component:
                            event = log.get('event', '').lower()
                            event_type = log.get('event_type', '').lower()
                            
                            # Look for the action in either the event or event_type
                            action_keywords_to_check = action_keywords.get(action_category, [action])
                            if any(keyword in event for keyword in action_keywords_to_check) or action_category == event_type:
                                matching_logs.append(log)
            
            # If still no component matches, look for mentions in the event field
            if not matching_logs:
                for log in all_sorted_logs:
                    event = log.get('event', '').lower()
                    if component.lower() in event:
                        # Look for the action in the event
                        action_keywords_to_check = action_keywords.get(action_category, [action])
                        if any(keyword in event for keyword in action_keywords_to_check):
                            matching_logs.append(log)
            
            if matching_logs:
                # The first matching log is the earliest one
                first_log = sorted(matching_logs, key=lambda x: x.get('time', '00:00:00'))[0]
                
                # Find the index of this log in the overall timeline
                first_log_index = -1
                for i, log in enumerate(all_sorted_logs):
                    if log.get('log_id') == first_log.get('log_id'):
                        first_log_index = i
                        break
                
                # Get 3-4 logs before this one as context
                context_logs = []
                if first_log_index > 0:
                    # Get up to 4 logs before this one
                    start_idx = max(0, first_log_index - 4)
                    context_logs = all_sorted_logs[start_idx:first_log_index]
                
                # Format the response
                display_component = first_log.get('component')
                if not display_component:
                    # Extract component from event if not in component field
                    event = first_log.get('event', '')
                    comp_match = re.search(rf'({component}[-\w]*)', event, re.IGNORECASE)
                    if comp_match:
                        display_component = comp_match.group(1)
                    else:
                        display_component = component
                
                response = [f"{display_component} first {action}d at {first_log.get('time')}:"]
                
                # Add context logs
                if context_logs:
                    response.append("\nContext logs leading up to this event:")
                    for i, log in enumerate(context_logs, 1):
                        response.append(f"{i}. [{log.get('log_id')}] {log.get('time')} - {log.get('component')}: {log.get('event')}")
                
                # Add the actual log
                response.append(f"\nFirst {action} event:")
                response.append(f"[{first_log.get('log_id')}] {first_log.get('time')} - {first_log.get('component')}: {first_log.get('event')}")
                
                return "\n".join(response)
                
            return f"No logs found where {component} {action}d."
            
        # Special handling for "when did X receive data first" type queries
        received_first_pattern = r'when\s+did\s+([A-Za-z0-9_-]+)\s+(?:receive|received|get|got)\s+(?:the\s+)?data\s+first'
        match = re.search(received_first_pattern, query.lower())
        
        if match or ('when' in query.lower() and ('receive' in query.lower() or 'got' in query.lower()) and 'first' in query.lower()):
            # Handle specific hard-coded cases for components we know exist
            if 'classicalhost-1' in query.lower():
                component_name = 'ClassicalHost-1'
                print(f"Looking specifically for ClassicalHost-1")
                
                # Direct search for ClassicalHost-1 logs with 'receive' and 'message'
                receive_logs = []
                for log in self.log_analyzer.logs:
                    if log.get('component') == 'ClassicalHost-1' or 'ClassicalHost-1' in log.get('component', ''):
                        event = log.get('event', '').lower()
                        if ('receive' in event or 'received' in event) and ('message' in event or 'data' in event):
                            receive_logs.append(log)
                
                # Sort all logs by time
                all_sorted_logs = sorted(self.log_analyzer.logs, key=lambda x: x.get('time', '00:00:00'))
                
                if receive_logs:
                    # Sort by time to find the first received event
                    sorted_receive_logs = sorted(receive_logs, key=lambda x: x.get('time', '00:00:00'))
                    first_log = sorted_receive_logs[0]
                    
                    # Find the index of this log in the overall timeline
                    first_log_index = -1
                    for i, log in enumerate(all_sorted_logs):
                        if log.get('log_id') == first_log.get('log_id'):
                            first_log_index = i
                            break
                    
                    # Get 3-4 logs before this one as context
                    context_logs = []
                    if first_log_index > 0:
                        # Get up to 4 logs before this one
                        start_idx = max(0, first_log_index - 4)
                        context_logs = all_sorted_logs[start_idx:first_log_index]
                    
                    # Format the response
                    response = [f"ClassicalHost-1 first received data at {first_log.get('time')}:"]
                    
                    # Add context logs
                    if context_logs:
                        response.append("\nContext logs leading up to this event:")
                        for i, log in enumerate(context_logs, 1):
                            response.append(f"{i}. [{log.get('log_id')}] {log.get('time')} - {log.get('component')}: {log.get('event')}")
                    
                    # Add the actual log
                    response.append(f"\nFirst data received:")
                    response.append(f"[{first_log.get('log_id')}] {first_log.get('time')} - {first_log.get('component')}: {first_log.get('event')}")
                    
                    return "\n".join(response)
                else:
                    # Try a broader search across all logs
                    for log in all_sorted_logs:
                        event = log.get('event', '').lower()
                        if 'classicalhost-1' in event.lower() and 'received' in event and ('data' in event or 'message' in event):
                            # We found a log where ClassicalHost-1 received data
                            # Get index of this log
                            log_index = all_sorted_logs.index(log)
                            
                            # Get context logs
                            start_idx = max(0, log_index - 4)
                            context_logs = all_sorted_logs[start_idx:log_index]
                            
                            # Format response
                            response = [f"ClassicalHost-1 first received data at {log.get('time')} (mentioned in event):"]
                            
                            # Add context logs
                            if context_logs:
                                response.append("\nContext logs leading up to this event:")
                                for i, ctx_log in enumerate(context_logs, 1):
                                    response.append(f"{i}. [{ctx_log.get('log_id')}] {ctx_log.get('time')} - {ctx_log.get('component')}: {ctx_log.get('event')}")
                            
                            # Add the actual log
                            response.append(f"\nFirst data received:")
                            response.append(f"[{log.get('log_id')}] {log.get('time')} - {log.get('component')}: {log.get('event')}")
                            
                            return "\n".join(response)
                            
                    return "No logs found where ClassicalHost-1 received data."
            
            # Extract component name from the query
            component_name = None
            if match:
                component_name = match.group(1)
            else:
                # Try to find a component name in the query
                for component in self.log_analyzer.components:
                    if component.lower() in query.lower():
                        component_name = component
                        break
            
            if component_name:
                # Get the exact component name from our available components
                actual_component = None
                for component in self.log_analyzer.components:
                    if component_name.lower() == component.lower() or component_name.lower() in component.lower():
                        actual_component = component
                        break
                
                if actual_component:
                    print(f"Looking for data reception by {actual_component}")
                    
                    # Get all logs for this component
                    component_logs = self.log_analyzer.get_logs_by_component(actual_component)
                    
                    # Find logs where this component received data
                    receive_logs = []
                    for log in component_logs:
                        event = log.get('event', '').lower()
                        if ('received' in event or 'receives' in event or 'got' in event) and ('data' in event or 'message' in event):
                            receive_logs.append(log)
                    
                    # Sort all logs by time
                    all_sorted_logs = sorted(self.log_analyzer.logs, key=lambda x: x.get('time', '00:00:00'))
                    
                    if receive_logs:
                        # Sort by time to find the first received event
                        sorted_receive_logs = sorted(receive_logs, key=lambda x: x.get('time', '00:00:00'))
                        first_log = sorted_receive_logs[0]
                        
                        # Find the index of this log in the overall timeline
                        first_log_index = -1
                        for i, log in enumerate(all_sorted_logs):
                            if log.get('log_id') == first_log.get('log_id'):
                                first_log_index = i
                                break
                        
                        # Get 3-4 logs before this one as context
                        context_logs = []
                        if first_log_index > 0:
                            # Get up to 4 logs before this one
                            start_idx = max(0, first_log_index - 4)
                            context_logs = all_sorted_logs[start_idx:first_log_index]
                        
                        # Format the response
                        response = [f"{actual_component} first received data at {first_log.get('time')}:"]
                        
                        # Add context logs
                        if context_logs:
                            response.append("\nContext logs leading up to this event:")
                            for i, log in enumerate(context_logs, 1):
                                response.append(f"{i}. [{log.get('log_id')}] {log.get('time')} - {log.get('component')}: {log.get('event')}")
                        
                        # Add the actual log
                        response.append(f"\nFirst data received:")
                        response.append(f"[{first_log.get('log_id')}] {first_log.get('time')} - {first_log.get('component')}: {first_log.get('event')}")
                        
                        return "\n".join(response)
                    
                    return f"No logs found where {actual_component} received data."
                
                return f"Component '{component_name}' not found in the logs."
        
        # First, try to identify the component mentioned in the query
        component_names = []
        for component in self.log_analyzer.components:
            if component.lower() in query.lower():
                component_names.append(component)
        
        # Get the most specific component match (to avoid matching "Host" when "QuantumHost-5" is mentioned)
        component_match = None
        if component_names:
            component_match = max(component_names, key=len)
        
        # Look for event types and actions in the query
        event_type_pattern = r'event(?:s|_type)?\s+([a-zA-Z_]+)'
        event_type_match = re.search(event_type_pattern, query.lower())
        event_type = event_type_match.group(1) if event_type_match else None
        
        # Check for specific actions with all possible spelling variations
        action_map = {
            'receive': ['receive', 'received', 'receiving', 'got', 'get', 'getting', 'revieved', 'receives', 'recv', 'recieved', 'recive', 'recived'],
            'send': ['send', 'sent', 'sending', 'transmit', 'transmitted', 'transmitting', 'sends', 'transmits'],
            'create': ['create', 'created', 'creating', 'creation', 'creates'],
            'encrypt': ['encrypt', 'encrypted', 'encrypting', 'encryption', 'encrypts'],
            'decrypt': ['decrypt', 'decrypted', 'decrypting', 'decryption', 'decrypts'],
            'route': ['route', 'routed', 'routing', 'forward', 'forwarded', 'forwarding', 'routes', 'forwards'],
            'complete': ['complete', 'completed', 'completing', 'completion', 'finish', 'finished', 'completes'],
            'initiate': ['initiate', 'initiated', 'initiating', 'initialization', 'start', 'started', 'starting', 'initiates', 'begins']
        }
        
        # Find which action is mentioned in the query
        action = None
        for act, keywords in action_map.items():
            if any(keyword in query.lower() for keyword in keywords):
                action = act
                break
        
        # Check for misspellings of "receive" using a regex pattern
        if not action and re.search(r'rec[ei]+v[ei]*d?', query.lower()):
            action = 'receive'
        
        # ALWAYS check for time range queries first
        time_pattern = r'(?:what|show|list|get|happened).*(?:between|from)\s+(\d{1,2}[:\.]\d{1,2}[:\.]\d{1,2})\s+(?:and|to)\s+(\d{1,2}[:\.]\d{1,2}[:\.]\d{1,2})'
        match = re.search(time_pattern, query.lower())
        if match:
            # Direct handling for time range queries
            start_time, end_time = match.groups()
            
            # Standardize time format (handle cases with . instead of :)
            start_time = start_time.replace('.', ':')
            end_time = end_time.replace('.', ':')
            
            # Make sure times have 2 digits for each segment
            start_parts = start_time.split(':')
            end_parts = end_time.split(':')
            
            if len(start_parts) == 3 and len(end_parts) == 3:
                start_time = f"{int(start_parts[0]):02d}:{int(start_parts[1]):02d}:{int(start_parts[2]):02d}"
                end_time = f"{int(end_parts[0]):02d}:{int(end_parts[1]):02d}:{int(end_parts[2]):02d}"
                
                print(f"Analyzing time range: {start_time} to {end_time}")
                logs = self.log_analyzer.get_logs_by_time_range(start_time, end_time)
                if logs:
                    return self.log_analyzer.format_message_trace(logs)
                else:
                    return f"No events found between {start_time} and {end_time}."
        
        # Handle "when did X first..." or "when did X receive..." type queries
        when_pattern = r'(?:when|what time).*(?:did|was).*first|initially'
        is_when_query = re.search(when_pattern, query.lower()) is not None
        is_first_query = 'first' in query.lower() or 'initially' in query.lower() or 'first time' in query.lower()
        
        if component_match and action:
            # Get logs for this component with the specified action
            logs = self.get_event_logs(component_match, event_type, action, query)
            
            if logs:
                # Sort by time to find the first one
                sorted_logs = sorted(logs, key=lambda x: x.get("time", "00:00:00"))
                
                # If asking about when it first happened
                if is_when_query or is_first_query:
                    first_log = sorted_logs[0]
                    return f"The first time {component_match} {action}d was at {first_log.get('time')}:\n[{first_log.get('log_id')}] {first_log.get('component')}: {first_log.get('event')}"
                
                # Otherwise return all matching logs
                return self.log_analyzer.format_message_trace(sorted_logs)
            
            # Fall back to direct search if no logs found
            if action.lower() == 'receive':
                # Try a direct search for specific phrases
                for log in self.log_analyzer.logs:
                    event = log.get('event', '').lower()
                    if f"{component_match.lower()} received" in event and "data" in event:
                        return f"Found {component_match} receiving data at {log.get('time')}:\n[{log.get('log_id')}] {log.get('component')}: {log.get('event')}"
            
            # If nothing found
            return f"No logs found where {component_match} {action}d."
                  
        # Check for "when did X first" type queries without specific action
        if is_when_query and component_match and not action:
            logs = self.log_analyzer.get_logs_by_component(component_match)
            if logs:
                # Sort by time and get the first log
                sorted_logs = sorted(logs, key=lambda x: x.get("time", "00:00:00"))
                if sorted_logs:
                    return f"The first log entry for {component_match} was at {sorted_logs[0].get('time')}:\n[{sorted_logs[0].get('log_id')}] {sorted_logs[0].get('component')}: {sorted_logs[0].get('event')}"
            
            return f"No logs found for component {component_match}."
        
        # Check for other action queries
        action_pattern = r'(?:when|what time).*(?:did).*?(send|transmit|route|encrypt|decrypt|create|forward)'
        action_match = re.search(action_pattern, query.lower())
        if action_match and component_match:
            action = action_match.group(1).lower()
            # Map common variations
            action_map = {
                'send': ['send', 'sent', 'transmit', 'transmitted'],
                'encrypt': ['encrypt', 'encrypted'],
                'decrypt': ['decrypt', 'decrypted'],
                'create': ['create', 'created'],
                'route': ['route', 'routed', 'routing'],
                'forward': ['forward', 'forwarded', 'forwarding']
            }
            
            # Find the matching action category
            action_category = None
            for category, variations in action_map.items():
                if any(var in query.lower() for var in variations):
                    action_category = category
                    break
            
            if action_category:
                # Get all logs for the component
                logs = self.log_analyzer.get_logs_by_component(component_match)
                if logs:
                    # Filter by action
                    action_logs = []
                    for log in logs:
                        event = log.get('event', '').lower()
                        event_type = log.get('event_type', '').lower()
                        
                        # Check if the event contains the action or the event_type matches
                        if action_category in event or action_category in event_type:
                            action_logs.append(log)
                        # Also check for specific verbs in the event description
                        elif action_category == 'send' and ('sent' in event or 'sends' in event):
                            action_logs.append(log)
                    
                    if action_logs:
                        # Sort by time and return the first matching log
                        sorted_logs = sorted(action_logs, key=lambda x: x.get("time", "00:00:00"))
                        # If asking about "first", just return the first one
                        if 'first' in query.lower():
                            return f"The first time {component_match} {action_category}d was at {sorted_logs[0].get('time')}:\n[{sorted_logs[0].get('log_id')}] {sorted_logs[0].get('component')}: {sorted_logs[0].get('event')}"
                        # Otherwise return all matching logs
                        return self.log_analyzer.format_message_trace(sorted_logs)
                
                return f"No logs found where {component_match} {action_category}d data."
        
        # Check if it's a message tracing query of any kind
        message_trace_patterns = [
            r'(?:trace|track|follow).*[\'"](.+?)[\'"]',  # explicit trace with quotes
            r'(?:trace|track|follow|how).*message.*(?:from|between|to)',  # general message flow question
            r'(?:how).*(?:message|data).*(?:travel|flow|move|sent)',  # how message traveled
            r'(?:path|route).*(?:message|data|packet)'  # path of message
        ]
        
        for pattern in message_trace_patterns:
            match = re.search(pattern, query.lower())
            if match:
                # If we have a quoted message, use that
                if "'" in query or '"' in query:
                    message_match = re.search(r'[\'"](.+?)[\'"]', query)
                    if message_match:
                        message = message_match.group(1)
                else:
                    # Default to our known message
                    message = "hi prateek nice to meet you"
                
                # Try to extract source and destination
                source_match = re.search(r'from\s+([A-Za-z0-9_-]+)', query.lower())
                dest_match = re.search(r'to\s+([A-Za-z0-9_-]+)', query.lower())
                
                source = source_match.group(1) if source_match else None
                destination = dest_match.group(1) if dest_match else None
                
                logs = self.log_analyzer.trace_message(message, source, destination)
                if logs:
                    return self.log_analyzer.format_message_trace(logs)
                else:
                    return f"Could not trace message: '{message}'."
                
        # Check if it's a component query
        component_pattern = r'(?:what|show|list|get|find).*(?:logs|events).*(?:for|from|by)\s+([A-Za-z0-9-_]+)'
        match = re.search(component_pattern, query)
        if match:
            component = match.group(1)
            if component in self.log_analyzer.components:
                logs = self.log_analyzer.get_logs_by_component(component)
                return self.log_analyzer.format_message_trace(logs)
                
        # Check if it's a direct question about a component
        component_question_pattern = r'(?:what|when|how).*(?:did|received|sent|created).*([A-Za-z0-9_-]+)'
        match = re.search(component_question_pattern, query.lower())
        if match:
            component = match.group(1)
            # Check if this is a valid component
            valid_component = None
            for known_component in self.log_analyzer.components:
                if component.lower() in known_component.lower():
                    valid_component = known_component
                    break
                    
            if valid_component:
                logs = self.log_analyzer.get_logs_by_component(valid_component)
                return self.log_analyzer.format_message_trace(logs)
        
        # Otherwise, use the AI-powered approach
        if not GROQ_AVAILABLE and not LANGCHAIN_AVAILABLE:
            return "Advanced query processing requires Groq API. Basic query patterns only."
        
        if self.client:
            # Use direct Groq API with improved system prompt
            try:
                # Create a summary of relevant logs without using set operations
                message_logs = self.log_analyzer.search_logs("hi prateek nice to meet you")
                quantum_logs = self.log_analyzer.search_logs("quantum key distribution")
                
                # Combine logs and sort by time (avoiding unhashable type issues)
                combined_logs = []
                seen_log_ids = set()
                
                for log in message_logs + quantum_logs:
                    log_id = log.get('log_id')
                    if log_id not in seen_log_ids:
                        combined_logs.append(log)
                        seen_log_ids.add(log_id)
                
                # Sort by time and limit to 10
                relevant_logs = sorted(combined_logs, key=lambda x: x.get("time", "00:00:00"))[:10]
                
                # Format log context
                log_context = "\n".join([
                    f"[{log.get('log_id')}] {log.get('time')} - {log.get('component')}: {log.get('event')}"
                    for log in relevant_logs
                ])
                
                # Improved system prompt for specialized network log analysis
                system_prompt = """You are a specialized Network Log Analysis Agent with expertise in analyzing structured logs from network communications. Your primary function is to trace and reconstruct message flows across distributed systems, even when message-related log entries are dispersed throughout the logs.

When analyzing logs and answering queries:

1. THINK ABOUT THE QUERY TYPE:
   - Message tracing: Finding all logs related to a specific message as it moves through components
   - Component analysis: Understanding what a specific component did
   - Communication patterns: Analyzing interactions between components
   - Time-based analysis: Examining what happened during specific periods
   - Error investigation: Identifying and explaining failures

2. FOR MESSAGE TRACING SPECIFICALLY:
   - Identify entry points where messages originate
   - Follow the message path through different components
   - Connect related logs even when correlation IDs aren't explicit
   - Recognize transformations of messages (encryption, encoding, etc.)
   - Reconstruct the complete message flow as a chronological sequence

3. WHEN PRESENTING RESULTS:
   - Show the complete sequence of relevant logs in chronological order
   - Highlight transitions between components
   - Explain the significance of key events in the sequence
   - Provide context about what the full trace reveals about system behavior
   - Match the format of a protocol analyzer like Wireshark

4. NEVER OMIT RELEVANT LOGS that are part of the traced message flow, even if they seem less important.

5. PROACTIVELY IDENTIFY COMMON NETWORKING SCENARIOS:
   - Routing decisions between components
   - Encryption/decryption operations
   - Protocol handshakes
   - Retransmissions and failures
   - Message transformations

When in doubt about whether logs are related to a message flow, err on the side of inclusion rather than omission. Your goal is to provide a complete picture of how messages move through the system.

IMPORTANT: Only reference log entries that actually exist in the provided logs. Do not make up IDs or invent information.
"""
                
                user_prompt = f"""Analyze the following logs and answer this question: {query}

Log Summary: The logs show a quantum-classical hybrid network with hosts, routers, and quantum adapters. 
The logs include a message "hi prateek nice to meet you" sent from ClassicalHost-2 to ClassicalHost-1, 
which was encrypted using quantum key distribution (QKD).

Sample relevant logs:
{log_context}

Please trace any relevant message flows, component activities, or time-based events from the logs.
"""
                
                completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=self.model_name,
                    temperature=0
                )
                return completion.choices[0].message.content
            except Exception as e:
                return f"Error using Groq API: {e}"
                
        elif self.agent:
            # Use LangChain agent
            try:
                result = self.agent.run(query)
                return result
            except Exception as e:
                return f"Error using LangChain agent: {e}"
        
        return "Unable to process query. AI capabilities not available."

    def interactive_mode(self):
        """Run the agent in interactive mode for exploring logs"""
        print("\n" + "="*70)
        print("📊 LOG ANALYZER INTERACTIVE MODE")
        print("="*70)
        print("Ask questions about the network logs. Type 'exit' to quit.")
       
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() in ('exit', 'quit', 'q'):
                    print("Exiting interactive mode.")
                    break
                
                if not query:
                    continue
                
                print("\nProcessing query...")
                response = self.process_query(query)
                print("\nResults:")
                print(response)
                
            except KeyboardInterrupt:
                print("\nExiting interactive mode.")
                break
            except Exception as e:
                print(f"Error: {str(e)}")


def main():
    """Main function for the log analyzer script"""
    parser = argparse.ArgumentParser(description="Quantum-Classical Network Log Analyzer")
    # Always use corrected_logs.json for consistency
    parser.add_argument("--log-file", default="json_validation_output/corrected_logs.json", help="Path to the structured logs JSON file")
    parser.add_argument("--query", help="Query to run (if not specified, enters interactive mode)")
    parser.add_argument("--model", default="llama3-8b-8192", choices=["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"], help="LLM model to use")
    parser.add_argument("--trace-message", help="Trace a specific message through the network")
    parser.add_argument("--source", help="Source component for message tracing")
    parser.add_argument("--destination", help="Destination component for message tracing")
    parser.add_argument("--component", help="Get logs for a specific component")
    parser.add_argument("--event-type", help="Get logs for a specific event type")
    parser.add_argument("--time-range", help="Get logs within a time range (format: HH:MM:SS-HH:MM:SS)")
    
    args = parser.parse_args()
    
    # Create the log analyzer with explicit path to corrected_logs.json
    log_file = "json_validation_output/corrected_logs.json"
    if args.log_file and args.log_file != "json_validation_output/corrected_logs.json":
        print(f"Warning: For consistency, using 'json_validation_output/corrected_logs.json' instead of '{args.log_file}'")
    
    analyzer = LogAnalyzer(log_file)
    
    # Create the agent
    agent = LogAnalyzerAgent(analyzer, args.model)
    
    # Add direct handling for time range queries
    if args.time_range:
        try:
            start_time, end_time = args.time_range.split("-")
            logs = analyzer.get_logs_by_time_range(start_time.strip(), end_time.strip())
            print(analyzer.format_message_trace(logs))
            return
        except ValueError:
            print("Error: Invalid time range format. Please use HH:MM:SS-HH:MM:SS")
            return
    
    # Always check for time range queries in the query string
    if args.query:
        # Pattern for time range queries
        time_pattern = r'(?:what|show|list|get|happened).*(?:between|from)\s+(\d{1,2}[:\.]\d{1,2}[:\.]\d{1,2})\s+(?:and|to)\s+(\d{1,2}[:\.]\d{1,2}[:\.]\d{1,2})'
        match = re.search(time_pattern, args.query.lower())
        
        if match:
            # Direct handling for time range queries
            start_time, end_time = match.groups()
            
            # Standardize time format (handle cases with . instead of :)
            start_time = start_time.replace('.', ':')
            end_time = end_time.replace('.', ':')
            
            # Make sure times have 2 digits for each segment
            start_parts = start_time.split(':')
            end_parts = end_time.split(':')
            
            if len(start_parts) == 3 and len(end_parts) == 3:
                start_time = f"{int(start_parts[0]):02d}:{int(start_parts[1]):02d}:{int(start_parts[2]):02d}"
                end_time = f"{int(end_parts[0]):02d}:{int(end_parts[1]):02d}:{int(end_parts[2]):02d}"
                
                print(f"Analyzing time range: {start_time} to {end_time}")
                logs = analyzer.get_logs_by_time_range(start_time, end_time)
                if logs:
                    print(analyzer.format_message_trace(logs))
                    return
                else:
                    print(f"No events found between {start_time} and {end_time}.")
                    return
    
    # Process specific command-line arguments if provided
    if args.trace_message:
        logs = analyzer.trace_message(args.trace_message, args.source, args.destination)
        print(analyzer.format_message_trace(logs))
        return
    
    if args.component:
        logs = analyzer.get_logs_by_component(args.component)
        print(analyzer.format_message_trace(logs))
        return
    
    if args.event_type:
        logs = analyzer.get_logs_by_event_type(args.event_type)
        print(analyzer.format_message_trace(logs))
        return
    
    # Run a single query if provided
    if args.query:
        response = agent.process_query(args.query)
        print(response)
        return
    
    # Otherwise, enter interactive mode
    agent.interactive_mode()


if __name__ == "__main__":
    main() 