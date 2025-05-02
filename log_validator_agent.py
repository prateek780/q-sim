#!/usr/bin/env python3
"""
Log Validator Agent

This script creates an AI agent using Google AI Studio to analyze
quantum network simulation logs and generate validation rules for log entries.

The agent:
1. Connects to Google AI Studio using an API key
2. Reads and parses JSON logs from Redis
3. Uses AI to analyze log structure and patterns 
4. Generates comprehensive validation rules based on the analysis
5. Formats and saves the rules as a structured JSON schema



import os
import json
import sys
import re
import glob
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import hashlib
import logging
import traceback
import redis

# Import Google's Generative AI directly
import google.generativeai as genai

# Import functions from retrieve_rejson_logs
from retrieve_rejson_logs import get_rejson_data, REDIS_HOST, REDIS_PORT, REDIS_USERNAME, REDIS_PASSWORD, REDIS_DB, REDIS_SSL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("log_validator_agent")

# Google AI API key
GOOGLE_API_KEY = "AIzaSyAMefcGA9_a5UblqPd3wU5nUVbNzrVCnbk"

# Import the log validator module
from log_validator import validate_logs, pinpoint_message, load_and_validate

def load_logs_from_redis(pattern: str = "network-sim:log:*") -> dict:
    """Load logs from Redis using the specified pattern."""
    try:
        # Connect to Redis
        logger.info(f"Connecting to Redis: {REDIS_HOST}:{REDIS_PORT}")
        redis_conn = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            username=REDIS_USERNAME,
            password=REDIS_PASSWORD,
            db=REDIS_DB,
            ssl=REDIS_SSL,
            decode_responses=True
        )
        
        # Test connection
        if not redis_conn.ping():
            logger.error("Failed to connect to Redis")
            return {}
            
        logger.info("Connected to Redis successfully")
        
        # Get all keys matching the pattern
        logger.info(f"Scanning for keys matching pattern: {pattern}")
        all_logs = {}
        cursor = 0
        keys = []
        
        while True:
            cursor, batch = redis_conn.scan(cursor=cursor, match=pattern, count=100)
            keys.extend(batch)
            if cursor == 0:
                break
        
        total_keys = len(keys)
        logger.info(f"Found {total_keys} keys matching the pattern")
        
        # Process each key
        for i, key in enumerate(keys):
            try:
                key_type = redis_conn.type(key)
                logger.info(f"Processing key {i+1}/{total_keys}: {key} (Type: {key_type})")
                
                # Extract the log ID from the key
                log_id = key.split(":")[-1] if ":" in key else key
                
                # Get data using appropriate method
                if key_type == "ReJSON-RL":
                    data = get_rejson_data(redis_conn, key)
                    if data:
                        all_logs[log_id] = data
                    else:
                        all_logs[log_id] = {"error": "Unable to retrieve ReJSON data"}
                elif key_type == "string":
                    raw_data = redis_conn.get(key)
                    try:
                        all_logs[log_id] = json.loads(raw_data)
                    except json.JSONDecodeError:
                        all_logs[log_id] = {"raw_text": raw_data}
                elif key_type == "hash":
                    all_logs[log_id] = redis_conn.hgetall(key)
                else:
                    logger.warning(f"Skipping key with type {key_type}: {key}")
                    continue
                
            except Exception as e:
                logger.error(f"Error processing key {key}: {e}")
                all_logs[log_id] = {"error": str(e)}
        
        # Format the data to match the expected structure
        data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_keys": total_keys,
                "pattern": pattern
            },
            "logs": all_logs
        }
        
        logger.info(f"Successfully loaded {len(all_logs)} logs from Redis")
        return data
        
    except Exception as e:
        logger.error(f"Error loading logs from Redis: {str(e)}")
        return {}

def extract_field_info(logs: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract field information from logs to determine types, patterns, and value distributions
    
    Args:
        logs: Dictionary containing log entries
        
    Returns:
        Dictionary with field information including types, patterns, required status, etc.
    """
    field_info = {}
    
    # Get log entries as a list
    log_entries = logs.get('logs', [])
    if isinstance(log_entries, dict):
        log_entries = list(log_entries.values())
    
    if not log_entries:
        logger.error("No valid log entries found")
        return {}
    
    # Count total logs
    total_logs = len(log_entries)
    logger.info(f"Analyzing {total_logs} log entries")
    
    # First pass: identify all fields and their occurrences
    all_fields = set()
    field_presence = {}
    
    for log_entry in log_entries:
        # Skip any non-dictionary entries
        if not isinstance(log_entry, dict):
            continue
        
        # Process first-level fields
        for field, value in log_entry.items():
            field_path = field
            all_fields.add(field_path)
            
            # Track presence
            field_presence[field_path] = field_presence.get(field_path, 0) + 1
            
            # Track nested fields for objects
            if isinstance(value, dict):
                _extract_nested_fields(value, field, all_fields, field_presence)
    
    # Second pass: analyze field types and values
    for field_path in all_fields:
        parts = field_path.split('.')
        field_types = {}
        allowed_values = set()
        is_required = False
        value_samples = []  # For pattern analysis
        
        # Calculate if field is required (present in >80% of logs)
        presence_ratio = field_presence.get(field_path, 0) / total_logs
        is_required = presence_ratio > 0.8
        
        # Collect field information
        for log_entry in log_entries:
            value = _get_nested_value(log_entry, parts)
            
            if value is not None:
                # Track value type
                value_type = type(value).__name__
                field_types[value_type] = field_types.get(value_type, 0) + 1
                
                # Track allowed values for potential enums (don't track for complex types)
                if value_type in ['str', 'int', 'float', 'bool'] and len(allowed_values) < 100:
                    allowed_values.add(value)
                
                # Store sample values for string pattern analysis
                if value_type == 'str' and len(value_samples) < 50:
                    value_samples.append(value)
        
        # Determine primary type(s)
        sorted_types = sorted(field_types.items(), key=lambda x: x[1], reverse=True)
        primary_types = [t[0] for t in sorted_types if t[1] > 0]
        
        # Determine if field is an enum (small set of values)
        possible_enum = False
        if len(allowed_values) <= 20 and len(allowed_values) / field_presence.get(field_path, 1) < 0.1:
            possible_enum = True
        
        # Determine string patterns for string fields
        pattern = None
        if 'str' in primary_types and value_samples:
            pattern = _detect_string_pattern(value_samples)
        
        # Store field information
        field_info[field_path] = {
            'required': is_required,
            'types': primary_types,
            'presence': field_presence.get(field_path, 0),
            'presence_ratio': presence_ratio,
            'possible_enum': possible_enum,
            'allowed_values': list(allowed_values) if possible_enum else None,
            'pattern': pattern
        }
    
    return field_info

