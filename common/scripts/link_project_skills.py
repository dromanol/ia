#!/usr/bin/env python3
"""SessionStart bootstrap: copy per-project skills from the canonical `ia` repo into the clone.

The `common` plugin acts as a bootstrapper. At session start it copies the skills for the current
project from the single source of truth -- the `ia` marketplace repo (`C:\\_dd\\git\\ia`) -- into the
working clone's `.claude/skills/`, which Claude Code auto-discovers. This means the external,
personal per-project skills become first-class invocable WITHOUT registering a per-project plugin or
marketplace, and there is exactly ONE place to edit them.

    <ia>/<project>/skills/<name>/   ->   <clone>/.claude/skills/<name>/   (plain copy, source wins)

Design notes (by intent, not bugs):
  * Source of truth is the canonical `ia` repo (resolved from the `dromanol` marketplace registration),
    NOT a per-clone sibling. Every clone gets the same skills copied in.
  * The source wins: managed copies are refreshed every session; local edits to the copy are discarded.
    Edit the skills in the `ia` repo, not in the clone.
  * Each managed copy carries a `.ia-managed` marker. A same-named directory WITHOUT the marker is a
    foreign skill (e.g. a repo's own committed `.claude/skills/<name>`) and is left untouched.
  * Junctions/symlinks left by the previous design are removed safely (the link only, never the target)
    and replaced by a real copy.
  * Managed copies whose source skill no longer exists are pruned.
  * Copied names are added to `<clone>/.git/info/exclude` so they don't pollute `git status`.
  * Skills are enumerated at startup BEFORE this hook runs: a newly copied skill becomes invocable only
    on the NEXT session / `/reload-plugins`; refreshed existing ones work immediately.

Strict no-op when the canonical `ia` has no `<project>/skills` for the current repo. Never blocks the
session; swallows all errors.
"""
import json
import os
import shutil
import sys

MARKER = ".ia-managed"


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


def canonical_ia():
    """Resolve the single source-of-truth `ia` repo. Tries, in order:
    1. $IA_ROOT override.
    2. `dromanol` marketplace installLocation/source from ~/.claude/plugins/known_marketplaces.json.
    3. The `ia` dir derived from this script's own location (<ia>/common/scripts/this.py).
    """
    env = os.environ.get("IA_ROOT")
    if env and os.path.isdir(env):
        return env

    km = os.path.expanduser(os.path.join("~", ".claude", "plugins", "known_marketplaces.json"))
    try:
        with open(km, encoding="utf-8") as fh:
            data = json.load(fh)
        entry = data.get("dromanol", {})
        loc = entry.get("installLocation") or entry.get("source", {}).get("path")
        if loc and os.path.isdir(loc):
            return loc
    except Exception:
        pass

    try:
        here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if os.path.isdir(here):
            return here
    except Exception:
        pass
    return None


