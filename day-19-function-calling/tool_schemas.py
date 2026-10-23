"""
tool_schemas.py

Function calling needs each tool described as a JSON schema instead of
a prose description. This file builds that schema straight from a
Python function's real signature and docstring, using the inspect
module, the same no-drift idea as Day 16's tool_builder.py, just
producing JSON instead of a ToolRegistry entry.
"""

import inspect
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-16-custom-tools"))
from support_tools import check_refund_eligibility, create_ticket, lookup_order  # Day 16

PYTHON_TYPE_TO_JSON_TYPE = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}


def infer_json_type(default_value):
    """
    Maps a Python value's type to its JSON schema equivalent. Day 16's
    tools have no type annotations, so this infers a type from the
    parameter's default value when one exists, and falls back to
    "string" (the most common tool argument type in this project) when
    there is no default to inspect.
    """
    if default_value is inspect.Parameter.empty:
        return "string"
    return PYTHON_TYPE_TO_JSON_TYPE.get(type(default_value), "string")


def build_json_schema(function):
    """
    Builds a JSON schema for one function:
      - "name": the function's real name, read via inspect so it can
        never drift from the actual callable.
      - "description": the function's docstring, what the model reads
        to decide when this tool is the right one to call.
      - "parameters": a JSON Schema object describing the function's
        arguments: each one's inferred "type", and which ones have no
        default and are therefore "required".
    """
    name = function.__name__
    description = (function.__doc__ or "No description provided.").strip().splitlines()[0]

    signature = inspect.signature(function)
    properties = {}
    required = []

    for param_name, param in signature.parameters.items():
        properties[param_name] = {
            "type": infer_json_type(param.default),
            "description": f"The {param_name.replace('_', ' ')} argument for {name}.",
        }
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


def main():
    print("=== Building JSON Schemas From Tool Functions ===\n")

    for function in (lookup_order, check_refund_eligibility, create_ticket):
        schema = build_json_schema(function)
        print(json.dumps(schema, indent=2))
        print()

    print(
        "Field notes:\n"
        "  name: read from the function itself, cannot drift from reality.\n"
        "  description: the function's docstring, what tells the model when to use this tool.\n"
        "  parameters.properties: one entry per argument, with an inferred type.\n"
        "  parameters.required: arguments with no default value, which the model must always supply.\n"
    )

    print(
        "Why this matters: a schema generated this way can never claim a "
        "parameter is optional when the function actually requires it, or "
        "describe a tool using text the function's own docstring doesn't "
        "support, the same no-drift guarantee Day 16's tool_builder.py gave "
        "the Day 15 ToolRegistry, just in the JSON shape a real function "
        "calling API expects instead."
    )


if __name__ == "__main__":
    main()
