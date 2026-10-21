"""
tool_builder.py

Day 15's tool_registry.py required typing out a tool's name,
description, and parameter list by hand. This file automates that:
given a plain Python function with a docstring, it reads the
function's real name and parameter names with the `inspect` module and
registers it automatically -- so the documentation can never drift out
of sync with the function's actual signature.
"""

import inspect
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-15-agentic-ai"))
from tool_registry import ToolRegistry  # Day 15


def build_tool_from_function(registry, function):
    """
    AUTO-REGISTER A PLAIN FUNCTION AS A TOOL:
    1. Read the function's real name via inspect, so the registered
       name always matches the actual callable.
    2. Read its docstring to use as the description an agent reads.
    3. Read its parameter names via inspect.signature, so the
       parameter list is generated from the real signature instead of
       typed out separately (and possibly getting out of sync with it).
    """
    name = function.__name__
    description = (function.__doc__ or "No description provided.").strip().splitlines()[0]
    parameters = list(inspect.signature(function).parameters.keys())

    registry.register(
        name=name,
        function=function,
        description=description,
        parameters=parameters,
    )
    return name, description, parameters


def add_numbers(a, b):
    """Adds two numbers together and returns the sum."""
    return a + b


def greet_customer(customer_name, greeting="Hello"):
    """Builds a greeting message for a customer, using a custom greeting word if given."""
    return f"{greeting}, {customer_name}!"


def main():
    print("=== Turning Plain Functions Into Tools ===\n")

    registry = ToolRegistry()

    for function in (add_numbers, greet_customer):
        name, description, parameters = build_tool_from_function(registry, function)
        print(f"Registered '{name}'")
        print(f"  description: {description}")
        print(f"  parameters:  {parameters}\n")

    print("--- What the agent would see (auto-generated docs) ---\n")
    print(registry.get_documentation())

    print("\n--- Calling the auto-registered tools ---\n")
    print(f"add_numbers(2, 3) -> {registry.call('add_numbers', 2, 3)}")
    print(f"greet_customer('Jordan') -> {registry.call('greet_customer', 'Jordan')}")
    print(f"greet_customer('Jordan', 'Welcome back') -> {registry.call('greet_customer', 'Jordan', 'Welcome back')}")

    print(
        "\nWhy this matters: hand-writing a tool's description and parameter "
        "list is one more place for it to drift out of sync with the "
        "function it describes. Generating both straight from the function "
        "itself means the agent's view of the tool can never lie about what "
        "the tool actually accepts."
    )


if __name__ == "__main__":
    main()
