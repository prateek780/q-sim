#!/usr/bin/env python3
import json
import os
import re
import datetime
import argparse
from datetime import datetime, timedelta

# Fix for dotenv import issue
try:
    from python_dotenv import load_dotenv
except ImportError:
    try:
        from dotenv import load_dotenv
    except ImportError:
        # Define a simple load_dotenv function if the package is not available
        def load_dotenv():
            print("Warning: dotenv package not found, using fallback method")
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value

# Try direct import of groq for AI processing
try:
    from groq import Groq
    USE_GROQ = True
except ImportError:
    USE_GROQ = False
    print("Warning: Groq package not found. Will use rule-based processing only.")

# Load environment variables for API keys
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def extract_component(log_line):
    """Extract the component name from a log line"""
    # Common component types in our logs
    component_patterns = [
        r'(ClassicalHost-\d+)',
        r'(ClassicalRouter-\d+)',
        r'(QuantumHost-\d+)',
        r'(QuantumAdapter-\d+)',
        r'(QC_Router_QuantumAdapter-\d+)',
        r'(Internet Exchange)',
        r'(Quantum channel)',
        r'(Start(?:ClassicalHost-\d+))'
    ]
    
    # Check for timestamped format: [HH:MM:SS] Component: Message
    timestamp_format = re.match(r'\[(\d{2}:\d{2}:\d{2})\]\s+(\w+[-\d]*):?', log_line)
    if timestamp_format:
        return timestamp_format.group(2)
    
    # First, check if the line starts with a component name (no timestamp prefix)
    # This handles logs like "ClassicalHost-1 created"
    first_word = log_line.split(' ')[0]
    for pattern in component_patterns:
        if re.match(pattern, first_word):
            return first_word
    
    # Then check for components anywhere in the line
    for pattern in component_patterns:
        match = re.search(pattern, log_line)
        if match:
            return match.group(1)
    
    # If no specific component found, try to extract any entity at the start of the line
    match = re.match(r'^(\w+)', log_line)
    if match:
        return match.group(1)
    
    return "Unknown"

def identify_event_type(log_line):
    """Identify the type of event in a log line"""
    # Check for component creation
    if re.search(r'created', log_line, re.IGNORECASE):
        return "creation"
    # Check for sending events
    elif re.search(r'(sending|sent|transmitting)', log_line, re.IGNORECASE):
        return "send"
    # Check for receiving events
    elif re.search(r'(receiving|received)', log_line, re.IGNORECASE):
        return "receive"
    # Check for routing events
    elif re.search(r'(routing|routed|forwarding)', log_line, re.IGNORECASE):
        return "routing"
    # Check for encryption events
    elif re.search(r'(encrypt|encrypted)', log_line, re.IGNORECASE):
        return "encrypt"
    # Check for decryption events
    elif re.search(r'(decrypt|decrypted)', log_line, re.IGNORECASE):
        return "decrypt"
    # Check for initiation events
    elif re.search(r'(initiating|initiated)', log_line, re.IGNORECASE):
        return "initiate"
    # Check for completion events
    elif re.search(r'(completed|established|successfully)', log_line, re.IGNORECASE):
        return "complete"
    # Check for processing events
    elif re.search(r'(processing)', log_line, re.IGNORECASE):
        return "process"
    # Check for quantum-specific events
    elif re.search(r'(qubit|quantum|QKD)', log_line, re.IGNORECASE):
        return "quantum"
    # Check for forwarding events
    elif "forwarding" in log_line:
        return "forwarding"
    # Check for event handling
    elif "received event" in log_line:
        return "event_handling"
    # Check for classical data received
    elif "received classical data" in log_line:
        return "classical_data_received"
    # Default event type
    else:
        return "other"

def process_with_ai(log_lines):
    """Use Groq AI to enhance log parsing"""
    if not USE_GROQ or not GROQ_API_KEY:
        print("Groq API not available, skipping AI processing")
        return None
    
    client = Groq(api_key=GROQ_API_KEY)
    
    # Sample of logs to send to the AI
    sample_logs = log_lines[:min(20, len(log_lines))]
    sample_text = "\n".join(sample_logs)
    
    prompt = f"""
    I need to parse the following network simulation logs into structured JSON entries.
    Here are some sample log lines:
    
    ```
    {sample_text}
    ```
    
    For each log line, extract:
    1. Component - The network component generating the log (e.g., ClassicalHost-1, QuantumAdapter-3)
    2. Event - A descriptive summary of what happened
    3. Event Type - A category for the event (creation, message_sent, packet_received, etc.)
    
    Return a JSON object with parsing rules I can use for each type of log line pattern.
    Format:
    {{
        "patterns": [
            {{
                "regex": "REGEX_PATTERN",
                "component_group": GROUP_NUMBER_FOR_COMPONENT,
                "event_template": "TEMPLATE_WITH_PLACEHOLDERS",
                "event_type": "TYPE_OF_EVENT"
            }}
        ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a log parsing expert, creating regular expressions and rules to extract structured data from logs."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content
        # Extract JSON from response
        json_start = result.find('{')
        json_end = result.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_content = result[json_start:json_end]
            try:
                return json.loads(json_content)
            except json.JSONDecodeError:
                print("Could not parse AI response as JSON")
        
    except Exception as e:
        print(f"Error using Groq API: {str(e)}")
    
    return None

def format_logs(input_file, output_file):
    """Convert log.txt into structured JSON format"""
    print(f"Converting {input_file} to structured JSON format...")
    
    # Read the input log file
    with open(input_file, 'r', encoding='utf-8') as f:
        log_lines = [line.strip() for line in f.readlines() if line.strip()]
    
    print(f"Found {len(log_lines)} log entries in {input_file}")
    
    # Try AI-based processing first
    ai_patterns = process_with_ai(log_lines)
    
    # Start time for log entries (since logs may not have timestamps)
    # Use a fixed start time and increment for each log entry
    start_time = datetime.now().replace(microsecond=0) - timedelta(minutes=len(log_lines))
    
    structured_logs = []
    
    # Process each log line
    for i, line in enumerate(log_lines):
        # Generate timestamp
        timestamp = (start_time + timedelta(seconds=i)).strftime("%H:%M:%S")
        
        # Generate log ID
        log_id = f"LOG_{i:04d}"
        
        # Extract component
        component = extract_component(line)
        
        # Determine event type
        event_type = identify_event_type(line)
        
        # Create structured log entry
        log_entry = {
            "log_id": log_id,
            "component": component,
            "time": timestamp,
            "event": line,
            "event_type": event_type
        }
        
        structured_logs.append(log_entry)
    
    # Verify all logs were processed
    if len(structured_logs) != len(log_lines):
        print(f"WARNING: Not all logs were processed! Expected {len(log_lines)}, got {len(structured_logs)}")
    
    # Write structured logs to output file
    output_data = {"logs": structured_logs}
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Converted {len(structured_logs)} log entries to JSON format")
    print(f"Output written to {output_file}")
    
    return structured_logs

def main():
    parser = argparse.ArgumentParser(description="Convert log.txt to structured JSON format")
    parser.add_argument("--input", default="log.txt", help="Input log file")
    parser.add_argument("--output", default="structured_logs.json", help="Output JSON file")
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        return 1
    
    # Process the logs
    format_logs(args.input, args.output)
    
    return 0

if __name__ == "__main__":
    main() 