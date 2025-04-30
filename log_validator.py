#!/usr/bin/env python3
"""
Log Validator

This module provides functions for validating quantum network simulation logs
against a set of validation rules.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("log_validator")

def validate_logs(logs_data: Dict[str, Any], validation_rules: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate log entries against specified rules
    
    Args:
        logs_data: Dictionary containing quantum network simulation logs
        validation_rules: Schema dictionary with validation rules
        
    Returns:
        Dictionary with validation results and statistics
    """
    result = {
        "overall_valid": True,
        "errors": [],
        "stats": {
            "total_logs": 0,
            "valid_logs": 0,
            "invalid_logs": 0,
            "validation_rate": 0.0
        }
    }
    
    if not logs_data or not isinstance(logs_data, dict):
        result["overall_valid"] = False
        result["errors"].append({
            "log_id": "global",
            "field_path": "",
            "error_message": "Invalid logs data format - expected dictionary"
        })
        return result
    
    logs = logs_data.get('logs', {})
    if not isinstance(logs, dict):
        result["overall_valid"] = False
        result["errors"].append({
            "log_id": "global",
            "field_path": "logs",
            "error_message": "Invalid logs format - expected dictionary"
        })
        return result
    
    # Count total logs excluding the 'hash' entry
    total_logs = len([log_id for log_id in logs.keys() if log_id != 'hash'])
    result["stats"]["total_logs"] = total_logs
    
    for log_id, log_entry in logs.items():
        # Skip validation for the 'hash' entry as it's a special metadata entry
        if log_id == 'hash':
            continue
            
        errors = _validate_log_entry(log_entry, validation_rules)
        if errors:
            result["overall_valid"] = False
            result["errors"].extend([{
                "log_id": log_id,
                "field_path": error["field_path"],
                "error_message": error["error_message"]
            } for error in errors])
            result["stats"]["invalid_logs"] += 1
        else:
            result["stats"]["valid_logs"] += 1
    
    if result["stats"]["total_logs"] > 0:
        result["stats"]["validation_rate"] = (
            result["stats"]["valid_logs"] / result["stats"]["total_logs"] * 100
        )
    
    return result

