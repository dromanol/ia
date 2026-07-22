#!/usr/bin/env python3
"""PreCompact hook for the GLOBAL (cross-project) knowledge base.

When context is about to be compacted (a natural "long session / about to lose context" checkpoint),
remind the model to capture reusable cross-project knowledge. Fires in every session, regardless of
repo. Prints a plain reminder line (injected into context).
"""

print(
    "[GLOBAL KNOWLEDGE CAPTURE] Context is compacting. If this session produced reusable, non-obvious "
    "CROSS-PROJECT knowledge (internal tools/commands, org conventions, recurring how-tos, decisions), "
    "save it now with `/knowledge-base save` before it is lost. Repo-specific knowledge belongs in that "
    "repo's own plugin instead."
)