def _extract_nested_fields(obj: Dict[str, Any], parent_path: str, all_fields: set, field_presence: Dict[str, int]):
    """Helper function to extract nested fields from an object"""
    for key, value in obj.items():
        field_path = f"{parent_path}.{key}"
        all_fields.add(field_path)
        field_presence[field_path] = field_presence.get(field_path, 0) + 1
        
        # Recursively process nested objects
        if isinstance(value, dict):
            _extract_nested_fields(value, field_path, all_fields, field_presence)
        # Process list items if they're dictionaries
        elif isinstance(value, list):
            # Add a field for the list itself
            list_path = f"{field_path}[]"
            all_fields.add(list_path)
            field_presence[list_path] = field_presence.get(list_path, 0) + 1
            
            # Process first few list items if they're objects
            for i, item in enumerate(value[:5]):  # Limit to first 5 items
                if isinstance(item, dict):
                    _extract_nested_fields(item, f"{field_path}[{i}]", all_fields, field_presence)

def _get_nested_value(obj: Dict[str, Any], path_parts: List[str]) -> Any:
    """Helper function to get a nested value from an object based on path parts"""
    if not obj or not isinstance(obj, dict):
        return None
    
    value = obj
    for part in path_parts:
        # Handle array index notation like 'field[0]'
        index_match = re.match(r'(.*)\[(\d+)\]$', part)
        if index_match:
            field = index_match.group(1)
            index = int(index_match.group(2))
            if field in value and isinstance(value[field], list) and index < len(value[field]):
                value = value[field][index]
            else:
                return None
        else:
            # Regular field access
            if part in value:
                value = value[part]
            else:
                return None
    
    return value

