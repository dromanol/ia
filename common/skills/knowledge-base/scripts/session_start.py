#!/usr/bin/env python3
"""SessionStart hook for the GLOBAL (cross-project) knowledge base.

Injects the curated global knowledge INDEX into the model's context in EVERY session, regardless of
the repository. Prints a SessionStart `additionalContext` JSON object; stays silent (exit 0, no
output) if the index can't be found or is empty.

The knowledge lives in the SOURCE `ia` repo (not the plugin cache), so it persists across plugin
reinstalls and is committable. We resolve that source dir from the local marketplace registration.
"""
import json
import os
import sys


def read_event():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def get_cwd(event):
    return event.get("cwd") or os.getcwd()


def find_knowledge_dir(cwd):
    """Return the global knowledge dir in the SOURCE ia repo, or None. Tries, in order:
    1. $KNOWLEDGE_BASE_DIR_COMMON override.
    2. dromanol marketplace source from ~/.claude/plugins/known_marketplaces.json (authoritative).
    3. sibling `ia` repo next to the working repo.
    """
    candidates = []
    env = os.environ.get("KNOWLEDGE_BASE_DIR_COMMON")
    if env:
        candidates.append(env)

    km = os.path.expanduser(os.path.join("~", ".claude", "plugins", "known_marketplaces.json"))
    try:
        with open(km, encoding="utf-8") as fh:
            data = json.load(fh)
        loc = data.get("dromanol", {}).get("installLocation") or \
            data.get("dromanol", {}).get("source", {}).get("path")
        if loc:
            candidates.append(os.path.join(loc, "common", "skills", "knowledge-base", "knowledge"))
    except Exception:
        pass

    if cwd:
        parent = os.path.dirname(os.path.normpath(cwd))
        candidates.append(os.path.join(parent, "ia", "common", "skills", "knowledge-base", "knowledge"))

    for cand in candidates:
        if cand and os.path.isdir(cand):
            return cand
    return None


def main():
    event = read_event()
    cwd = get_cwd(event)

    kdir = find_knowledge_dir(cwd)
    if not kdir:
        return
    index_path = os.path.join(kdir, "INDEX.md")
    try:
        with open(index_path, encoding="utf-8") as fh:
            content = fh.read().strip()
    except Exception:
        return
    if not content:
        return

    context = (
        "# global knowledge base (auto-loaded)\n"
        "Reusable cross-project knowledge accumulated from past sessions. Use "
        "`/knowledge-base recall <topic>` to pull a full entry, and `/knowledge-base save` to add new "
        "learnings at the end of a session.\n\n" + content
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    main()
