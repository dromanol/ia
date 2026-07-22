#!/usr/bin/env python3
"""SessionStart bootstrap: surface per-project skills that live OUTSIDE the repo.

Convention (see ia/README.md): each clone lays out sibling directories under a common parent, e.g.

    <parent>/<project>/      <- the working repo (Claude's cwd)
    <parent>/ia/<project>/   <- personal, per-project skills for that repo

Claude Code auto-discovers skills under a repo's `.claude/skills/<name>/`, and follows symlinks /
junctions there. So we link each `<parent>/ia/<project>/skills/<name>` into
`<repo>/.claude/skills/<name>` (Windows: directory junction, no admin needed). This makes the
external skills first-class invocable WITHOUT registering a per-project plugin or marketplace.

Caveats (by design, not bugs):
  * Skills are enumerated at startup, BEFORE this hook runs. A *newly* created link only becomes
    invocable on the NEXT session / `/reload-plugins`. Already-present links work immediately.
  * We add each linked name to `<repo>/.git/info/exclude` so the junctions don't pollute `git status`
    (some repos, e.g. dd-trace-dotnet, track `.claude/skills/`).

This hook is a strict no-op for any repo that has no sibling `../ia/<project>/skills` directory.
It never blocks the session and swallows all errors.
"""
import json
import os
import subprocess
import sys


def read_event():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def get_cwd(event):
    return event.get("cwd") or os.getcwd()


def find_repo_root(cwd):
    """Walk up from cwd until a `.git` entry is found; return that dir, or cwd if none."""
    cur = os.path.abspath(cwd)
    while True:
        if os.path.exists(os.path.join(cur, ".git")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return os.path.abspath(cwd)
        cur = parent


def create_link(dest, src):
    """Create a directory junction (Windows) or symlink (POSIX) at dest -> src."""
    try:
        if os.name == "nt":
            r = subprocess.run(
                ["cmd", "/c", "mklink", "/J", dest, src],
                capture_output=True, text=True,
            )
            return r.returncode == 0
        os.symlink(src, dest)
        return True
    except Exception:
        return False


def add_git_exclude(repo_root, name):
    """Add `.claude/skills/<name>/` to the repo's local (non-committed) git exclude file."""
    exclude = os.path.join(repo_root, ".git", "info", "exclude")
    line = "/.claude/skills/{}/".format(name)
    try:
        os.makedirs(os.path.dirname(exclude), exist_ok=True)
        existing = ""
        if os.path.isfile(exclude):
            with open(exclude, encoding="utf-8") as fh:
                existing = fh.read()
        if line in existing:
            return
        with open(exclude, "a", encoding="utf-8") as fh:
            if existing and not existing.endswith("\n"):
                fh.write("\n")
            fh.write(line + "\n")
    except Exception:
        pass


def read_knowledge_index(ia_skills):
    """If the linked project ships a knowledge-base skill, return its INDEX.md content."""
    index_path = os.path.join(ia_skills, "knowledge-base", "knowledge", "INDEX.md")
    try:
        with open(index_path, encoding="utf-8") as fh:
            return fh.read().strip()
    except Exception:
        return ""


def main():
    event = read_event()
    cwd = get_cwd(event)
    repo_root = find_repo_root(cwd)
    project = os.path.basename(os.path.normpath(repo_root))
    ia_skills = os.path.join(os.path.dirname(repo_root), "ia", project, "skills")
    if not os.path.isdir(ia_skills):
        return  # no sibling per-project skills -> no-op

    dest_dir = os.path.join(repo_root, ".claude", "skills")
    try:
        os.makedirs(dest_dir, exist_ok=True)
    except Exception:
        return

    already, newly = [], []
    for name in sorted(os.listdir(ia_skills)):
        src = os.path.join(ia_skills, name)
        if not os.path.isdir(src) or not os.path.isfile(os.path.join(src, "SKILL.md")):
            continue
        dest = os.path.join(dest_dir, name)
        if os.path.exists(dest) or os.path.islink(dest):
            already.append(name)
            continue
        if create_link(dest, src):
            newly.append(name)
            add_git_exclude(repo_root, name)

    if not already and not newly:
        return  # nothing to report

    parts = ["# Project skills for `{}` (auto-linked by `common` from `{}`)".format(project, ia_skills)]
    if already:
        parts.append("Available now (invocable): " + ", ".join("`{}`".format(n) for n in already) + ".")
    if newly:
        parts.append(
            "Newly linked this session: " + ", ".join("`{}`".format(n) for n in newly) + ". "
            "These become invocable after you restart Claude Code or run `/reload-plugins`."
        )

    index = read_knowledge_index(ia_skills)
    if index:
        parts.append(
            "\n---\n# {} knowledge base (auto-loaded)\n"
            "Use `/knowledge-base recall <topic>` to pull a full entry, "
            "`/knowledge-base save` to add learnings.\n\n{}".format(project, index)
        )

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n\n".join(parts),
            "reloadSkills": True,
        }
    }))


if __name__ == "__main__":
    main()
