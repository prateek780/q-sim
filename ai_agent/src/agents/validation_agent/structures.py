from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class ValidationStatus(Enum):
    PASSED = "Passed"
    PASSED_WITH_WARNINGS = "Passed with Warnings"
    FAILED = "Failed"
    FAILED_WITH_ERRORS = "Failed with Errors"
    FAILED_RETRY_RECOMMENDED = "Failed - Retry Recommended"
    MANUAL_REVIEW_REQUIRED = "Manual Review Required"

class ValidationIssue(BaseModel):
    issue_type: str = Field(description="Category of the issue (e.g., 'MissingComponent', 'IncorrectConnection', 'UnnecessaryComponent', 'LogicalError', 'PlausibilityWarning', 'SchemaCompliance').")
    description: str = Field(description="A human-readable explanation of the validation issue found.")
    relevant_query_part: Optional[str] = Field(None, description="The part of the user's original query related to this issue, if applicable.")
    relevant_topology_path: Optional[str] = Field(None, description="JSONPath or dot-notation path to the problematic part in the generated topology, if applicable.")
    suggestion_for_fix: Optional[str] = Field(None, description="A specific suggestion on how the generating agent could address this issue in a retry.")


class TopologyValidationResult(BaseModel):
    validation_status: ValidationStatus = Field(description="Overall status of the validation.")   
    static_errors: List[str] = []
    summary: str = Field(description="A brief overall summary of the validation findings.")
    issues_found: List[ValidationIssue] = Field(default=[], description="A list of specific validation issues identified.")
    regeneration_feedback: Optional[str] = Field(None, description="Consolidated feedback and specific instructions for the Generating Agent if a retry is recommended. This should be a clear, actionable prompt addition or modification.")