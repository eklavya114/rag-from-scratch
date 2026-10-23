"""
argument_validation.py

A tool schema describes what arguments SHOULD look like. Nothing
enforces that a model's actual tool call matches it. This file
validates a parsed argument dict against its schema before the tool
ever runs: required fields present, types matching, and no unexpected
extra fields, each returning a clear error the model could plausibly
read and correct on its next turn.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-16-custom-tools"))
from support_tools import create_ticket  # Day 16

from tool_schemas import build_json_schema

JSON_TYPE_CHECKS = {
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
}


def validate_arguments(schema, arguments):
    """
    Validates one argument dict against a tool's JSON schema. Returns
    (True, None) if everything checks out, or (False, error_message)
    on the first problem found: a missing required field, a type
    mismatch, or a field that isn't in the schema at all.
    """
    properties = schema["parameters"]["properties"]
    required = schema["parameters"]["required"]

    # CHECK REQUIRED FIELDS ARE PRESENT.
    for field in required:
        if field not in arguments:
            return False, f"Missing required field '{field}' for tool '{schema['name']}'."

    # REJECT UNEXPECTED EXTRA FIELDS.
    for field in arguments:
        if field not in properties:
            return False, f"Unexpected field '{field}' is not part of '{schema['name']}''s schema."

    # CHECK TYPES MATCH THE SCHEMA.
    for field, value in arguments.items():
        expected_type = properties[field]["type"]
        check = JSON_TYPE_CHECKS.get(expected_type)
        if check is not None and not check(value):
            return False, f"Field '{field}' should be type '{expected_type}', got {type(value).__name__} instead."

    return True, None


def main():
    print("=== Validating Tool Arguments ===\n")

    schema = build_json_schema(create_ticket)
    print(f"Schema for '{schema['name']}':")
    print(f"  required: {schema['parameters']['required']}")
    print(f"  properties: {list(schema['parameters']['properties'].keys())}\n")

    test_cases = [
        ("Valid call", {"issue": "Item arrived damaged", "priority": "high"}),
        ("Missing required field", {"priority": "high"}),
        ("Wrong type", {"issue": 12345}),
        ("Unexpected extra field", {"issue": "Item arrived damaged", "urgency_level": 10}),
    ]

    for label, arguments in test_cases:
        is_valid, error = validate_arguments(schema, arguments)
        status = "VALID" if is_valid else "REJECTED"
        print(f"--- {label} ---")
        print(f"Arguments: {arguments}")
        print(f"Result: {status}" + (f", {error}" if error else ""))
        print()

    print(
        "Why validation protects the tools: a tool function like "
        "create_ticket already checks its own inputs, but it only sees "
        "whatever the model actually sent. Validating against the schema "
        "FIRST catches a malformed call with a specific, actionable error "
        "before it ever reaches the tool, and gives the model something it "
        "can act on next turn ('missing required field') instead of a "
        "generic failure."
    )


if __name__ == "__main__":
    main()
