#!/usr/bin/env python3
"""PreCompact hook for the dd-trace-dotnet knowledge base.

When context is about to be compacted (a natural "long session / about to lose context" checkpoint),
remind the model to capture reusable knowledge — but only inside the dd-trace-dotnet repo. Prints a
plain reminder line (injected into context); stays silent otherwise.
"""
import json
import os
import sys


def get_cwd():
    try:
        return (json.load(sys.stdin).get("cwd")) or os.getcwd()
    except Exception:
        return os.getcwd()


def is_dd_trace_dotnet(cwd):
    if not cwd:
        return False
    if os.path.isdir(os.path.join(cwd, "tracer", "build", "_build")):
        return True
    return os.path.basename(os.path.normpath(cwd)).lower() == "dd-trace-dotnet"


cwd = get_cwd()
if not is_dd_trace_dotnet(cwd):
    sys.exit(0)

print(
    "[KNOWLEDGE CAPTURE] Context is compacting. If this session produced reusable, non-obvious "
    "dd-trace-dotnet knowledge (gotchas, where things live, how-tos, decisions), save it now with "
    "`/knowledge-base save` before it is lost."
)
