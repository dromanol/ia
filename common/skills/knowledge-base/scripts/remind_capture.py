#!/usr/bin/env python3
"""PreCompact hook for the knowledge bases (global + the current project's, if it has one).

When context is about to be compacted (a natural "long session / about to lose context" checkpoint),
remind the model to capture reusable knowledge. Fires in every session, regardless of repo; when the
canonical `ia` repo has a `project-knowledge` skill for the current project it also names that store,
so both tiers get a prompt from this single hook. Prints a plain reminder line (injected into context).
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "scripts"))
try:
    from link_project_skills import PROJECT_KB, canonical_ia, find_repo_root
except Exception:  # never let a broken import block compaction
    PROJECT_KB, canonical_ia, find_repo_root = None, None, None


def get_cwd():
    try:
        return json.load(sys.stdin).get("cwd") or os.getcwd()
    except Exception:
        return os.getcwd()


def project_with_knowledge(cwd):
    """Return the current project's name if the canonical `ia` repo holds a knowledge base for it."""
    if not canonical_ia:
        return None
    try:
        repo_root = find_repo_root(cwd)
        project = os.path.basename(os.path.normpath(repo_root))
        ia = canonical_ia()
        if not ia:
            return None
        if os.path.isdir(os.path.join(ia, project, "skills", PROJECT_KB)):
            return project
    except Exception:
        pass
    return None


project = project_with_knowledge(get_cwd())

msg = (
    "[KNOWLEDGE CAPTURE] Context is compacting. If this session produced reusable, non-obvious "
    "CROSS-PROJECT knowledge (internal tools/commands, org conventions, recurring how-tos, decisions), "
    "save it now with `/knowledge-base save` before it is lost."
)
if project:
    msg += (
        " Knowledge specific to `{p}` (gotchas, where things live, build/test pitfalls) belongs in its "
        "own store instead: `/{kb} save`.".format(p=project, kb=PROJECT_KB)
    )
else:
    msg += " Repo-specific knowledge belongs in that project's own knowledge base instead."

print(msg)