def _detect_string_pattern(samples: List[str]) -> Optional[str]:
    """
    Detect common patterns in string samples
    
    Returns:
        RegEx pattern string or None if no pattern detected
    """
    if not samples:
        return None
    
    # Check for common patterns
    
    # UUID pattern
    if all(re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', s, re.IGNORECASE) for s in samples[:5]):
        return r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    
    # ID pattern (like the 'pk' field)
    if all(re.match(r'^[0-9A-Z]{26}$', s) for s in samples[:5]):
        return r'^[0-9A-Z]{26}$'
    
    # Timestamp pattern
    if all(re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', s) for s in samples[:5]):
        return r'^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d+)?$'
    
    # IP address pattern
    if all(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', s) for s in samples[:5]):
        return r'^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$'
    
    # Python class pattern
    if all("<class '" in s and "'>" in s for s in samples[:5]):
        return None  # Don't enforce a pattern, just use allowed_values
    
    return None

def analyze_log_relationships(logs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze relationships between fields based on conditional patterns
    
    Args:
        logs: Dictionary containing log entries
        
    Returns:
        Dictionary of field relationships and conditional patterns
    """
    relationships = {}
    
    # Skip metadata and other non-log entries
    log_entries = logs.get('logs', {})
    if not log_entries or not isinstance(log_entries, dict):
        logger.error("No valid log entries found")
        return {}
    
    # Find potential conditional relationships, especially for 'details' fields
    # Focus on 'event_type' field and how it relates to other fields
    event_type_relations = {}
    
    for log_id, log_entry in log_entries.items():
        if not isinstance(log_entry, dict) or 'details' not in log_entry:
            continue
            
        details = log_entry.get('details', {})
        if not isinstance(details, dict):
            continue
            
        event_type = details.get('event_type')
        if not event_type:
            continue
            
        # Track which fields are present for each event_type
        if event_type not in event_type_relations:
            event_type_relations[event_type] = {
                'count': 0,
                'fields': {},
                'data_fields': {}
            }
            
        event_type_relations[event_type]['count'] += 1
        
        # Track details fields
        for field, value in details.items():
            field_path = f"details.{field}"
            if field_path not in event_type_relations[event_type]['fields']:
                event_type_relations[event_type]['fields'][field_path] = 0
            event_type_relations[event_type]['fields'][field_path] += 1
            
        # Track data subfields
        if 'data' in details and isinstance(details['data'], dict):
            for field, value in details['data'].items():
                field_path = f"details.data.{field}"
                if field_path not in event_type_relations[event_type]['data_fields']:
                    event_type_relations[event_type]['data_fields'][field_path] = 0
                event_type_relations[event_type]['data_fields'][field_path] += 1
                
                # Special handling for message types in data_received events
                if event_type == 'data_received' and field == 'message' and isinstance(value, dict):
                    message_type = value.get('type')
                    if message_type:
                        message_relation_key = f"details.data.message.type={message_type}"
                        if message_relation_key not in relationships:
                            relationships[message_relation_key] = {
                                'count': 0,
                                'fields': {}
                            }
                        relationships[message_relation_key]['count'] += 1
                        
                        # Track message fields
                        for msg_field, msg_value in value.items():
                            field_path = f"details.data.message.{msg_field}"
                            if field_path not in relationships[message_relation_key]['fields']:
                                relationships[message_relation_key]['fields'][field_path] = 0
                            relationships[message_relation_key]['fields'][field_path] += 1
    
    # Add event_type relationships to overall relationships
    for event_type, data in event_type_relations.items():
        relationships[f"details.event_type={event_type}"] = data
    
    return relationships

def clean_json_with_comments(json_str: str) -> str:
    """
    Clean JSON string that might contain comments
    
    Args:
        json_str: JSON string that might contain comments
        
    Returns:
        Cleaned JSON string without comments
    """
    # Remove single-line comments (e.g., // This is a comment)
    # This regex handles comments not inside string literals
    lines = json_str.split('\n')
    cleaned_lines = []
    
    for line in lines:
        in_string = False
        prev_char = ''
        comment_start = -1
        
        for i, char in enumerate(line):
            # Track string boundaries
            if char == '"' and prev_char != '\\':
                in_string = not in_string
            
            # Detect comments outside strings
            if not in_string and char == '/' and prev_char == '/':
                # Found a comment, adjust its starting position (account for the first slash)
                comment_start = i - 1
                break
                
            prev_char = char
        
        # Remove the comment part if found
        if comment_start >= 0:
            cleaned_lines.append(line[:comment_start].rstrip())
        else:
            cleaned_lines.append(line)
    
    # Join lines back together
    cleaned_json = '\n'.join(cleaned_lines)
    
    # Remove any trailing commas before closing brackets/braces
    cleaned_json = re.sub(r',(\s*[\]}])', r'\1', cleaned_json)
    
    return cleaned_json

class LogAnalyzerAgent:
    """Agent for analyzing logs and generating validation rules using Google AI directly"""
    
    def __init__(self):
        """Initialize the log analyzer with Google AI connection"""
        try:
            # Configure the Google GenAI API
            genai.configure(api_key=GOOGLE_API_KEY)
            
            # Initialize the Gemini model
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            logger.info("Successfully initialized Google AI model")
        except Exception as e:
            logger.error(f"Error initializing Google AI model: {str(e)}")
            self.model = None
    
    def analyze_logs(self, logs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze log data and generate validation rules
        
        Args:
            logs: Dictionary containing log entries
            
        Returns:
            Dictionary with validation schema
        """
        if not self.model:
            logger.error("AI model not initialized")
            return {"schema_version": "1.0", "rules": []}
        
        try:
            # Extract field information from logs
            field_info = extract_field_info(logs)
            if not field_info:
                logger.error("Failed to extract field information from logs")
                return {"schema_version": "1.0", "rules": []}
            
            # Analyze relationships between fields
            relationships = analyze_log_relationships(logs)
            
            # Use all logs for analysis
            log_entries = logs.get('logs', {})
            logger.info(f"Analyzing all {len(log_entries)} log entries")
            
            # Convert to JSON strings for prompt insertion
            logs_json = json.dumps(log_entries, indent=2)
            field_info_json = json.dumps(field_info, indent=2)
            relationships_json = json.dumps(relationships, indent=2)
            
            # Prepare the prompt for the model
            prompt = f"""
            You are an expert in log validation schema creation. 
            Your task is to analyze the provided log data and create a JSON validation schema that exactly matches the expected format.
            
            LOG ENTRIES:
            ```json
            {logs_json}
            ```
            
            FIELD ANALYSIS RESULTS:
            ```json
            {field_info_json}
            ```
            
            RELATIONSHIP ANALYSIS:
            ```json
            {relationships_json}
            ```
            
            Create a comprehensive validation schema that follows this EXACT format:
            ```json
            {{
              "schema_version": "1.0",
              "rules": [
                {{
                  "field": "pk",
                  "required": true,
                  "type": "string",
                  "pattern": "^[0-9A-Z]{{26}}$", 
                  "description": "Unique identifier for the log entry."
                }},
                {{
                  "field": "entity_id",
                  "required": true,
                  "type": ["string", "null"],
                  "description": "Identifier for the entity, supports both null and string values."
                }},
                {{
                  "field": "details",
                  "required": true,
                  "type": "object",
                  "description": "Detailed information about the log event.",
                  "rules": [
                    {{
                      "field": "event_type",
                      "required": true,
                      "type": "string",
                      "allowed_values": ["packet_transmitted", "packet_received", "qkd_initiated", "data_received", "data_sent"],
                      "description": "Type of the event."
                    }},
                    {{
                      "field": "data",
                      "required": true,
                      "type": "object",
                      "description": "Event-specific data.",
                      "conditional_rules": [
                        {{
                          "condition": {{"../event_type": "packet_transmitted"}},
                          "rules": [
                            {{"field": "packet", "required": true, "type": "object", "rules": [
                              {{"field": "type", "required": true, "type": "string"}},
                              {{"field": "from", "required": true, "type": "string"}},
                              {{"field": "to", "required": true, "type": "string"}},
                              {{"field": "hops", "required": true, "type": "list", "item_type": "string"}},
                              {{"field": "data", "required": true, "type": ["string", "object"]}},
                              {{"field": "destination_address", "required": false, "type": ["string", "null"]}}
                            ]}}
                          ]
                        }},
                        {{
                          "condition": {{"../event_type": "packet_received"}},
                          "rules": [
                            {{"field": "packet", "required": true, "type": "object", "rules": [
                              {{"field": "type", "required": true, "type": "string"}},
                              {{"field": "from", "required": true, "type": "string"}},
                              {{"field": "to", "required": true, "type": "string"}},
                              {{"field": "hops", "required": true, "type": "list", "item_type": "string"}},
                              {{"field": "data", "required": true, "type": ["string", "object"]}},
                              {{"field": "destination_address", "required": false, "type": ["string", "null"]}}
                            ]}}
                          ]
                        }},
                        {{
                          "condition": {{"../event_type": "data_received"}},
                          "rules": [
                            {{"field": "message", "required": false, "type": "object", "rules": [
                              {{"field": "type", "required": true, "type": "string"}}
                            ]}},
                            {{"field": "packet", "required": false, "type": "object"}}
                          ]
                        }}
                      ]
                    }}
                  ]
                }}
              ]
            }}
            ```
            
            Pay special attention to these requirements:
            
            1. For "data_received" event type - they can have different structures. Some have a "message" field,
               some have a "packet" field, and some have direct "data" content. Make sure your rules can
               validate all variants properly. Use "required": false for optional fields.
               
            2. For packet data or message data fields, use "type": ["string", "object"] to support both
               string serialized formats and structured object formats.
               
            3. The "hash" field appears outside of individual log entries in the data structure, so it should
               be a top-level field in the rules, not part of individual log validation. Make this clear in its
               description.
               
            4. For entity_id field - even though it might currently only contain null values in the sample logs,
               make sure to specify "type": ["string", "null"] to future-proof the validation for when string
               IDs might be added.
               
            5. For destination_address field in packet_received events - this field can be both string or null,
               so ensure it's specified as "type": ["string", "null"] to handle both cases.
               
            6. IMPORTANT: Make sure the validation for packet_received is as complete as packet_transmitted,
               with the same set of fields validated. Both should validate type, from, to, hops, data, and
               destination_address fields with the same rules.
            
            Follow these specific formatting rules:
            1. Use proper nesting with the "rules" array for object fields
            2. Use "conditional_rules" for validation that depends on field values
            3. When a field can be multiple types, use syntax like: "type": ["string", "null"]
            4. For list fields, use "type": "list", "item_type": "string" and optional "min_items"/"max_items"
            5. Include the "pattern" attribute for fields with specific formats
            6. Add meaningful descriptions for each field
            7. IMPORTANT: DO NOT include actual JSON comments with // notation as they make the JSON invalid.
               Instead, include explanatory information in the "description" field.
            
            Your output must be valid parseable JSON without any comments or non-standard JSON syntax.
            
            Only return the JSON object, nothing else.
            """
            
            # For easier debugging, let's truncate logs in prompt (they can be large)
            debug_prompt = prompt.replace(logs_json, "... [logs truncated for debug log] ...")
            logger.info(f"Prepared prompt: {debug_prompt[:300]}...")
            
            # Generate content using the model
            logger.info("Generating validation schema with Google AI...")
            
            # Generate with safety settings adjusted
            generation_config = {
                "temperature": 0.2,
                "top_p": 0.95,
                "top_k": 0,
                "max_output_tokens": 8192,
            }
            
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
            
            response = self.model.generate_content(
                prompt, 
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            logger.info("Response received from Google AI")
            
            # Parse the response
            result_text = response.text
            logger.info(f"Raw response: {result_text[:300]}...")
            
            # Extract JSON from response
            match = re.search(r'```(?:json)?\s*({.*?})\s*```', result_text, re.DOTALL)
            if match:
                logger.info("Found JSON in code block")
                json_str = match.group(1)
            else:
                logger.info("No code block found, trying to parse entire response")
                json_str = result_text
            
            # Clean up any non-JSON parts
            json_str = re.sub(r'```.*?```', '', json_str, flags=re.DOTALL)
            
            # Clean up comments and other issues
            json_str = clean_json_with_comments(json_str)
            
            # Write the JSON string to a file for debug purposes
            with open("ai_response_debug.json", "w") as f:
                f.write(json_str)
            logger.info("Wrote JSON response to ai_response_debug.json")
            
            try:
                # Try to parse the JSON
                schema = json.loads(json_str)
                logger.info(f"Schema generated with {len(schema.get('rules', []))} top-level rules")
                
                # Validate that the schema has the expected format
                if 'schema_version' not in schema or 'rules' not in schema:
                    logger.warning("Schema missing required top-level keys")
                    raise ValueError("Invalid schema format")
                
                if not isinstance(schema['rules'], list):
                    logger.warning("Schema 'rules' is not a list")
                    raise ValueError("Invalid schema format")
                
                return schema
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                # Try to clean up further by finding just the outermost JSON object
                try:
                    # Use a simpler approach to find and extract JSON
                    start_idx = json_str.find('{"schema_version"')
                    if start_idx >= 0:
                        # Find the matching closing brace by counting braces
                        brace_count = 0
                        end_idx = -1
                        in_string = False
                        escape_next = False
                        
                        for i in range(start_idx, len(json_str)):
                            char = json_str[i]
                            
                            # Handle string boundaries and escapes
                            if char == '\\' and not escape_next:
                                escape_next = True
                                continue
                            
                            if char == '"' and not escape_next:
                                in_string = not in_string
                            
                            escape_next = False
                            
                            # Only count braces outside of strings
                            if not in_string:
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        end_idx = i + 1
                                        break
                        
                        if end_idx > 0:
                            cleaner_json = json_str[start_idx:end_idx]
                            # Clean up the JSON again
                            cleaner_json = clean_json_with_comments(cleaner_json)
                            try:
                                schema = json.loads(cleaner_json)
                                logger.info(f"Schema generated after cleanup with {len(schema.get('rules', []))} top-level rules")
                                return schema
                            except json.JSONDecodeError as inner_e:
                                logger.error(f"Still couldn't parse JSON after cleanup: {str(inner_e)}")
                except Exception as e:
                    logger.error(f"Error during JSON extraction: {str(e)}")
                
                # If all else fails, create fallback schema
                logger.warning("Creating fallback schema due to JSON parse error")
                schema = self.create_fallback_schema(field_info)
                return schema
                
        except Exception as e:
            logger.error(f"Error generating schema with Google AI: {str(e)}")
            traceback.print_exc()
            
            # Create a fallback schema manually
            logger.info("Generating fallback schema based on field analysis")
            schema = self.create_fallback_schema(field_info)
            return schema
    
    def create_fallback_schema(self, field_info: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a basic schema from field information when AI generation fails
        
        Args:
            field_info: Field information dictionary
            
        Returns:
            Basic validation schema
        """
        rules = []
        
        # Map Python types to JSON schema types
        type_mapping = {
            'str': 'string',
            'int': 'integer',
            'float': 'number',
            'bool': 'boolean',
            'dict': 'object',
            'list': 'list',
            'NoneType': 'null'
        }
        
        # Process top-level fields first
        top_level_fields = [field for field in field_info.keys() if '.' not in field]
        for field_path in top_level_fields:
            info = field_info[field_path]
            
            # Skip 'details' field - will handle separately
            if field_path == 'details':
                continue
            
            # Skip 'hash' field - it's not part of the log entries structure
            if field_path == 'hash':
                continue
            
            # Handle entity_id specially
            if field_path == 'entity_id':
                # Always allow both string and null for entity_id
                rule = {
                    "field": field_path,
                    "required": info.get('required', False),
                    "type": ["string", "null"],
                    "description": "The entity identifier that may contain string values in the future."
                }
                rules.append(rule)
                continue
            
            # Handle multiple types
            field_types = info.get('types', [])
            if len(field_types) > 1:
                # Convert each type and put in array
                schema_types = [type_mapping.get(t, 'string') for t in field_types]
                schema_type = schema_types
            else:
                field_type = field_types[0] if field_types else 'string'
                schema_type = type_mapping.get(field_type, 'string')
            
            # Create rule
            rule = {
                "field": field_path,
                "required": info.get('required', False),
                "type": schema_type,
                "description": f"The {field_path} field for the log entry."
            }
            
            # Add pattern if available
            if info.get('pattern'):
                rule["pattern"] = info.get('pattern')
            
            # Add allowed values if it's an enum
            if info.get('possible_enum', False) and info.get('allowed_values'):
                rule["allowed_values"] = info.get('allowed_values')
            
            rules.append(rule)
        
        # Handle 'details' field
        details_rule = self._create_details_rule(field_info)
        if details_rule:
            rules.append(details_rule)
        
        # Add "hash" field as a top-level field if it appears in the data, but outside log entries
        hash_fields = [field for field in field_info.keys() if field.startswith('hash.')]
        if hash_fields:
            hash_rule = {
                "field": "hash",
                "required": False,
                "type": "object",
                "description": "Hash information for the entire log file, not part of individual log entries.",
                "rules": []
            }
            
            # Add hash subfields
            for hash_field in hash_fields:
                field_name = hash_field.split('.', 1)[1]
                info = field_info.get(hash_field, {})
                
                field_types = info.get('types', [])
                if len(field_types) > 1:
                    schema_type = [type_mapping.get(t, 'string') for t in field_types]
                else:
                    field_type = field_types[0] if field_types else 'string'
                    schema_type = type_mapping.get(field_type, 'string')
                
                # Create field rule
                field_rule = {
                    "field": field_name,
                    "required": info.get('required', False),
                    "type": schema_type,
                    "description": f"The {field_name} field within the hash information."
                }
                
                # Add pattern if available
                if info.get('pattern'):
                    field_rule["pattern"] = info.get('pattern')
                
                # Add allowed values if it's an enum
                if info.get('possible_enum', False) and info.get('allowed_values'):
                    field_rule["allowed_values"] = info.get('allowed_values')
                
                hash_rule["rules"].append(field_rule)
            
            # Add hash rule as a separate validation, not part of log entries
            # We'll add it as a comment in the schema to indicate it's outside log entries
            hash_rule["description"] += " NOTE: This should be validated separately from individual log entries."
            rules.append(hash_rule)
        
        return {
            "schema_version": "1.0",
            "rules": rules
        }
    
    def _create_details_rule(self, field_info: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Helper to create the details rule with proper structure"""
        if 'details' not in field_info and not any(key.startswith('details.') for key in field_info.keys()):
            return None
            
        # Create the details object rule
        details_rule = {
            "field": "details",
            "required": True,
            "type": "object",
            "description": "Detailed information about the log event.",
            "rules": []
        }
        
        # Add direct children of details object
        detail_keys = [k.split('.')[1] for k in field_info.keys() 
                       if k.startswith('details.') and len(k.split('.')) == 2]
        
        # Add each direct child field
        for field in detail_keys:
            field_path = f"details.{field}"
            info = field_info.get(field_path, {})
            
            # Skip 'data' field - will handle separately with conditional rules
            if field == 'data':
                continue
                
            # Handle multiple types
            field_types = info.get('types', [])
            if len(field_types) > 1:
                schema_types = [self._map_type(t) for t in field_types]
                schema_type = schema_types 
            else:
                field_type = field_types[0] if field_types else 'string'
                schema_type = self._map_type(field_type)
            
            # Create field rule
            field_rule = {
                "field": field,
                "required": info.get('required', False),
                "type": schema_type,
                "description": f"The {field} field within details."
            }
            
            # Add pattern if available
            if info.get('pattern'):
                field_rule["pattern"] = info.get('pattern')
            
            # Add allowed values if it's an enum
            if info.get('possible_enum', False) and info.get('allowed_values'):
                field_rule["allowed_values"] = info.get('allowed_values')
            
            details_rule["rules"].append(field_rule)
        
        # Add the data field with conditional rules
        data_rule = self._create_data_rule(field_info)
        if data_rule:
            details_rule["rules"].append(data_rule)
            
        return details_rule
    
    def _create_data_rule(self, field_info: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Create the data field rule with conditional validation"""
        if 'details.data' not in field_info:
            return None
            
        # Build the data object rule
        data_rule = {
            "field": "data",
            "required": field_info.get('details.data', {}).get('required', True),
            "type": "object",
            "description": "Event-specific data.",
            "conditional_rules": []
        }
        
        # Get event types safely
        field_info_event_type = field_info.get("details.event_type", {})
        allowed_values = field_info_event_type.get("allowed_values", [])
        event_types = [] if allowed_values is None else allowed_values
        event_types = [e for e in event_types if e is not None]
        
        for event_type in event_types:
            # Basic structure for the conditional rule
            conditional_rule = {
                "condition": {"../event_type": event_type},
                "rules": []
            }
            
            # Add packet validation for event types that need it
            if event_type in ["packet_transmitted", "packet_received"]:
                packet_rule = {
                    "field": "packet",
                    "required": True,
                    "type": "object",
                    "rules": self._create_packet_field_rules(field_info, event_type)
                }
                conditional_rule["rules"].append(packet_rule)
                
            # Add validation for qkd_initiated events
            elif event_type == "qkd_initiated":
                adapter_rule = {
                    "field": "with_adapter",
                    "required": True,
                    "type": "object",
                    "rules": self._create_adapter_field_rules(field_info)
                }
                conditional_rule["rules"].append(adapter_rule)
                
            # Add validation for data_received events with different possible structures
            elif event_type == "data_received":
                # Check for presence of message field in field_info
                has_message = any(key.startswith("details.data.message.") for key in field_info.keys())
                has_packet = any(key.startswith("details.data.packet.") for key in field_info.keys())
                
                # Handle different possible structures
                if has_message:
                    message_rule = {
                        "field": "message",
                        "required": False,  # Changed to optional since some data_received might use packet
                        "type": "object",
                        "rules": self._create_message_field_rules(field_info)
                    }
                    conditional_rule["rules"].append(message_rule)
                
                if has_packet:
                    packet_rule = {
                        "field": "packet",
                        "required": False,  # Optional since some data_received might use message
                        "type": "object",
                        "rules": self._create_packet_field_rules(field_info, event_type)
                    }
                    conditional_rule["rules"].append(packet_rule)
                
                # Add generic data field for other data_received events
                if not has_message and not has_packet:
                    data_field_rule = {
                        "field": "data",
                        "required": True,
                        "type": ["string", "object"],  # Allow either strings or objects for flexibility
                        "description": "Data content for the data_received event."
                    }
                    conditional_rule["rules"].append(data_field_rule)
                
            # Add validation for data_sent events
            elif event_type == "data_sent":
                data_sent_rules = [
                    {
                        "field": "data",
                        "required": True,
                        "type": ["string", "object"],  # Support both string and object formats
                        "description": "The data being sent, either as a serialized string or object."
                    },
                    {
                        "field": "destination",
                        "required": True,
                        "type": "object",
                        "rules": self._create_entity_field_rules(field_info, "destination")
                    }
                ]
                conditional_rule["rules"].extend(data_sent_rules)
            
            # Only add non-empty conditional rules
            if conditional_rule["rules"]:
                data_rule["conditional_rules"].append(conditional_rule)
        
        # Special handling for message types in data_received events
        message_types = self._extract_message_types(field_info)
        
        # For each message type, create a specialized conditional rule
        for msg_type in message_types:
            conditional_rule = {
                "condition": {
                    "../event_type": "data_received",
                    "./message/type": msg_type
                },
                "rules": [
                    {
                        "field": "message",
                        "required": True,
                        "type": "object",
                        "rules": self._create_message_type_rules(field_info, msg_type)
                    }
                ]
            }
            
            data_rule["conditional_rules"].append(conditional_rule)
        
        return data_rule
    
    def _map_type(self, python_type: str) -> str:
        """Map Python type to JSON schema type"""
        type_mapping = {
            'str': 'string',
            'int': 'integer',
            'float': 'number',
            'bool': 'boolean',
            'dict': 'object',
            'list': 'list',
            'NoneType': 'null'
        }
        return type_mapping.get(python_type, 'string')
    
    def _create_packet_field_rules(self, field_info: Dict[str, Dict[str, Any]], event_type: str) -> List[Dict[str, Any]]:
        """Create validation rules for packet fields"""
        rules = []
        
        # Find all fields that are part of a packet
        packet_fields = [
            k.split('details.data.packet.')[1] 
            for k in field_info.keys() 
            if k.startswith('details.data.packet.') and len(k.split('.')) == 4
        ]
        
        for field in packet_fields:
            field_path = f"details.data.packet.{field}"
            info = field_info.get(field_path, {})
            
            # Get field type
            field_types = info.get('types', [])
            if field == "hops":
                # Special handling for hops array
                rule = {
                    "field": field,
                    "required": True,
                    "type": "list",
                    "item_type": "string",
                    "description": f"The {field} in the packet."
                }
            elif field == "data":
                # Special handling for data field - allow both string and object
                rule = {
                    "field": field,
                    "required": True,
                    "type": ["string", "object"],
                    "description": f"The data content in the packet, which can be a string or parsed object."
                }
            elif field == "destination_address":
                # Special handling for destination_address field - always allow null
                rule = {
                    "field": field,
                    "required": False,
                    "type": ["string", "null"],
                    "description": f"The destination address in the packet (can be null)."
                }
            else:
                # Regular field handling
                if len(field_types) > 1:
                    schema_type = [self._map_type(t) for t in field_types]
                else:
                    field_type = field_types[0] if field_types else 'string'
                    schema_type = self._map_type(field_type)
                
                rule = {
                    "field": field,
                    "required": True if field in ["type", "from", "to"] else False,
                    "type": schema_type,
                    "description": f"The {field} in the packet."
                }
                
            # Add pattern if available
            if info.get('pattern'):
                rule["pattern"] = info.get('pattern')
            
            # Add allowed values if it's an enum
            if info.get('possible_enum', False) and info.get('allowed_values'):
                rule["allowed_values"] = info.get('allowed_values')
            
            rules.append(rule)
        
        return rules
    
    def _create_adapter_field_rules(self, field_info: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create validation rules for adapter fields"""
        rules = []
        
        # Find adapter fields
        adapter_fields = [
            k.split('details.data.with_adapter.')[1]
            for k in field_info.keys()
            if k.startswith('details.data.with_adapter.') and len(k.split('.')) == 4
        ]
        
        for field in adapter_fields:
            field_path = f"details.data.with_adapter.{field}"
            info = field_info.get(field_path, {})
            
            # Handle location field specially
            if field == "location":
                rule = {
                    "field": field,
                    "required": True,
                    "type": "list",
                    "item_type": ["int", "float"],
                    "min_items": 2,
                    "max_items": 2,
                    "description": "The location coordinates of the adapter."
                }
            else:
                # Regular field handling
                field_types = info.get('types', [])
                if len(field_types) > 1:
                    schema_type = [self._map_type(t) for t in field_types]
                else:
                    field_type = field_types[0] if field_types else 'string'
                    schema_type = self._map_type(field_type)
                
                rule = {
                    "field": field,
                    "required": field in ["name", "type", "description", "network"],
                    "type": schema_type,
                    "description": f"The {field} of the adapter."
                }
                
                # Add pattern if available
                if info.get('pattern'):
                    rule["pattern"] = info.get('pattern')
                
                # Add allowed values if it's an enum
                if info.get('possible_enum', False) and info.get('allowed_values'):
                    rule["allowed_values"] = info.get('allowed_values')
            
            rules.append(rule)
        
        return rules
    
    def _create_message_field_rules(self, field_info: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create validation rules for message fields"""
        rules = []
        
        # Find message fields
        message_fields = [
            k.split('details.data.message.')[1]
            for k in field_info.keys()
            if k.startswith('details.data.message.') and len(k.split('.')) == 4
        ]
        
        for field in message_fields:
            field_path = f"details.data.message.{field}"
            info = field_info.get(field_path, {})
            
            # Handle data field specially if it's an array
            if field == "data" and "details.data.message.data[]" in field_info:
                field_info_array = field_info.get("details.data.message.data[]", {})
                item_types = field_info_array.get('types', [])
                
                if item_types:
                    # If the array contains objects (like sender info)
                    if 'dict' in item_types:
                        rule = {
                            "field": field,
                            "required": True,
                            "type": "list",
                            "item_type": "object",
                            "description": "Array of data objects in the message."
                        }
                    # If it's a simple array
                    else:
                        item_type = self._map_type(item_types[0]) if item_types else 'string'
                        rule = {
                            "field": field,
                            "required": True,
                            "type": "list",
                            "item_type": item_type,
                            "description": "Array of data in the message."
                        }
                else:
                    rule = {
                        "field": field,
                        "required": True,
                        "type": "list",
                        "description": "Array of data in the message."
                    }
            else:
                # Regular field handling
                field_types = info.get('types', [])
                if len(field_types) > 1:
                    schema_type = [self._map_type(t) for t in field_types]
                else:
                    field_type = field_types[0] if field_types else 'string'
                    schema_type = self._map_type(field_type)
                
                rule = {
                    "field": field,
                    "required": field == "type",
                    "type": schema_type,
                    "description": f"The {field} of the message."
                }
                
                # Add pattern if available
                if info.get('pattern'):
                    rule["pattern"] = info.get('pattern')
                
                # Add allowed values if it's an enum
                if info.get('possible_enum', False) and info.get('allowed_values'):
                    rule["allowed_values"] = info.get('allowed_values')
            
            rules.append(rule)
        
        return rules
    
    def _extract_message_types(self, field_info: Dict[str, Dict[str, Any]]) -> List[str]:
        """Extract message types from field info"""
        message_types = []
        
        # Find message type field
        if "details.data.message.type" in field_info:
            type_info = field_info["details.data.message.type"]
            allowed_values = type_info.get("allowed_values", [])
            if allowed_values is not None:
                message_types = [v for v in allowed_values if v is not None]
        
        return message_types
    
    def _create_message_type_rules(self, field_info: Dict[str, Dict[str, Any]], message_type: str) -> List[Dict[str, Any]]:
        """Create validation rules for specific message types"""
        rules = [{
            "field": "type",
            "required": True,
            "type": "string",
            "allowed_values": [message_type],
            "description": f"The message type is {message_type}."
        }]
        
        # Add specific rules based on message type
        if message_type == "estimate_error_rate":
            rules.append({
                "field": "data",
                "required": True,
                "type": "list",
                "item_type": "list",
                "item_rules": [
                    {"type": "int"}, {"type": "int"}
                ],
                "description": "The error rate data as a list of integer pairs."
            })
        elif message_type == "reconcile_bases":
            rules.append({
                "field": "data",
                "required": True,
                "type": "list",
                "item_type": "string",
                "allowed_values": ["Z", "X"],
                "description": "The reconciled bases data."
            })
        elif message_type == "shared_bases_indices":
            rules.append({
                "field": "data",
                "required": True,
                "type": "list",
                "item_type": "int",
                "description": "The shared bases indices."
            })
            rules.append({
                "field": "sender",
                "required": True,
                "type": "object",
                "rules": self._create_entity_field_rules(field_info, "sender"),
                "description": "The sender of the shared bases indices."
            })
        
        return rules
    
    def _create_entity_field_rules(self, field_info: Dict[str, Dict[str, Any]], entity_prefix: str) -> List[Dict[str, Any]]:
        """Create validation rules for entity fields (sender, destination)"""
        rules = []
        
        # Try to find entity fields based on the prefix
        entity_fields = []
        for key in field_info.keys():
            # Look for fields that match entity fields in common entity objects
            if (key.startswith(f"details.data.{entity_prefix}.") or 
                key.startswith("details.data.message.sender.") or 
                key.startswith("details.data.with_adapter.")):
                
                # Extract the field name
                parts = key.split(".")
                if len(parts) >= 4:
                    field = parts[-1]
                    if field not in entity_fields:
                        entity_fields.append(field)
        
        # Basic entity fields if none found
        if not entity_fields:
            entity_fields = ["name", "description", "type", "location", "network", "zone", "address"]
        
        for field in entity_fields:
            # Handle location field specially
            if field == "location":
                rule = {
                    "field": field,
                    "required": True,
                    "type": "list",
                    "item_type": ["int", "float"],
                    "min_items": 2,
                    "max_items": 2,
                    "description": f"The location coordinates of the {entity_prefix}."
                }
            # Handle address field specially for classical hosts
            elif field == "address" and entity_prefix == "destination":
                rule = {
                    "field": field,
                    "required": True,
                    "type": "string",
                    "pattern": "^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$",
                    "description": f"The IP address of the {entity_prefix}."
                }
            else:
                # Regular field
                rule = {
                    "field": field,
                    "required": field in ["name", "type", "description", "network"],
                    "type": "string",
                    "description": f"The {field} of the {entity_prefix}."
                }
                
                # Add allowed values for type field
                if field == "type":
                    if entity_prefix == "destination":
                        rule["allowed_values"] = ["classical_host"]
                    elif entity_prefix == "sender":
                        rule["allowed_values"] = ["quantum_host"]
            
            rules.append(rule)
        
        return rules
    
    def save_schema_to_file(self, schema: Dict[str, Any], output_file: str) -> bool:
        """
        Save validation schema to a JSON file
        
        Args:
            schema: Schema dictionary
            output_file: File to save the schema to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(schema, f, indent=2)
                
            logger.info(f"Schema saved to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving schema to file: {str(e)}")
            return False

def main():
    """Main function to run the log validator agent"""
    try:
        parser = argparse.ArgumentParser(description="Log Validator Agent")
        parser.add_argument("--pattern", "-p", type=str, default="network-sim:log:*",
                          help="Redis key pattern to match log entries")
        parser.add_argument("--validate", "-v", action="store_true",
                          help="Validate logs against permanent rules")
        
        args = parser.parse_args()
        
        if args.validate:
            logs = load_logs_from_redis(args.pattern)
            if not logs:
                logger.error("Failed to load log data from Redis")
                return 1
                
            try:
                with open("generated_validation_rules.json", 'r') as f:
                    validation_rules = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load validation rules: {str(e)}")
                return 1
            
            validation_results = validate_logs(logs, validation_rules)
            
            try:
                with open("validation_results.json", 'w') as f:
                    json.dump(validation_results, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save validation results: {str(e)}")
            
            print("\nValidation Results:")
            print("=" * 50)
            print(f"Total logs checked: {len(logs.get('logs', {}))}")
            print(f"Valid logs: {validation_results['stats']['valid_logs']}")
            print(f"Invalid logs: {validation_results['stats']['invalid_logs']}")
            print(f"Validation rate: {validation_results['stats']['validation_rate']:.2f}%")
            
            if validation_results['errors']:
                print("\nDetailed Errors:")
                print("=" * 50)
                for error in validation_results['errors']:
                    print(f"\nLog ID: {error['log_id']}")
                    print(f"Field: {error['field_path']}")
                    print(f"Error: {error['error_message']}")
        else:
            logs = load_logs_from_redis(args.pattern)
            if not logs:
                logger.error("Failed to load logs from Redis")
                return 1
                
            agent = LogAnalyzerAgent()
            schema = agent.analyze_logs(logs)
            
            if agent.save_schema_to_file(schema, "generated_validation_rules.json"):
                logger.info("Successfully created rules and saved to generated_validation_rules.json")
            else:
                logger.error("Failed to save rules")
                return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
