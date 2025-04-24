#!/usr/bin/env python3
"""
JSON Schema Validator for Quantum Network Logs

This script validates structured log files from quantum-classical network simulations
against a JSONSchema and provides corrections for invalid logs.
"""

import json
import os
import sys
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple, Set

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    print("Error: jsonschema package not found. Please install with:")
    print("pip install jsonschema")
    sys.exit(1)


class JSONSchemaValidator:
    """Validates quantum network logs against a JSONSchema."""

    def __init__(self):
        """Initialize the JSON Schema validator."""
        self.schema = self.create_log_schema()
        self.components = set()
        self.event_types = set()
        self.validator = Draft7Validator(self.schema["properties"]["logs"]["items"])

    def create_log_schema(self) -> Dict[str, Any]:
        """
        Create and return a JSON schema for quantum network logs.
        
        Returns:
            JSON schema as a dictionary
        """
        # Define valid event types based on observed logs
        valid_event_types = [
            "creation", "send", "receive", "routing", "encrypt", 
            "decrypt", "complete", "initiate", "buffer", "process"
        ]
        
        # JSON Schema for a log entry
        log_entry_schema = {
            "type": "object",
            "required": ["log_id", "component", "time", "event", "event_type"],
            "properties": {
                "log_id": {
                    "type": "string",
                    "pattern": "^LOG_\\d{4}$",
                    "description": "Unique identifier for the log entry"
                },
                "component": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Name of the component generating the log"
                },
                "time": {
                    "type": "string",
                    "pattern": "^([01]\\d|2[0-3]):([0-5]\\d):([0-5]\\d)$",
                    "description": "Time of the event in HH:MM:SS format"
                },
                "event": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Description of the event"
                },
                "event_type": {
                    "type": "string",
                    "enum": valid_event_types,
                    "description": "Type of event"
                }
            },
            "additionalProperties": False
        }
        
        # Schema for the entire logs file
        logs_schema = {
            "type": "object",
            "required": ["logs"],
            "properties": {
                "logs": {
                    "type": "array",
                    "items": log_entry_schema
                }
            },
            "additionalProperties": False
        }
        
        return logs_schema

    def load_logs(self, file_path: str) -> Dict[str, Any]:
        """
        Load logs from a file.
        
        Args:
            file_path: Path to the logs file
            
        Returns:
            Dictionary with loading result and data or error
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, dict) or "logs" not in data or not isinstance(data["logs"], list):
                return {"success": False, "error": "Invalid log format. Expected JSON with 'logs' array."}
            
            # Collect components and event types
            for log in data["logs"]:
                if "component" in log:
                    self.components.add(log["component"])
                if "event_type" in log:
                    self.event_types.add(log["event_type"])
                    
            return {"success": True, "data": data}
        except FileNotFoundError:
            return {"success": False, "error": f"File not found: {file_path}"}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Error loading logs: {str(e)}"}

    def validate_logs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate logs against the JSON schema.
        
        Args:
            data: Dictionary containing logs to validate
            
        Returns:
            Dictionary with validation results
        """
        logs = data["logs"]
        results = {
            "valid": True,
            "total_logs": len(logs),
            "valid_logs": 0,
            "invalid_logs": 0,
            "log_results": [],
            "components": list(self.components),
            "event_types": list(self.event_types)
        }
        
        # Validate each log entry individually to collect detailed errors
        for i, log in enumerate(logs):
            log_result = {
                "log_index": i,
                "log_id": log.get("log_id", f"UNKNOWN_{i}"),
                "valid": True,
                "errors": [],
                "validation_details": {"missing_fields": [], "invalid_fields": []}
            }
            
            # Check for schema validation errors
            errors = list(self.validator.iter_errors(log))
            
            if errors:
                log_result["valid"] = False
                results["valid"] = False
                results["invalid_logs"] += 1
                
                # Collect specific validation errors
                for error in errors:
                    error_path = ".".join([str(p) for p in error.path]) or "root"
                    
                    if error.validator == 'required':
                        try:
                            missing_field = error.validator_value[0]
                            log_result["errors"].append(f"Missing required field: {missing_field}")
                            log_result["validation_details"]["missing_fields"].append(missing_field)
                        except (IndexError, TypeError):
                            for field in error.validator_value:
                                if field not in log:
                                    log_result["errors"].append(f"Missing required field: {field}")
                                    log_result["validation_details"]["missing_fields"].append(field)
                    
                    elif error.validator == 'pattern':
                        field_name = error.path[-1] if error.path else error_path
                        log_result["errors"].append(f"Field '{field_name}' does not match required pattern")
                        log_result["validation_details"]["invalid_fields"].append(field_name)
                    
                    elif error.validator == 'enum':
                        field_name = error.path[-1] if error.path else error_path
                        allowed_values = ", ".join([str(v) for v in error.validator_value])
                        log_result["errors"].append(
                            f"Field '{field_name}' has invalid value: '{error.instance}'. " +
                            f"Allowed values: {allowed_values}"
                        )
                        log_result["validation_details"]["invalid_fields"].append(field_name)
                    
                    elif error.validator == 'additionalProperties':
                        try:
                            # Get the schema properties
                            valid_properties = set(self.schema["properties"]["logs"]["items"]["properties"].keys())
                            # Get the instance properties
                            instance_properties = set(error.instance.keys())
                            # Find extra properties
                            extra_properties = instance_properties - valid_properties
                            
                            for extra_prop in extra_properties:
                                log_result["errors"].append(f"Unexpected additional field: {extra_prop}")
                                log_result["validation_details"]["invalid_fields"].append(extra_prop)
                        except Exception as e:
                            log_result["errors"].append(f"Invalid additional properties: {str(e)}")
                    
                    else:
                        log_result["errors"].append(f"Validation error at {error_path}: {error.message}")
                        if error.path and error.path[-1] not in log_result["validation_details"]["invalid_fields"]:
                            log_result["validation_details"]["invalid_fields"].append(error.path[-1])
            else:
                results["valid_logs"] += 1
            
            results["log_results"].append(log_result)
        
        return results

    def fix_logs(self, data: Dict[str, Any], validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fix invalid logs based on validation results.
        
        Args:
            data: Original logs data
            validation_results: Validation results
            
        Returns:
            Dictionary with fixed logs
        """
        logs = data["logs"]
        fixed_logs = []
        
        for i, log in enumerate(logs):
            log_result = validation_results["log_results"][i]
            
            if log_result["valid"]:
                # Log is already valid, no changes needed
                fixed_logs.append(log.copy())
            else:
                # Try to fix the log
                fixed_log = self._fix_log(log, log_result)
                fixed_logs.append(fixed_log)
        
        return {"logs": fixed_logs}

    def _fix_log(self, log: Dict[str, Any], log_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply fixes to a single invalid log.
        
        Args:
            log: Original log entry
            log_result: Validation result for this log
            
        Returns:
            Fixed log entry
        """
        fixed_log = log.copy()
        validation_details = log_result["validation_details"]
        
        # Fix missing fields
        for field in validation_details["missing_fields"]:
            if field == "log_id":
                # Generate a log ID based on index if available
                fixed_log["log_id"] = f"LOG_{log_result['log_index']:04d}"
            elif field == "time":
                # Use current time
                fixed_log["time"] = datetime.now().strftime("%H:%M:%S")
            elif field == "event_type":
                # Try to infer event type from event text
                event_text = fixed_log.get("event", "").lower()
                if "created" in event_text:
                    fixed_log["event_type"] = "creation"
                elif "sent" in event_text or "sending" in event_text:
                    fixed_log["event_type"] = "send"
                elif "received" in event_text or "receiving" in event_text:
                    fixed_log["event_type"] = "receive"
                elif "routing" in event_text or "route" in event_text:
                    fixed_log["event_type"] = "routing"
                elif "encrypted" in event_text:
                    fixed_log["event_type"] = "encrypt"
                elif "decrypted" in event_text:
                    fixed_log["event_type"] = "decrypt"
                elif "completed" in event_text or "complete" in event_text:
                    fixed_log["event_type"] = "complete"
                elif "initiating" in event_text or "started" in event_text:
                    fixed_log["event_type"] = "initiate"
                else:
                    fixed_log["event_type"] = "process"  # Default
            elif field == "component":
                # Try to extract component from event
                event_text = fixed_log.get("event", "")
                component_match = re.match(r"^([A-Za-z0-9_-]+)", event_text)
                if component_match:
                    fixed_log["component"] = component_match.group(1)
                else:
                    fixed_log["component"] = "Unknown"
            elif field == "event":
                # Create a default event if component is available
                if "component" in fixed_log:
                    fixed_log["event"] = f"{fixed_log['component']} event"
                else:
                    fixed_log["event"] = "Unknown event"
        
        # Fix invalid fields
        for field in validation_details["invalid_fields"]:
            if field == "log_id" and "log_id" in fixed_log:
                # Fix log_id format
                if not re.match(r"^LOG_\d{4}$", fixed_log["log_id"]):
                    # Extract numbers if present
                    num_match = re.search(r"(\d+)", fixed_log["log_id"])
                    if num_match:
                        num = int(num_match.group(1))
                        fixed_log["log_id"] = f"LOG_{num:04d}"
                    else:
                        fixed_log["log_id"] = f"LOG_{log_result.get('log_index', 0):04d}"
            
            elif field == "time" and "time" in fixed_log:
                # Fix time format
                time_str = fixed_log["time"]
                # Try to parse common formats
                formats = ["%H:%M:%S", "%H.%M.%S", "%H-%M-%S", "%H%M%S"]
                fixed = False
                
                for fmt in formats:
                    try:
                        dt = datetime.strptime(time_str, fmt)
                        fixed_log["time"] = dt.strftime("%H:%M:%S")
                        fixed = True
                        break
                    except ValueError:
                        continue
                
                if not fixed:
                    # If all parsing attempts fail, set current time
                    fixed_log["time"] = datetime.now().strftime("%H:%M:%S")
            
            elif field == "event_type" and "event_type" in fixed_log:
                # Fix event_type to be one of the allowed values
                event_type = fixed_log["event_type"].lower()
                
                # Map similar terms to valid event types
                event_type_map = {
                    "create": "creation",
                    "created": "creation",
                    "generating": "creation",
                    "generated": "creation",
                    
                    "sent": "send",
                    "sending": "send",
                    "transmit": "send",
                    "transmitted": "send",
                    
                    "received": "receive",
                    "receiving": "receive",
                    "get": "receive",
                    "got": "receive",
                    
                    "route": "routing",
                    "routed": "routing",
                    "forwarded": "routing",
                    "forwarding": "routing",
                    
                    "encrypt": "encrypt",
                    "encrypted": "encrypt",
                    "encoding": "encrypt",
                    "encoded": "encrypt",
                    
                    "decrypt": "decrypt",
                    "decrypted": "decrypt",
                    "decoding": "decrypt",
                    "decoded": "decrypt",
                    
                    "complete": "complete",
                    "completed": "complete",
                    "finished": "complete",
                    "done": "complete",
                    
                    "initiate": "initiate",
                    "initiated": "initiate",
                    "start": "initiate",
                    "started": "initiate",
                    "begin": "initiate",
                    "beginning": "initiate",
                    
                    "buffer": "buffer",
                    "buffered": "buffer",
                    "buffering": "buffer",
                    
                    "process": "process",
                    "processed": "process",
                    "processing": "process",
                    "handled": "process",
                    "handling": "process"
                }
                
                # Check if current event_type maps to a valid one
                if event_type in event_type_map:
                    fixed_log["event_type"] = event_type_map[event_type]
                else:
                    # If not found in map, use a default
                    fixed_log["event_type"] = "process"
        
        # Remove any unrecognized fields
        valid_fields = ["log_id", "component", "time", "event", "event_type"]
        field_keys = list(fixed_log.keys())
        for key in field_keys:
            if key not in valid_fields:
                del fixed_log[key]
        
        return fixed_log

    def validate_and_fix_file(self, input_file: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Validate and fix logs from a file.
        
        Args:
            input_file: Path to the input log file
            
        Returns:
            Tuple containing validation results and fixed logs
        """
        # Load logs
        load_result = self.load_logs(input_file)
        if not load_result["success"]:
            print(f"Error: {load_result['error']}")
            return None, None
        
        data = load_result["data"]
        
        # Validate logs
        validation_results = self.validate_logs(data)
        
        # Fix logs if needed
        if not validation_results["valid"]:
            fixed_logs = self.fix_logs(data, validation_results)
        else:
            fixed_logs = data.copy()
        
        return validation_results, fixed_logs
    
    def save_schema(self, output_file: str):
        """
        Save the JSON schema to a file.
        
        Args:
            output_file: Path to the output file
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(self.schema, f, indent=2)
            
            print(f"Schema saved to {output_file}")
        except Exception as e:
            print(f"Error saving schema: {str(e)}")
    
    def save_validation_report(self, results: Dict[str, Any], output_file: str):
        """
        Save validation results to a JSON file.
        
        Args:
            results: Validation results
            output_file: Path to the output file
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"Validation report saved to {output_file}")
        except Exception as e:
            print(f"Error saving validation report: {str(e)}")
    
    def save_fixed_logs(self, fixed_logs: Dict[str, Any], output_file: str):
        """
        Save fixed logs to a JSON file.
        
        Args:
            fixed_logs: Dictionary containing fixed logs
            output_file: Path to the output file
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(fixed_logs, f, indent=2)
            
            print(f"Fixed logs saved to {output_file}")
        except Exception as e:
            print(f"Error saving fixed logs: {str(e)}")


def main():
    """Main function to run the validator."""
    if len(sys.argv) < 2:
        print("Usage: python json_schema_validator.py <input_log_file>")
        return
    
    input_file = sys.argv[1]
    
    # Create validator
    validator = JSONSchemaValidator()
    
    # Validate and fix logs
    validation_results, fixed_logs = validator.validate_and_fix_file(input_file)
    
    if validation_results is None:
        return
    
    # Print summary
    print("\nValidation Summary:")
    print(f"Total logs: {validation_results['total_logs']}")
    print(f"Valid logs: {validation_results['valid_logs']}")
    print(f"Invalid logs: {validation_results['invalid_logs']}")
    print(f"Overall validity: {'Valid' if validation_results['valid'] else 'Invalid'}")
    
    # Generate output files
    output_dir = "json_validation_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save schema
    validator.save_schema(f"{output_dir}/log_schema.json")
    
    # Save validation report
    validator.save_validation_report(validation_results, f"{output_dir}/validation_report.json")
    
    # Save fixed logs
    validator.save_fixed_logs(fixed_logs, f"{output_dir}/corrected_logs.json")


if __name__ == "__main__":
    main() 