def is_link_or_junction(path):
    """True if path is a symlink (POSIX) or a reparse point / junction (Windows)."""
    if os.path.islink(path):
        return True
    try:
        st = os.lstat(path)
        return bool(getattr(st, "st_reparse_tag", 0)) or bool(st.st_file_attributes & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT
    except Exception:
        return False


def remove_dest(path):
    """Remove a destination entry without ever following a link/junction into its target."""
    if is_link_or_junction(path):
        try:
            os.rmdir(path)   # removes the link/junction itself, not the target
        except OSError:
            try:
                os.unlink(path)
            except Exception:
                pass
        return
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    elif os.path.exists(path):
        try:
            os.unlink(path)
        except Exception:
            pass


def add_git_exclude(repo_root, name):
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


def read_knowledge_index(src_skills):
    index_path = os.path.join(src_skills, "knowledge-base", "knowledge", "INDEX.md")
    try:
        with open(index_path, encoding="utf-8") as fh:
            return fh.read().strip()
    except Exception:
        return ""


def missing_required_siblings(ia, project, repo_root):
    """Read <ia>/<project>/required-siblings.json and return [(name, reason), ...] for the sibling
    repos it declares that are NOT present next to the clone (same parent dir). Empty if no manifest."""
    manifest = os.path.join(ia, project, "required-siblings.json")
    try:
        with open(manifest, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return []
    parent = os.path.dirname(os.path.normpath(repo_root))
    missing = []
    for entry in data.get("required_siblings", []):
        name = entry.get("name") if isinstance(entry, dict) else entry
        reason = entry.get("reason", "") if isinstance(entry, dict) else ""
        if not name:
            continue
        if not os.path.isdir(os.path.join(parent, name)):
            missing.append((name, reason))
    return missing


def main():
    event = read_event()
    cwd = get_cwd(event)
    repo_root = find_repo_root(cwd)
    project = os.path.basename(os.path.normpath(repo_root))

    ia = canonical_ia()
    if not ia:
        return
    src_skills = os.path.join(ia, project, "skills")
    if not os.path.isdir(src_skills):
        return  # canonical ia has nothing for this project -> no-op

    dest_dir = os.path.join(repo_root, ".claude", "skills")
    try:
        os.makedirs(dest_dir, exist_ok=True)
    except Exception:
        return

    src_names = set()
    refreshed, newly, skipped = [], [], []
    for name in sorted(os.listdir(src_skills)):
        src = os.path.join(src_skills, name)
        if not os.path.isdir(src) or not os.path.isfile(os.path.join(src, "SKILL.md")):
            continue
        src_names.add(name)
        dest = os.path.join(dest_dir, name)

        existed = os.path.exists(dest) or is_link_or_junction(dest)
        if existed and not is_link_or_junction(dest) and not os.path.isfile(os.path.join(dest, MARKER)):
            skipped.append(name)  # foreign, non-managed skill with same name -> don't clobber
            continue

        remove_dest(dest)
        try:
            shutil.copytree(src, dest)
        except Exception:
            continue
        try:
            with open(os.path.join(dest, MARKER), "w", encoding="utf-8") as fh:
                fh.write("Managed copy from {}\nDo not edit here; edit the source in the ia repo.\n".format(src))
        except Exception:
            pass
        add_git_exclude(repo_root, name)
        (refreshed if existed else newly).append(name)

    # Prune managed copies whose source skill no longer exists.
    pruned = []
    try:
        for name in sorted(os.listdir(dest_dir)):
            dest = os.path.join(dest_dir, name)
            if name in src_names:
                continue
            if os.path.isfile(os.path.join(dest, MARKER)):
                remove_dest(dest)
                pruned.append(name)
    except Exception:
        pass

    missing = missing_required_siblings(ia, project, repo_root)

    if not (refreshed or newly or skipped or pruned or missing):
        return

    parts = ["# Project skills for `{}` (copied by `common` from `{}`)".format(project, src_skills)]
    if refreshed:
        parts.append("Refreshed (invocable now): " + ", ".join("`{}`".format(n) for n in refreshed) + ".")
    if newly:
        parts.append(
            "Newly copied this session: " + ", ".join("`{}`".format(n) for n in newly) + ". "
            "Restart Claude Code or run `/reload-plugins` to make them invocable."
        )
    if skipped:
        parts.append("Skipped (a non-managed skill with the same name already exists): "
                     + ", ".join("`{}`".format(n) for n in skipped) + ".")
    if pruned:
        parts.append("Removed (no longer in the source): " + ", ".join("`{}`".format(n) for n in pruned) + ".")
    if missing:
        parent = os.path.dirname(os.path.normpath(repo_root))
        lines = ["⚠️ Missing sibling repo(s) that this project's skills need, expected next to "
                 "this clone under `{}`:".format(parent)]
        for name, reason in missing:
            lines.append("  - `{}`".format(name) + (" — {}".format(reason) if reason else ""))
        lines.append("Clone them there (or the skills that depend on them will fail).")
        parts.append("\n".join(lines))

    index = read_knowledge_index(src_skills)
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