def _validate_log_entry(log_entry: Any, validation_rules: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Validate a single log entry against its rules
    
    Args:
        log_entry: The log entry to validate
        validation_rules: Schema dictionary with validation rules
        
    Returns:
        List of error dictionaries, empty if no errors
    """
    errors = []
    
    # Get the rules section
    rules = validation_rules.get("rules", [])
    if not rules or not isinstance(rules, list):
        errors.append({
            "field_path": "",
            "error_message": "Invalid or missing validation rules - expected list"
        })
        return errors
    
    # Validate each top-level rule
    for rule in rules:
        field_name = rule.get("field", "")
        if not field_name:
            continue
            
        field_errors = _validate_field(log_entry, rule, field_name, "")
        
        if field_errors:
            errors.extend(field_errors)
    
    return errors

def _validate_field(data: Any, rule: Dict[str, Any], field_name: str, path_prefix: str) -> List[Dict[str, str]]:
    """
    Validate a single field against its rule
    
    Args:
        data: The data object containing the field to validate
        rule: The validation rule for this field
        field_name: The name of the field to validate
        path_prefix: The path prefix for nested fields
        
    Returns:
        List of error dictionaries, empty if no errors
    """
    errors = []
    field_path = f"{path_prefix}{field_name}" if path_prefix else field_name
    
    # For conditional rules, check parent fields first
    if "conditional_rules" in rule and isinstance(rule["conditional_rules"], list):
        return _validate_conditional_rules(data, rule["conditional_rules"], field_name, path_prefix)
    
    # If data is None and field can be null, skip further validation
    field_value = data.get(field_name) if isinstance(data, dict) else None
    
    # Check if field is required
    is_required = rule.get("required", False)
    if is_required and (field_value is None and not _can_be_null(rule)):
        errors.append({
            "field_path": field_path,
            "error_message": f"Required field '{field_path}' is missing"
        })
        return errors
    
    # If field is not present and not required, skip further validation
    if field_value is None:
        return errors
    
    # Validate field type
    expected_types = rule.get("type", "any")
    if expected_types != "any":
        type_valid = _validate_type(field_value, expected_types, field_path)
        if not type_valid["valid"]:
            errors.append({
                "field_path": field_path,
                "error_message": type_valid["error"]
            })
            # Skip further validation if type is wrong
            return errors
    
    # Validate enum values
    if "allowed_values" in rule and rule["allowed_values"]:
        if field_value not in rule["allowed_values"]:
            allowed_values_str = ", ".join([str(v) for v in rule["allowed_values"]])
            errors.append({
                "field_path": field_path,
                "error_message": f"Value '{field_value}' for field '{field_path}' is not among allowed values: {allowed_values_str}"
            })
    
    # Validate string pattern
    if "pattern" in rule and rule["pattern"] and isinstance(field_value, str):
        try:
            pattern = re.compile(rule["pattern"])
            if not pattern.match(field_value):
                errors.append({
                    "field_path": field_path,
                    "error_message": f"Value '{field_value}' for field '{field_path}' does not match pattern '{rule['pattern']}'"
                })
        except re.error:
            errors.append({
                "field_path": field_path,
                "error_message": f"Invalid regex pattern '{rule['pattern']}' for field '{field_path}'"
            })
    
    # Validate nested object fields
    if isinstance(field_value, dict) and "rules" in rule and isinstance(rule["rules"], list):
        for nested_rule in rule["rules"]:
            nested_field = nested_rule.get("field", "")
            if not nested_field:
                continue
            
            nested_errors = _validate_field(field_value, nested_rule, nested_field, f"{field_path}.")
            errors.extend(nested_errors)
    
    # Validate list items
    if isinstance(field_value, list) and "item_type" in rule:
        for i, item in enumerate(field_value):
            item_type_valid = _validate_type(item, rule["item_type"], f"{field_path}[{i}]")
            if not item_type_valid["valid"]:
                errors.append({
                    "field_path": f"{field_path}[{i}]",
                    "error_message": item_type_valid["error"]
                })
            
            # If item is an object and has item_rules, validate each item against those rules
            if isinstance(item, dict) and "item_rules" in rule and isinstance(rule["item_rules"], list):
                for item_rule in rule["item_rules"]:
                    item_field = item_rule.get("field", "")
                    if not item_field:
                        continue
                    
                    item_errors = _validate_field(item, item_rule, item_field, f"{field_path}[{i}].")
                    errors.extend(item_errors)
    
    return errors

def _validate_type(value: Any, expected_types: Union[str, List[str]], field_path: str) -> Dict[str, Any]:
    """
    Validate that the value matches one of the expected types
    
    Args:
        value: The value to validate
        expected_types: String or list of strings of expected types
        field_path: The path to the field for error messages
        
    Returns:
        Dictionary with 'valid' boolean and 'error' message if invalid
    """
    # Initialize result
    result = {
        "valid": False,
        "error": ""
    }
    
    # Convert single type to list
    if isinstance(expected_types, str):
        expected_types = [expected_types]
    
    # Special case for null/None
    if value is None:
        if "null" in expected_types:
            result["valid"] = True
            return result
        else:
            result["error"] = f"Field '{field_path}' is null but null is not an allowed type"
            return result
    
    # Map Python types to schema types
    type_mapping = {
        "string": str,
        "str": str,
        "integer": int,
        "int": int,
        "number": (int, float),
        "float": float,
        "boolean": bool,
        "bool": bool,
        "object": dict,
        "dict": dict,
        "list": list,
        "array": list,
        "null": type(None)
    }
    
    # Check if value matches any of the expected types
    for expected_type in expected_types:
        # Skip 'null' since we already handled it
        if expected_type == "null":
            continue
            
        # Handle 'any' type
        if expected_type == "any":
            result["valid"] = True
            return result
            
        # Get the Python type for this expected_type
        python_type = type_mapping.get(expected_type)
        if not python_type:
            # If we don't recognize the type name, consider it an error
            result["error"] = f"Unknown type '{expected_type}' specified for field '{field_path}'"
            return result
            
        # Check if value is of the expected type
        if isinstance(value, python_type):
            result["valid"] = True
            return result
    
    # If we get here, the value didn't match any of the expected types
    actual_type = type(value).__name__
    expected_types_str = ", ".join(expected_types)
    result["error"] = f"Field '{field_path}' has type '{actual_type}' but expected one of: {expected_types_str}"
    
    return result

def _validate_conditional_rules(data: Any, conditional_rules: List[Dict[str, Any]], field_name: str, path_prefix: str) -> List[Dict[str, str]]:
    """
    Validate field against conditional rules
    
    Args:
        data: The data object to validate
        conditional_rules: List of conditional rules
        field_name: The name of the field to validate
        path_prefix: The path prefix for nested fields
        
    Returns:
        List of error dictionaries, empty if no errors
    """
    errors = []
    
    for conditional_rule in conditional_rules:
        condition = conditional_rule.get("condition", {})
        rules = conditional_rule.get("rules", [])
        
        # Check if condition is met
        condition_met = True
        for condition_field, expected_value in condition.items():
            # Handle parent reference notation (../field_name)
            if condition_field.startswith("../"):
                parent_field = condition_field[3:]  # Remove '../'
                # Handle parent object since we're in a nested field
                if isinstance(data, dict) and parent_field in data:
                    actual_value = data.get(parent_field)
                    if actual_value != expected_value:
                        condition_met = False
                        break
                else:
                    condition_met = False
                    break
            else:
                # Regular field reference
                if isinstance(data, dict) and condition_field in data:
                    actual_value = data.get(condition_field)
                    if actual_value != expected_value:
                        condition_met = False
                        break
                else:
                    condition_met = False
                    break
        
        # If condition is met, apply these rules
        if condition_met:
            for rule in rules:
                rule_field = rule.get("field", "")
                if not rule_field:
                    continue
                
                field_errors = _validate_field(data.get(field_name, {}), rule, rule_field, f"{path_prefix}{field_name}.")
                errors.extend(field_errors)
    
    return errors

def _can_be_null(rule: Dict[str, Any]) -> bool:
    """
    Check if a field can be null based on its type definition
    
    Args:
        rule: The rule to check
        
    Returns:
        Boolean indicating if null is an acceptable value
    """
    expected_types = rule.get("type", "any")
    
    if expected_types == "any":
        return True
        
    if isinstance(expected_types, str):
        return expected_types == "null"
        
    if isinstance(expected_types, list):
        return "null" in expected_types
        
    return False

def pinpoint_message(validation_result: Dict[str, Any]) -> str:
    """
    Generate a human-readable message from validation results
    
    Args:
        validation_result: Dictionary containing validation results
        
    Returns:
        String with formatted validation message
    """
    if validation_result["overall_valid"]:
        return "All logs are valid"
    
    error_count = len(validation_result["errors"])
    if error_count == 1:
        error = validation_result["errors"][0]
        return f"Found 1 error in log {error['log_id']}: {error['error_message']}"
    
    return f"Found {error_count} errors in logs"

def load_and_validate(logs_file: str, rules_file: str) -> Dict[str, Any]:
    """
    Load logs and rules from files and validate
    
    Args:
        logs_file: Path to logs JSON file
        rules_file: Path to rules JSON file
        
    Returns:
        Dictionary with validation results
    """
    try:
        with open(logs_file, 'r') as f:
            logs = json.load(f)
        with open(rules_file, 'r') as f:
            rules = json.load(f)
        return validate_logs(logs, rules)
    except Exception as e:
        logger.error(f"Error loading or validating files: {str(e)}")
        return {
            "overall_valid": False,
            "errors": [{"log_id": "global", "field_path": "", "error_message": str(e)}],
            "stats": {"total_logs": 0, "valid_logs": 0, "invalid_logs": 0, "validation_rate": 0.0}
        }

if __name__ == "__main__":
    # Example usage when run directly
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python log_validator.py <logs_file> <rules_file>")
        sys.exit(1)
    
    logs_file = sys.argv[1]
    rules_file = sys.argv[2]
    
    validation_result = load_and_validate(logs_file, rules_file)
    message = pinpoint_message(validation_result)
    
    print(message)
    
    # Exit with appropriate status code
    sys.exit(0 if validation_result["overall_valid"] else 1) 